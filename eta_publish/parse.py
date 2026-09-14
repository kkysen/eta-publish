"""Build a `Document` tree from Google Docs API JSON.

The only module that knows the shape of the Docs API;
everything downstream sees the tree in `nodes.py`.

Several pieces of ETA house style are recognized here rather than in the emitters,
because they are facts about how the docs are written:

- a leading `Header` section carrying `Key: value` front matter
- the report headline living in the body as a `Title`-styled paragraph,
  since the Drive filename is a working name (`SAS West Feasibility Response`)
  and not what gets published
- a figure's `Source:` line between the image and its caption,
  with the caption and `Credit:` lines after that
"""

import re
from dataclasses import replace
from datetime import datetime
from urllib.parse import parse_qs, urlsplit

from .docs_json import JsonObject
from .naming import AnchorAllocator, image_filename, image_filenames, names_nothing
from .nodes import (
    Block,
    Crop,
    Document,
    Figure,
    Footnote,
    FootnoteRef,
    Heading,
    Image,
    Inline,
    LineBreak,
    List,
    Listed,
    ListItem,
    ListKind,
    Paragraph,
    Shown,
    Table,
    Text,
    Vector,
    document_url,
    plain_text,
    unwrap_snapshot,
)

HEADING_LEVELS = {
    "HEADING_1": 2,
    "HEADING_2": 3,
    "HEADING_3": 4,
    "HEADING_4": 5,
    "HEADING_5": 6,
    "HEADING_6": 6,
}

# Carry no content of their own, so dropping them loses nothing.
IGNORED_ELEMENTS = frozenset({"pageBreak", "columnBreak", "horizontalRule", "equation"})

# Ids the emitters generate for themselves, which no heading may take.
RESERVED_ANCHORS = frozenset({"footnotes", "contributors"})

# Docs writes a Shift+Enter line break as a vertical tab inside the run,
# a teletype control character for advancing the paper without returning the carriage.
# Nothing has used it for that in fifty years,
# and Docs uses it because its own model is the one it inherited:
# a paragraph is a run of text, so a break inside one cannot be structure
# and has to be a character, and the character set has exactly one spare.
SOFT_BREAK = "\v"


# Anything still marked unfinished, e.g. the real doc's `Source: TODO`.
# Not `TK`: these reports are not written with it,
# so here it would only ever match a word that happened to be spelled that way.
TODO_RE = re.compile(r"\b(?:TODO|FIXME|XXX)\b")


def _is_word(text: str) -> bool:
    """Whether `text` is a single word, the way a word boundary divides one."""
    return bool(text) and all(c.isalnum() or c == "_" for c in text)


# How much of a line a warning quotes back before it is just repeating the document.
CLIP = 60


def _clipped(line: str) -> str:
    """A line short enough to quote in a warning, cut on a word where it has to be."""
    if len(line) <= CLIP:
        return line
    return line[:CLIP].rsplit(" ", 1)[0] + "..."


def source_name(source: list[Inline]) -> str:
    """The file a `Source:` line names, or nothing if it names no file.

    The value after the colon:
    a Drive chip's title where the line links the file, plain text where it was typed.
    `Source: TODO` is a note rather than a name,
    and a bare URL names a page rather than a file,
    so neither becomes a filename.
    """
    text = plain_text(source)
    _, colon, value = text.partition(":")
    value = value.strip() if colon else ""
    if not value or TODO_RE.search(value) or value.startswith(("http:", "https:", "//")):
        return ""
    return value


def date_text(chip: JsonObject) -> str:
    """A date smart chip as the document shows it, e.g. `Aug 19, 2026`."""
    stamp = chip.get("dateElementProperties", {}).get("timestamp", "")
    try:
        # Docs writes the `Z` form, which `fromisoformat` has read since 3.11.
        moment = datetime.fromisoformat(stamp)
    except ValueError:
        return stamp
    # `%-d` avoids the zero padding Docs does not show.
    return moment.strftime("%b %-d, %Y")


def element_text(el: JsonObject) -> str:
    """The text an inline element contributes, smart chips included.

    Reading only `textRun` loses every chip.
    In the real report that emptied `Project Manager:` and all three date fields,
    and dropped the first name from `Public Contributors:`,
    leaving it starting with a comma.
    """
    if "textRun" in el:
        # A soft break is a line break, so it reads as one here too.
        return el["textRun"].get("content", "").replace(SOFT_BREAK, "\n")
    if "person" in el:
        props = el["person"].get("personProperties", {})
        return props.get("name") or props.get("email", "")
    if "dateElement" in el:
        return date_text(el["dateElement"])
    if "richLink" in el:
        return el["richLink"].get("richLinkProperties", {}).get("title", "")
    return ""


def strip_leading_space(blocks: list[Block]) -> list[Block]:
    """Drop the space Docs puts after a footnote's marker.

    It separates the marker from the text in the document
    rather than being part of what the note says,
    and left in it doubles the space after the number.
    """
    for block in blocks:
        if not isinstance(block, Paragraph) or not block.content:
            break
        first = block.content[0]
        if isinstance(first, Text):
            block.content[0] = replace(first, text=first.text.lstrip())
        break
    return blocks


def split_lines(content: list[Inline]) -> list[list[Inline]]:
    """Break inline content at soft line breaks."""
    lines: list[list[Inline]] = [[]]
    for node in content:
        if isinstance(node, LineBreak):
            lines.append([])
        else:
            lines[-1].append(node)
    return lines


def _normalized(text: str) -> str:
    """A section name as written, for matching a reference to it.

    Case and spacing vary between the heading and the sentence referring to it;
    anything more forgiving starts matching prose."""
    return " ".join(text.split()).casefold()


def plain(para: JsonObject) -> str:
    """The paragraph's text with styling dropped, for matching conventions."""
    return "".join(element_text(el) for el in para.get("elements", [])).strip()


def style_of(para: JsonObject) -> str:
    return para.get("paragraphStyle", {}).get("namedStyleType", "NORMAL_TEXT")


def has_image(para: JsonObject) -> bool:
    return any("inlineObjectElement" in el for el in para.get("elements", []))


class Parser:
    def __init__(self, doc_json: JsonObject) -> None:
        self.json = doc_json
        self.inline_objects: JsonObject = doc_json.get("inlineObjects", {})
        self.lists: JsonObject = doc_json.get("lists", {})
        self.footnote_defs: JsonObject = doc_json.get("footnotes", {})
        self.doc = Document()
        self.anchors = AnchorAllocator()
        self._heading_anchors: dict[str, str] = {}
        self._footnote_numbers: dict[str, int] = {}
        self._source_names: dict[str, str] = {}

    # ---- inline ------------------------------------------------------

    def inlines(self, para: JsonObject) -> list[Inline]:
        out: list[Inline] = []
        for el in para.get("elements", []):
            if "textRun" in el:
                out.extend(self._text_run(el["textRun"]))
            elif "footnoteReference" in el:
                out.append(self._footnote_ref(el["footnoteReference"]))
            elif "inlineObjectElement" in el:
                image = self._image(el["inlineObjectElement"])
                if image is not None:
                    out.append(image)
            elif "person" in el:
                out.append(self._person(el["person"]))
            elif "dateElement" in el:
                out.append(self._date(el["dateElement"]))
            elif "richLink" in el:
                out.append(self._rich_link(el["richLink"]))
            elif not (IGNORED_ELEMENTS & el.keys()):
                kinds = sorted(k for k in el if k not in ("startIndex", "endIndex"))
                self.doc.warn("unhandled document element {}, dropped", Shown(", ".join(kinds)))
        self._soft_breaks(para)
        # A soft break at either end is spacing rather than part of what the paragraph says,
        # and renders as a stray line break with nothing on one side of it.
        while out and isinstance(out[0], LineBreak):
            out.pop(0)
        while out and isinstance(out[-1], LineBreak):
            out.pop()
        return self.cross_references(out)

    def _soft_breaks(self, para: JsonObject) -> None:
        """Warn about a paragraph broken with Shift+Enter rather than Enter.

        Docs draws the two almost the same and stores them differently:
        Enter starts another paragraph, Shift+Enter writes a vertical tab
        inside this one. Nothing on the page says which is which,
        so nobody finds out until something reads the two lines as one,
        which is how this brief's `Short:` and `SEO Description:`
        went unpublished for sharing a paragraph.

        Both spellings still publish: the line break is emitted where it was written.
        The warning is that the document does not mean what it looks like it means.
        """
        text = "".join(el.get("textRun", {}).get("content", "") for el in para.get("elements", []))
        if SOFT_BREAK not in text:
            return
        lines = [line.strip() for line in text.strip().split(SOFT_BREAK)]
        written = [line for line in lines if line]
        if len(written) < 2:
            # Nothing on one side of it, so it is blank space rather than a break
            # between two things, and it is dropped rather than published.
            self.doc.warn(
                "a paragraph has a stray {} standing in for blank space; "
                "it is dropped, and a paragraph's spacing belongs in its style: {}",
                Shown("Shift+Enter"),
                Shown(_clipped(written[0]) if written else ""),
            )
            return
        self.doc.warn(
            "a paragraph is broken with {} rather than {}, "
            "so lines that look separate are one paragraph; give each line its own:{}",
            Shown("Shift+Enter"),
            Shown("Enter"),
            Listed(*((Shown(_clipped(line)),) for line in written)),
        )

    def cross_references(self, content: list[Inline]) -> list[Inline]:
        """Turn italicized section names into links to those sections.

        Google Docs cannot write a link to a heading in the same document,
        so ETA writes the section's name in italics and means a link by it.

        Matching is on the whole italic run, not on each styled piece of one,
        so a section name with a bold word in it still resolves.
        The italics come off: they stood in for the link, and now there is one.
        """
        if not self._heading_anchors:
            return content
        out: list[Inline] = []
        run: list[Text] = []

        def flush() -> None:
            anchor = self._heading_anchors.get(_normalized("".join(t.text for t in run)))
            if anchor is None:
                out.extend(run)
            else:
                out.extend(replace(t, italic=False, href=f"#{anchor}") for t in run)
            run.clear()

        for node in content:
            if isinstance(node, Text) and node.italic and node.href is None:
                run.append(node)
                continue
            flush()
            out.append(node)
        flush()
        return out

    def _person(self, chip: JsonObject) -> Text:
        """A person smart chip renders as the person's name.

        The chip also carries their email address:
        contact information the document happens to hold rather than something
        the report says, so it is not emitted.
        """
        props = chip.get("personProperties", {})
        return Text(text=props.get("name") or props.get("email", ""))

    def _date(self, chip: JsonObject) -> Text:
        """A date smart chip renders the way the document shows it."""
        text = date_text(chip)
        if not text:
            self.doc.warn("a date chip carries no timestamp; dropped")
        return Text(text=text)

    def _href(self, url: str | None) -> str | None:
        """A link as the tree holds it: the page it is of, not the capture of it.

        A `web.archive.org` URL typed into the document is a source already
        archived, so the wrapping comes off here and the capture it named is
        recorded as the one that source has. Doing it at the door means every
        output, the record, and the numbering all see one URL for one page,
        however the document happened to write it.
        """
        if url is None:
            return None
        original, archived = unwrap_snapshot(url)
        if archived is not None:
            # Keyed by the document, which is what was captured: one PDF cited
            # at fifteen of its pages is one entry in the record.
            self.doc.archives.setdefault(document_url(original), archived)
        return original

    def _rich_link(self, chip: JsonObject) -> Text:
        """A linked Drive file, which is how `Source:` lines name an asset."""
        props = chip.get("richLinkProperties", {})
        return Text(text=props.get("title", ""), href=self._href(props.get("uri")))

    def _text_run(self, run: JsonObject) -> list[Inline]:
        """One run, split at any soft line breaks it contains."""
        text = run.get("content", "")
        # A trailing newline is paragraph structure, not content.
        if text.endswith("\n"):
            text = text[:-1]
        if not text:
            return []
        style = run.get("textStyle", {})
        offset = style.get("baselineOffset")

        def styled(part: str) -> Text:
            return Text(
                text=part,
                bold=bool(style.get("bold")),
                italic=bool(style.get("italic")),
                underline=bool(style.get("underline")) and "link" not in style,
                sup=offset == "SUPERSCRIPT",
                sub=offset == "SUBSCRIPT",
                href=self._href(style.get("link", {}).get("url")),
            )

        out: list[Inline] = []
        for n, part in enumerate(text.split(SOFT_BREAK)):
            if n:
                out.append(LineBreak())
            if part:
                out.append(styled(part))
        return out

    def _footnote_ref(self, ref: JsonObject) -> FootnoteRef:
        fid = ref["footnoteId"]
        # Numbered in document order,
        # so a reference and its definition cannot disagree the way hand-written ones did.
        if fid not in self._footnote_numbers:
            self._footnote_numbers[fid] = len(self._footnote_numbers) + 1
        return FootnoteRef(footnote_id=fid, number=self._footnote_numbers[fid])

    def _image(self, ioe: JsonObject) -> Image | None:
        object_id = ioe.get("inlineObjectId", "")
        embedded = (
            self.inline_objects.get(object_id, {})
            .get("inlineObjectProperties", {})
            .get("embeddedObject", {})
        )
        if "imageProperties" not in embedded:
            self.doc.warn("inline object {} has no image; skipped", Shown(object_id))
            return None
        image_props = embedded["imageProperties"]
        # `contentUri` says where to fetch this image, not whether it is one:
        # a saved response has none, since they expire and are dropped rather
        # than committed, and everything but the download still works.
        uri = image_props.get("contentUri")
        crop = self._crop(object_id, image_props.get("cropProperties", {}))
        return Image(
            object_id=object_id,
            filename=image_filename(object_id, crop_key=crop.key),
            alt=embedded.get("description") or embedded.get("title") or "",
            source_uri=uri,
            crop=crop,
        )

    # Where a Drive link keeps the file id, in either shape Docs produces.
    DRIVE_PATH = "/file/d/"
    DRIVE_QUERY = "id"

    @classmethod
    def _drive_id(cls, uri: str) -> str:
        """The Drive file id a link names, or nothing where it names none."""
        split = urlsplit(uri)
        _, found, rest = split.path.partition(cls.DRIVE_PATH)
        if found:
            return rest.partition("/")[0]
        ids = parse_qs(split.query).get(cls.DRIVE_QUERY, [])
        return ids[0] if ids else ""

    def _vector(self, para: JsonObject) -> Vector | None:
        """The vector original a `SVG:` line links, if it links one.

        Only a link to Drive counts.
        `SVG: TODO` is a note, with nothing to publish for it.
        """
        for el in para.get("elements", []):
            props = el.get("richLink", {}).get("richLinkProperties", {})
            uri = props.get("uri", "")
            if not uri or "image/svg" not in props.get("mimeType", ""):
                continue
            file_id = self._drive_id(uri)
            if not file_id:
                self.doc.warn("cannot read a Drive file id from {}; the raster is used", Shown(uri))
                continue
            title = props.get("title", "")
            return Vector(
                file_id=file_id,
                # Drive's name for the linked file names the picture,
                # the same as a `Source:` line does.
                # No crop key: the crop is applied to pixels.
                filename=image_filename(file_id, extension=".svg", name=title),
                title=title,
                uri=uri,
            )
        return None

    def _crop(self, object_id: str, props: JsonObject) -> Crop:
        """How much of the image the document trims from each side.

        Docs stores tiny negative offsets for an edge that is not trimmed,
        so the values are clamped rather than trusted.
        """
        if props.get("angle"):
            self.doc.warn(
                "image {} is rotated in the document; the rotation is not applied",
                Shown(object_id),
            )

        def side(name: str) -> float:
            return max(0.0, min(1.0, float(props.get(name, 0.0) or 0.0)))

        return Crop(
            left=side("offsetLeft"),
            right=side("offsetRight"),
            top=side("offsetTop"),
            bottom=side("offsetBottom"),
        )

    # ---- lists -------------------------------------------------------

    def _list_kind(self, list_id: str, level: int) -> ListKind:
        levels = self.lists.get(list_id, {}).get("listProperties", {}).get("nestingLevels", [])
        glyph = levels[level] if level < len(levels) else {}
        numbered = glyph.get("glyphType") not in (None, "GLYPH_TYPE_UNSPECIFIED")
        return ListKind.NUMBER if numbered else ListKind.BULLET

    def _consume_list(self, content: list[JsonObject], start: int) -> tuple[List, int]:
        """Absorb the run of consecutive bulleted paragraphs starting at `start`.

        Docs gives each paragraph a flat `nestingLevel` rather than nesting them,
        so the tree is rebuilt here with a stack of sibling lists.
        """
        list_id = content[start]["paragraph"]["bullet"].get("listId", "")
        root: list[ListItem] = []
        stack: list[list[ListItem]] = [root]

        i = start
        while i < len(content):
            para = content[i].get("paragraph")
            if para is None or "bullet" not in para:
                break
            if para["bullet"].get("listId", "") != list_id:
                break

            level = para["bullet"].get("nestingLevel", 0)
            while len(stack) > level + 1:
                stack.pop()
            while len(stack) < level + 1:
                siblings = stack[-1]
                if not siblings:
                    # Docs permits an indented item with no item above it.
                    siblings.append(ListItem())
                stack.append(siblings[-1].children)
            stack[-1].append(ListItem(content=self.inlines(para)))
            i += 1

        return List(kind=self._list_kind(list_id, 0), items=root), i

    # ---- blocks ------------------------------------------------------

    # Editorial notes naming where an image came from, none of which is published.
    # The real report uses four spellings:
    # `Source:` under an image, `Uncropped Source:` for one that was trimmed,
    # and, after a caption,
    # either `[Image Source](<url>)` or a bare `Image Source` whose whole text is the link.
    # One optional qualifying word covers all of them and whatever the next one is.
    SOURCE_LABEL = "source"

    # The same idea for chart assets: `SVG:` and `PNG:` name the file to link beside a figure.
    # Notes to whoever assembles the page; the published report carries real links.
    ASSET_LABELS = frozenset({"svg", "png", "pdf"})

    CREDIT_LABEL = "credit"

    # What ends a label: a colon where the line was typed,
    # a bracket where the label is the text of a link.
    LABEL_MARKS = ":]"

    @staticmethod
    def _labelled(line: str) -> tuple[str, str]:
        """A note line read as the label it is headed with and the mark that ends it.

        `Uncropped Source:` is `("uncropped source", ":")`
        and `[Image Source]` is `("image source", "]")`.
        A line with neither mark is all label and an empty mark,
        which only the bare spelling is allowed to be.

        The opening bracket is optional for every label, not only the linked ones.
        Wider than the lines the reports actually write,
        deliberately: a bracketed `[SVG: ...]` is the note it looks like,
        and publishing it as prose because of the bracket helps nobody.
        """
        head = line.lstrip().removeprefix("[").lstrip()
        for index, character in enumerate(head):
            if character in Parser.LABEL_MARKS:
                return head[:index].strip().casefold(), character
        return head.strip().casefold(), ""

    @classmethod
    def _is_source(cls, line: str) -> bool:
        """Whether `line` is a `Source:` note rather than prose.

        The bare spelling needs no mark, which is why the label has to be
        the whole of what precedes it:
        a paragraph beginning "Source of the estimate is ..." is prose,
        and only one saying nothing but "Image Source" is a note.
        """
        label, _ = cls._labelled(line)
        words = label.split()
        if not words or words[-1] != cls.SOURCE_LABEL:
            return False
        # The qualifier is one word: `Uncropped Source`, `Image Source`.
        # Anything else before the label is a sentence that happens to end in it.
        return len(words) == 1 or (len(words) == 2 and _is_word(words[0]))

    @classmethod
    def _is_asset(cls, line: str) -> bool:
        """Whether `line` is a `SVG:`/`PNG:`/`PDF:` note.

        A colon and nothing else: these are typed, never linked,
        and a bare `PDF` is a word.
        """
        label, mark = cls._labelled(line)
        return mark == ":" and label in cls.ASSET_LABELS

    @classmethod
    def _is_credit(cls, line: str) -> bool:
        """Whether `line` is a `Credit:` note. Never bare, for the same reason."""
        label, mark = cls._labelled(line)
        return bool(mark) and label == cls.CREDIT_LABEL

    def blocks(self, content: list[JsonObject]) -> list[Block]:
        out: list[Block] = []
        pending_source: list[Inline] | None = None
        # 1 while the paragraph directly after a figure is still unclaimed.
        caption_slot = 0

        def drop_pending() -> None:
            nonlocal pending_source
            if pending_source is not None:
                text = plain_text(pending_source)
                self.doc.warn(
                    "{} line not followed by an image, dropped: {}",
                    Shown("Source:"),
                    Shown(text[:80]),
                )
                pending_source = None

        i = 0
        while i < len(content):
            item = content[i]

            if "table" in item:
                drop_pending()
                caption_slot = 0
                out.append(self.table(item["table"]))
                i += 1
                continue

            para = item.get("paragraph")
            if para is None:
                i += 1
                continue

            if "bullet" in para:
                drop_pending()
                caption_slot = 0
                node, i = self._consume_list(content, i)
                out.append(node)
                continue

            i += 1
            style = style_of(para)
            text = plain(para)

            if not text and not has_image(para):
                caption_slot = 0
                continue

            if style in HEADING_LEVELS and not text and has_image(para):
                # An image inserted while a heading style was still active.
                # Treating it as a heading yields an empty one
                # whose anchor is a published URL, and buries the image inside it.
                self.doc.warn(
                    "an image is styled as a {}; treating it as a figure. "
                    "Set that paragraph to {} in the doc.",
                    Shown("Heading"),
                    Shown("Normal text"),
                )
                style = "NORMAL_TEXT"

            if style in HEADING_LEVELS:
                drop_pending()
                caption_slot = 0
                out.append(
                    Heading(
                        level=HEADING_LEVELS[style],
                        anchor=self.anchors.allocate(text),
                        content=self.inlines(para),
                    )
                )
                continue

            if TODO_RE.search(text):
                self.doc.warn("unfinished text in the document: {}", Shown(text[:80]))

            if self._is_source(text) or self._is_asset(text):
                last = out[-1] if out else None
                if isinstance(last, Figure):
                    # A source line after a figure sits between the image and
                    # its caption, so it belongs to the figure above it.
                    note = self.inlines(para)
                    last.source = last.source + note
                    self._claim_name(last, note)
                    self._attach_vector(last, para)
                    continue
                drop_pending()
                pending_source = self.inlines(para)
                caption_slot = 0
                continue

            if has_image(para):
                figure = Figure(image=self._only_image(para), source=pending_source or [])
                self._claim_name(figure, pending_source or [])
                out.append(figure)
                pending_source = None
                caption_slot = 1
                continue

            # A caption is the one paragraph directly after a figure;
            # `Credit:` lines keep attaching after that.
            # Matching on length would swallow short body paragraphs,
            # and a report with 50-odd figures has a great many.
            last = out[-1] if out else None
            if isinstance(last, Figure):
                # A caption and its credit are often one paragraph split by a soft line break,
                # so each line is classified separately.
                claimed = False
                # Read once: a caption that turns out to be prose is emitted below,
                # and parsing it twice says everything it has to say twice.
                inlines = self.inlines(para)
                for line in split_lines(inlines):
                    line_text = plain_text(line).strip()
                    if not line_text:
                        continue
                    if self._is_credit(line_text):
                        last.credit = line
                        claimed = True
                    elif self._is_source(line_text) or self._is_asset(line_text):
                        last.source = last.source + line
                        self._claim_name(last, line)
                        claimed = True
                    elif caption_slot:
                        last.caption = line
                        caption_slot = 0
                        claimed = True
                if claimed:
                    continue

            else:
                inlines = self.inlines(para)

            caption_slot = 0
            out.append(Paragraph(content=inlines))

        drop_pending()
        for block in out:
            if isinstance(block, Figure) and not block.image.alt and not block.caption:
                self.doc.warn(
                    "image {} has no alt text and no caption; add a description to it in the doc",
                    Shown(block.image.object_id),
                )
            if isinstance(block, Figure) and not block.image.alt and block.caption:
                # The published page uses the caption as alt text as well as showing it,
                # so an image with no description in Docs is not left unlabelled.
                caption = plain_text(block.caption)
                block.image = replace(block.image, alt=caption.strip())
        return out

    def _claim_name(self, figure: Figure, source: list[Inline]) -> None:
        """Note what a source line calls this figure's image, if it calls it anything.

        Kept until the whole document has been read rather than applied here:
        what an image ends up called
        depends on whether another one further down names the same file.

        The first line to name a file wins, so a figure with both a `Source:`
        and an `Image Source` link takes its name from the `Source:`.
        """
        name = source_name(source)
        if name:
            self._source_names.setdefault(figure.image.object_id, name)

    def _attach_vector(self, figure: Figure, para: JsonObject) -> None:
        """Promote a `SVG:` line's link from a note to the figure's file."""
        vector = self._vector(para)
        if vector is None:
            return
        if figure.image.crop.trims:
            self.doc.warn(
                "image {} is both cropped and given a vector original; "
                "the crop cannot be applied to it, so the raster is used",
                Shown(figure.image.object_id),
            )
            return
        figure.image = replace(figure.image, vector=vector)

    def _only_image(self, para: JsonObject) -> Image:
        inlines = self.inlines(para)
        images = [i for i in inlines if isinstance(i, Image)]
        if len(images) > 1:
            self.doc.warn(
                f"{len(images)} images share one paragraph; only the first becomes a figure"
            )
        prose = plain_text(inlines).strip()
        if prose:
            self.doc.warn(
                "text sharing a paragraph with an image was dropped: {}", Shown(prose[:80])
            )
        return images[0]

    def table(self, table: JsonObject) -> Table:
        return Table(
            rows=[
                [self.blocks(cell.get("content", [])) for cell in row.get("tableCells", [])]
                for row in table.get("tableRows", [])
            ]
        )

    # ---- document ----------------------------------------------------

    def _split_at_title(
        self, content: list[JsonObject]
    ) -> tuple[list[JsonObject], list[JsonObject]]:
        """What sits above the headline, and the report itself below it.

        A document with no headline has nothing above it: everything is the report.
        """
        for i, item in enumerate(content):
            if "paragraph" in item and style_of(item["paragraph"]) == "TITLE":
                return content[:i], content[i + 1 :]
        return [], content

    def card(self, above: list[JsonObject]) -> Image | None:
        """The share card, which is an image the document puts above the headline.

        ETA reports open with a wide image with the title set into it,
        for whatever is linking to the report to show as a thumbnail.
        It is metadata, publishing as `og:image` rather than as a figure,
        and recognized by position, since an image above the headline
        is not in the report.
        """
        for item in above:
            para = item.get("paragraph")
            if para is None:
                continue
            for el in para.get("elements", []):
                if "inlineObjectElement" not in el:
                    continue
                image = self._image(el["inlineObjectElement"])
                if image is not None:
                    return image
        return None

    KEY_RE = re.compile(r"^(?P<key>[A-Z][^:\n]{0,60}?)\s*:\s*(?P<value>.*)$")

    def front_matter(self, content: list[JsonObject]) -> list[JsonObject]:
        """Consume the leading `Header` section into `doc.meta`.

        Front matter is the run of `Key: value` paragraphs following the `Header` heading.
        It ends at the first paragraph that is not one:
        a heading of any level, the `Title`-styled headline,
        a paragraph holding an image, or ordinary prose.

        Not "until the next heading of the same or higher level".
        In the real doc `Header` is an `h2` while the body sections are `h1`,
        so that rule runs past the headline and the hero image to the first
        body section, and the image would vanish without a warning.

        Unrecognized keys are kept rather than ending the scan,
        so adding a header field to a future report cannot leak that line into the body.

        Anything before `Header` is production scaffolding rather than the report,
        and is dropped, one reported line at a time.
        A document with no `Header` at all is left untouched
        instead of being eaten a paragraph at a time.
        """
        start = self._header_index(content)
        if start is None:
            self.doc.warn(
                "no front matter found; expected a leading {} section with {}, {}, and {} lines",
                Shown("Header"),
                Shown("URL:"),
                Shown("Short:"),
                Shown("SEO Description:"),
            )
            return content

        self.doc.has_header = True

        for item in content[:start]:
            para = item.get("paragraph")
            text = plain(para) if para is not None else ""
            if text:
                self.doc.warn(
                    "dropped a line before the {} section: {}",
                    Shown("Header"),
                    Shown(text[:80]),
                )

        end = start + 1
        for i in range(start + 1, len(content)):
            para = content[i].get("paragraph")
            if para is None:
                break

            style = style_of(para)
            text = plain(para)

            if style == "TITLE" or HEADING_LEVELS.get(style) is not None or has_image(para):
                break

            if not text:
                end = i + 1
                continue

            # The header section never reaches `inlines`, so it says this for itself.
            self._soft_breaks(para)

            # A paragraph can hold more than one field:
            # the real brief writes `Short:` and `SEO Description:`
            # with a Shift+Enter between them rather than a paragraph break.
            # The two read alike in the document and are not alike here,
            # so every line of the paragraph is considered, not just the first.
            lines = text.split("\n")
            if self.KEY_RE.match(lines[0]) is None:
                break  # prose: the header section is over

            key = ""
            for line in lines:
                match = self.KEY_RE.match(line)
                if match is None:
                    # A line that names no field continues the value above it.
                    # Ending the scan here would drop the rest of the paragraph,
                    # and every field after it, over a value that merely wrapped.
                    self.doc.meta[key] = f"{self.doc.meta[key]} {line}".strip()
                    continue
                key = self._meta_line(match)
            end = i + 1

        if not self.doc.meta:
            self.doc.warn(
                "the {} section holds no {} lines; expected {}, {}, and {}",
                Shown("Header"),
                Shown("Key: value"),
                Shown("URL:"),
                Shown("Short:"),
                Shown("SEO Description:"),
            )
        return content[end:]

    # A note to whoever fills the field in, not part of its name.
    # The real doc writes `SEO Description (300 char limit):`,
    # and a lookup for `seo description` finds nothing unless the note is stripped.
    KEY_NOTE_RE = re.compile(r"\s*\([^)]*\)\s*$")

    def _meta_line(self, match: re.Match[str]) -> str:
        """Record one `Key: value` header line, and answer which key it set."""
        written = self.KEY_NOTE_RE.sub("", match.group("key").strip())
        key = written.lower()
        value = match.group("value").strip()
        if key in self.doc.meta:
            # The later line wins, and says so: a corrected line pasted
            # below the original and a duplicate nobody meant look
            # identical, and neither is visible in what gets published.
            # Matched on the key as it is read, so a `Short:` and a
            # `Short (60 char limit):` count as the two they are.
            self.doc.warn(
                "the {} section has more than one {} line; using {} and ignoring {}",
                Shown("Header"),
                Shown(f"{written}:"),
                Shown(value),
                Shown(self.doc.meta[key]),
            )
        self.doc.meta[key] = value
        return key

    def _header_index(self, content: list[JsonObject]) -> int | None:
        """Where the `Header` heading is, if the report has one.

        Found before anything is consumed, so a document without one is left untouched.
        The search stops at the headline or the first figure,
        since past either the report has already started.
        """
        for i, item in enumerate(content):
            para = item.get("paragraph")
            if para is None:
                continue
            style = style_of(para)
            if HEADING_LEVELS.get(style) is not None and plain(para).strip().lower() == "header":
                return i
            if style == "TITLE" or has_image(para):
                return None
        return None

    def title(self, content: list[JsonObject]) -> str:
        """The headline, which is the `Title`-styled paragraph and only that.

        Not a `Title:` line in the `Header` section as well:
        the style is the one that shows, where a headline set in the header
        is one nobody reading the document sees at the top of it.

        The Drive filename is the last resort and a warning, not a third way:
        it is a working name, and the SAS West report lives in a doc called
        `SAS West Feasibility Response`.
        """
        for item in content:
            para = item.get("paragraph")
            if para is not None and style_of(para) == "TITLE" and plain(para):
                return plain(para)

        filename = self.json.get("title", "")
        self.doc.warn(
            "no {}-styled paragraph, so the document name {} is being used as the "
            "headline; style the headline as {} in the doc",
            Shown("Title"),
            Shown(filename),
            Shown("Title"),
        )
        if self.doc.meta.get("title"):
            # Said separately, because it is a different thing to fix:
            # the headline is written down, in a line that does not set it.
            self.doc.warn(
                "the {} section has {}, which is not what the headline comes from; "
                "style that line as {} in the body instead",
                Shown("Header"),
                Shown(f"Title: {self.doc.meta['title']}"),
                Shown("Title"),
            )
        return filename

    def footnotes(self) -> list[Footnote]:
        """Only footnotes the body actually references, in reference order.

        A definition with no reference cannot be numbered,
        so it is reported rather than emitted with a number that means nothing.
        """
        for fid in self.footnote_defs:
            if fid not in self._footnote_numbers:
                self.doc.warn("footnote {} is defined but never referenced; omitted", Shown(fid))
        return [
            Footnote(
                footnote_id=fid,
                number=number,
                content=strip_leading_space(
                    self.blocks(self.footnote_defs.get(fid, {}).get("content", []))
                ),
            )
            for number, fid in sorted(
                (number, fid) for fid, number in self._footnote_numbers.items()
            )
        ]

    def parse(self) -> Document:
        content: list[JsonObject] = self.json.get("body", {}).get("content", [])
        content = self.front_matter(content)
        self.doc.title = self.title(content)
        self.doc.file_title = self.json.get("title", "")
        self.doc.tab_title = self.json.get("tabTitle", "")
        read_review(self.doc, self.json)

        # Allocated knowing every heading up front,
        # so two headings that slugify alike keep their anchors when the document reorders.
        heading_texts = [
            plain(item["paragraph"])
            for item in content
            if "paragraph" in item and style_of(item["paragraph"]) in HEADING_LEVELS
        ]
        self.anchors = AnchorAllocator(heading_texts, reserved=RESERVED_ANCHORS)
        # Built before the body is walked,
        # because a section can be referred to from above itself:
        # the report links to `Station Depth` long before reaching it.
        self._heading_anchors = {}
        for text in heading_texts:
            if not text:
                continue
            anchor = self.anchors.allocate(text)
            self._heading_anchors.setdefault(_normalized(text), anchor)
            # The part before the colon names the section and the part after
            # describes it, so `Appendix A: Freedom Tunnel` is referred to as
            # `Appendix A`.
            name, colon, _ = text.partition(":")
            if colon and name.strip():
                self._heading_anchors.setdefault(_normalized(name), anchor)

        above, below = self._split_at_title(content)
        self.doc.card = self.card(above)
        self.doc.blocks = self.blocks(below)
        # After the body, so that every reference has been numbered.
        self.doc.footnotes = self.footnotes()
        # Last, because a name is only known to be unambiguous
        # once every image in the document has claimed one.
        self._name_images()
        return self.doc

    def _name_images(self) -> None:
        """Rename every figure the document named a source file for.

        Settled here rather than where the images are read,
        because an image's name depends on what the other images are called,
        and the report goes on naming them for several pages after the first is built.

        Only figures: a source line is written above a figure,
        so an image inside a paragraph keeps the name it was given.
        """
        names = image_filenames(
            (image.object_id, image.crop.key, self._source_names.get(image.object_id, ""))
            for image in self.doc.images
        )
        for figure in self.doc.figures:
            claimed = self._source_names.get(figure.image.object_id, "")
            figure.image = replace(
                figure.image,
                filename=names[figure.image.object_id],
                named=not names_nothing(claimed),
            )


def read_review(doc: Document, document: JsonObject) -> None:
    """Tell `doc` what the fetch recorded about the editing still open on it.

    Its own function because it is read twice:
    once when the response is parsed,
    and again once a run that could not read it
    has carried the last answer over from the saved one.
    """
    doc.open_suggestions = int(document.get("openSuggestions", 0))
    doc.open_comments = int(document.get("openComments", 0))


def parse(doc_json: JsonObject) -> Document:
    return Parser(doc_json).parse()
