"""Build a `Document` tree from Google Docs API JSON.

This is the only module that knows the shape of the Docs API. Everything
downstream sees the tree in `nodes.py`.

Three pieces of ETA house style are recognized here rather than in the
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

from .naming import AnchorAllocator, image_filename
from .nodes import (
    Block,
    Document,
    Footnote,
    FootnoteRef,
    Image,
    Inline,
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

KEY_RE = re.compile(r"^(?P<key>[A-Z][^:\n]{0,60}?)\s*:\s*(?P<value>.*)$")
SOURCE_RE = re.compile(r"^\s*Source\s*:", re.IGNORECASE)
CREDIT_RE = re.compile(r"^\s*\[?\s*Credit\s*[:\]]", re.IGNORECASE)


class Parser:
    def __init__(self, doc_json: dict) -> None:
        self.json = doc_json
        self.inline_objects = doc_json.get("inlineObjects", {})
        self.lists = doc_json.get("lists", {})
        self.footnote_defs = doc_json.get("footnotes", {})
        self.doc = Document()
        self.anchors = AnchorAllocator()
        self._footnote_numbers: dict[str, int] = {}

    # ---- inline ------------------------------------------------------

    def inlines(self, para: dict) -> list[Inline]:
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

    def _text_run(self, run: dict) -> Text | None:
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

    def _footnote_ref(self, ref: dict) -> FootnoteRef:
        fid = ref["footnoteId"]
        # Numbered in document order, so a reference and its definition
        # cannot disagree the way hand-written anchors did.
        if fid not in self._footnote_numbers:
            self._footnote_numbers[fid] = len(self._footnote_numbers) + 1
        return FootnoteRef(footnote_id=fid, number=self._footnote_numbers[fid])

    def _image(self, ioe: dict) -> Image | None:
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

    # ---- blocks ------------------------------------------------------

    def blocks(self, content: list[dict]) -> list[Block]:
        raise NotImplementedError("block assembly")

    def table(self, table: dict) -> Table:
        raise NotImplementedError("tables")

    # ---- document ----------------------------------------------------

    def front_matter(self, content: list[dict]) -> list[dict]:
        """Consume the leading `Header` section into `doc.meta`.

        Front matter runs from the `Header` heading to the next heading of
        the same or higher level. Unrecognized `Key: value` lines are kept
        rather than ending the scan, so adding a header field to a future
        report cannot leak that line into the body. The real doc already
        has one such line (`MTA SAS West Feasibility Study:`).
        """
        raise NotImplementedError("front matter")

    def title(self, content: list[dict]) -> str:
        """Prefer a TITLE-styled paragraph over the Drive filename."""
        raise NotImplementedError("title")

    def footnotes(self) -> list[Footnote]:
        raise NotImplementedError("footnotes")

    def parse(self) -> Document:
        raise NotImplementedError("parse")


def parse(doc_json: dict) -> Document:
    return Parser(doc_json).parse()


def _plain(para: dict) -> str:
    """The paragraph's text with styling dropped, for matching conventions."""
    return "".join(
        el.get("textRun", {}).get("content", "") for el in para.get("elements", [])
    ).strip()
