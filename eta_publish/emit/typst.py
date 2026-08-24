"""Typst source, compiled to the report PDF.

Typst rather than HTML-to-PDF because footnotes belong at the bottom of the
page. HTML can only place them at the end of the document, and with 21 of
them carrying real argument, that is the difference between a report and a
printout of a web page.

A footnote's body is therefore inlined at the reference site, which is how
Typst wants it: `#footnote[...]` both marks the spot and carries the text,
and Typst does the numbering and the placement. Nothing here maintains a
separate list to keep in sync, which is the failure the HTML output has to
guard against explicitly.

The emitted file is a document body that imports `template.typ`, so the ETA
house style lives in one place rather than being regenerated per report.
"""

from __future__ import annotations

import re
from typing import override

from ..nodes import (
    Document,
    Figure,
    FootnoteRef,
    Heading,
    Image,
    LineBreak,
    List,
    ListItem,
    ListKind,
    Paragraph,
    Table,
    Text,
)
from ..sentences import split
from .base import Emitter

# Typst's markup characters. `#` and `@` start code and references, and the
# rest delimit markup, so any of them in prose has to be escaped.
ESCAPE = re.compile(r"([\\#$*_`<>@\[\]])")


def escape(text: str) -> str:
    return ESCAPE.sub(r"\\\1", text)


def string(value: str) -> str:
    """A Typst string literal."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


class TypstEmitter(Emitter):
    extension = ".typ"

    def __init__(self, template: str = "template.typ", image_dir: str = "images") -> None:
        super().__init__()
        self.template = template
        self.image_dir = image_dir.rstrip("/")

    @override
    def document(self, doc: Document) -> str:
        meta = "\n".join(
            f"  {key.replace(' ', '_')}: {string(value)}," for key, value in doc.meta.items()
        )
        header = (
            f"#import {string(self.template)}: report\n\n"
            f"#show: report.with(\n"
            f"  title: {string(doc.title)},\n"
            f"{meta}\n"
            f")\n"
        )
        return header + "\n" + self.blocks(doc.blocks) + "\n"

    @override
    def join(self, parts: list[str]) -> str:
        return "\n\n".join(p for p in parts if p)

    # ---- blocks -----------------------------------------------------

    @override
    def heading(self, node: Heading) -> str:
        # Typst counts heading depth from 1, where the tree counts the title
        # as level 1 and the first section as 2.
        return f"{'=' * (node.level - 1)} {self.inlines(node.content)}"

    @override
    def paragraph(self, node: Paragraph) -> str:
        return "\n".join(split(self.inlines(node.content)))

    @override
    def list_(self, node: List) -> str:
        return self.items(node.items, node.kind, depth=0)

    def items(self, items: list[ListItem], kind: ListKind, depth: int) -> str:
        marker = "+" if kind is ListKind.NUMBER else "-"
        lines = []
        for item in items:
            lines.append(f"{'  ' * depth}{marker} {self.inlines(item.content)}")
            if item.children:
                lines.append(self.items(item.children, kind, depth + 1))
        return "\n".join(lines)

    @override
    def figure(self, node: Figure) -> str:
        # As in the HTML, `Figure.source` is not emitted: it names a file in
        # Drive for whoever assembles the report, and is not part of it.
        caption_parts = []
        if node.caption:
            caption_parts.append(self.inlines(node.caption))
        if node.credit:
            caption_parts.append(f"#emph[{self.inlines(node.credit)}]")
        caption = " ".join(caption_parts)
        path = f"{self.image_dir}/{self.doc.image_href(node.image)}"
        body = f"  image({string(path)}, width: 100%),"
        if caption:
            return f"#figure(\n{body}\n  caption: [{caption}],\n)"
        return f"#figure(\n{body}\n)"

    @override
    def table(self, node: Table) -> str:
        if not node.rows:
            return ""
        columns = max(len(row) for row in node.rows)
        cells: list[str] = []
        for row in node.rows:
            padded = list(row) + [[]] * (columns - len(row))
            cells += [f"  [{' '.join(self.blocks(cell).split())}]," for cell in padded]
        body = "\n".join(cells)
        return f"#table(\n  columns: {columns},\n{body}\n)"

    # ---- inline -----------------------------------------------------

    @override
    def text(self, node: Text) -> str:
        out = escape(node.text)
        if node.sup:
            out = f"#super[{out}]"
        elif node.sub:
            out = f"#sub[{out}]"
        if node.bold:
            out = f"#strong[{out}]"
        if node.italic:
            out = f"#emph[{out}]"
        if node.underline:
            out = f"#underline[{out}]"
        if node.href:
            out = f"#link({string(node.href)})[{out}]"
        return out

    @override
    def line_break(self, node: LineBreak) -> str:
        return " \\\n"

    @override
    def footnote_ref(self, node: FootnoteRef) -> str:
        """Typst places and numbers footnotes itself, so the body goes here.

        This is the whole reason for a PDF path of its own: the note lands at
        the bottom of the page it is cited on, which no HTML-to-PDF route can
        do.
        """
        note = next((f for f in self.doc.footnotes if f.number == node.number), None)
        if note is None:
            self.doc.warn(f"footnote {node.number} has no definition; omitted from the PDF")
            return ""
        body = " ".join(self.blocks(note.content).split())
        return f"#footnote[{body}]"

    @override
    def image(self, node: Image) -> str:
        path = f"{self.image_dir}/{self.doc.image_href(node)}"
        return f"#image({string(path)}, width: 100%)"
