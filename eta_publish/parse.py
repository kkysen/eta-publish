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

# Ids the emitters generate for themselves, which no heading may take.
RESERVED_ANCHORS = frozenset({"footnotes"})

KEY_RE = re.compile(r"^(?P<key>[A-Z][^:\n]{0,60}?)\s*:\s*(?P<value>.*)$")
SOURCE_RE = re.compile(r"^\s*Source\s*:", re.IGNORECASE)
CREDIT_RE = re.compile(r"^\s*\[?\s*Credit\s*[:\]]", re.IGNORECASE)


def plain(para: JsonObject) -> str:
    """The paragraph's text with styling dropped, for matching conventions."""
    return "".join(
        el.get("textRun", {}).get("content", "") for el in para.get("elements", [])
    ).strip()


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
                node = self._text_run(el["textRun"])
                if node is not None:
                    out.append(node)
            elif "footnoteReference" in el:
                out.append(self._footnote_ref(el["footnoteReference"]))
            elif "inlineObjectElement" in el:
                image = self._image(el["inlineObjectElement"])
                if image is not None:
                    out.append(image)
        return out

    def _text_run(self, run: JsonObject) -> Text | None:
        text = run.get("content", "")
        # A trailing newline is paragraph structure, not content.
        if text.endswith("\n"):
            text = text[:-1]
        if not text:
            return None
        style = run.get("textStyle", {})
        offset = style.get("baselineOffset")
        return Text(
            text=text,
            bold=bool(style.get("bold")),
            italic=bool(style.get("italic")),
            underline=bool(style.get("underline")) and "link" not in style,
            sup=offset == "SUPERSCRIPT",
            sub=offset == "SUBSCRIPT",
            href=style.get("link", {}).get("url"),
        )

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

            if SOURCE_RE.match(text):
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
                if CREDIT_RE.match(text):
                    last.credit = self.inlines(para)
                    continue
                if caption_slot:
                    last.caption = self.inlines(para)
                    caption_slot = 0
                    continue

            caption_slot = 0
            out.append(Paragraph(content=self.inlines(para)))

        drop_pending()
        return out

    def _only_image(self, para: JsonObject) -> Image:
        images = [i for i in self.inlines(para) if isinstance(i, Image)]
        if len(images) > 1:
            self.doc.warn(
                f"{len(images)} images share one paragraph; only the first becomes a figure"
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
        """
        header_seen = False
        end = 0

        for i, item in enumerate(content):
            para = item.get("paragraph")
            if para is None:
                if header_seen:
                    break
                continue

            style = style_of(para)
            level = HEADING_LEVELS.get(style)
            text = plain(para)

            if not header_seen:
                if level is not None and text.strip().lower() == "header":
                    header_seen = True
                    end = i + 1
                elif text or has_image(para):
                    break  # no `Header` section at all
                continue

            if style == "TITLE" or level is not None or has_image(para):
                break

            if not text:
                end = i + 1
                continue

            match = KEY_RE.match(text)
            if match is None:
                break  # prose: the header section is over

            self.doc.meta[match.group("key").strip().lower()] = match.group("value").strip()
            end = i + 1

        if not self.doc.meta:
            self.doc.warn(
                "no front matter found; expected a leading `Header` section with "
                "`URL:`, `Short:`, and `SEO Description:` lines"
            )
        return content[end:]

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
