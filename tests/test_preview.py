"""The preview page, whose whole purpose is being readable before publishing."""

import json
import re
from pathlib import Path

import pytest

from eta_publish.build import emit
from eta_publish.emit.html import preview_page
from eta_publish.nodes import Document
from eta_publish.parse import parse

FIXTURE = json.loads((Path(__file__).parent / "fixture-doc.json").read_text())


@pytest.fixture
def doc() -> Document:
    parsed = parse(FIXTURE)
    parsed.image_files["io.1"] = "img-1933bef5.png"
    return parsed


def test_preview_images_resolve_next_to_the_page(doc: Document, tmp_path: Path) -> None:
    """Everything a build writes references its images the same way: by the
    path they sit at, right beside the page."""
    images = tmp_path / "images"
    images.mkdir()
    (images / "img-1933bef5.png").write_bytes(b"not really a png")

    emit(doc, tmp_path)
    page = (tmp_path / "preview.html").read_text()

    sources = re.findall(r'<img src="([^"]+)"', page)
    assert sources
    for src in sources:
        assert not src.startswith("http")
        assert (tmp_path / src).exists(), f"{src} does not resolve next to preview.html"


def test_the_published_fragment_points_beside_itself(doc: Document, tmp_path: Path) -> None:
    """A build writes the images it references, so the fragment names them
    where they were written. Serving them from somewhere else is the
    emitter's `image_base`, which is not something a build decides."""
    (tmp_path / "images").mkdir()
    emit(doc, tmp_path)
    fragment = (tmp_path / "report.html").read_text()
    assert 'src="images/img-1933bef5.png"' in fragment
    assert "http" not in re.findall(r'<img src="([^"]+)"', fragment)[0]


def test_warnings_are_shown_where_someone_will_see_them() -> None:
    doc = parse(FIXTURE)
    doc.warn("something looked wrong")
    assert "something looked wrong" in preview_page(doc)


def test_no_warnings_means_no_warning_box(doc: Document) -> None:
    assert doc.warnings == []
    assert 'class="warnings"' not in preview_page(doc)


def test_markdown_images_resolve_next_to_the_archive(doc: Document, tmp_path: Path) -> None:
    """The archive is read from the repository, where the files sit beside
    it, not from whatever host serves the published site."""
    images = tmp_path / "images"
    images.mkdir()
    (images / "img-1933bef5.png").write_bytes(b"not really a png")

    emit(doc, tmp_path)
    archive = (tmp_path / "report.md").read_text()

    links = re.findall(r"!\[[^\]]*\]\(<([^>]+)>\)", archive)
    assert links
    for link in links:
        assert not link.startswith("http")
        assert (tmp_path / link).exists(), f"{link} does not resolve next to report.md"
