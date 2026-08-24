"""Snapshot of the real SAS West report, end to end.

`tests/sas-west/` is literally a publish of the real report:

    uv run eta-publish <doc-url> -o tests/sas-west

That writes `doc.json`, the four outputs, `images/`, and `report.pdf`, and
this test asserts the committed outputs still match what the code produces
from the committed response. It is the only test that runs against a
document nobody wrote to make a point, and every bug that mattered so far
came from this document's shape rather than from a hand-built fixture.

Only the text is committed. The images are 18 MB and the PDF 19 MB, and
because a re-fetch rewrites every image, each one would add another copy to
history permanently. They are ignored, so the command above is safe to rerun.

`images.json` is the one derived thing kept: a Docs `inlineObject` carries a
`contentUri` with no extension and no mime type, so the only way to learn an
image is a JPEG is to fetch it, and this test does not use the network. It
is refreshed from `images/` whenever that directory is present.

When a snapshot changes, read the diff: it is exactly what the change does
to a real published report. Accept it with `pytest --regenerate-snapshots`.
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

REAL = Path(__file__).parent / "sas-west"
EXTENSIONS_PATH = REAL / "images.json"
DOWNLOADED = REAL / "images"
DOC_JSON = json.loads((REAL / "doc.json").read_text())

# The snapshots are a plain publish, so no `--image-base`: where images are
# hosted is still undecided, and pinning a placeholder into them would make
# every snapshot line depend on a value nobody has chosen yet. That the flag
# is applied when given is covered in `test_preview.py`.


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
def doc(regenerate_snapshots: bool) -> Document:
    parsed = parse(DOC_JSON)
    parsed.image_extensions.update(image_extensions(regenerate_snapshots))
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
        "before accepting it, then rerun with --regenerate-snapshots."
    )


# ---- snapshots ------------------------------------------------------


def test_html_snapshot(doc: Document, regenerate_snapshots: bool) -> None:
    check("report.html", HtmlEmitter().emit(doc), regenerate_snapshots)


def test_markdown_snapshot(doc: Document, regenerate_snapshots: bool) -> None:
    check("report.md", MarkdownEmitter().emit(doc), regenerate_snapshots)


def test_typst_snapshot(doc: Document, regenerate_snapshots: bool) -> None:
    check("report.typ", TypstEmitter().emit(doc), regenerate_snapshots)


def test_preview_snapshot(doc: Document, regenerate_snapshots: bool) -> None:
    check("preview.html", preview_page(doc), regenerate_snapshots)


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

    size = len(HtmlEmitter(image_base="https://assets.etany.org/sas-west").emit(doc).encode())
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
