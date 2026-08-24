"""Nothing may vanish between the Google Doc and an output.

This is the failure the whole tool exists to prevent, and the one it has
actually hit: an early front-matter bug dropped the hero image and its
caption with nothing reported. Structure tests did not catch it, because
the structure that remained was perfectly well-formed.

There are two separate halves to check, and only together do they cover it:

- **source to tree**, that the parser keeps everything the document holds.
  This is the half that catches a bug like the front-matter overrun.
- **tree to output**, that no emitter loses what the parser produced.

The second cannot substitute for the first. If the parser drops something,
it is absent from both sides of a tree-to-output comparison, and that check
passes while the content is gone.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import override

import pytest
from test_front_matter import REAL_SHAPE

from eta_publish.docs_json import JsonObject
from eta_publish.emit.base import Emitter
from eta_publish.emit.html import HtmlEmitter
from eta_publish.emit.markdown import MarkdownEmitter
from eta_publish.emit.typst import TypstEmitter
from eta_publish.nodes import (
    Block,
    Document,
    Figure,
    Heading,
    Inline,
    List,
    ListItem,
    Paragraph,
    Table,
    Text,
)
from eta_publish.parse import parse

FIXTURE = json.loads((Path(__file__).parent / "fixture-doc.json").read_text())


def _inline_text(content: list[Inline]) -> list[str]:
    return [i.text for i in content if isinstance(i, Text)]


def _block_text(block: Block) -> list[str]:
    match block:
        case Paragraph() | Heading():
            return _inline_text(block.content)
        case List():
            return _items_text(block.items)
        case Figure():
            # `source` is excluded on purpose: it is an editorial note, and
            # the published outputs are supposed to drop it.
            return _inline_text(block.caption) + _inline_text(block.credit)
        case Table():
            return [t for row in block.rows for cell in row for t in _tree_text(cell)]
    return []


def _items_text(items: list[ListItem]) -> list[str]:
    out: list[str] = []
    for item in items:
        out += _inline_text(item.content)
        out += _items_text(item.children)
    return out


def _tree_text(blocks: list[Block]) -> list[str]:
    return [t for block in blocks for t in _block_text(block)]


def document_text(doc: Document) -> list[str]:
    """Every piece of prose the document carries, including footnote bodies."""
    out = _tree_text(doc.blocks)
    for note in doc.footnotes:
        out += _tree_text(note.content)
    return [t.strip() for t in out if t.strip()]


def normalize(text: str) -> str:
    """Compare on words alone.

    Each emitter escapes differently, and differently again per character:
    HTML turns `MTA's` into `MTA&#x27;s`, Typst backslash-escapes `$`, and
    the Markdown emitter re-breaks lines at sentences. Anything finer than
    words would be comparing formatting rather than content.
    """
    unescaped = html.unescape(re.sub(r"\\(.)", r"\1", text))
    return " ".join(unescaped.split())


@pytest.fixture
def doc() -> Document:
    parsed = parse(FIXTURE)
    parsed.image_extensions["io.1"] = ".png"
    return parsed


@pytest.mark.parametrize(
    "emitter", [HtmlEmitter(), MarkdownEmitter(), TypstEmitter()], ids=lambda e: type(e).__name__
)
def test_no_text_is_lost(emitter: Emitter, doc: Document) -> None:
    haystack = normalize(emitter.emit(doc))
    missing = [t for t in document_text(doc) if normalize(t) not in haystack]
    assert not missing, f"{type(emitter).__name__} dropped: {missing}"


@pytest.mark.parametrize(
    "emitter", [HtmlEmitter(), MarkdownEmitter(), TypstEmitter()], ids=lambda e: type(e).__name__
)
def test_every_image_reaches_the_output(emitter: Emitter, doc: Document) -> None:
    out = emitter.emit(doc)
    for image in doc.images:
        assert image.filename in out, f"{type(emitter).__name__} dropped {image.object_id}"


def test_the_check_can_actually_fail(doc: Document) -> None:
    """A completeness test that cannot fail is worse than none, since it
    reads like coverage. Drop a block and the check must notice."""

    class Lossy(HtmlEmitter):
        @override
        def paragraph(self, node: Paragraph) -> str:
            return ""

    haystack = normalize(Lossy().emit(doc))
    assert [t for t in document_text(doc) if normalize(t) not in haystack]


# ---- source to tree -------------------------------------------------


def source_text(doc_json: JsonObject) -> list[str]:
    """Every text run in the raw API response, body and footnotes alike."""
    out: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            run = node.get("textRun")
            if isinstance(run, dict):
                out.append(str(run.get("content", "")))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(doc_json.get("body", {}))
    walk(doc_json.get("footnotes", {}))
    return [t.strip() for t in out if t.strip()]


# The `Header` marker itself is structure, not content: it names the front
# matter block and is meant to be consumed with it.
CONSUMED = {"header"}


def tree_text(doc: Document) -> str:
    """Everything the parser kept, including what it moved into metadata.

    Front-matter lines are reassembled as `key: value`, since that is how
    they appear in the document, and folded to lowercase because the parser
    lowercases keys on the way in. Case is not what this check is about.
    """
    parts = document_text(doc) + [doc.title]
    parts += [f"{key}: {value}" for key, value in doc.meta.items()]
    for block in doc.blocks:
        if isinstance(block, Figure):
            parts += _inline_text(block.source)
    return normalize(" \u241f ".join(parts)).lower()


@pytest.mark.parametrize("fixture", [FIXTURE, REAL_SHAPE], ids=["fixture", "real-shape"])
def test_the_parser_keeps_everything_the_document_holds(fixture: JsonObject) -> None:
    """The half that catches a parser bug rather than an emitter bug."""
    doc = parse(fixture)
    kept = tree_text(doc)
    missing = [
        t
        for t in source_text(fixture)
        if t.lower() not in CONSUMED and normalize(t).lower() not in kept
    ]
    assert not missing, f"the parser dropped: {missing}"


def test_the_parser_check_catches_the_front_matter_overrun() -> None:
    """The bug that motivated all of this: a front-matter scan running past
    the headline swallowed the hero image, its caption, and the addendum."""
    doc = parse(REAL_SHAPE)
    overrun = Document(
        title=doc.title,
        meta=doc.meta,
        blocks=[],  # everything after the header consumed
        footnotes=doc.footnotes,
    )
    kept = tree_text(overrun)
    missing = [
        t
        for t in source_text(REAL_SHAPE)
        if t.lower() not in CONSUMED and normalize(t).lower() not in kept
    ]
    assert missing, "the check must notice content the parser never produced"
