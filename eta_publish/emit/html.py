"""HTML for the Squarespace code block, and for the standalone preview.

Scoped to `.eta-report` so the same CSS works inlined into the pasted
fragment and injected once site-wide under Custom CSS. A Squarespace code
block applies no styling of its own, so without this the captions, table
of contents, and footnotes render as undifferentiated body text.
"""

from __future__ import annotations

import html

from ..nodes import Document, Figure, FootnoteRef, Heading, Image, List, ListItem, Paragraph, Table, Text
from .base import Emitter


class HtmlEmitter(Emitter):
    extension = ".html"

    def __init__(self, image_base: str = "") -> None:
        self.image_base = image_base.rstrip("/")

    def document(self, doc: Document) -> str:
        parts = ['<div class="eta-report">', self.toc(doc), self.blocks(doc.blocks)]
        parts.append(self.footnotes(doc))
        parts.append("</div>")
        return self.join(parts)

    def toc(self, doc: Document) -> str:
        raise NotImplementedError

    def footnotes(self, doc: Document) -> str:
        raise NotImplementedError

    def heading(self, node: Heading) -> str:
        raise NotImplementedError

    def paragraph(self, node: Paragraph) -> str:
        raise NotImplementedError

    def list(self, node: List) -> str:
        raise NotImplementedError

    def figure(self, node: Figure) -> str:
        raise NotImplementedError

    def table(self, node: Table) -> str:
        raise NotImplementedError

    def text(self, node: Text) -> str:
        raise NotImplementedError

    def footnote_ref(self, node: FootnoteRef) -> str:
        raise NotImplementedError

    def image(self, node: Image) -> str:
        raise NotImplementedError
