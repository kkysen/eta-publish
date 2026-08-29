"""HTML two ways: a fragment to embed, and a page to read.

Scoped to `.eta-report` so the same CSS works inlined into the pasted
fragment and injected once site-wide under Custom CSS. A Squarespace code
block applies no styling of its own, so without this the captions, table of
contents, and footnotes render as undifferentiated body text.
"""

import html
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
from .base import Emitter

# Only styles what the emitter produces, and inherits everything else from
# the theme, so a report does not fight the rest of the site.
REPORT_CSS = """
.eta-report figure { margin: 2.5em 0; }
.eta-report figure img { width: 100%; height: auto; display: block; }
/* Caption and credit are styled alike, which is what the published report
   does: both are small text, and neither is italic. The classes stay
   distinct so they can be told apart without reading them. */
.eta-report figcaption { font-size: .85rem; opacity: .75; margin-top: .6em; }
.eta-report .byline { font-size: .95rem; }
.eta-report .dateline { font-size: .95rem; opacity: .75; }
.eta-report .toc { font-size: .95rem; line-height: 1.9; }
.eta-report .toc ul { list-style: none; margin: .2em 0 0; padding-left: 1.4em; }
.eta-report .toc > ul { padding-left: 0; }
.eta-report .footnotes { font-size: .9rem; opacity: .85; }
.eta-report .footnotes-sep { margin-top: 3em; }
.eta-report .footnote-ref a,
.eta-report .footnote-back { text-decoration: none; }
.eta-report .table-scroll { overflow-x: auto; }
.eta-report table { border-collapse: collapse; width: 100%; font-size: .9rem; }
.eta-report td { border: 1px solid currentColor; padding: .4em .6em; vertical-align: top; }
"""


# A Squarespace code block holds 400 KB. Warn well before that, because the
# limit is what the editor accepts, not what it is pleasant to paste: a
# 200 KB paste into a browser textarea is already slow to save.
CODE_BLOCK_LIMIT = 400_000
CODE_BLOCK_WARN = 250_000


def escape(text: str) -> str:
    return html.escape(text, quote=True)


def split_at_headings(fragment: str) -> list[str]:
    """Cut a fragment into pieces at `h2` boundaries, for oversized reports.

    Each piece is a standalone `.eta-report` div, so they can be pasted into
    consecutive code blocks and still pick up the same CSS.
    """
    opening = '<div class="eta-report">'
    body = fragment
    prefix = ""
    if opening in body:
        head, _, body = body.partition(opening)
        prefix = head
    body = body.removesuffix("</div>")

    pieces = re.split(r"(?=<h2 id=)", body)
    return [f"{prefix}{opening}\n{piece.strip()}\n</div>" for piece in pieces if piece.strip()]


class HtmlEmitter(Emitter):
    extension = ".html"

    def __init__(self, image_base: str = "", inline_css: bool = True) -> None:
        super().__init__()
        self.image_base = image_base.rstrip("/")
        # Turn off once `REPORT_CSS` lives in the site's Custom CSS.
        self.inline_css = inline_css

    @override
    def document(self, doc: Document) -> str:
        parts = []
        if self.inline_css:
            parts.append(f"<style>{REPORT_CSS}</style>")
        parts.append('<div class="eta-report">')
        parts.append(self.byline(doc))
        parts.append(self.dateline(doc))
        parts.append(self.toc(doc))
        parts.append(self.blocks(doc.blocks))
        parts.append(self.footnotes(doc))
        parts.append("</div>")
        return self.join(parts)

    def byline(self, doc: Document) -> str:
        """Who is credited, from the header block rather than typed again.

        The names are listed the way the document lists them, separated by
        commas and in its order, with no "and" spliced in before the last:
        the header block is the one place the credits are maintained, and
        rewording them here would make the published line something no one
        wrote.

        A report with no `Public Contributors:` gets no byline at all, the
        way `slug` is simply empty when the header names no URL.
        """
        names = doc.contributors
        if not names:
            return ""
        return f'<p class="byline">By {escape(", ".join(names))}</p>'

    def dateline(self, doc: Document) -> str:
        """When the report published, from `Final Due Date:` in the header.

        Absent entirely when the header names no date. Plain text rather
        than a `<time>`: that element only carries machine-readable meaning
        with an ISO stamp, and `date_text` keeps the formatted string the
        chip displays and drops the timestamp behind it.
        """
        date = doc.dateline
        if not date:
            return ""
        return f'<p class="dateline">{escape(date)}</p>'

    def toc(self, doc: Document) -> str:
        """The sections, as a list rather than a run of separated links.

        A list is what a table of contents is: one entry per line, which
        leaves room for the entries to be indented under the section they
        belong to. The published report runs them together separated by
        pipes, which reads as a sentence and has nowhere to put a subsection.
        """
        headings = doc.headings(level=2)
        if not headings:
            return ""
        items = "\n".join(
            f'<li><a href="#{h.anchor}">{escape(plain(h.content))}</a></li>' for h in headings
        )
        return (
            '<nav class="toc" aria-label="Table of contents">\n'
            "<strong>Table of Contents</strong>\n"
            f"<ul>\n{items}\n</ul>\n"
            "</nav>"
        )

    def footnotes(self, doc: Document) -> str:
        if not doc.footnotes:
            return ""
        items = "\n".join(self.footnote(f) for f in doc.footnotes)
        return (
            '<hr class="footnotes-sep">\n'
            '<section class="footnotes">\n'
            '<h2 id="footnotes">Footnotes</h2>\n'
            f"<ol>\n{items}\n</ol>\n"
            "</section>"
        )

    def footnote(self, note: Footnote) -> str:
        body = self.blocks(note.content)
        back = (
            f'<a href="#fnref{note.number}" class="footnote-back" '
            f'aria-label="Back to footnote {note.number} in the text">↑</a>'
        )
        # Immediately after the number the list renders, rather than after the
        # note. Several of these run to a paragraph, and the way back should
        # be where the eye already is instead of at the end of the reading.
        if body.startswith("<p>"):
            return f'<li id="fn{note.number}"><p>{back} {body.removeprefix("<p>")}</li>'
        return f'<li id="fn{note.number}">{back} {body}</li>'

    # ---- blocks -----------------------------------------------------

    @override
    def heading(self, node: Heading) -> str:
        return f'<h{node.level} id="{node.anchor}">{self.inlines(node.content)}</h{node.level}>'

    @override
    def paragraph(self, node: Paragraph) -> str:
        return f"<p>{self.inlines(node.content)}</p>"

    @override
    def list_(self, node: List) -> str:
        tag = "ol" if node.kind is ListKind.NUMBER else "ul"
        return f"<{tag}>{self.items(node.items, tag)}</{tag}>"

    def items(self, items: list[ListItem], tag: str) -> str:
        out = []
        for item in items:
            inner = self.inlines(item.content)
            if item.children:
                inner += f"<{tag}>{self.items(item.children, tag)}</{tag}>"
            out.append(f"<li>{inner}</li>")
        return "".join(out)

    @override
    def figure(self, node: Figure) -> str:
        # `Figure.source` is deliberately not emitted. It names the original
        # file in Drive, for whoever is assembling the report, and does not
        # appear on the published page.
        parts = [self.image(node.image)]
        if node.caption:
            parts.append(
                f'<figcaption class="figure-caption">{self.inlines(node.caption)}</figcaption>'
            )
        if node.credit:
            parts.append(
                f'<figcaption class="figure-credit">{self.inlines(node.credit)}</figcaption>'
            )
        return f"<figure>{''.join(parts)}</figure>"

    @override
    def table(self, node: Table) -> str:
        rows = "".join(
            "<tr>" + "".join(f"<td>{self.blocks(cell)}</td>" for cell in row) + "</tr>"
            for row in node.rows
        )
        return f'<div class="table-scroll"><table>{rows}</table></div>'

    # ---- inline -----------------------------------------------------

    @override
    def text(self, node: Text) -> str:
        out = escape(node.text)
        if node.sup:
            out = f"<sup>{out}</sup>"
        elif node.sub:
            out = f"<sub>{out}</sub>"
        if node.bold:
            out = f"<strong>{out}</strong>"
        if node.italic:
            out = f"<em>{out}</em>"
        if node.underline:
            out = f"<u>{out}</u>"
        if node.href:
            out = f'<a href="{escape(node.href)}">{out}</a>'
        return out

    @override
    def line_break(self, node: LineBreak) -> str:
        return "<br>"

    @override
    def footnote_ref(self, node: FootnoteRef) -> str:
        return (
            f'<sup id="fnref{node.number}" class="footnote-ref">'
            f'<a href="#fn{node.number}">{node.number}</a></sup>'
        )

    @override
    def image(self, node: Image) -> str:
        href = self.doc.image_href(node)
        src = f"{self.image_base}/{href}" if self.image_base else href
        return f'<img src="{escape(src)}" alt="{escape(node.alt)}" loading="lazy">'


def plain(content: list[Inline]) -> str:
    """Inline content with all markup dropped, for the table of contents."""
    return "".join(i.text for i in content if isinstance(i, Text))


# Enough to read the report as it will look, and nothing more. A page
# pasted into Squarespace inherits that site's typography, so matching it
# here would be a guess that goes stale.
PAGE_CSS = """
:root { color-scheme: light dark; --fg: #1a1a1a; --bg: #fff; }
@media (prefers-color-scheme: dark) { :root { --fg: #eaeaea; --bg: #141414; } }
body { background: var(--bg); color: var(--fg); max-width: 46rem;
       margin: 0 auto; padding: 3rem 1.25rem 6rem;
       font: 17px/1.65 Georgia, "Times New Roman", serif; }
h1, h2, h3, h4 { font-family: system-ui, sans-serif; line-height: 1.25; }
h1 { font-size: 2.1rem; margin-bottom: .2em; }
h2 { margin-top: 2.5em; border-top: 1px solid currentColor; padding-top: .8em; }
a { color: inherit; }
.standfirst { font-size: 1.15rem; opacity: .75; margin-top: 0; }
.warnings { border-left: 3px solid #c60; padding: .4em 1em; margin: 2em 0;
            font-family: system-ui, sans-serif; font-size: .9rem; }
"""


def report_page(doc: Document, image_base: str = IMAGE_DIR) -> str:
    """The whole report as a page, which is what a build writes as
    `index.html` and what the site serves.

    Deliberately not the fragment with a wrapper bolted on. `report.html` is
    the fragment: a `div` to paste into a Squarespace code block, which
    inherits the site's typography and has nowhere to put a warning. This is
    a document, with its own head, its own type, and the parser's warnings
    where whoever is about to publish will see them.
    """
    body = HtmlEmitter(image_base=image_base, inline_css=False).emit(doc)
    warnings = ""
    if doc.warnings:
        items = "\n".join(f"<li>{escape(w)}</li>" for w in doc.warnings)
        warnings = f'<div class="warnings"><strong>Warnings</strong><ul>{items}</ul></div>'
    short = doc.meta.get("short", "")
    return (
        "<!doctype html>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(doc.title)}</title>\n"
        f'<meta name="description" content="{escape(doc.meta.get("seo description", ""))}">\n'
        f"<style>{PAGE_CSS}{REPORT_CSS}</style>\n"
        f"<h1>{escape(doc.title)}</h1>\n"
        f'<p class="standfirst">{escape(short)}</p>\n'
        f"{warnings}\n"
        f"{body}\n"
    )
