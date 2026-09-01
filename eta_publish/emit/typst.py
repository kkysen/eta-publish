"""Typst source, compiled to the report PDF.

Typst rather than HTML-to-PDF because footnotes belong at the bottom of the page.
HTML can only place them at the end of the document,
and with 21 of them carrying real argument,
that is the difference between a report and a printout of a web page.

A footnote's body is inlined at the reference site, which is how Typst wants it:
`#footnote[...]` marks the spot and carries the text,
and Typst does the numbering and the placement.
Nothing here keeps a separate list in sync,
which is the failure the HTML output has to guard against explicitly.

The emitted file is a document body that imports `template.typ`,
which carries the house style.
"""

import json
import re
from typing import override

from ..naming import IMAGE_DIR
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
from .base import CONTRIBUTORS_NOTE, Emitter

# Typst's markup characters.
# `#` and `@` start code and references, and the rest delimit markup,
# so any of them in prose has to be escaped.
ESCAPE = re.compile(r"([\\#$*_`<>@\[\]])")


def escape(text: str) -> str:
    return ESCAPE.sub(r"\\\1", text)


def string(value: str) -> str:
    """A Typst string literal.

    `json.dumps` rather than a pair of `replace` calls:
    a JSON string and a Typst one are quoted and escaped the same way,
    and this one has been tested by more people than we will ever test ours.
    `ensure_ascii=False` keeps the text readable and avoids `\\uXXXX`,
    which JSON writes and Typst does not spell that way.
    """
    return json.dumps(value, ensure_ascii=False)


class TypstEmitter(Emitter):
    extension = ".typ"

    def __init__(self, template: str = "template.typ", image_dir: str = IMAGE_DIR) -> None:
        super().__init__()
        self.template = template
        self.image_dir = image_dir.rstrip("/")

    @override
    def document(self, doc: Document) -> str:
        """The header block as written, plus what the page publishes.

        `doc.meta` is the fields as typed, handed over whole.
        The page has an opinion about two, so they are passed separately
        rather than silently rewritten:
        the date written out, and the contributors in credited order.
        """
        # One dictionary rather than one named argument each.
        # A field name is whatever someone typed in the document,
        # and as an argument name it was Typst code:
        # a field called `x:read("/etc/hostname"),y` ran when the PDF was built.
        # As a key it is a string, and a string cannot be anything but itself.
        # One field per line, and `(:)` for none:
        # this file is committed, so a changed field should be a one-line diff,
        # and `()` is an empty array in Typst rather than an empty dictionary.
        fields = "".join(
            f"    {string(key)}: {string(value)},\n" for key, value in doc.meta.items()
        )
        meta = f"  meta: (\n{fields}  )," if fields else "  meta: (:),"
        header = (
            f"#import {string(self.template)}: capped_image, report\n\n"
            f"#show: report.with(\n"
            f"  title: {string(doc.title)},\n"
            f"{meta}\n"
            f"  dateline: {string(doc.dateline)},\n"
            f"  contributors: ({self.contributors(doc)}),\n"
            f"  contributors_note: {string(CONTRIBUTORS_NOTE)},\n"
            f"{self.hero(doc)}"
            f")\n"
        )
        return header + "\n" + self.blocks(doc.body) + "\n"

    def hero(self, doc: Document) -> str:
        """The opening figure, passed to the template rather than emitted.

        It belongs above the outline, with the title,
        and the template knows where the outline goes.
        """
        if doc.hero is None:
            return ""
        return f"  hero: [\n{self.blocks([doc.hero])}\n  ],\n"

    def contributors(self, doc: Document) -> str:
        """The credited names as a Typst array, so the template can list them."""
        return "".join(f"{string(name)}, " for name in doc.contributors)

    @override
    def join(self, parts: list[str]) -> str:
        return "\n\n".join(p for p in parts if p)

    # ---- blocks -----------------------------------------------------

    @override
    def heading(self, node: Heading) -> str:
        # Typst counts heading depth from 1,
        # where the tree counts the title as level 1 and the first section as 2.
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
        # As in the HTML, `Figure.source` is not emitted:
        # it names a file in Drive for whoever assembles the report.
        # Not emphasized: the published report styles the credit like the caption,
        # and the template decides how a caption looks.
        caption_parts = []
        if node.caption:
            caption_parts.append(self.inlines(node.caption))
        if node.credit:
            caption_parts.append(self.inlines(node.credit))
        caption = " ".join(caption_parts)
        body = f"  {self.image_call(node.image)},"
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

        The whole reason for a PDF path of its own:
        the note lands at the bottom of the page it is cited on,
        which no HTML-to-PDF route can do.
        """
        note = next((f for f in self.doc.footnotes if f.number == node.number), None)
        if note is None:
            self.doc.warn(f"footnote {node.number} has no definition; omitted from the PDF")
            return ""
        body = " ".join(self.blocks(note.content).split())
        return f"#footnote[{body}]"

    @override
    def image(self, node: Image) -> str:
        return f"#{self.image_call(node)}"

    def image_call(self, node: Image) -> str:
        """The `image` call, which a figure wraps and a bare image does not.

        Written once so the two cannot drift:
        alt text added here once reached inline images only,
        because the figure built its own call.
        A PDF carries alt text the way a page does, and it is the same sentence in both.
        """
        path = f"{self.image_dir}/{self.doc.image_href(node)}"
        alt = f", alt: {string(node.alt)}" if node.alt else ""
        # `capped_image` rather than `image`: the width is the column's,
        # except for a picture tall enough to break the page it opens.
        return f"capped_image({string(path)}{alt})"
