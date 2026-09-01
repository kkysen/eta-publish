"""Markdown for the committed, diffable archive.

Pandoc-flavored, because CommonMark has no footnotes and these reports run on them.
Where Pandoc and GitHub disagree, GitHub wins:
this file is read in the repository,
and GitHub supports the footnotes that made Pandoc necessary in the first place.

This is not what gets published.
It exists so that every regeneration lands in git as a readable diff:
what changed between draft 6 and draft 7, what the August 21 addendum added.
That is why the output breaks lines at sentences (see `sentences.py`).

The same report as the page and the PDF, not a different view of it:
the same headline, standfirst, date, and hero, in the same order,
and the same contributors at the end.
The header block is not here.
It is production scaffolding, `Draft Due Date:` and a discussion channel,
and `doc.json` beside this file keeps every field verbatim.
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

# Characters that would otherwise be read as Markdown syntax.
# Escaping is minimal: over-escaping makes the archive harder to read by hand,
# which is most of the point of having it.
ESCAPE = re.compile(r"([\\`*_\[\]|])")


def escape(text: str) -> str:
    return ESCAPE.sub(r"\\\1", text)


def url(href: str) -> str:
    """A link destination, angle-bracketed so parentheses cannot end it.

    These reports cite heavily, and plenty of real URLs contain brackets:
    Wikipedia disambiguation paths, agency PDF links.
    Bare, the first `)` closes the link and the rest of the URL lands in the prose.
    The angle-bracket form is always valid, so it is used unconditionally.
    """
    return "<" + href.replace("<", "%3C").replace(">", "%3E") + ">"


def strip_trailing_space(text: str) -> str:
    """Drop whitespace at the end of every line.

    Two trailing spaces mean a hard line break and any other number means nothing,
    so linters reject the in-between cases.
    Thirteen lines of the SAS West report end in a single space,
    carried over from where the sentence ends in the document.

    Nothing is lost by removing them:
    a hard break here is a trailing backslash, which is unambiguous and visible.
    """
    return "\n".join(line.rstrip() for line in text.split("\n"))


class MarkdownEmitter(Emitter):
    extension = ".md"

    def __init__(self, image_dir: str = IMAGE_DIR) -> None:
        """`image_dir` is relative to the `.md`, which sits beside it.

        Not a published URL prefix:
        the archive is read from the repository, where the files sit next to it,
        rather than from whatever host serves the site.
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
            self.phase(doc),
            self.dateline(doc),
            self.warnings(doc),
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

        `#` is free: the document's own sections are `##`,
        because the tree counts the title as the level above them.
        """
        if not doc.title:
            return ""
        short = doc.meta.get("short", "")
        heading = f"# {escape(doc.title)}"
        return f"{heading}\n\n{escape(short)}" if short else heading

    def phase(self, doc: Document) -> str:
        """Bold, because the archive has no styling to give it and it is a warning."""
        return f"**{escape(doc.phase)}**" if doc.phase else ""

    def warnings(self, doc: Document) -> str:
        """The build's notes about this report, above it and below the dateline.

        Written as a list, and not escaped:
        a warning is written with backticks around a name,
        which is already how Markdown spells code.
        """
        if not doc.warnings:
            return ""
        notes = "\n".join(f"- {w}" for w in doc.warnings)
        return f"**Warnings**\n\n{notes}"

    def dateline(self, doc: Document) -> str:
        """When the report published, as the page and the PDF date it."""
        return escape(doc.dateline)

    def contributors(self, doc: Document) -> str:
        """Credited at the end, as they are on the page.

        The front matter above carries `public contributors` as the header writes it,
        which is the field. This is the credit, in the order it publishes in.
        """
        names = doc.contributors
        if not names:
            return ""
        listed = "\n".join(f"- {name}" for name in names)
        return f"## Contributors\n\n{CONTRIBUTORS_NOTE}\n\n{listed}"

    def footnotes(self, doc: Document) -> str:
        """The notes themselves, with no heading over them.

        Pandoc and GitHub both collect these at the end under a rule of their own,
        and both build a table of contents from the headings.
        What the format provides, this does not write again.
        """
        return self.join([self.footnote(f) for f in doc.footnotes])

    def footnote(self, note: Footnote) -> str:
        body = self.blocks(note.content)
        # Pandoc continues a footnote across lines when they are indented,
        # so a multi-sentence note keeps its line-per-sentence shape.
        indented = body.replace("\n", "\n    ")
        return f"[^{note.number}]: {indented}"

    # ---- blocks -----------------------------------------------------

    @override
    def heading(self, node: Heading) -> str:
        """Just the heading, with no explicit identifier.

        Pandoc's `{#anchor}` syntax was here
        so the archive's anchors matched the published ones.
        GitHub has no attribute syntax and renders it as literal text in the heading,
        which is where this file is actually read, and it bought nothing:
        the anchor is a property of the HTML,
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

        It records which file in Drive an image came from, and nothing here is published.
        """
        # Caption and credit are their own lines rather than emphasized:
        # the published report italicizes neither,
        # and marking them up would put styling in the archive that the report lacks.
        caption = self.inlines(node.caption)
        lines = [f"![{escape(node.image.alt)}]({url(self.href(node.image))})"]
        if caption:
            lines.append(caption)
        if node.credit:
            lines.append(self.inlines(node.credit))

        # A bare newline is a soft break, which is a space:
        # the picture, its caption and its credit rendered as one running line.
        # The trailing backslash is the hard break that is visible in the source,
        # rather than the two trailing spaces that mean the same
        # and that any editor is entitled to strip.
        #
        # The source line is a comment, which renders as nothing,
        # so a break before it would be a break to nowhere,
        # and the backslash asking for it would be the last thing on a visible line.
        out = "\\\n".join(lines)
        if node.source:
            out += f"\n<!-- {self.inlines(node.source)} -->"
        return out

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
        # HTML rather than Pandoc's `^x^` and `~x~`, which both accept.
        # GitHub renders `^x^` literally and `~x~` as strikethrough, which is wrong.
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
        # A backslash is the unambiguous hard break;
        # two trailing spaces are invisible and get stripped by anything tidying whitespace.
        return "\\\n"

    @override
    def footnote_ref(self, node: FootnoteRef) -> str:
        return f"[^{node.number}]"

    @override
    def image(self, node: Image) -> str:
        return f"![{escape(node.alt)}]({url(self.href(node))})"


def plain(content: list[Inline]) -> str:
    return "".join(i.text for i in content if isinstance(i, Text))
