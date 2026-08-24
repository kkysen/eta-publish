"""Markdown for the committed, diffable archive.

Pandoc-flavored, because CommonMark has no footnotes and these reports are
built on them.

This is not what gets published. It exists so that every regeneration lands
in git as a readable diff: what changed between draft 6 and draft 7, what
the August 21 addendum actually added. That is why the output breaks lines
at sentences (see `sentences.py`) and why the front matter is written as
YAML rather than prose.
"""

from __future__ import annotations

import re
from typing import override

from ..nodes import (
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
from ..sentences import split
from .base import Emitter

# Characters that would otherwise be read as Markdown syntax. Escaping is
# deliberately minimal: over-escaping prose makes the archive harder to read
# by hand, which is most of the point of having it.
ESCAPE = re.compile(r"([\\`*_\[\]|])")


def escape(text: str) -> str:
    return ESCAPE.sub(r"\\\1", text)


def url(href: str) -> str:
    """A link destination, angle-bracketed so parentheses cannot end it.

    These reports cite heavily, and plenty of real URLs contain brackets:
    Wikipedia disambiguation paths, agency PDF links. Bare, the first `)`
    closes the link and the rest of the URL lands in the prose. The
    angle-bracket form is always valid, so it is used unconditionally rather
    than only when it looks necessary.
    """
    return "<" + href.replace("<", "%3C").replace(">", "%3E") + ">"


def yaml_value(value: str) -> str:
    """Quote only when the value could be read as something other than text."""
    if value == "":
        return '""'
    if re.fullmatch(r"[\w /.,'&()-]+", value) and not value[0].isdigit():
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


class MarkdownEmitter(Emitter):
    extension = ".md"

    @override
    def document(self, doc: Document) -> str:
        parts = [self.front_matter(doc), self.blocks(doc.blocks), self.footnotes(doc)]
        return self.join(parts) + "\n"

    @override
    def join(self, parts: list[str]) -> str:
        # A blank line between blocks, which is Markdown's block separator.
        return "\n\n".join(p for p in parts if p)

    def front_matter(self, doc: Document) -> str:
        lines = ["---", f"title: {yaml_value(doc.title)}"]
        lines += [f"{key}: {yaml_value(value)}" for key, value in doc.meta.items()]
        lines.append("---")
        return "\n".join(lines)

    def footnotes(self, doc: Document) -> str:
        return self.join([self.footnote(f) for f in doc.footnotes])

    def footnote(self, note: Footnote) -> str:
        body = self.blocks(note.content)
        # Pandoc continues a footnote across lines when they are indented, so
        # a multi-sentence note keeps its line-per-sentence shape.
        indented = body.replace("\n", "\n    ")
        return f"[^{note.number}]: {indented}"

    # ---- blocks -----------------------------------------------------

    @override
    def heading(self, node: Heading) -> str:
        # The anchor is a published URL, so it is pinned explicitly rather
        # than left to whatever the renderer would derive from the text.
        return f"{'#' * node.level} {self.inlines(node.content)} {{#{node.anchor}}}"

    @override
    def paragraph(self, node: Paragraph) -> str:
        return self.wrap(self.inlines(node.content))

    def wrap(self, text: str) -> str:
        """One line per sentence, so a one-word fix is a one-line diff."""
        return "\n".join(split(text))

    @override
    def list_(self, node: List) -> str:
        return self.items(node.items, node.kind, depth=0)

    def items(self, items: list[ListItem], kind: ListKind, depth: int) -> str:
        lines = []
        for n, item in enumerate(items, start=1):
            marker = f"{n}." if kind is ListKind.NUMBER else "-"
            indent = "  " * depth
            lines.append(f"{indent}{marker} {self.inlines(item.content)}")
            if item.children:
                lines.append(self.items(item.children, kind, depth + 1))
        return "\n".join(lines)

    @override
    def figure(self, node: Figure) -> str:
        """Unlike the published outputs, the archive keeps the `Source:` line.

        It records which file in Drive an image came from, which is exactly
        the provenance worth having in a durable record, and nothing here is
        published.
        """
        caption = self.inlines(node.caption)
        lines = [f"![{escape(node.image.alt)}]({url(self.doc.image_href(node.image))})"]
        if caption:
            lines.append(f"*{caption}*")
        if node.credit:
            lines.append(f"*{self.inlines(node.credit)}*")
        if node.source:
            lines.append(f"<!-- {self.inlines(node.source)} -->")
        return "\n".join(lines)

    @override
    def table(self, node: Table) -> str:
        if not node.rows:
            return ""
        rows = [[" ".join(self.blocks(cell).split()) for cell in row] for row in node.rows]
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        # Markdown tables require a header row, so the first one serves.
        header, *body = rows
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join("---" for _ in header) + " |",
        ]
        lines += ["| " + " | ".join(r) + " |" for r in body]
        return "\n".join(lines)

    # ---- inline -----------------------------------------------------

    @override
    def text(self, node: Text) -> str:
        out = escape(node.text)
        if node.sup:
            out = f"^{out}^"
        elif node.sub:
            out = f"~{out}~"
        if node.bold:
            out = f"**{out}**"
        if node.italic:
            out = f"*{out}*"
        if node.href:
            out = f"[{out}]({url(node.href)})"
        return out

    @override
    def footnote_ref(self, node: FootnoteRef) -> str:
        return f"[^{node.number}]"

    @override
    def image(self, node: Image) -> str:
        return f"![{escape(node.alt)}]({url(self.doc.image_href(node))})"


def plain(content: list[Inline]) -> str:
    return "".join(i.text for i in content if isinstance(i, Text))
