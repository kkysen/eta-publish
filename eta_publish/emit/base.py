"""The shape every emitter shares.

Emitters are pure: tree in, string out.
Nothing here touches the network or the filesystem,
so an emitter can be tested against a fixture tree without credentials.
"""

from abc import ABC, abstractmethod

from ..nodes import (
    Block,
    Document,
    Figure,
    FootnoteRef,
    Heading,
    Image,
    Inline,
    LineBreak,
    List,
    Paragraph,
    Table,
    Text,
)

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
        return "\n".join(p for p in parts if p)

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
