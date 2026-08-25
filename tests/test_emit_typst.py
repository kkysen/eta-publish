"""Typst source, and that it actually compiles."""

import base64
import json
import shutil
from pathlib import Path

import pytest

from eta_publish.emit.typst import TypstEmitter
from eta_publish.nodes import Document
from eta_publish.parse import parse
from eta_publish.pdf import compile_pdf, install_template

FIXTURE_DIR = Path(__file__).parent / "fixture"
FIXTURE = json.loads((FIXTURE_DIR / "doc.json").read_text())
# A 1x1 PNG, so the figure path is exercised without checking in an asset.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture
def doc() -> Document:
    parsed = parse(FIXTURE)
    parsed.image_files["io.1"] = "img-1933bef5.png"
    return parsed


@pytest.fixture
def out(doc: Document) -> str:
    return TypstEmitter().emit(doc)


def test_footnote_bodies_are_inlined_at_the_reference(out: str) -> None:
    """Typst numbers and places footnotes itself, so there is no separate
    list that can fall out of sync with the references."""
    assert "#footnote[Inflation-adjusted from the 2024 capital plan.]" in out
    assert "#footnote[Measured from street level to platform.]" in out


def test_headings_map_to_typst_depth(out: str) -> None:
    assert "\n= The Elephants in the Room" in out
    assert "\n== Ground Conditions" in out


def test_the_source_line_is_not_emitted(out: str) -> None:
    assert "sas-west-036.jpg" not in out
    assert "Source:" not in out


def test_figures_carry_caption_and_credit(out: str) -> None:
    assert 'image("images/img-1933bef5.png", width: 100%)' in out
    assert "The SAS West and Phase 2 alignments." in out
    assert "Credit: MTA" in out
    assert "#emph[Credit: MTA]" not in out


def test_markup_characters_in_prose_are_escaped(out: str) -> None:
    """`$` starts math mode in Typst, so an unescaped price breaks the build."""
    assert r"\$7.7 billion" in out


def test_metadata_keys_become_valid_identifiers(out: str) -> None:
    assert "seo_description:" in out
    assert "seo description:" not in out


@pytest.mark.skipif(shutil.which("typst") is None, reason="typst is not installed")
def test_the_emitted_source_compiles(doc: Document, tmp_path: Path) -> None:
    """Escaping and syntax errors only show up here."""
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "img-1933bef5.png").write_bytes(PNG)
    source = tmp_path / "report.typ"
    source.write_text(TypstEmitter().emit(doc))
    install_template(tmp_path)

    pdf = compile_pdf(source)
    assert pdf.exists()
    assert pdf.read_bytes().startswith(b"%PDF")


def test_tables_declare_their_column_count(out: str) -> None:
    assert "#table(\n  columns: 2," in out
    assert "[Grand Paris Express]," in out
    # `$` opens math mode, so a currency figure in a cell needs escaping too.
    assert r"[\$530M]," in out
