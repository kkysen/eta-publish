"""HTML two ways: a fragment to embed, and a page to read.

Scoped to `.eta-report` so the same CSS works inlined into the pasted fragment
and injected once site-wide under Custom CSS.
A Squarespace code block applies no styling of its own,
so without this the captions, table of contents, and footnotes
render as undifferentiated body text.
"""

from collections.abc import Callable, Iterable
from typing import cast, override

import htpy
from htpy import Element, Node
from htpy._types import Renderable
from markupsafe import Markup

from ..assets import read
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
    Notice,
    Paragraph,
    Table,
    Text,
    plain_text,
)
from ..sentences import split
from .base import CONTRIBUTORS_NOTE, Emitter, warning_markup

# Only styles what the emitter produces, inheriting the rest from the theme,
# so a report does not fight the site around it.
REPORT_CSS = read("report.css")
"""How a report is set, in the one place the three outputs cannot share.

A file rather than a string, because it is a stylesheet and an editor
that knows one when it sees one is worth more than having it nearby.
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
REPORT_JS = read("report.js")


# A Squarespace code block holds 400 KB.
# Warn well before that: the limit is what the editor accepts,
# not what is pleasant to paste, and 200 KB into a textarea is already slow to save.
CODE_BLOCK_LIMIT = 400_000
CODE_BLOCK_WARN = 250_000


type Piece = Renderable | str | int | bool | None | Iterable[Piece]
"""What may go inside an element here: `htpy`'s `Node`, less the callable.

`htpy` will take a function returning children as a child, and nothing on
this page is one. Leaving it out is what lets `pyrefly` read the file:
it matches an element against every other member of that union on its own,
and against the whole union only once the callable is gone. `htpy` is
annotated throughout and `ty` accepts it either way, so the narrowing is
this file's, not a doubt about the library.
"""


class Tag(Element):
    """An element that takes the children this file has to give it.

    One place says the narrowing is deliberate, rather than every tag on
    the page saying it, and `htpy` keeps its own types either way.
    """

    @override
    # A parameter narrowed on purpose, which is worth saying out loud twice
    # rather than turning either checker off over.
    # pyrefly: ignore[bad-override]
    def __getitem__(self, children: Piece) -> Tag:  # ty: ignore[invalid-method-override]
        return super().__getitem__(cast(Node, children))


class Tags:
    """Every tag, by name, as a `Tag`.

    Void elements are not here: `htpy.br` and `htpy.img` hold nothing,
    and a `Tag` would offer to put something in them.
    """

    def __getattr__(self, name: str) -> Tag:
        return Tag(name.rstrip("_"))


tag = Tags()


def joined(separator: Piece, parts: Iterable[Piece]) -> Piece:
    """`parts` with `separator` between them, still as nodes.

    The string equivalent would flatten each part on the way past,
    which is where escaping gets lost: what comes back is markup again
    and the next element to hold it cannot tell that it already is.
    """
    out: list[Piece] = []
    for i, part in enumerate(parts):
        if i:
            out.append(separator)
        out.append(part)
    return out


def lines(parts: Iterable[Piece]) -> Piece:
    """One part per line.

    A newline between two blocks is whitespace HTML collapses,
    and it is what makes a diff of a rebuilt report readable:
    a changed sentence is a changed line rather than a changed file.
    """
    return joined("\n", parts)


def markup(node: Piece) -> Markup:
    """A tree of `htpy` nodes as the string the rest of the emitter passes around.

    `Markup` rather than a bare `str` because the difference matters on the way
    back in: a value that has already been escaped must not be escaped again
    when it is placed inside the next element, and `Markup` is what says so.
    The emitters share one signature, returning `str`, and `Markup` is a `str`,
    so this satisfies it without weakening it.
    """
    return Markup(htpy.fragment[node])


HTML_H2 = 2
"""The heading level a piece is cut at.

`h2` is what a report's sections are: `Heading 1` in the document,
which publishes one level down because the headline is the `h1`.
"""


def link_mark(anchor: str, what: str = "section") -> Tag:
    """The link a block carries to itself.

    Ahead of the block's own content rather than after it,
    so every mark on the page hangs in one column:
    the link to a figure is where the link to the paragraph above it was.
    The `#` is the stylesheet's,
    so quoting a heading does not copy a character nobody wrote.

    A function rather than only a method,
    because the headline and the standfirst are the page's rather than the report's:
    `report_page` writes those two itself and never walks to them,
    and the mark they carry has to be the same mark.
    """
    return tag.a(class_="link-mark", href=f"#{anchor}", aria_label=f"Link to this {what}")


class HtmlEmitter(Emitter):
    extension = ".html"

    def __init__(self, image_base: str = "", inline_css: bool = True) -> None:
        super().__init__()
        self.image_base = image_base.rstrip("/")
        # Turn off once `REPORT_CSS` lives in the site's Custom CSS.
        self.inline_css = inline_css
        self._in_tip = False
        """Whether what is being emitted is the box a reference carries,
        which is a copy of a note and so cannot carry boxes of its own."""
        self._taken: set[str] = set()
        # A paragraph's id is its section's id and its place in that section,
        # so both reset at every heading.
        self._scope = ""
        self._paragraphs = 0
        self._marked = True
        self._lead: Piece = None
        """Markup for the next paragraph to open with, inside its own tag.

        A footnote's way back into the text belongs in the first line of the
        note rather than on a line of its own above it, and where the first
        line begins is a fact about the tree.
        The paragraph that takes it clears it, so it is placed once.
        """

    @override
    def join(self, parts: list[str]) -> str:
        """The base class joins with a separator, which flattens to a plain string.

        Every part here is already markup, and a plain string is exactly what
        the next element would escape on the way in. Joined as nodes and
        marked as markup, the fact survives the join.
        """
        return markup(joined(self.separator, [part for part in parts if part]))

    @override
    def inlines(self, content: list[Inline]) -> str:
        """As `join`, for the run of inline nodes inside a block."""
        return markup([self.inline(node) for node in content])

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
        return self.join(self.wrapped(self.whole(doc)))

    def restart(self, doc: Document) -> None:
        """Forget what the last document allocated.

        Every id on the page is allocated while walking it,
        so a second walk of the same document has to start where the first did
        or it produces the same ids suffixed to avoid themselves.

        Called by `groups`, which is the walk. A report emitted whole and the
        same report emitted in pieces are two walks of one document,
        and the pieces have to carry the ids the whole one published.

        The document is set here as well as by `emit`, because a walk needs it:
        a footnote reference carries a copy of its note, which is read off the
        document rather than passed down the tree. Without this a piece keeps
        its references and loses every preview behind them, which is a
        difference nothing about the piece would show.
        """
        self.doc = doc
        self._taken = {"title", "short", "table-of-contents", "footnotes", "contributors"}
        self._scope = ""
        self._paragraphs = 0
        self._marked = True
        self._lead = None
        self._taken.update(b.anchor for b in doc.blocks if isinstance(b, Heading))

    def whole(self, doc: Document) -> list[str]:
        """Everything in the report, in one group."""
        return [part for group in self.groups(doc) for part in group]

    def wrapped(self, group: list[str]) -> list[str]:
        """One group as a standalone fragment: what a piece is, and what a report is.

        The stylesheet and the script ride on each, and each is its own
        `.eta-report` div, so consecutive code blocks still pick up the same CSS.
        """
        shell = []
        if self.inline_css:
            shell.append(markup(tag.style[Markup(f"\n{REPORT_CSS}")]))
        # Unlike the stylesheet, which a site can carry once under Custom CSS,
        # this travels with the report: it is small, and a fragment pasted
        # without it puts a tooltip off the edge of the screen.
        shell.append(markup(tag.script[Markup(f"\n{REPORT_JS}")]))
        # The wrapper is opened and closed around lines this does not hold,
        # so it is the one tag written rather than built: a `div` whose
        # children are joined by the caller cannot also be a `div` object.
        # The one pair of tags written out rather than built.
        # A group is a list of lines the caller joins, and the wrapper opens
        # before the first and closes after the last, so there is no element
        # here whose children they are. Both are constants holding nothing
        # from the document, which is what makes writing them safe.
        return [*shell, Markup('<div class="eta-report">'), *group, Markup("</div>")]

    def groups(self, doc: Document) -> list[list[str]]:
        """The report in the groups a split cuts it into: one per `h2` in the body.

        Everything ahead of the first heading goes with the first group,
        and the back matter with the last, which is where they read.

        Cut here rather than out of the finished markup.
        The emitter knows which block is a second-level heading;
        the markup only knows that some line starts with `<h2 id=`,
        which is the same fact told worse and read back out of a string
        this very method wrote.
        """
        self.restart(doc)
        parts = []
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
        parts.append(self.warnings(doc))
        parts.append(self.blocks([doc.hero] if doc.hero is not None else []))
        parts.append(self.toc(doc))

        groups: list[list[str]] = [[part for part in parts if part]]
        for block, markup in self.chunks(doc.body):
            if isinstance(block, Heading) and block.level == HTML_H2:
                groups.append([])
            if markup:
                groups[-1].append(markup)

        back = [part for part in (self.footnotes(doc), self.contributors(doc)) if part]
        groups[-1].extend(back)
        return [group for group in groups if group]

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
        return markup(
            tag.section(class_="contributors", id="contributors")[
                "\n",
                tag.h2[self.mark("contributors"), "Contributors"],
                "\n",
                tag.p[CONTRIBUTORS_NOTE],
                "\n",
                tag.ul["\n", lines(tag.li[name] for name in names), "\n"],
                "\n",
            ]
        )

    def phase(self, doc: Document) -> str:
        """What a reader of a draft has to be told before reading it.

        Above the dateline rather than below it, because it qualifies the whole page:
        the date a draft is due says nothing useful
        until you know it is a draft you are holding.
        """
        if not doc.phase:
            return ""
        return markup(tag.p(class_="phase")[doc.phase])

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
        return markup(tag.p(class_="dateline", id="date")[self.mark("date", "date"), date])

    def warnings(self, doc: Document) -> str:
        """Everything the build has to say about this report, where it will be read.

        Named as the Markdown and Typst emitters name theirs,
        because it is the same section of the same report in a third format.

        A warning names a field, a file, or a line, and marks it with backticks
        the way this project writes prose everywhere else.
        Rendered as code rather than shown with the backticks in it,
        which is what a reader of the page would otherwise see.
        """
        if not doc.warnings:
            return ""
        return markup(
            tag.div(class_="warnings")[
                tag.strong["Warnings"],
                tag.ul[lines(tag.li[self.marked_up(w)] for w in doc.warnings)],
            ]
        )

    def marked_up(self, warning: Notice) -> str:
        """One warning as HTML: names as code, and what gets cut struck through."""
        return Markup(
            warning_markup(
                warning,
                code=lambda c: markup(tag.code[c]),
                cut=lambda c: markup(tag.s[c]),
                text=lambda t: markup(t),
                quote=lambda q: markup(tag.blockquote[Markup(q)]),
                bullets=lambda items: markup(tag.ul[[tag.li[Markup(i)] for i in items]]),
            )
        )

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
        return markup(
            tag.nav(class_="toc", id="table-of-contents", aria_label="Table of contents")[
                "\n",
                self.mark("table-of-contents", "table of contents"),
                "\n",
                tag.strong["Table of Contents"],
                "\n",
                self.toc_list(headings),
                "\n",
            ]
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

    def toc_list(self, headings: list[Heading]) -> Tag:
        """The headings as nested lists, one level of nesting per level.

        A heading that skips a level, an `h4` directly under an `h2`,
        opens one list rather than two:
        the empty list a strict reading emits is an indent with nothing in it,
        and the document meant a subsection either way.

        Built as the nesting it is rather than as a run of opening and closing
        tags counted onto a stack. Nothing here can leave a list unclosed,
        because nothing here closes one.
        """
        # The shallowest level rather than the first heading's:
        # a document may open with a subsection, and the outermost list has to
        # hold every heading or the ones above it are left with nowhere to go.
        entries, rest = self.toc_level(headings, min(h.level for h in headings))
        assert not rest, "the outermost list holds every heading"
        return entries

    def toc_level(self, headings: list[Heading], depth: int) -> tuple[Tag, list[Heading]]:
        """A list of everything at `depth` or below, and the headings left over.

        A heading deeper than the one before it opens a list under that entry,
        which this calls itself to build;
        one shallower than `depth` ends this list and is handed back
        to whichever call has a level shallow enough to hold it.
        """
        items: list[Piece] = []
        while headings and headings[0].level >= depth:
            heading, headings = headings[0], headings[1:]
            link = tag.a(href=f"#{heading.anchor}")[plain_text(heading.content)]
            if headings and headings[0].level > heading.level:
                nested, headings = self.toc_level(headings, headings[0].level)
                items.append(tag.li[link, "\n", nested])
            else:
                items.append(tag.li[link])
        return tag.ul["\n", lines(items), "\n"], headings

    def footnotes(self, doc: Document) -> str:
        if not doc.footnotes:
            return ""
        return markup(
            tag.section(class_="footnotes", id="footnotes")[
                "\n",
                tag.h2[self.mark("footnotes"), "Footnotes"],
                "\n",
                tag.ol["\n", lines(self.footnote(f) for f in doc.footnotes), "\n"],
                "\n",
            ]
        )

    def footnote(self, note: Footnote) -> str:
        back = markup(
            [
                tag.a(
                    href=f"#fnref{note.number}",
                    class_="footnote-back",
                    aria_label=f"Back to footnote {note.number} in the text",
                )["↑"],
                " ",
            ]
        )
        # Immediately after the number the list renders, rather than after the note.
        # Several of these run to a paragraph,
        # and the way back should be where the eye already is.
        #
        # Inside that first paragraph, not before it: a paragraph is a block,
        # so an arrow ahead of one sits on a line of its own
        # with the note beginning underneath.
        # Handed to the paragraph to open with rather than spliced into the
        # markup afterwards: whether the note starts with a paragraph is a
        # question about the tree, and the tree is here to answer it.
        leads = bool(note.content) and isinstance(note.content[0], Paragraph)
        if leads:
            self._lead = back
        body = self.within(f"fn{note.number}", lambda: self.blocks(note.content))
        # The mark hangs outside the footnote's own number
        # rather than beside the arrow, which it crowded.
        mark = self.mark(f"fn{note.number}", "footnote")
        return markup(tag.li(id=f"fn{note.number}")[mark, None if leads else back, body])

    def tip(self, blocks: list[Block]) -> str:
        """A footnote as it reads, for the box its reference carries.

        The same markup the note itself is written in, links included:
        a note that cites a source is citing it here too,
        and a reader who can see the citation should be able to follow it.

        Inline markup only, though the note is made of blocks.
        The box lives inside a `sup` inside a paragraph,
        where a `p` of its own would end the paragraph around it,
        so each block becomes a line and the lines are separated by breaks.
        A list keeps its bullets, which are what its items are;
        a figure or a table has nothing to say in a line and says nothing.
        """
        shown: list[str] = []
        self._in_tip = True
        for block in blocks:
            match block:
                case Paragraph():
                    shown.append(self.inlines(block.content))
                case List():
                    shown.extend(
                        f"{'•' if block.kind is ListKind.BULLET else f'{n}.'} "
                        f"{self.inlines(item.content)}"
                        for n, item in enumerate(block.items, 1)
                    )
                case _:
                    continue
        self._in_tip = False
        return markup(htpy.fragment[joined(htpy.br, [line for line in shown if line])])

    def tip_text(self, blocks: list[Block]) -> str:
        """A footnote as one line of text, for deciding whether it has a box to show.

        Every kind of markup is dropped, links included:
        what is being asked is whether the note says anything,
        and `tip` is what renders it once the answer is yes.
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
        return self.join([markup for _, markup in self.chunks(blocks)])

    def chunks(self, blocks: list[Block]) -> list[tuple[Block, str]]:
        """The same markup, each piece paired with the block it starts at.

        What `blocks` joins, and what a split cuts between.
        A run of figures is one chunk paired with the first of them,
        because a row of pictures is one thing and cutting into it
        would leave half a row at the end of a piece.

        Nothing here reads the markup back:
        which chunk begins a section is a question about the blocks,
        and the blocks are right here.
        """
        out: list[tuple[Block, str]] = []
        i = 0
        while i < len(blocks):
            run = i
            while run < len(blocks) and isinstance(blocks[run], Figure):
                run += 1
            if run - i > 1:
                row = lines(self.block(b) for b in blocks[i:run])
                out.append((blocks[i], markup(tag.div(class_="figure-row")["\n", row, "\n"])))
                i = run
            else:
                out.append((blocks[i], self.block(blocks[i])))
                i += 1
        return out

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

    def mark(self, anchor: str, what: str = "section") -> Tag:
        return link_mark(anchor, what)

    def link(self, href: str) -> Tag:
        """An `a` for the prose, opened but not yet given what it holds.

        Inside the box a reference carries, every link is a copy of one the
        note already has, and the note is a jump away: the keyboard should
        walk past the copy rather than stop at it.
        Decided here, where the link is written and the emitter knows which
        of the two it is writing, rather than by rewriting `<a ` afterwards
        in the finished markup.
        """
        return tag.a(tabindex="-1" if self._in_tip else None, href=href)

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
        # The level is a number the document chose, so the element is looked up
        # by name. `htpy` answers for any tag, which is the one place here
        # a tag is not written down.
        heading = getattr(tag, f"h{node.level}")
        return markup(heading(id=node.anchor)[self.mark(node.anchor), self.inlines(node.content)])

    @override
    def paragraph(self, node: Paragraph) -> str:
        """A paragraph is linkable, because a report this long gets quoted
        a paragraph at a time.
        One holding no text is not: nothing to hash, and nothing anyone would link to."""
        lead, self._lead = self._lead, None
        if not plain_text(node.content):
            return markup(tag.p[lead, self.inlines(node.content)])
        self._paragraphs += 1
        counted = f"{self._scope}-p{self._paragraphs}" if self._scope else f"p{self._paragraphs}"
        anchor = self.take(counted)
        mark = self.mark(anchor, "paragraph") if self._marked else None
        return markup(tag.p(id=anchor)[lead, mark, self.inlines(node.content)])

    @override
    def list_(self, node: List) -> str:
        """The list is linkable; its items are not.

        An item is a line rather than a passage,
        and each would want an id derived from a few words a copy edit moves around.
        The list is the unit someone links to."""
        listing = tag.ol if node.kind is ListKind.NUMBER else tag.ul
        text = " ".join(plain_text(item.content) for item in node.items)
        items = listing[self.items(node.items, listing)]
        if not text:
            return markup(items)
        # Wrapped, because a list may hold only list items:
        # the mark cannot be a child of the `ul` the way it is a child of a `p`,
        # and inside the first item it would hang beside that item's bullet.
        anchor = self.anchor("list", text)
        return markup(tag.div(class_="list-block", id=anchor)[self.mark(anchor, "list"), items])

    def items(self, items: list[ListItem], listing: Tag) -> Piece:
        out: list[Piece] = []
        for item in items:
            nested = listing[self.items(item.children, listing)] if item.children else None
            out.append(tag.li[self.inlines(item.content), nested])
        return out

    @override
    def figure(self, node: Figure) -> str:
        # `Figure.source` is not emitted:
        # it names the original file in Drive, for whoever assembles the report,
        # and does not appear on the published page.
        parts: list[Piece] = [self.image(node.image)]
        if node.caption:
            parts.append(tag.figcaption(class_="figure-caption")[self.inlines(node.caption)])
        if node.credit:
            parts.append(tag.figcaption(class_="figure-credit")[self.inlines(node.credit)])
        # Named for the image it holds, so the anchor is whatever the image is called:
        # the file its `Source:` line names,
        # or `img-` and a hash of the object id where there is no such line.
        # `--aspect` is a fact about the picture, written wherever it is known.
        # The stylesheet reads it twice:
        # to divide a line between the figures of a row,
        # and to cap how tall any one figure gets.
        aspect = self.doc.image_aspect(node.image)
        shape = f"--aspect: {aspect:.3f}" if aspect is not None else None
        anchor = self.take(node.image.filename)
        return markup(tag.figure(id=anchor, style=shape)[self.mark(anchor, "figure"), parts])

    @override
    def table(self, node: Table) -> str:
        text = " ".join(
            plain_text(block.content)
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
            lambda: markup(
                [tag.tr[[tag.td[self.blocks(cell)] for cell in row]] for row in node.rows]
            ),
        )
        if not anchor:
            return markup(tag.div(class_="table-scroll")[tag.table[rows]])
        return markup(
            tag.div(class_="table-scroll", id=anchor)[self.mark(anchor, "table"), tag.table[rows]]
        )

    # ---- inline -----------------------------------------------------

    @override
    def text(self, node: Text) -> str:
        out: Piece = joined("\n", split(node.text))
        if node.sup:
            out = tag.sup[out]
        elif node.sub:
            out = tag.sub_[out]
        if node.bold:
            out = tag.strong[out]
        if node.italic:
            out = tag.em[out]
        if node.underline:
            out = tag.u[out]
        if node.href:
            out = self.link(node.href)[out]
        return markup(out)

    @override
    def line_break(self, node: LineBreak) -> str:
        return markup(htpy.br)

    @override
    def footnote_ref(self, node: FootnoteRef) -> str:
        # A footnote can itself carry a reference to another one.
        # Inside a box there is nothing to hover, and a note that reaches
        # itself would build a box out of a box without end,
        # so a reference in a box is only the number it is.
        if self._in_tip:
            return markup(
                tag.sup(class_="footnote-ref")[self.link(f"#fn{node.number}")[node.number]]
            )
        # Matched by the Docs id rather than by the number,
        # which is the identity the parser guarantees on both sides.
        note = next(
            (f for f in self.doc.footnotes if f.footnote_id == node.footnote_id),
            None,
        )
        # A footnote that is a table or a figure has no sentence to show,
        # and an empty box hovering over the text is worse than none.
        tip = self.tip(note.content) if note and self.tip_text(note.content) else ""
        preview = tag.span(class_="footnote-tip", aria_hidden="true")[tip] if tip else None
        return markup(
            tag.sup(id=f"fnref{node.number}", class_="footnote-ref")[
                tag.a(href=f"#fn{node.number}")[node.number], preview
            ]
        )

    @override
    def image(self, node: Image) -> str:
        href = self.doc.image_href(node)
        src = f"{self.image_base}/{href}" if self.image_base else href
        return markup(htpy.img(src=src, alt=node.alt, loading="lazy"))


# Enough to read the report as it will look, and nothing more.
# A page pasted into Squarespace inherits that site's typography,
# so matching it here would be a guess that goes stale.
PAGE_CSS = read("page.css")


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
    card: list[Piece] = []
    if doc.card is not None:
        href = doc.image_href(doc.card)
        src = f"{image_base}/{href}" if image_base else href
        card.append(htpy.meta(property="og:image", content=src))
        if doc.card.alt:
            card.append(htpy.meta(property="og:image:alt", content=doc.card.alt))
    head: list[Piece] = [
        htpy.meta(charset="utf-8"),
        htpy.meta(name="viewport", content="width=device-width, initial-scale=1"),
        tag.title[doc.title],
        htpy.meta(name="description", content=doc.meta.get("seo description", "")),
        *card,
        tag.style[Markup(f"\n{PAGE_CSS}\n{REPORT_CSS}")],
        tag.h1(id="title")[link_mark("title", "title"), doc.title],
        tag.p(class_="standfirst", id="short")[link_mark("short", "standfirst"), short],
    ]
    # `<!doctype html>` is not an element and no builder emits one.
    return markup([Markup("<!doctype html>"), "\n", lines(head), "\n", Markup(body), "\n"])
