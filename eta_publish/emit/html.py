"""HTML two ways: a fragment to embed, and a page to read.

Scoped to `.eta-report` so the same CSS works inlined into the pasted
fragment and injected once site-wide under Custom CSS. A Squarespace code
block applies no styling of its own, so without this the captions, table of
contents, and footnotes render as undifferentiated body text.
"""

import html
import re
from typing import override

from ..naming import IMAGE_DIR, content_anchor
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
from .base import CONTRIBUTORS_NOTE, Emitter

# Only styles what the emitter produces, and inherits everything else from
# the theme, so a report does not fight the rest of the site.
REPORT_CSS = """
.eta-report figure { margin: 2.5em 0; }
.eta-report figure img { width: 100%; height: auto; display: block; }
/* Caption and credit are styled alike, which is what the published report
   does: both are small text, and neither is italic. The classes stay
   distinct so they can be told apart without reading them. */
.eta-report figcaption { font-size: .85rem; opacity: .75; margin-top: .6em; }
.eta-report .dateline { font-size: .95rem; opacity: .75; }
.eta-report .toc { font-size: .95rem; line-height: 1.9; }
.eta-report .toc ul { list-style: none; margin: .2em 0 0; padding-left: 1.4em; }
.eta-report .toc > ul { padding-left: 0; }
.eta-report .footnotes { font-size: .9rem; opacity: .85; }
.eta-report .footnote-ref a,
.eta-report .footnote-back { text-decoration: none; }
.eta-report .contributors { font-size: .95rem; }
/* The back matter is set off by space, not by a rule. A page gives every
   `h2` a rule of its own, so a separator here drew a second one. */
.eta-report .footnotes, .eta-report .contributors { margin-top: 3em; }
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
        self._taken: set[str] = set()

    def anchor(self, prefix: str, text: str) -> str:
        """An id for a block, unique within the page.

        Two blocks saying exactly the same thing hash the same, and the
        second one gets a counted suffix. That suffix is positional, which
        nothing else here is, and it is the least bad option available: the
        blocks are indistinguishable, so there is nothing else to tell them
        apart with. It applies only to the duplicates.
        """
        return self.take(content_anchor(prefix, text))

    def take(self, base: str) -> str:
        """`base`, or the first counted variant of it not already used."""
        candidate = base
        n = 1
        while candidate in self._taken:
            n += 1
            candidate = f"{base}-{n}"
        self._taken.add(candidate)
        return candidate

    @override
    def document(self, doc: Document) -> str:
        # Every id on the page is allocated here, so a second `emit` of the
        # same document produces the same ids rather than suffixed ones.
        self._taken = {"title", "short", "contents", "footnotes", "contributors"}
        self._taken.update(b.anchor for b in doc.blocks if isinstance(b, Heading))
        parts = []
        if self.inline_css:
            parts.append(f"<style>{REPORT_CSS}</style>")
        parts.append('<div class="eta-report">')
        parts.append(self.blocks([doc.hero] if doc.hero is not None else []))
        parts.append(self.dateline(doc))
        parts.append(self.toc(doc))
        parts.append(self.blocks(doc.body))
        parts.append(self.footnotes(doc))
        parts.append(self.contributors(doc))
        parts.append("</div>")
        return self.join(parts)

    def contributors(self, doc: Document) -> str:
        """Who is credited, in a section at the end, the way ETA credits them.

        Not a byline under the title. A report is the work of most of a
        chapter, nine people here, and a line of nine names above the first
        paragraph reads as a masthead rather than as a credit. The published
        report puts them at the bottom, after the footnotes, and says what
        they did.

        The names come from `Public Contributors:` and are listed in the
        order the document lists them: the header block is the one place the
        credits are maintained, so reordering them here would publish
        something no one wrote.

        A report with no `Public Contributors:` gets no section at all, the
        way `slug` is simply empty when the header names no URL.
        """
        names = doc.contributors
        if not names:
            return ""
        items = "\n".join(f"<li>{escape(name)}</li>" for name in names)
        return (
            '<section class="contributors" id="contributors">\n'
            "<h2>Contributors</h2>\n"
            f"<p>{CONTRIBUTORS_NOTE}</p>\n"
            f"<ul>\n{items}\n</ul>\n"
            "</section>"
        )

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
        return f'<p class="dateline" id="date">{escape(date)}</p>'

    def toc(self, doc: Document) -> str:
        """The sections, as a list rather than a run of separated links.

        A list is what a table of contents is: one entry per line, which
        leaves room for the entries to be indented under the section they
        belong to. The published report runs them together separated by
        pipes, which reads as a sentence and has nowhere to put a subsection.

        Every heading is listed, not just the top level. A reader who wants
        `Station Depth` should be able to see that it is there, and a
        document that bothered to write a subsection is a document that
        thinks it worth finding. The published report lists two levels and
        stops, which is why `Ground Conditions` appears nowhere.

        The back matter is listed too, though the emitter writes those two
        headings rather than the document. They are sections of the page
        like any other, and "at the end" is not an address in a report this
        long: the only other way to the footnotes is to click a reference,
        which means finding one first. So every heading the page shows is
        in here, which is a simpler promise than every heading but two.

        A document with no headings of its own still gets no table of
        contents. A table listing only the footnotes is not a table of
        contents, it is a link.
        """
        headings = doc.headings()
        if not headings:
            return ""
        headings = headings + self.back_matter(doc)
        return (
            '<nav class="toc" id="contents" aria-label="Table of contents">\n'
            "<strong>Table of Contents</strong>\n"
            f"{self.toc_list(headings)}\n"
            "</nav>"
        )

    def back_matter(self, doc: Document) -> list[Heading]:
        """The sections this emitter appends, as headings a table can list.

        At the top level, so they close the appendices rather than joining
        them: the footnotes are not part of the last section, whatever
        level the document happens to give that section's neighbours.
        """
        sections = []
        if doc.footnotes:
            sections.append(Heading(level=2, anchor="footnotes", content=[Text("Footnotes")]))
        if doc.contributors:
            sections.append(Heading(level=2, anchor="contributors", content=[Text("Contributors")]))
        return sections

    def toc_list(self, headings: list[Heading]) -> str:
        """The headings as nested lists, one level of nesting per level.

        A heading that skips a level, an `h4` directly under an `h2`, opens
        one list rather than two: the empty list a strict reading would
        emit renders as an indent with nothing in it, and the document
        meant a subsection either way.
        """
        out: list[str] = []
        # The level each open `<ul>` holds, outermost first.
        open_levels: list[int] = []
        for i, heading in enumerate(headings):
            if not open_levels or heading.level > open_levels[-1]:
                out.append("<ul>")
                open_levels.append(heading.level)
            else:
                while len(open_levels) > 1 and heading.level < open_levels[-1]:
                    out.append("</ul></li>")
                    open_levels.pop()
            link = f'<a href="#{heading.anchor}">{escape(plain(heading.content))}</a>'
            # An entry with subsections stays open until its own list closes.
            nests = i + 1 < len(headings) and headings[i + 1].level > heading.level
            out.append(f"<li>{link}" if nests else f"<li>{link}</li>")
        while open_levels:
            open_levels.pop()
            out.append("</ul></li>" if open_levels else "</ul>")
        return "\n".join(out)

    def footnotes(self, doc: Document) -> str:
        if not doc.footnotes:
            return ""
        items = "\n".join(self.footnote(f) for f in doc.footnotes)
        return (
            '<section class="footnotes" id="footnotes">\n'
            "<h2>Footnotes</h2>\n"
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
        #
        # Inside that first paragraph, not before it: a paragraph is a block,
        # so an arrow placed ahead of one sits on a line of its own with the
        # note beginning underneath it. Matched as a tag rather than as the
        # literal `<p>`, because the paragraph carries an id.
        opening = re.match(r"<p\b[^>]*>", body)
        if opening:
            rest = body[opening.end() :]
            return f'<li id="fn{note.number}">{opening.group()}{back} {rest}</li>'
        return f'<li id="fn{note.number}">{back} {body}</li>'

    # ---- blocks -----------------------------------------------------

    @override
    def heading(self, node: Heading) -> str:
        return f'<h{node.level} id="{node.anchor}">{self.inlines(node.content)}</h{node.level}>'

    @override
    def paragraph(self, node: Paragraph) -> str:
        """A paragraph is linkable, because a report this long gets quoted
        a paragraph at a time. One holding no text is not: there is nothing
        to hash and nothing anyone would link to."""
        text = plain(node.content)
        if not text:
            return f"<p>{self.inlines(node.content)}</p>"
        return f'<p id="{self.anchor("p", text)}">{self.inlines(node.content)}</p>'

    @override
    def list_(self, node: List) -> str:
        """The list is linkable; its items are not.

        An item is a line rather than a passage, and every one of them
        would want an id derived from a few words that a copy edit moves
        around. The list is the unit someone links to."""
        tag = "ol" if node.kind is ListKind.NUMBER else "ul"
        text = " ".join(plain(item.content) for item in node.items)
        anchor = f' id="{self.anchor("list", text)}"' if text else ""
        return f"<{tag}{anchor}>{self.items(node.items, tag)}</{tag}>"

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
        # Named for the image it holds, so the anchor is whatever the image
        # is called. Today that is `img-` and a hash of the Docs object id;
        # when the document names its images, this becomes that name.
        return f'<figure id="{self.take(node.image.filename)}">{"".join(parts)}</figure>'

    @override
    def table(self, node: Table) -> str:
        rows = "".join(
            "<tr>" + "".join(f"<td>{self.blocks(cell)}</td>" for cell in row) + "</tr>"
            for row in node.rows
        )
        text = " ".join(
            plain(block.content)
            for row in node.rows
            for cell in row
            for block in cell
            if isinstance(block, Paragraph)
        )
        anchor = f' id="{self.anchor("table", text)}"' if text else ""
        return f'<div class="table-scroll"{anchor}><table>{rows}</table></div>'

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
    # The share card is what a link to the report unfurls as, and the only
    # place it appears: it is a picture of the title, which a reader who has
    # arrived does not need. `og:image` is read by everything that unfurls a
    # link, Slack and Twitter included, so it is the one tag worth writing.
    card = ""
    if doc.card is not None:
        href = doc.image_href(doc.card)
        src = f"{image_base}/{href}" if image_base else href
        card = f'<meta property="og:image" content="{escape(src)}">\n'
        if doc.card.alt:
            card += f'<meta property="og:image:alt" content="{escape(doc.card.alt)}">\n'
    return (
        "<!doctype html>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(doc.title)}</title>\n"
        f'<meta name="description" content="{escape(doc.meta.get("seo description", ""))}">\n'
        f"{card}"
        f"<style>{PAGE_CSS}{REPORT_CSS}</style>\n"
        f'<h1 id="title">{escape(doc.title)}</h1>\n'
        f'<p class="standfirst" id="short">{escape(short)}</p>\n'
        f"{warnings}\n"
        f"{body}\n"
    )
