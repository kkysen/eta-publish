"""Markdown for the committed, diffable archive.

Pandoc-flavored, because CommonMark has no footnotes and these reports are
built on them.

Lines break at sentence and clause boundaries rather than wrapping to a
fixed width. Without that a paragraph is one line, and correcting a single
word shows up as the whole paragraph changing. The splitter is
deliberately conservative: the text is full of `125 St.`, `Phase 2.`, and
`$7.7 billion.`, and an over-eager rule would churn the diff on every
regeneration. Its behavior is pinned; changing it reflows every file and
should be its own commit.
"""

from __future__ import annotations

from ..nodes import Document, Figure, FootnoteRef, Heading, Image, List, Paragraph, Table, Text
from .base import Emitter


class MarkdownEmitter(Emitter):
    extension = ".md"

    def document(self, doc: Document) -> str:
        raise NotImplementedError

    def front_matter(self, doc: Document) -> str:
        """The doc's `Header` section, as YAML."""
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
