"""Typst source, compiled to the report PDF.

Typst rather than HTML-to-PDF because footnotes belong at the bottom of
the page. HTML can only place them at the end of the document, and with 21
of them carrying real argument, that is the difference between a report
and a printout of a web page.

The emitted file is a document body that imports a template, so the ETA
house style lives in one place and is not regenerated per report.
"""

from __future__ import annotations

from typing import override

from ..nodes import Document, Figure, FootnoteRef, Heading, Image, List, Paragraph, Table, Text
from .base import Emitter


class TypstEmitter(Emitter):
    extension = ".typ"

    @override
    def document(self, doc: Document) -> str:
        raise NotImplementedError

    @override
    def heading(self, node: Heading) -> str:
        raise NotImplementedError

    @override
    def paragraph(self, node: Paragraph) -> str:
        raise NotImplementedError

    @override
    def list_(self, node: List) -> str:
        raise NotImplementedError

    @override
    def figure(self, node: Figure) -> str:
        raise NotImplementedError

    @override
    def table(self, node: Table) -> str:
        raise NotImplementedError

    @override
    def text(self, node: Text) -> str:
        raise NotImplementedError

    @override
    def footnote_ref(self, node: FootnoteRef) -> str:
        """Typst inlines the footnote body at the reference site, so this
        reaches back into `self.doc.footnotes` rather than emitting a marker."""
        raise NotImplementedError

    @override
    def image(self, node: Image) -> str:
        raise NotImplementedError
