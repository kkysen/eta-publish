"""HTML two ways: a fragment to embed, and a page to read.

Scoped to `.eta-report` so the same CSS works inlined into the pasted fragment
and injected once site-wide under Custom CSS.
A Squarespace code block applies no styling of its own,
so without this the captions, table of contents, and footnotes
render as undifferentiated body text.
"""

import html
import re
from collections.abc import Callable
from typing import override

from ..naming import IMAGE_DIR, content_anchor
from ..nodes import (
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
from .base import CONTRIBUTORS_NOTE, Emitter, warning_markup

# Only styles what the emitter produces, inheriting the rest from the theme,
# so a report does not fight the site around it.
REPORT_CSS = """
.eta-report figure { margin: 2.5em 0; }
/* Figures the document puts next to each other sit next to each other, if
   the reader's screen has room for them. `flex-basis` is what decides: two
   fit in the 46rem the page is set at, and one does on a phone, with no
   width named anywhere and nothing to keep in step with a media query.

   Both the basis and the growth are the image's own aspect ratio, so the
   widths a row settles on are proportional to it and the pictures come out
   the same height rather than the same width. A cross-section next to the
   cross-section it is compared with is read across, and equal heights are
   what make that comparison one line rather than two scales. The ratio is
   measured from the file and written on the figure; 1.4 is the landscape
   photo the report is mostly made of, for an image whose size a build did
   not learn.

   The 10rem is the wrap point rather than a width: it is one page's worth
   of column divided by the widest pair the report puts in a row, so the
   pairs that fit on a tablet still do and a phone still stacks them. */
.eta-report .figure-row { display: flex; flex-wrap: wrap; gap: 1.5em;
                          align-items: flex-start; margin: 2.5em 0; }
.eta-report .figure-row > figure {
  flex: var(--aspect, 1.4) 1 calc(var(--aspect, 1.4) * 10rem); margin: 0; }
.eta-report figure img { width: 100%; height: auto; display: block; }
/* No figure is taller than this. The pictures arrive at whatever size
   someone dropped them into the document at, and a tall one filled the
   screen on its own before a word of the report was read. The cap is a
   `max-width` on the figure derived from the picture's own shape rather
   than a `max-height` on the image, because `max-height` against the
   `width: 100%` above would squash the picture, and because two figures
   sharing a row have to come out the same height, which capping their
   widths in proportion to `--aspect` keeps true. An image whose shape a
   build did not learn, which is any SVG, falls back to the 1.4 the row
   assumes and so caps at roughly the same place. The 34rem is the PDF's
   4.5in cap scaled to this column, so that a picture cut down in one is
   cut down in the other. Centred, because a capped figure is narrower
   than the column it sits in. */
.eta-report figure { max-width: calc(var(--aspect, 1.4) * 34rem);
                     margin-left: auto; margin-right: auto; }
/* Everything with an id carries a link to itself, because everything with
   an id is something a reader may want to send someone: a section, a
   figure, a paragraph they are quoting. The `#` is written by the
   stylesheet rather than by the emitter, so that it is not part of the
   text: selecting a heading to quote it should not pick up a stray
   character, and a reader who cannot see the mark hears the label instead.

   It hangs in the margin ahead of the block rather than sitting at the end
   of it, so that every mark on the page is in the same column and the eye
   knows where to look. Shown on hover, and on focus as well, or it would be
   a control only a mouse can reach. */
.eta-report :has(> .link-mark) { position: relative; }
/* No `top`: an absolutely positioned box with `top: auto` stays at the
   vertical position it would have had in the line, which is beside the
   first line of the block. Pinning it to the top of the box instead put
   the mark of a heading with a rule above it up in the padding between the
   rule and the words. */
.eta-report .link-mark { position: absolute; left: -1.15em;
                         text-decoration: none; font-weight: normal;
                         opacity: 0; }
.eta-report .link-mark::before { content: "#"; }
.eta-report :has(> .link-mark):hover > .link-mark,
.eta-report .link-mark:focus-visible { opacity: .45; }
.eta-report .link-mark:hover { opacity: 1; }
/* Inside a table cell there is no margin to hang a mark in: ahead of a cell
   is the cell before it. Those marks stay in the line instead. */
.eta-report td .link-mark { position: static; margin-left: .35em; }
/* A footnote's mark goes outside its number rather than after it, where it
   was crowding the arrow back to the text. The list is indented far enough
   to leave room for both. */
.eta-report .footnotes ol { padding-left: 3.4em; }
.eta-report .footnotes li > .link-mark { left: -3.4em; }
@media print { .eta-report .link-mark { display: none; } }
/* Caption and credit are styled alike, which is what the published report
   does: both are small text, and neither is italic. The classes stay
   distinct so they can be told apart without reading them. */
.eta-report figcaption { font-size: .85rem; opacity: .75; margin-top: .6em; }
.eta-report .dateline { font-size: .95rem; opacity: .75; }
/* The build's own notes about this report, not part of it, and never in the
   fragment that is pasted into the live site. A colour of its own, because it
   is the one thing on the page that is not the report and should not be read
   as though it were, and sans-serif for the same reason. */
.eta-report .warnings { border-left: 3px solid #c60; padding: .4em 1em;
                        margin: 2em 0; font-size: .9rem;
                        font-family: system-ui, sans-serif; }
.eta-report .warnings ul { margin: .4em 0 0; padding-left: 1.2em; }
/* Marked the way a code span is marked anywhere else, because a warning
   naming a field or a file is naming something exact and the eye should be
   able to find it. A grey of no hue at 15%, which is a tint on a light page
   and a lift on a dark one, so one rule serves both. */
.eta-report code { background: rgba(127, 127, 127, .15); border-radius: .25em;
                   padding: .1em .3em; font-size: .9em; }
/* A value the warning is about, shown rather than described. Indented and
   ranged left so that a long one is read as the quotation it is and not as
   more of the sentence above it. */
.eta-report .warnings blockquote { margin: .5em 0 .5em 1em; padding-left: .8em;
                                   border-left: 2px solid currentColor;
                                   opacity: .8; }
/* A draft says so, in the one place nobody scrolls past. Bordered rather than
   coloured: the page is read on a site whose palette this does not know, and
   a rule in the current text colour is legible whatever that turns out to be. */
.eta-report .phase { font-size: .8rem; letter-spacing: .08em;
                     text-transform: uppercase; font-weight: bold;
                     border: 1px solid currentColor; border-radius: .2em;
                     display: inline-block; padding: .15em .5em; margin: 0 0 1em; }
.eta-report .toc { font-size: .95rem; line-height: 1.9; }
.eta-report .toc ul { list-style: none; margin: .2em 0 0; padding-left: 1.4em; }
.eta-report .toc > ul { padding-left: 0; }
.eta-report .footnotes { font-size: .9rem; opacity: .85; }
.eta-report .footnote-ref a,
.eta-report .footnote-back { text-decoration: none; }
/* The note itself, shown where the reference is, so that reading a sentence
   does not mean leaving it. The link stays exactly what it was: this is a
   preview for a reader who has a pointer, and the way to the note at the
   bottom is still a click.

   Only where hovering is a thing the device does. On a touch screen the
   first tap on a link raises `:hover` instead of following it, which would
   turn every footnote reference into a two-tap link to buy a tooltip nobody
   asked for. That gate also keeps the box off the narrow screens it has the
   least room on.

   `display` rather than `opacity`, so the duplicated text is out of the
   layout, out of print, and out of what a screen reader reads. The note is
   already reachable as a link, and `aria-hidden` keeps this copy from being
   read a second time in the middle of the sentence. */
@media (hover: hover) {
  .eta-report .footnote-ref { position: relative; }
  .eta-report .footnote-tip { display: none; }
  .eta-report .footnote-ref:hover .footnote-tip,
  .eta-report .footnote-ref:focus-within .footnote-tip { display: block; }
  /* Under the reference rather than over it, which is where the script
     below will usually put it too, and where it goes when there is no
     script: over it is outside the window whenever the reader arrived by a
     backlink, which scrolls the reference to the top of the page. Under it
     there is at least the rest of the paragraph.

     Which edge has room is a question about the window, and CSS cannot ask
     it. So this is the placement to fall back to and not the one to rely
     on; the script measures. */
  .eta-report .footnote-tip {
      position: absolute; top: 1.6em; left: 50%; transform: translateX(-50%);
      z-index: 1; width: max-content; max-width: min(24rem, calc(100vw - 2.5rem));
      padding: .5em .7em; border-radius: .3em;
      /* The page names these two, and a site pasted into does not, where the
         system pair is the one thing known to be legible against itself. A
         tooltip is the one place here that needs an opaque surface: it is
         over text. */
      background: var(--bg, Canvas); color: var(--fg, CanvasText);
      border: 1px solid currentColor;
      /* `rem`, not `em`: this is inside a `sup`, and an `em` size would be a
         fraction of an already smaller font, twice over in the footnotes
         section. The rest is set back to running text because a reference can
         sit inside a heading or an emphasized run. */
      font-size: .85rem; font-style: normal; font-weight: normal;
      line-height: 1.5; text-align: left; vertical-align: baseline;
      white-space: normal;
      /* It is a preview, not a target: it never takes a click meant for the
         reference underneath it, and it is not part of the sentence a reader
         drags across to copy. */
      pointer-events: none; user-select: none; }
}
@media print { .eta-report .footnote-tip { display: none; } }
.eta-report .contributors { font-size: .95rem; }
/* The back matter is set off by space, not by a rule. A page gives every
   `h2` a rule of its own, so a separator here drew a second one. */
.eta-report .footnotes, .eta-report .contributors { margin-top: 3em; }
.eta-report .table-scroll { overflow-x: auto; }
.eta-report table { border-collapse: collapse; width: 100%; font-size: .9rem; }
.eta-report td { border: 1px solid currentColor; padding: .4em .6em; vertical-align: top; }
"""


# Placement is the one thing about this tooltip that CSS cannot decide.
# Whether there is room under the reference is a question about the window,
# and the answer changes with the scroll position, so the stylesheet can only
# guess and be wrong at the top and bottom of the screen, which is exactly
# where a footnote reference the reader just jumped to tends to sit.
#
# So the box is measured and placed: under the reference when it fits there,
# over it when it does not, and never past either side. `fixed` rather than
# `absolute`, because the question was about the window and this is the
# coordinate system that answers in the window's terms.
#
# Everything else stays in the stylesheet. Without this script the tooltip
# still appears on hover, under the reference, and only near an edge of the
# screen is it in the wrong place. This positions it; it does not enable it.
REPORT_JS = """
(() => {
  const GAP = 8;
  const tipOf = (e) =>
    e.target.closest?.(".eta-report .footnote-ref")?.querySelector(".footnote-tip");
  const place = (event) => {
    // The stylesheet shows this on hover only where the device hovers, and a
    // tap raises hover on a touch screen. Asking the same question here keeps
    // the two from disagreeing.
    if (!matchMedia("(hover: hover)").matches) return;
    const tip = tipOf(event);
    if (!tip) return;
    // Laid out where it can be measured, and not yet shown there. The event
    // handler runs before the frame is painted, so nothing is drawn in this
    // position.
    tip.style.cssText =
      "display:block;visibility:hidden;position:fixed;left:0;top:0;transform:none";
    const box = tip.getBoundingClientRect();
    const ref = tip.parentElement.getBoundingClientRect();
    const below = ref.bottom + GAP;
    const above = ref.top - GAP - box.height;
    // Under it unless that runs off the bottom, and over it only if that is
    // somewhere the box actually fits: when neither edge has room, under is
    // the one the reader can scroll to.
    const top = below + box.height <= innerHeight - GAP || above < GAP ? below : above;
    const middle = ref.left + ref.width / 2 - box.width / 2;
    const left = Math.min(Math.max(middle, GAP), innerWidth - box.width - GAP);
    tip.style.cssText = `display:block;position:fixed;left:${left}px;top:${top}px;transform:none`;
  };
  // Handed back to the stylesheet, so that a box measured against one scroll
  // position is not still carrying those numbers at the next one.
  const clear = (event) => { const tip = tipOf(event); if (tip) tip.style.cssText = ""; };
  for (const name of ["pointerover", "focusin"]) document.addEventListener(name, place);
  for (const name of ["pointerout", "focusout"]) document.addEventListener(name, clear);
})();
"""


# A Squarespace code block holds 400 KB.
# Warn well before that: the limit is what the editor accepts,
# not what is pleasant to paste, and 200 KB into a textarea is already slow to save.
CODE_BLOCK_LIMIT = 400_000
CODE_BLOCK_WARN = 250_000


def escape(text: str) -> str:
    return html.escape(text, quote=True)


def split_at_headings(fragment: str) -> list[str]:
    """Cut a fragment into pieces at `h2` boundaries, for oversized reports.

    Each piece is a standalone `.eta-report` div,
    so consecutive code blocks still pick up the same CSS.
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
        # A paragraph's id is its section's id and its place in that section,
        # so both reset at every heading.
        self._scope = ""
        self._paragraphs = 0
        self._marked = True

    def anchor(self, prefix: str, text: str) -> str:
        """An id for a block, unique within the page.

        Two blocks saying exactly the same thing hash the same,
        and the second gets a counted suffix.
        That suffix is positional, which nothing else here is,
        but the blocks are indistinguishable,
        so there is nothing else to tell them apart with.
        It applies only to the duplicates.
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
        # Every id on the page is allocated here,
        # so a second `emit` of the same document produces the same ids, not suffixed ones.
        self._taken = {"title", "short", "table-of-contents", "footnotes", "contributors"}
        self._scope = ""
        self._paragraphs = 0
        self._marked = True
        self._taken.update(b.anchor for b in doc.blocks if isinstance(b, Heading))
        parts = []
        if self.inline_css:
            parts.append(f"<style>{REPORT_CSS}</style>")
        # Unlike the stylesheet, which a site can carry once under Custom CSS,
        # this travels with the report: it is small, and a fragment pasted
        # without it puts a tooltip off the edge of the screen.
        parts.append(f"<script>{REPORT_JS}</script>")
        parts.append('<div class="eta-report">')
        parts.append(self.phase(doc))
        parts.append(self.dateline(doc))
        # Below the dateline and above the hero,
        # because the hero fills the screen
        # and a warning under it is a warning nobody scrolls to.
        #
        # In the fragment as well as the page, though the fragment is what gets
        # pasted into the live site. That is the point: a report pasted with
        # warnings still on it says so at the top, where `Phase:` says it too,
        # which is what makes an accidental publish obvious rather than quiet.
        parts.append(warnings_block(doc))
        parts.append(self.blocks([doc.hero] if doc.hero is not None else []))
        parts.append(self.toc(doc))
        parts.append(self.blocks(doc.body))
        parts.append(self.footnotes(doc))
        parts.append(self.contributors(doc))
        parts.append("</div>")
        return self.join(parts)

    def contributors(self, doc: Document) -> str:
        """Who is credited, in a section at the end, the way ETA credits them.

        Not a byline under the title.
        A report is the work of most of a chapter, nine people here,
        and nine names above the first paragraph read as a masthead rather than a credit.
        The published report puts them at the bottom, after the footnotes.

        The names come from `Public Contributors:`, in the order the document lists them:
        the header block is the one place the credits are maintained,
        so reordering here would publish something no one wrote.

        No `Public Contributors:` means no section at all,
        the way `slug` is empty when the header names no URL.
        """
        names = doc.contributors
        if not names:
            return ""
        items = "\n".join(f"<li>{escape(name)}</li>" for name in names)
        return (
            '<section class="contributors" id="contributors">\n'
            f"<h2>{self.mark('contributors')}Contributors</h2>\n"
            f"<p>{CONTRIBUTORS_NOTE}</p>\n"
            f"<ul>\n{items}\n</ul>\n"
            "</section>"
        )

    def phase(self, doc: Document) -> str:
        """What a reader of a draft has to be told before reading it.

        Above the dateline rather than below it, because it qualifies the whole page:
        the date a draft is due says nothing useful
        until you know it is a draft you are holding.
        """
        if not doc.phase:
            return ""
        return f'<p class="phase">{escape(doc.phase)}</p>'

    def dateline(self, doc: Document) -> str:
        """When the report published, from `Final Due Date:` in the header.

        Absent when the header names no date.
        Plain text rather than a `<time>`,
        which only carries machine-readable meaning with an ISO stamp:
        `date_text` keeps the string the chip displays and drops the timestamp behind it.
        """
        date = doc.dateline
        if not date:
            return ""
        return f'<p class="dateline" id="date">{self.mark("date", "date")}{escape(date)}</p>'

    def toc(self, doc: Document) -> str:
        """The sections, as a list rather than a run of separated links.

        A list is what a table of contents is: one entry per line,
        leaving room to indent entries under the section they belong to.
        The published report runs them together separated by pipes,
        which reads as a sentence and has nowhere to put a subsection.

        Every heading is listed, not just the top level.
        A document that bothered to write a subsection thinks it worth finding.
        The published report lists two levels and stops,
        which is why `Ground Conditions` appears nowhere.

        The back matter is listed too, though the emitter writes those two headings.
        They are sections of the page like any other,
        and "at the end" is not an address in a report this long:
        the only other way to the footnotes is to find a reference and click it.
        Every heading the page shows is in here,
        a simpler promise than every heading but two.

        A document with no headings of its own gets no table of contents:
        a table listing only the footnotes is a link.
        """
        headings = doc.headings()
        if not headings:
            return ""
        headings = headings + self.back_matter(doc)
        return (
            '<nav class="toc" id="table-of-contents" aria-label="Table of contents">\n'
            f"{self.mark('table-of-contents', 'table of contents')}\n"
            "<strong>Table of Contents</strong>\n"
            f"{self.toc_list(headings)}\n"
            "</nav>"
        )

    def back_matter(self, doc: Document) -> list[Heading]:
        """The sections this emitter appends, as headings a table can list.

        At the top level, so they close the appendices rather than joining them:
        the footnotes are not part of the last section,
        whatever level the document gives that section's neighbours.
        """
        sections = []
        if doc.footnotes:
            sections.append(Heading(level=2, anchor="footnotes", content=[Text("Footnotes")]))
        if doc.contributors:
            sections.append(Heading(level=2, anchor="contributors", content=[Text("Contributors")]))
        return sections

    def toc_list(self, headings: list[Heading]) -> str:
        """The headings as nested lists, one level of nesting per level.

        A heading that skips a level, an `h4` directly under an `h2`,
        opens one list rather than two:
        the empty list a strict reading emits is an indent with nothing in it,
        and the document meant a subsection either way.
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
            f"<h2>{self.mark('footnotes')}Footnotes</h2>\n"
            f"<ol>\n{items}\n</ol>\n"
            "</section>"
        )

    def footnote(self, note: Footnote) -> str:
        body = self.within(f"fn{note.number}", lambda: self.blocks(note.content))
        back = (
            f'<a href="#fnref{note.number}" class="footnote-back" '
            f'aria-label="Back to footnote {note.number} in the text">↑</a>'
        )
        # Immediately after the number the list renders, rather than after the note.
        # Several of these run to a paragraph,
        # and the way back should be where the eye already is.
        #
        # Inside that first paragraph, not before it: a paragraph is a block,
        # so an arrow ahead of one sits on a line of its own
        # with the note beginning underneath.
        # Matched as a tag rather than the literal `<p>`, because the paragraph has an id.
        # The mark hangs outside the footnote's own number
        # rather than beside the arrow, which it crowded.
        mark = self.mark(f"fn{note.number}", "footnote")
        opening = re.match(r"<p\b[^>]*>", body)
        if opening:
            rest = body[opening.end() :]
            return f'<li id="fn{note.number}">{mark}{opening.group()}{back} {rest}</li>'
        return f'<li id="fn{note.number}">{mark}{back} {body}</li>'

    # ---- blocks -----------------------------------------------------

    @override
    def blocks(self, blocks: list[Block]) -> str:
        """Blocks in order, with runs of figures kept together in a row.

        The document has no way to say "these two go side by side",
        but it says they belong together
        by putting them one after another with nothing in between.
        That is the whole signal.

        A lone figure is left alone:
        wrapping one in a row would make every figure in the report
        say something about a run of one.
        """
        out: list[str] = []
        i = 0
        while i < len(blocks):
            run = i
            while run < len(blocks) and isinstance(blocks[run], Figure):
                run += 1
            if run - i > 1:
                figures = "\n".join(self.block(b) for b in blocks[i:run])
                out.append(f'<div class="figure-row">\n{figures}\n</div>')
                i = run
            else:
                out.append(self.block(blocks[i]))
                i += 1
        return self.join(out)

    def within(self, scope: str, emit: Callable[[], str]) -> str:
        """`emit()`, with the paragraphs inside it numbered from `scope`.

        A footnote and a table cell are made of paragraphs,
        but they are not passages of the report:
        numbering them along with it would put 43 between 12 and 13.
        They are numbered within whatever holds them,
        which is where anyone would count them from anyway.
        """
        was = self._scope, self._paragraphs, self._marked
        # And unmarked:
        # a footnote already has a mark and an arrow back to the text,
        # and a table cell has no margin to hang one in.
        # The ids are still there, for a link written by hand.
        self._scope, self._paragraphs, self._marked = scope, 0, False
        try:
            return emit()
        finally:
            self._scope, self._paragraphs, self._marked = was

    def mark(self, anchor: str, what: str = "section") -> str:
        """The link a block carries to itself.

        Ahead of the block's own content rather than after it,
        so every mark on the page hangs in one column:
        the link to a figure is where the link to the paragraph above it was.
        The `#` is the stylesheet's,
        so quoting a heading does not copy a character nobody wrote.
        """
        return f'<a class="link-mark" href="#{anchor}" aria-label="Link to this {what}"></a>'

    @override
    def heading(self, node: Heading) -> str:
        """Every heading carries a link to itself.

        A section of a report this long is what people send each other,
        and the anchor is already there:
        this only gives the reader something to copy it from,
        rather than reading the id out of the page source.
        """
        # The section every paragraph after this one is numbered within,
        # until the next heading opens the next one.
        self._scope, self._paragraphs = node.anchor, 0
        mark = self.mark(node.anchor)
        return (
            f'<h{node.level} id="{node.anchor}">{mark}{self.inlines(node.content)}</h{node.level}>'
        )

    @override
    def paragraph(self, node: Paragraph) -> str:
        """A paragraph is linkable, because a report this long gets quoted
        a paragraph at a time.
        One holding no text is not: nothing to hash, and nothing anyone would link to."""
        if not plain(node.content):
            return f"<p>{self.inlines(node.content)}</p>"
        self._paragraphs += 1
        counted = f"{self._scope}-p{self._paragraphs}" if self._scope else f"p{self._paragraphs}"
        anchor = self.take(counted)
        mark = self.mark(anchor, "paragraph") if self._marked else ""
        return f'<p id="{anchor}">{mark}{self.inlines(node.content)}</p>'

    @override
    def list_(self, node: List) -> str:
        """The list is linkable; its items are not.

        An item is a line rather than a passage,
        and each would want an id derived from a few words a copy edit moves around.
        The list is the unit someone links to."""
        tag = "ol" if node.kind is ListKind.NUMBER else "ul"
        text = " ".join(plain(item.content) for item in node.items)
        items = f"<{tag}>{self.items(node.items, tag)}</{tag}>"
        if not text:
            return items
        # Wrapped, because a list may hold only list items:
        # the mark cannot be a child of the `ul` the way it is a child of a `p`,
        # and inside the first item it would hang beside that item's bullet.
        anchor = self.anchor("list", text)
        return f'<div class="list-block" id="{anchor}">{self.mark(anchor, "list")}{items}</div>'

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
        # `Figure.source` is not emitted:
        # it names the original file in Drive, for whoever assembles the report,
        # and does not appear on the published page.
        parts = [self.image(node.image)]
        if node.caption:
            parts.append(
                f'<figcaption class="figure-caption">{self.inlines(node.caption)}</figcaption>'
            )
        if node.credit:
            parts.append(
                f'<figcaption class="figure-credit">{self.inlines(node.credit)}</figcaption>'
            )
        # Named for the image it holds, so the anchor is whatever the image is called:
        # the file its `Source:` line names,
        # or `img-` and a hash of the object id where there is no such line.
        # `--aspect` is a fact about the picture, written wherever it is known.
        # The stylesheet reads it twice:
        # to divide a line between the figures of a row,
        # and to cap how tall any one figure gets.
        aspect = self.doc.image_aspect(node.image)
        shape = f' style="--aspect: {aspect:.3f}"' if aspect is not None else ""
        anchor = self.take(node.image.filename)
        return (
            f'<figure id="{anchor}"{shape}>{self.mark(anchor, "figure")}{"".join(parts)}</figure>'
        )

    @override
    def table(self, node: Table) -> str:
        text = " ".join(
            plain(block.content)
            for row in node.rows
            for cell in row
            for block in cell
            if isinstance(block, Paragraph)
        )
        # The anchor first,
        # because the paragraphs in the cells are numbered within the table
        # rather than the section it sits in:
        # a comparison table's cells are not passages of the report.
        anchor = self.anchor("table", text) if text else ""
        rows = self.within(
            anchor,
            lambda: "".join(
                "<tr>" + "".join(f"<td>{self.blocks(cell)}</td>" for cell in row) + "</tr>"
                for row in node.rows
            ),
        )
        if not anchor:
            return f'<div class="table-scroll"><table>{rows}</table></div>'
        mark = self.mark(anchor, "table")
        return f'<div class="table-scroll" id="{anchor}">{mark}<table>{rows}</table></div>'

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
        # Matched by the Docs id rather than by the number,
        # which is the identity the parser guarantees on both sides.
        note = next(
            (f for f in self.doc.footnotes if f.footnote_id == node.footnote_id),
            None,
        )
        tip = tip_text(note.content) if note else ""
        # A footnote that is a table or a figure has no sentence to preview,
        # and an empty box hovering over the text is worse than none.
        preview = (
            f'<span class="footnote-tip" aria-hidden="true">{escape(tip)}</span>' if tip else ""
        )
        return (
            f'<sup id="fnref{node.number}" class="footnote-ref">'
            f'<a href="#fn{node.number}">{node.number}</a>{preview}</sup>'
        )

    @override
    def image(self, node: Image) -> str:
        href = self.doc.image_href(node)
        src = f"{self.image_base}/{href}" if self.image_base else href
        return f'<img src="{escape(src)}" alt="{escape(node.alt)}" loading="lazy">'


def plain(content: list[Inline]) -> str:
    """Inline content with all markup dropped, for the table of contents."""
    return "".join(i.text for i in content if isinstance(i, Text))


def tip_text(blocks: list[Block]) -> str:
    """A footnote as one line of text, for the tooltip its reference carries.

    Every kind of markup is dropped, links included:
    a preview is read, not clicked,
    and the note at the bottom of the page is where the link still lives.
    A line break inside a paragraph becomes a space,
    so that the words on either side of it do not run together.
    """
    words: list[str] = []
    for block in blocks:
        content: list[Inline] = []
        if isinstance(block, Paragraph):
            content = block.content
        elif isinstance(block, List):
            content = [i for item in block.items for i in item.content]
        for node in content:
            if isinstance(node, Text):
                words.append(node.text)
            elif isinstance(node, LineBreak):
                words.append(" ")
        words.append(" ")
    return " ".join("".join(words).split())


# Enough to read the report as it will look, and nothing more.
# A page pasted into Squarespace inherits that site's typography,
# so matching it here would be a guess that goes stale.
PAGE_CSS = """
:root { color-scheme: light dark; --fg: #1a1a1a; --bg: #fff; }
@media (prefers-color-scheme: dark) { :root { --fg: #eaeaea; --bg: #141414; } }
body { background: var(--bg); color: var(--fg); max-width: 46rem;
       margin: 0 auto; padding: 3rem 1.25rem 6rem;
       font: 17px/1.65 Georgia, "Times New Roman", serif; }
h1, h2, h3, h4 { font-family: system-ui, sans-serif; line-height: 1.25; }
/* The headline and standfirst sit outside `.eta-report`, so the rules that
   hang a mark beside a block do not reach them. These two do. */
#title, #short { position: relative; }
#title > .link-mark, #short > .link-mark {
  position: absolute; left: -1.15em; text-decoration: none;
  font-weight: normal; font-size: 1rem; opacity: 0; }
#title > .link-mark::before, #short > .link-mark::before { content: "#"; }
#title:hover > .link-mark, #short:hover > .link-mark,
#title > .link-mark:focus-visible, #short > .link-mark:focus-visible { opacity: .45; }
h1 { font-size: 2.1rem; margin-bottom: .2em; }
h2 { margin-top: 2.5em; border-top: 1px solid currentColor; padding-top: .8em; }
a { color: inherit; }
.standfirst { font-size: 1.15rem; opacity: .75; margin-top: 0; }
"""


def _page_mark(what: str) -> str:
    """The same self-link the emitter writes, for the two blocks the page writes itself.
    The headline and the standfirst are the page's rather than the report's,
    so they are built here and not walked to."""
    anchor = "title" if what == "title" else "short"
    return f'<a class="link-mark" href="#{anchor}" aria-label="Link to this {what}"></a>'


def _marked_up(warning: str) -> str:
    """One warning as HTML: names as code, and what gets cut struck through."""
    return warning_markup(
        warning,
        code=lambda c: f"<code>{escape(c)}</code>",
        cut=lambda c: f"<s>{escape(c)}</s>",
        text=escape,
        quote=lambda q: f"<blockquote>{q}</blockquote>",
        bullets=lambda items: "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>",
    )


def warnings_block(doc: Document) -> str:
    """Everything the build has to say about this report, where it will be read.

    A warning names a field, a file, or a line, and marks it with backticks
    the way this project writes prose everywhere else.
    Rendered as code rather than shown with the backticks in it,
    which is what a reader of the page would otherwise see.
    """
    if not doc.warnings:
        return ""
    items = "\n".join(f"<li>{_marked_up(w)}</li>" for w in doc.warnings)
    return f'<div class="warnings"><strong>Warnings</strong><ul>{items}</ul></div>'


def report_page(doc: Document, image_base: str = IMAGE_DIR) -> str:
    """The whole report as a page,
    which is what a build writes as `index.html` and what the site serves.

    Not the fragment with a wrapper bolted on.
    `report.html` is the fragment: a `div` to paste into a Squarespace code block,
    which inherits the site's typography and has nowhere to put a warning.
    This is a document, with its own head and type,
    and the parser's warnings where whoever is about to publish will see them.
    """
    body = HtmlEmitter(image_base=image_base, inline_css=False).emit(doc)
    short = doc.meta.get("short", "")
    # The share card is what a link to the report unfurls as, and the only place it appears:
    # a picture of the title, which a reader who has arrived does not need.
    # `og:image` is read by everything that unfurls a link, so it is the one tag worth writing.
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
        f'<h1 id="title">{_page_mark("title")}{escape(doc.title)}</h1>\n'
        f'<p class="standfirst" id="short">{_page_mark("standfirst")}{escape(short)}</p>\n'
        f"{body}\n"
    )
