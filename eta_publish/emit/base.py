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
) -> str:
    """`notice` rendered: its shown values, its quoted and listed lines, the rest as `text`.

    A walk over the pieces a warning is made of, not a parse of a string,
    so a value holding a backtick is a value holding a backtick
    rather than the end of one span and the start of another.

    An emitter that cannot set a quotation or a list apart passes neither,
    and gets the lines run together as the text they are.
    """
    out: list[str] = []
    for part in notice.parts:
        match part:
            case Shown(value):
                out.append(code(value))
            case Cut(value):
                out.append(cut(value))
            case Quoted(spans):
                rendered = _spans(spans, code, cut, text)
                out.append(quote(rendered) if quote is not None else rendered)
            case Listed(items):
                lines = [_spans(item, code, cut, text) for item in items]
                out.append(bullets(lines) if bullets is not None else "".join(lines))
            case _:
                out.append(text(part))
    return "".join(out)


def _spans(
    spans: tuple[Span, ...],
    code: Callable[[str], str],
    cut: Callable[[str], str],
    text: Callable[[str], str],
) -> str:
    """The spans of one line, which hold no lines of their own."""
    out = []
    for span in spans:
        match span:
            case Shown(value):
                out.append(code(value))
            case Cut(value):
                out.append(cut(value))
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

    def emit(self, doc: Document) -> str:
        self.doc = doc
        return self.document(doc)

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
