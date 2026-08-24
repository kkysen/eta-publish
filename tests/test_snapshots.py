"""Byte-for-byte comparison against committed output.

`emit(doc) == emit(doc)` in one process proves nothing: hash randomization
is per-interpreter, so anything order- or hash-dependent still matches
itself. A committed file compares across runs, and doubles as the diff that
shows what a parser change actually did to the output.

Regenerate with `pytest --regenerate-snapshots` after checking the diff.
"""

import json
from pathlib import Path

import pytest

from eta_publish.emit.html import HtmlEmitter
from eta_publish.emit.markdown import MarkdownEmitter
from eta_publish.emit.typst import TypstEmitter
from eta_publish.nodes import Document
from eta_publish.parse import parse

SNAPSHOTS = Path(__file__).parent / "snapshots"
FIXTURE = json.loads((Path(__file__).parent / "fixture-doc.json").read_text())


@pytest.fixture
def doc() -> Document:
    parsed = parse(FIXTURE)
    parsed.image_files["io.1"] = "img-1933bef5.png"
    return parsed


def check(name: str, actual: str, regenerate: bool) -> None:
    path = SNAPSHOTS / name
    if regenerate or not path.exists():
        path.write_text(actual)
        if not regenerate:
            pytest.fail(f"{path} did not exist; wrote it, review and commit")
        return
    assert actual == path.read_text(), (
        f"{path} differs; review the change and rerun with --regenerate-snapshots"
    )


def test_html_matches_snapshot(doc: Document, regenerate_snapshots: bool) -> None:
    emitted = HtmlEmitter(image_base="https://assets.etany.org/sas-west").emit(doc)
    check("report.html", emitted, regenerate_snapshots)


def test_markdown_matches_snapshot(doc: Document, regenerate_snapshots: bool) -> None:
    check("report.md", MarkdownEmitter().emit(doc), regenerate_snapshots)


def test_typst_matches_snapshot(doc: Document, regenerate_snapshots: bool) -> None:
    check("report.typ", TypstEmitter().emit(doc), regenerate_snapshots)
