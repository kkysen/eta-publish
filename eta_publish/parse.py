"""Build a `Document` tree from Google Docs API JSON.

The only module that knows the shape of the Docs API;
everything downstream sees the tree in `nodes.py`.

Several pieces of ETA house style are recognized here rather than in the emitters,
because they are facts about how the docs are written:

- a leading `Header` section carrying `Key: value` front matter
- the report headline living in the body as a TITLE-styled paragraph,
  since the Drive filename is a working name (`SAS West Feasibility Response`)
  and not what gets published
- a figure's `Source:` line between the image and its caption,
  with the caption and `Credit:` lines after that
"""

import re
from dataclasses import replace
from datetime import datetime

from .docs_json import JsonObject
from .naming import AnchorAllocator, image_filename, image_filenames
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
    ListItem,
    ListKind,
    Paragraph,
    Table,
    Text,
    Vector,
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

# Docs writes a Shift+Enter line break as a vertical tab inside the run.
SOFT_BREAK = "\v"

KEY_RE = re.compile(r"^(?P<key>[A-Z][^:\n]{0,60}?)\s*:\s*(?P<value>.*)$")
# A note to whoever fills the field in, not part of its name.
# The real doc writes `SEO Description (300 char limit):`,
# and a lookup for `seo description` finds nothing unless the note is stripped.
KEY_NOTE_RE = re.compile(r"\s*\([^)]*\)\s*$")
# Editorial notes naming where an image came from.
# The real report uses four spellings:
# `Source:` under an image, `Uncropped Source:` for one that was trimmed,
# and, after a caption,
# either `[Image Source](<url>)` or a bare `Image Source` whose whole text is the link.
# The first two name a file, and the published image is named after it.
# One optional qualifying word covers all of them and whatever the next one is.
# None appears on the published page, which is what makes them notes rather than content:
# the live SAS West report has zero occurrences of each, against 26 of `Credit:`.
#
# The trailing `$` admits the bare spelling,
# and is why the alternative before it is anchored rather than merely a prefix:
# a paragraph beginning "Source of the estimate is ..." is prose,
# and only one saying nothing but "Image Source" is a note.
SOURCE_RE = re.compile(r"^\s*\[?\s*(?:\w+\s+)?source\s*(?:[:\]]|$)", re.IGNORECASE)

# A Drive file id, from either shape of link Docs produces.
DRIVE_ID_RE = re.compile(r"/file/d/([\w-]+)|[?&]id=([\w-]+)")

# The same idea for chart assets: `SVG:` and `PNG:` name the file to link beside a figure.
# Notes to whoever assembles the page; the published report carries real links.
ASSET_RE = re.compile(r"^\s*(?:svg|png|pdf)\s*:", re.IGNORECASE)

# Anything still marked unfinished.
# The real doc has `Source: TODO` and `SVG: TODO`,
# fine while drafting and not fine on a published page,
# so they are worth one loud line before publishing.
# Not `TK`: it is a newsroom's mark for copy still owed,
# and it is not one these reports are written with,
# so here it would only ever match a word that happened to be spelled that way.
TODO_RE = re.compile(r"\bTODO\b|\bFIXME\b|\bXXX\b")
CREDIT_RE = re.compile(r"^\s*\[?\s*Credit\s*[:\]]", re.IGNORECASE)


def source_name(source: list[Inline]) -> str:
    """The file a `Source:` line names, or nothing if it names no file.

    The value after the colon:
    a Drive chip's title where the line links the file, plain text where it was typed.
    `Source: TODO` is a note rather than a name,
    and a bare URL names a page rather than a file,
    so neither becomes a filename.
    """
    text = "".join(i.text for i in source if isinstance(i, Text))
    _, colon, value = text.partition(":")
    value = value.strip() if colon else ""
    if not value or TODO_RE.search(value) or value.startswith(("http:", "https:", "//")):
        return ""
    return value


def date_text(chip: JsonObject) -> str:
    """A date smart chip as the document shows it, e.g. `Aug 19, 2026`."""
    stamp = chip.get("dateElementProperties", {}).get("timestamp", "")
    try:
        moment = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
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

    Every footnote body in the real report begins with one:
    it separates the marker from the text in the document
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
                self.doc.warn(f"unhandled document element {kinds}, dropped")
        # A soft break at either end is spacing rather than part of what the paragraph says,
        # and renders as a stray line break with nothing on one side of it.
        while out and isinstance(out[0], LineBreak):
            out.pop(0)
        while out and isinstance(out[-1], LineBreak):
            out.pop()
        return self.cross_references(out)

    def cross_references(self, content: list[Inline]) -> list[Inline]:
        """Turn italicized section names into links to those sections.

        Google Docs cannot write a link to a heading in the same document,
        so ETA writes the section's name in italics and means a link by it.
        The live report has these all through it, `See Station Depth`,
        each a dead end: a name, italicized, pointing nowhere. One was linked by hand.

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

    def _rich_link(self, chip: JsonObject) -> Text:
        """A linked Drive file, which is how `Source:` lines name an asset."""
        props = chip.get("richLinkProperties", {})
        return Text(text=props.get("title", ""), href=props.get("uri"))

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
                href=style.get("link", {}).get("url"),
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
            self.doc.warn(f"inline object {object_id} has no image; skipped")
            return None
        image_props = embedded["imageProperties"]
        # `contentUri` says where to fetch this image, not whether it is one.
        # A saved response has none: they expire, so they are dropped rather than committed.
        # The image is still an image, and its filename comes from the object id,
        # so everything but the download works from a response with no URIs.
        uri = image_props.get("contentUri")
        crop = self._crop(object_id, image_props.get("cropProperties", {}))
        return Image(
            object_id=object_id,
            filename=image_filename(object_id, crop_key=crop.key),
            alt=embedded.get("description") or embedded.get("title") or "",
            source_uri=uri,
            crop=crop,
        )

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
            match = DRIVE_ID_RE.search(uri)
            if match is None:
                self.doc.warn(f"cannot read a Drive file id from {uri}; the raster is used")
                continue
            file_id = match.group(1) or match.group(2)
            title = props.get("title", "")
            return Vector(
                file_id=file_id,
                # The `SVG:` line links the file,
                # so Drive's name for it is the document naming this picture,
                # the same as a `Source:` line does.
                # A vector is never cropped: the crop is applied to pixels,
                # and an image with both is refused above.
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
                f"image {object_id} is rotated in the document; the rotation is not applied"
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

    def blocks(self, content: list[JsonObject]) -> list[Block]:
        out: list[Block] = []
        pending_source: list[Inline] | None = None
        # 1 while the paragraph directly after a figure is still unclaimed.
        caption_slot = 0

        def drop_pending() -> None:
            nonlocal pending_source
            if pending_source is not None:
                text = "".join(i.text for i in pending_source if isinstance(i, Text))
                self.doc.warn(f"`Source:` line not followed by an image, dropped: {text[:80]}")
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
                    "an image is styled as a heading; treating it as a figure. "
                    "Set that paragraph to normal text in the doc."
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
                self.doc.warn(f"unfinished text in the document: {text[:80]}")

            if SOURCE_RE.match(text) or ASSET_RE.match(text):
                last = out[-1] if out else None
                if isinstance(last, Figure):
                    # The `[Image Source](...)` spelling follows its figure,
                    # and so, in this report, does every `Source:` line:
                    # the note sits between the image and its caption.
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
                for line in split_lines(self.inlines(para)):
                    line_text = "".join(i.text for i in line if isinstance(i, Text)).strip()
                    if not line_text:
                        continue
                    if CREDIT_RE.match(line_text):
                        last.credit = line
                        claimed = True
                    elif SOURCE_RE.match(line_text) or ASSET_RE.match(line_text):
                        last.source = last.source + line
                        self._claim_name(last, line)
                        claimed = True
                    elif caption_slot:
                        last.caption = line
                        caption_slot = 0
                        claimed = True
                if claimed:
                    continue

            caption_slot = 0
            out.append(Paragraph(content=self.inlines(para)))

        drop_pending()
        for block in out:
            if isinstance(block, Figure) and not block.image.alt and not block.caption:
                # No alt text in Docs and no caption to borrow,
                # so screen readers get an unlabelled image.
                self.doc.warn(
                    f"image {block.image.object_id} has no alt text and no caption; "
                    "add a description to it in the doc"
                )
            if isinstance(block, Figure) and not block.image.alt and block.caption:
                # The published page uses the caption as alt text as well as showing it,
                # so an image with no description in Docs is not left unlabelled.
                caption = "".join(i.text for i in block.caption if isinstance(i, Text))
                block.image = replace(block.image, alt=caption.strip())
        return out

    def _claim_name(self, figure: Figure, source: list[Inline]) -> None:
        """Note what a source line calls this figure's image, if it calls it anything.

        Kept until the whole document has been read rather than applied here:
        what an image ends up called
        depends on whether another one further down names the same file.

        The first line to name a file wins.
        A figure with both a `Source:` and an `Image Source` link
        names the file once and links to where it came from once,
        and only the first is a name.
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
                f"image {figure.image.object_id} is both cropped and given a vector "
                "original; the crop cannot be applied to it, so the raster is used"
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
        prose = "".join(i.text for i in inlines if isinstance(i, Text)).strip()
        if prose:
            self.doc.warn(f"text sharing a paragraph with an image was dropped: {prose[:80]}")
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
        Not part of the report: the published page does not show it,
        and a reader who is already reading
        does not need the title again in a picture.

        So it is metadata, publishing as `og:image` rather than as a figure.
        Recognized by position, because that is what the document already says:
        an image above the headline is not in the report.

        Nothing warns about it lacking alt text or a caption:
        it has no business having either, and both warnings were about figures.
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

    def front_matter(self, content: list[JsonObject]) -> list[JsonObject]:
        """Consume the leading `Header` section into `doc.meta`.

        Front matter is the run of `Key: value` paragraphs following the `Header` heading.
        It ends at the first paragraph that is not one:
        a heading of any level, the TITLE-styled headline,
        a paragraph holding an image, or ordinary prose.

        Not "until the next heading of the same or higher level".
        In the real doc `Header` is an `h2` while the body sections are `h1`,
        so that rule runs past the headline, the hero image,
        its caption and credit, and the addendum, to the first body section.
        The image would vanish without a warning,
        since a paragraph holding only an image has no text to report.

        Unrecognized keys are kept rather than ending the scan,
        so adding a header field to a future report cannot leak that line into the body.
        The real doc already has one (`MTA SAS West Feasibility Study:`).

        Anything before `Header` is production scaffolding rather than the report.
        It is dropped, but each dropped line is reported.
        The SAS West tabs open with `Header` directly, so that part is defensive;
        what is load bearing is that a document with no `Header` at all
        is left untouched instead of being eaten a paragraph at a time.
        """
        start = self._header_index(content)
        if start is None:
            self.doc.warn(
                "no front matter found; expected a leading `Header` section with "
                "`URL:`, `Short:`, and `SEO Description:` lines"
            )
            return content

        for item in content[:start]:
            para = item.get("paragraph")
            text = plain(para) if para is not None else ""
            if text:
                self.doc.warn(f"dropped a line before the `Header` section: {text[:80]}")

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

            match = KEY_RE.match(text)
            if match is None:
                break  # prose: the header section is over

            key = KEY_NOTE_RE.sub("", match.group("key").strip()).lower()
            self.doc.meta[key] = match.group("value").strip()
            end = i + 1

        if not self.doc.meta:
            self.doc.warn(
                "the `Header` section holds no `Key: value` lines; expected "
                "`URL:`, `Short:`, and `SEO Description:`"
            )
        return content[end:]

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
        """Prefer a TITLE-styled paragraph over the Drive filename.

        The filename is a working name:
        the SAS West report lives in a doc called `SAS West Feasibility Response`.
        """
        for item in content:
            para = item.get("paragraph")
            if para is not None and style_of(para) == "TITLE" and plain(para):
                return plain(para)
        if self.doc.meta.get("title"):
            return self.doc.meta["title"]
        filename = self.json.get("title", "")
        self.doc.warn(
            "no TITLE-styled paragraph and no `Title:` header field, so the "
            f"document name {filename!r} is being used as the headline; "
            "style the headline as Title in the doc to fix this"
        )
        return filename

    def footnotes(self) -> list[Footnote]:
        """Only footnotes the body actually references, in reference order.

        A definition with no reference cannot be numbered,
        so it is reported rather than emitted with a number that means nothing.
        """
        for fid in self.footnote_defs:
            if fid not in self._footnote_numbers:
                self.doc.warn(f"footnote {fid} is defined but never referenced; omitted")
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
        self.doc.open_suggestions = int(self.json.get("openSuggestions", 0))
        self.doc.open_comments = int(self.json.get("openComments", 0))

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
            # `Appendix A: Freedom Tunnel` is referred to as `Appendix A`,
            # and `Ruling Grade: The Wrong Place to Scale Back` as `Ruling Grade`.
            # The part before the colon names the section and the part after describes it,
            # so a reference using only the name is naming this heading.
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
        so an image inside a paragraph is never named and keeps the name it was given.
        """
        names = image_filenames(
            (image.object_id, image.crop.key, self._source_names.get(image.object_id, ""))
            for image in self.doc.images
        )
        for figure in self.doc.figures:
            figure.image = replace(figure.image, filename=names[figure.image.object_id])


def parse(doc_json: JsonObject) -> Document:
    return Parser(doc_json).parse()
