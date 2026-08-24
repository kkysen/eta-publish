"""The shape every emitter shares.

Emitters are pure: tree in, string out. Nothing here touches the network
or the filesystem, so an emitter can be tested against a fixture tree
without credentials.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..nodes import Block, Document, Figure, Heading, Inline, List, Paragraph, Table


class Emitter(ABC):
    """Walks a `Document` and returns source in one output format.

    Subclasses implement the per-node methods. The dispatch and the
    traversal live here so that adding a node type fails loudly in every
    emitter at once rather than being silently skipped by one of them.
    """

    extension: str = ""

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
                return self.list(node)
            case Figure():
                return self.figure(node)
            case Table():
                return self.table(node)
        raise NotImplementedError(f"{type(self).__name__} cannot emit {type(node).__name__}")

    def inlines(self, content: list[Inline]) -> str:
        return "".join(self.inline(i) for i in content)

    def inline(self, node: Inline) -> str:
        from ..nodes import FootnoteRef, Image, Text

        match node:
            case Text():
                return self.text(node)
            case FootnoteRef():
                return self.footnote_ref(node)
            case Image():
                return self.image(node)
        raise NotImplementedError(f"{type(self).__name__} cannot emit {type(node).__name__}")

    # ---- overridable ------------------------------------------------

    def join(self, parts: list[str]) -> str:
        return "\n".join(p for p in parts if p)

    @abstractmethod
    def document(self, doc: Document) -> str: ...

    @abstractmethod
    def heading(self, node) -> str: ...

    @abstractmethod
    def paragraph(self, node) -> str: ...

    @abstractmethod
    def list(self, node) -> str: ...

    @abstractmethod
    def figure(self, node) -> str: ...

    @abstractmethod
    def table(self, node) -> str: ...

    @abstractmethod
    def text(self, node) -> str: ...

    @abstractmethod
    def footnote_ref(self, node) -> str: ...

    @abstractmethod
    def image(self, node) -> str: ...
