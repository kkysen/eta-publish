"""Markdown for the committed, diffable archive.

Pandoc-flavored, because CommonMark has no footnotes and these reports are
built on them. Where Pandoc and GitHub disagree, GitHub wins: this file is
read in the repository, and GitHub supports the footnotes that made Pandoc
necessary in the first place.

This is not what gets published. It exists so that every regeneration lands
in git as a readable diff: what changed between draft 6 and draft 7, what
the August 21 addendum actually added. That is why the output breaks lines
at sentences (see `sentences.py`).

It is the same report as the page and the PDF, not a different view of it:
the same headline, standfirst, date, and hero, in the same order, and the
same contributors at the end. The header block itself is not here. It is
production scaffolding, `Draft Due Date:` and a discussion channel, and
`doc.json` beside this file keeps every field of it verbatim.
"""

import re
from typing import override

from ..naming import IMAGE_DIR
from ..nodes import (
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
from ..sentences import split
from .base import CONTRIBUTORS_NOTE, Emitter

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


def strip_trailing_space(text: str) -> str:
    """Drop whitespace at the end of every line.

    In Markdown two trailing spaces mean a hard line break and any other
    number means nothing, so linters reject the in-between cases. Thirteen
    lines of the SAS West report end in a single space, carried over from
    where the sentence ends in the document.

    Nothing is lost by removing them, because a hard break here is written
    as a trailing backslash, which is unambiguous and visible.
    """
    return "\n".join(line.rstrip() for line in text.split("\n"))


class MarkdownEmitter(Emitter):
    extension = ".md"

    def __init__(self, image_dir: str = IMAGE_DIR) -> None:
        """`image_dir` is relative to the `.md`, which sits beside it.

        Not a published URL prefix: the archive is read from the
        repository, where the files are on disk next to it, rather than from
        whatever host serves the site.
        """
        super().__init__()
        self.image_dir = image_dir.rstrip("/")

    def href(self, image: Image) -> str:
        name = self.doc.image_href(image)
        return f"{self.image_dir}/{name}" if self.image_dir else name

    @override
    def document(self, doc: Document) -> str:
        parts = [
            self.title(doc),
            self.dateline(doc),
            self.blocks([doc.hero] if doc.hero is not None else []),
            self.blocks(doc.body),
            self.footnotes(doc),
            self.contributors(doc),
        ]
        return strip_trailing_space(self.join(parts)) + "\n"

    @override
    def join(self, parts: list[str]) -> str:
        # A blank line between blocks, which is Markdown's block separator.
        return "\n\n".join(p for p in parts if p)

    def title(self, doc: Document) -> str:
        """The headline, and the standfirst under it, as the page has them.

        `#` is free: the document's own sections are `##`, because the tree
        counts the title as the level above them.
        """
        if not doc.title:
            return ""
        short = doc.meta.get("short", "")
        heading = f"# {escape(doc.title)}"
        return f"{heading}\n\n{escape(short)}" if short else heading

    def dateline(self, doc: Document) -> str:
        """When the report published, as the page and the PDF date it."""
        return escape(doc.dateline)

    def contributors(self, doc: Document) -> str:
        """Credited at the end, as they are on the page.

        The front matter above carries `public contributors` as the header
        block writes it, which is the field. This is the credit, in the
        order it publishes in, so the archive says what the page said.
        """
        names = doc.contributors
        if not names:
            return ""
        listed = "\n".join(f"- {name}" for name in names)
        return f"## Contributors\n\n{CONTRIBUTORS_NOTE}\n\n{listed}"

    def footnotes(self, doc: Document) -> str:
        """The notes themselves, with no heading over them.

        Pandoc and GitHub both collect these at the end under a rule of
        their own, and a table of contents is likewise something a Markdown
        reader builds from the headings. What the format provides, this
        does not write again: the same content, reached the way the format
        reaches it.
        """
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
        """Just the heading, with no explicit identifier.

        Pandoc's `{#anchor}` syntax was here so the archive's anchors matched
        the published ones. GitHub has no attribute syntax and renders it as
        literal text inside the heading, which is where this file is actually
        read, and it bought nothing: the anchor is a property of the HTML,
        and a static site would be built from the tree rather than from here.
        """
        return f"{'#' * node.level} {self.inlines(node.content)}"

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
        # Caption and credit are their own lines rather than emphasized. The
        # published report does not italicize either, and marking them up
        # here would put styling in the archive that the report does not have.
        caption = self.inlines(node.caption)
        lines = [f"![{escape(node.image.alt)}]({url(self.href(node.image))})"]
        if caption:
            lines.append(caption)
        if node.credit:
            lines.append(self.inlines(node.credit))
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
        # HTML rather than Pandoc's `^x^` and `~x~`, which both Pandoc and
        # GitHub accept. GitHub renders `^x^` literally and, worse, renders
        # `~x~` as strikethrough, which is not merely ugly but wrong.
        if node.sup:
            out = f"<sup>{out}</sup>"
        elif node.sub:
            out = f"<sub>{out}</sub>"
        if node.bold:
            out = f"**{out}**"
        if node.italic:
            out = f"*{out}*"
        if node.href:
            out = f"[{out}]({url(node.href)})"
        return out

    @override
    def line_break(self, node: LineBreak) -> str:
        # A backslash is the unambiguous hard break; two trailing spaces are
        # invisible and get stripped by anything that tidies whitespace.
        return "\\\n"

    @override
    def footnote_ref(self, node: FootnoteRef) -> str:
        return f"[^{node.number}]"

    @override
    def image(self, node: Image) -> str:
        return f"![{escape(node.alt)}]({url(self.href(node))})"


def plain(content: list[Inline]) -> str:
    return "".join(i.text for i in content if isinstance(i, Text))
