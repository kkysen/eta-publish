"""The shape every emitter shares.

Emitters are pure: tree in, string out.
Nothing here touches the network or the filesystem,
so an emitter can be tested against a fixture tree without credentials.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

from ..nodes import (
    Block,
    Cut,
    Document,
    Figure,
    FootnoteRef,
    Heading,
    Highlighted,
    Image,
    Inline,
    LineBreak,
    List,
    Listed,
    Notice,
    Paragraph,
    Quoted,
    Shown,
    Span,
    Table,
    Text,
)


def warning_markup(
    notice: Notice,
    *,
    code: Callable[[str], str],
    cut: Callable[[str], str],
    text: Callable[[str], str],
    quote: Callable[[str], str] | None = None,
    bullets: Callable[[list[str]], str] | None = None,
    marked: Callable[[str, str, str], str] | None = None,
) -> str:
    """`notice` rendered: its shown values, its quoted and listed lines, the rest as `text`.

    A walk over the pieces a warning is made of, not a parse of a string,
    so a value holding a backtick is a value holding a backtick
    rather than the end of one span and the start of another.

    An emitter that cannot set a quotation or a list apart passes neither,
    and gets the lines run together as the text they are.

    `marked` is the same bargain for the part of a value a warning is pointing
    at: an emitter that can draw a highlight takes the three pieces and draws
    one, and an emitter that cannot gets the value whole, with the middle dot
    standing in for what it cannot show.
    """
    out: list[str] = []
    for part in notice.parts:
        match part:
            case Shown(value):
                out.append(code(value))
            case Cut(value):
                out.append(cut(value))
            case Highlighted():
                out.append(_highlighted(part, code, marked))
            case Quoted(spans):
                rendered = _spans(spans, code, cut, text, marked)
                out.append(quote(rendered) if quote is not None else rendered)
            case Listed(items):
                lines = [_spans(item, code, cut, text, marked) for item in items]
                out.append(bullets(lines) if bullets is not None else "".join(lines))
            case _:
                out.append(text(part))
    return "".join(out)


def _highlighted(
    part: Highlighted,
    code: Callable[[str], str],
    marked: Callable[[str, str, str], str] | None,
) -> str:
    """One highlighted value, marked where the emitter can mark part of one."""
    if marked is None:
        return code(part.value)
    return marked(part.before, part.marked, part.after)


def _spans(
    spans: tuple[Span, ...],
    code: Callable[[str], str],
    cut: Callable[[str], str],
    text: Callable[[str], str],
    marked: Callable[[str, str, str], str] | None = None,
) -> str:
    """The spans of one line, which hold no lines of their own."""
    out = []
    for span in spans:
        match span:
            case Shown(value):
                out.append(code(value))
            case Cut(value):
                out.append(cut(value))
            case Highlighted():
                out.append(_highlighted(span, code, marked))
            case _:
                out.append(text(span))
    return "".join(out)


# The line a report introduces its contributors with.
# The header block names who they are; this says what naming them means.
CONTRIBUTORS_NOTE = (
    "We wish to acknowledge the following ETA members who contributed to "
    "this report, and without whose hard work it would not be possible:"
)


class Emitter(ABC):
    """Walks a `Document` and returns source in one output format.

    Every node kind is an abstract method, so adding one
    fails loudly in every emitter rather than being skipped by one.

    `list_` carries a trailing underscore because a method named `list`
    would shadow the builtin throughout the class body,
    and every `list[...]` annotation in this file would resolve to the method.
    """

    extension: str = ""

    separator: str = "\n"
    """What `join` puts between blocks.

    A newline is enough for HTML, where the tags say where a block ends.
    """

    def __init__(self) -> None:
        # Set by `emit`, the only entry point.
        # Node methods read it for document-wide context, so calling one directly fails.
        self.doc = Document()
        self.source_numbers: dict[str, int] = {}

    def emit(self, doc: Document) -> str:
        self.doc = doc
        self.number_sources(doc)
        return self.document(doc)

    def number_sources(self, doc: Document) -> None:
        """Fix the number each source is cited by, once per document.

        Once, because every link asks: `Document.sources` walks the whole tree
        to answer, and asking it per link would walk the report once per
        citation of it.
        """
        self.source_numbers = {source: n for n, source in enumerate(doc.sources, start=1)}

    def source_number(self, href: str | None) -> int:
        """Which source `href` is, or zero if it is not one of them.

        Zero for a link no output points at: the `Source:` line of a figure is
        kept in the Markdown archive as a comment, and a comment is not a
        citation.
        """
        return self.source_numbers.get(href or "", 0)

    # ---- dispatch ---------------------------------------------------

    def blocks(self, blocks: list[Block]) -> str:
        return self.join([self.block(b) for b in blocks])

    def block(self, node: Block) -> str:
        match node:
            case Heading():
                return self.heading(node)
            case Paragraph():
                return self.paragraph(node)
            case List():
                return self.list_(node)
            case Figure():
                return self.figure(node)
            case Table():
                return self.table(node)

    def inlines(self, content: list[Inline]) -> str:
        return "".join(self.inline(i) for i in content)

    def inline(self, node: Inline) -> str:
        match node:
            case Text():
                return self.text(node)
            case LineBreak():
                return self.line_break(node)
            case FootnoteRef():
                return self.footnote_ref(node)
            case Image():
                return self.image(node)

    # ---- overridable ------------------------------------------------

    def join(self, parts: list[str]) -> str:
        return self.separator.join(p for p in parts if p)

    @abstractmethod
    def document(self, doc: Document) -> str: ...

    @abstractmethod
    def heading(self, node: Heading) -> str: ...

    @abstractmethod
    def paragraph(self, node: Paragraph) -> str: ...

    @abstractmethod
    def list_(self, node: List) -> str: ...

    @abstractmethod
    def figure(self, node: Figure) -> str: ...

    @abstractmethod
    def table(self, node: Table) -> str: ...

    @abstractmethod
    def text(self, node: Text) -> str: ...

    @abstractmethod
    def line_break(self, node: LineBreak) -> str: ...

    @abstractmethod
    def footnote_ref(self, node: FootnoteRef) -> str: ...

    @abstractmethod
    def image(self, node: Image) -> str: ...
