"""Snapshot of the real SAS West report, end to end.

`tests/real/sas-west.doc.json` is an actual `documents.get` response for the
published report, so this is the only test that exercises the parser against
a document nobody wrote to make a point. Every bug that mattered so far came
from that document's shape rather than from a hand-built fixture, and `out/`
is ignored, so without this the next refactor could regress all of it
silently.

The snapshots are committed output. When one changes, read the diff: it is
exactly what the change does to a real published report. Regenerate with
`pytest --regenerate-golden` once the diff looks right.

Image extensions are recorded alongside in `sas-west.images.json`. They
cannot be derived: a Docs `inlineObject` carries a `contentUri` with no
extension and no mime type, so the only way to learn that an image is a JPEG
is to fetch it. This test does not use the network, so a real run's answers
are committed.

To refresh both from a new fetch:

    uv run eta-publish <doc-url> -o out
    cp out/doc.json tests/real/sas-west.doc.json
    uv run pytest --regenerate-golden

The last step rereads `out/images/` when it is there, so the extensions
follow the response they came from.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from eta_publish.emit.html import HtmlEmitter, preview_page
from eta_publish.emit.markdown import MarkdownEmitter
from eta_publish.emit.typst import TypstEmitter
from eta_publish.nodes import Document, Figure, Heading
from eta_publish.parse import parse

REAL = Path(__file__).parent / "real"
EXTENSIONS_PATH = REAL / "sas-west.images.json"
DOWNLOADED = Path("out/images")
DOC_JSON = json.loads((REAL / "sas-west.doc.json").read_text())

IMAGE_BASE = "https://assets.etany.org/sas-west"


def image_extensions(regenerate: bool) -> dict[str, str]:
    """What a real run resolved each image's format to.

    Refreshed from a download when regenerating, so a re-fetched response
    does not keep the previous one's extensions.
    """
    if regenerate and DOWNLOADED.is_dir():
        by_stem = {i.filename: i.object_id for i in parse(DOC_JSON).images}
        found = {
            by_stem[p.stem]: p.suffix for p in sorted(DOWNLOADED.iterdir()) if p.stem in by_stem
        }
        if found:
            EXTENSIONS_PATH.write_text(json.dumps(found, indent=2, sort_keys=True) + "\n")
    return json.loads(EXTENSIONS_PATH.read_text())


@pytest.fixture
def doc(regenerate_golden: bool) -> Document:
    parsed = parse(DOC_JSON)
    parsed.image_extensions.update(image_extensions(regenerate_golden))
    return parsed


def check(name: str, actual: str, regenerate: bool) -> None:
    path = REAL / name
    if regenerate or not path.exists():
        path.write_text(actual)
        if not regenerate:
            pytest.fail(f"{path} did not exist; wrote it, review and commit")
        return
    expected = path.read_text()
    assert actual == expected, (
        f"{path} differs. This is a real published report, so read the diff "
        "before accepting it, then rerun with --regenerate-golden."
    )


# ---- snapshots ------------------------------------------------------


def test_html_snapshot(doc: Document, regenerate_golden: bool) -> None:
    check("sas-west.html", HtmlEmitter(image_base=IMAGE_BASE).emit(doc), regenerate_golden)


def test_markdown_snapshot(doc: Document, regenerate_golden: bool) -> None:
    check("sas-west.md", MarkdownEmitter().emit(doc), regenerate_golden)


def test_typst_snapshot(doc: Document, regenerate_golden: bool) -> None:
    check("sas-west.typ", TypstEmitter().emit(doc), regenerate_golden)


def test_preview_snapshot(doc: Document, regenerate_golden: bool) -> None:
    check("sas-west.preview.html", preview_page(doc), regenerate_golden)


# ---- what the document should parse to ------------------------------


def test_the_shape_of_the_report(doc: Document) -> None:
    assert doc.title == "Digging Out of a Very Deep Hole: Saving Billions on 125th Street"
    assert doc.slug == "/reports/digging-out-deep-hole-sas-west"
    assert len(doc.footnotes) == 20
    assert len(doc.images) == 29
    assert len([b for b in doc.blocks if isinstance(b, Figure)]) == 29
    assert len([b for b in doc.blocks if isinstance(b, Heading)]) == 19


def test_smart_chips_resolve(doc: Document) -> None:
    """Person and date chips are not text runs. Reading only text runs left
    every one of these empty, including the publication date."""
    assert doc.meta["project manager"] == "Khyber Sen"
    assert doc.meta["final due date"] == "Aug 19, 2026"
    assert doc.meta["public contributors"].startswith("Khyber Sen, Darius Jankauskas")
    assert doc.meta["seo description"].startswith("A 125 St subway should be a slam dunk")


def test_the_warnings_are_the_ones_we_expect(doc: Document) -> None:
    """Each of these is something to fix in the document, not in the code.
    A new warning appearing here means the report changed or the parser did."""
    assert sorted(doc.warnings) == [
        "an image is styled as a heading; treating it as a figure. "
        "Set that paragraph to normal text in the doc.",
        "image kix.6v8dr3hm2747 has no alt text and no caption; add a description to it in the doc",
        "unfinished text in the document: SVG: TODO",
        "unfinished text in the document: TODO insert PSD image, maybe JFK AirTrain?",
    ]


# ---- properties that must hold for any published report -------------


def test_no_editorial_note_reaches_a_published_output(doc: Document) -> None:
    """`Source:`, `Uncropped Source:`, `Image Source`, and `SVG:` name assets
    for whoever assembles the page. Each appears zero times on the live
    report, against 26 occurrences of `Credit:`."""
    for emitted in (HtmlEmitter().emit(doc), TypstEmitter().emit(doc)):
        for note in ("Source:", "Image Source", "SVG:", "drive.google.com"):
            assert note not in emitted, note
        assert "Credit: MTA" in emitted


def test_the_archive_keeps_the_editorial_notes(doc: Document) -> None:
    archive = MarkdownEmitter().emit(doc)
    assert "<!-- Source:" in archive
    assert "drive.google.com" in archive


def test_html_ids_are_unique_and_every_link_resolves(doc: Document) -> None:
    """The three defects on the live page, none of which can recur here."""
    html = HtmlEmitter().emit(doc)

    ids = re.findall(r'id="([^"]+)"', html)
    assert len(ids) == len(set(ids))

    refs = set(re.findall(r'id="fnref(\d+)"', html))
    notes = set(re.findall(r'id="fn(\d+)"', html))
    backlinks = set(re.findall(r'href="#fnref(\d+)"', html))
    assert refs == notes == backlinks
    assert len(refs) == 20

    targets = set(ids)
    for target in re.findall(r'href="#([^"]+)"', html):
        assert target in targets, target


def test_the_fragment_fits_in_one_code_block(doc: Document) -> None:
    """Squarespace allows 400 KB. This is the number the one-paste claim
    rests on, so it is asserted rather than estimated."""
    from eta_publish.emit.html import CODE_BLOCK_LIMIT

    size = len(HtmlEmitter(image_base=IMAGE_BASE).emit(doc).encode())
    assert size < CODE_BLOCK_LIMIT
    assert size < 120_000, f"grown to {size:,} bytes; still fits, worth a look"


def test_every_image_has_something_describing_it(doc: Document) -> None:
    """One image in the report has neither, and is reported. If a second
    appears, this catches it."""
    undescribed = [
        b.image.object_id
        for b in doc.blocks
        if isinstance(b, Figure) and not b.image.alt and not b.caption
    ]
    assert undescribed == ["kix.6v8dr3hm2747"]


def test_no_chip_email_reaches_any_output(doc: Document) -> None:
    """A person chip carries an email beside the name. The name is what the
    document displays and what belongs in a report; the address is contact
    information the document happens to hold, and publishing it would put a
    contributor's address on a public page.

    The fixture keeps the real addresses so this tests something.
    """
    emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", json.dumps(DOC_JSON))
    assert emails, "the fixture should still contain a chip to test against"
    for emitted in (
        HtmlEmitter().emit(doc),
        MarkdownEmitter().emit(doc),
        TypstEmitter().emit(doc),
        preview_page(doc),
    ):
        for email in emails:
            assert email not in emitted, email
