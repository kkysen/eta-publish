"""Build a `Document` tree from Google Docs API JSON.

This is the only module that knows the shape of the Docs API. Everything
downstream sees the tree in `nodes.py`.

Several pieces of ETA house style are recognized here rather than in the
emitters, because they are facts about how the docs are written:

- a leading `Header` section carrying `Key: value` front matter
- the report headline living in the body as a TITLE-styled paragraph,
  since the Drive filename is a working name (`SAS West Feasibility
  Response`) and not what gets published
- a figure's `Source:` line before the image, with caption and `Credit:`
  lines after it
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime

from .docs_json import JsonObject
from .naming import AnchorAllocator, image_filename
from .nodes import (
    Block,
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
RESERVED_ANCHORS = frozenset({"footnotes"})

# Docs writes a Shift+Enter line break as a vertical tab inside the run.
SOFT_BREAK = "\v"

KEY_RE = re.compile(r"^(?P<key>[A-Z][^:\n]{0,60}?)\s*:\s*(?P<value>.*)$")
# A trailing note to whoever fills the field in, not part of its name. The
# real doc writes `SEO Description (300 char limit):`, and a lookup for
# `seo description` finds nothing unless the note is stripped.
KEY_NOTE_RE = re.compile(r"\s*\([^)]*\)\s*$")
# Editorial notes naming where an image came from. The real report uses
# three spellings: `Source:` before an image, `Uncropped Source:` for one
# that was trimmed, and `[Image Source](<url>)` after a caption. One
# optional qualifying word covers all three and whatever the next one is.
# None of them appears on the published page, which is what makes them notes
# rather than content: the live SAS West report contains zero occurrences of
# each, against 26 of `Credit:`.
SOURCE_RE = re.compile(r"^\s*\[?\s*(?:\w+\s+)?source\s*[:\]]", re.IGNORECASE)

# The same idea for chart assets: `SVG:` and `PNG:` name the file to link
# beside a figure. They are notes to whoever assembles the page, and the
# published report carries real links instead.
ASSET_RE = re.compile(r"^\s*(?:svg|png|pdf)\s*:", re.IGNORECASE)

# Anything still marked as unfinished. The real doc has `Source: TODO` and
# `SVG: TODO` in it, which are fine while drafting and not fine on a
# published page, so they are worth one loud line before publishing.
TODO_RE = re.compile(r"\bTODO\b|\bTK\b|\bFIXME\b|\bXXX\b")
CREDIT_RE = re.compile(r"^\s*\[?\s*Credit\s*[:\]]", re.IGNORECASE)


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

    Reading only `textRun` loses every chip. In the real report that emptied
    `Project Manager:` and all three date fields, and dropped the first name
    from `Public Contributors:`, leaving it starting with a comma.
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


def split_lines(content: list[Inline]) -> list[list[Inline]]:
    """Break inline content at soft line breaks."""
    lines: list[list[Inline]] = [[]]
    for node in content:
        if isinstance(node, LineBreak):
            lines.append([])
        else:
            lines[-1].append(node)
    return lines


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
        self._footnote_numbers: dict[str, int] = {}

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
        return out

    def _person(self, chip: JsonObject) -> Text:
        """A person smart chip renders as the person's name.

        The chip also carries their email address. That is contact
        information the document happens to hold, not something the report
        says, so it is deliberately not emitted.
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
        # Numbered in document order, so a reference and its definition
        # cannot disagree the way hand-written anchors did.
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
        uri = embedded.get("imageProperties", {}).get("contentUri")
        if not uri:
            self.doc.warn(f"inline object {object_id} has no image; skipped")
            return None
        return Image(
            object_id=object_id,
            filename=image_filename(object_id),
            alt=embedded.get("description") or embedded.get("title") or "",
            source_uri=uri,
        )

    # ---- lists -------------------------------------------------------

    def _list_kind(self, list_id: str, level: int) -> ListKind:
        levels = self.lists.get(list_id, {}).get("listProperties", {}).get("nestingLevels", [])
        glyph = levels[level] if level < len(levels) else {}
        numbered = glyph.get("glyphType") not in (None, "GLYPH_TYPE_UNSPECIFIED")
        return ListKind.NUMBER if numbered else ListKind.BULLET

    def _consume_list(self, content: list[JsonObject], start: int) -> tuple[List, int]:
        """Absorb the run of consecutive bulleted paragraphs starting at `start`.

        Docs gives each paragraph a flat `nestingLevel` rather than nesting
        them, so the tree is rebuilt here with a stack of sibling lists.
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
                # Treating it as a heading yields an empty one, whose anchor
                # is a published URL, and buries the image inside it.
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
                    # The `[Image Source](...)` spelling follows its figure.
                    last.source = last.source + self.inlines(para)
                    continue
                drop_pending()
                pending_source = self.inlines(para)
                caption_slot = 0
                continue

            if has_image(para):
                out.append(Figure(image=self._only_image(para), source=pending_source or []))
                pending_source = None
                caption_slot = 1
                continue

            # A caption is the one paragraph directly after a figure; `Credit:`
            # lines keep attaching after that. Matching on length instead would
            # silently swallow short body paragraphs, and a report with 50-odd
            # figures has a great many of those.
            last = out[-1] if out else None
            if isinstance(last, Figure):
                # A caption and its credit are often one paragraph split by a
                # soft line break, so each line is classified separately.
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
                # Nothing to describe it with: no alt text in Docs and no
                # caption to borrow. Screen readers get an unlabelled image.
                self.doc.warn(
                    f"image {block.image.object_id} has no alt text and no caption; "
                    "add a description to it in the doc"
                )
            if isinstance(block, Figure) and not block.image.alt and block.caption:
                # The published page uses the caption as alt text as well as
                # showing it, so an image with no description in Docs is not
                # left unlabelled.
                caption = "".join(i.text for i in block.caption if isinstance(i, Text))
                block.image = replace(block.image, alt=caption.strip())
        return out

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

    def front_matter(self, content: list[JsonObject]) -> list[JsonObject]:
        """Consume the leading `Header` section into `doc.meta`.

        Front matter is the run of `Key: value` paragraphs following the
        `Header` heading. It ends at the first paragraph that is not one:
        a heading of any level, the TITLE-styled headline, a paragraph
        holding an image, or ordinary prose.

        Deliberately not "until the next heading of the same or higher
        level". In the real doc `Header` is an `h2` while the body sections
        are `h1`, so that rule runs past the headline, the hero image, its
        caption and credit, and the addendum, all the way to the first body
        section. The image would vanish without a warning, since a paragraph
        holding only an image has no text to report.

        Unrecognized keys are kept rather than ending the scan, so adding a
        header field to a future report cannot leak that line into the body.
        The real doc already has one such line
        (`MTA SAS West Feasibility Study:`).

        Anything before `Header` is production scaffolding rather than the
        report. It is dropped, but each dropped line is reported, so nothing
        leaves the document without saying so. The SAS West tabs happen to
        open with `Header` directly, so this is defensive rather than load
        bearing; what is load bearing is that a document with no `Header` at
        all is left untouched instead of being eaten a paragraph at a time.
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

        Found before anything is consumed, so a document without one is left
        untouched rather than being eaten a paragraph at a time. The search
        stops at the headline or the first figure, since past either of those
        the report has already started.
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

        The filename is a working name: the SAS West report lives in a doc
        called `SAS West Feasibility Response`, which is not what publishes.
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

        A definition with no reference cannot be numbered, so it is reported
        rather than emitted with a number that means nothing.
        """
        for fid in self.footnote_defs:
            if fid not in self._footnote_numbers:
                self.doc.warn(f"footnote {fid} is defined but never referenced; omitted")
        return [
            Footnote(
                footnote_id=fid,
                number=number,
                content=self.blocks(self.footnote_defs.get(fid, {}).get("content", [])),
            )
            for number, fid in sorted(
                (number, fid) for fid, number in self._footnote_numbers.items()
            )
        ]

    def parse(self) -> Document:
        content: list[JsonObject] = self.json.get("body", {}).get("content", [])
        content = self.front_matter(content)
        self.doc.title = self.title(content)

        # Allocated knowing every heading up front, so that two headings which
        # slugify alike keep their anchors when the document is reordered.
        self.anchors = AnchorAllocator(
            [
                plain(item["paragraph"])
                for item in content
                if "paragraph" in item and style_of(item["paragraph"]) in HEADING_LEVELS
            ],
            reserved=RESERVED_ANCHORS,
        )

        body = [
            item
            for item in content
            if not ("paragraph" in item and style_of(item["paragraph"]) == "TITLE")
        ]
        self.doc.blocks = self.blocks(body)
        # After the body, so that every reference has been numbered.
        self.doc.footnotes = self.footnotes()
        return self.doc


def parse(doc_json: JsonObject) -> Document:
    return Parser(doc_json).parse()
