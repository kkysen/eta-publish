"""Snapshot of the real SAS West report, end to end.

`site/` is literally a publish of the real report,
at the top level because it is the site this project publishes
rather than a test fixture:

    uv run eta-publish

The report lands under the path its own front matter names,
`reports/digging-out-deep-hole-sas-west/`, next to the index listing it.
That directory holds `doc.json`, the four outputs, `images/`, and `report.pdf`,
and this test asserts the committed outputs
still match what the code produces from the committed response.

`tests/fixture/` is the same directory in miniature,
built from a document nobody fetched, and the two differ by that and nothing else.
Either rebuilds from its own `doc.json` by passing the report directory back.
This is the only test running against a document nobody wrote to make a point,
and every bug that mattered so far
came from this document's shape rather than from a hand-built fixture.

Only the text is committed.
The images are 18 MB and the PDF 19 MB,
and a re-fetch rewrites every image, adding another copy to history permanently.
They are ignored, so the command above is safe to rerun.

`images.json` is the one derived thing kept:
a Docs `inlineObject` carries a `contentUri` with no extension and no mime type,
so the only way to learn an image is a JPEG is to fetch it,
and this test does not use the network.
It records the filename written for each image,
refreshed from `images/` whenever that directory is present.

When a snapshot changes, read the diff:
it is exactly what the change does to a real published report.
Accept it with `pytest --regenerate-snapshots`.
"""

import json
import re

import pytest
from paths import REAL_DIR as REAL

from eta_publish.checks import check as run_checks
from eta_publish.docs_json import JsonObject
from eta_publish.emit.html import HtmlEmitter, report_page
from eta_publish.emit.markdown import MarkdownEmitter
from eta_publish.emit.typst import TypstEmitter
from eta_publish.naming import IMAGE_DIR
from eta_publish.nodes import Document, Figure, Heading
from eta_publish.parse import parse

FILENAMES_PATH = REAL / "images.json"
DOWNLOADED = REAL / "images"
DOC_JSON = json.loads((REAL / "doc.json").read_text())

# The snapshots are a plain publish, so no `--image-base`:
# where images are hosted is still undecided,
# and pinning a placeholder in would make every snapshot line depend on it.
# That the flag is applied when given is covered in `test_preview.py`.


def image_index(regenerate: bool) -> dict[str, JsonObject]:
    """What a real run wrote for each image, read from `images.json`.

    Written by a build rather than by this test:
    a record of what was published rather than of what was asserted.
    The filename and the pixel size are facts only a fetch can learn,
    and the committed page is laid out from the size,
    so a test with no network reads them from here.
    The hash beside them lets CI check that a rebuild fetched the same pictures.
    """
    return json.loads(FILENAMES_PATH.read_text())


def image_files(regenerate: bool) -> dict[str, str]:
    return {object_id: entry["file"] for object_id, entry in image_index(regenerate).items()}


def image_shapes(regenerate: bool) -> dict[str, tuple[int, int]]:
    return {
        object_id: (entry["width"], entry["height"])
        for object_id, entry in image_index(regenerate).items()
        if "width" in entry
    }


@pytest.fixture
def doc(regenerate_snapshots: bool) -> Document:
    parsed = parse(DOC_JSON)
    parsed.image_files.update(image_files(regenerate_snapshots))
    parsed.image_shapes.update(image_shapes(regenerate_snapshots))
    # As a build does it, because the page carries the warnings
    # and these snapshots are the pages a build writes.
    # `run_checks` rather than `check`, which is this module's snapshot comparison.
    run_checks(parsed)
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
    check("report.html", HtmlEmitter(image_base=IMAGE_DIR).emit(doc), regenerate_snapshots)


def test_markdown_snapshot(doc: Document, regenerate_snapshots: bool) -> None:
    check("report.md", MarkdownEmitter().emit(doc), regenerate_snapshots)


def test_typst_snapshot(doc: Document, regenerate_snapshots: bool) -> None:
    check("report.typ", TypstEmitter().emit(doc), regenerate_snapshots)


def test_page_snapshot(doc: Document, regenerate_snapshots: bool) -> None:
    check("index.html", report_page(doc), regenerate_snapshots)


# ---- what the document should parse to ------------------------------


def test_the_shape_of_the_report(doc: Document) -> None:
    assert doc.title == "Digging Out of a Very Deep Hole: Saving Billions on 125th Street"
    assert doc.slug == "/reports/digging-out-deep-hole-sas-west"
    assert len(doc.footnotes) == 20
    assert len(doc.images) == 29, "28 figures and the share card"
    assert len([b for b in doc.blocks if isinstance(b, Figure)]) == 28
    assert len([b for b in doc.blocks if isinstance(b, Heading)]) == 20


def test_smart_chips_resolve(doc: Document) -> None:
    """Person and date chips are not text runs.
    Reading only text runs left every one of these empty,
    including the publication date."""
    assert doc.meta["project manager"] == "Khyber Sen"
    assert doc.meta["publish due date"] == "Aug 19, 2026"
    # The field has been renamed once, silently, and the date simply stopped
    # appearing. This is the assertion that would have said so.
    assert doc.dateline == "August 19, 2026"
    assert doc.meta["public contributors"].startswith("Khyber Sen, Darius Jankauskas")
    assert doc.meta["seo description"].startswith("A 125 St subway should be a slam dunk")


def test_the_warnings_are_the_ones_we_expect(doc: Document) -> None:
    """Each of these is something to fix in the document, not in the code.
    A new warning appearing here means the report changed or the parser did."""
    assert sorted(doc.warnings) == [
        "17 suggestions still open on this tab; "
        "the build publishes the document without them, as it reads today",
        "46 comment threads still open on this document",
        "`SEO Description:` is 398 characters, over the 300 a search result shows; "
        "the end of it will not be read",
        "the image `img-44bf278f` has no `Credit:` line",
        "the image `project_cost_comparison` has no `Credit:` line",
        "unfinished text in the document: SVG: TODO",
    ]


# ---- properties that must hold for any published report -------------


def test_no_editorial_note_reaches_a_published_output(doc: Document) -> None:
    """`Source:`, `Uncropped Source:`, `Image Source`, and `SVG:`
    name assets for whoever assembles the page.
    Each appears zero times on the live report, against 26 occurrences of `Credit:`.

    The report, not the warnings: a warning quotes the line it is about,
    so `unfinished text in the document: SVG: TODO` says `SVG:` on purpose.
    The fragment carries no warnings at all, and the Typst body begins after them.
    """
    typst = TypstEmitter().emit(doc)
    # Everything after the `#show: report.with(...)` call, which is the report itself.
    body = re.split(r"^\)$", typst, maxsplit=1, flags=re.MULTILINE)[-1]
    for emitted in (HtmlEmitter().emit(doc), body):
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
    """Squarespace allows 400 KB.
    This is the number the one-paste claim rests on,
    so it is asserted rather than estimated."""
    from eta_publish.emit.html import CODE_BLOCK_LIMIT

    size = len(HtmlEmitter(image_base="https://assets.etany.org/sas-west").emit(doc).encode())
    assert size < CODE_BLOCK_LIMIT
    assert size < 120_000, f"grown to {size:,} bytes; still fits, worth a look"


def test_every_image_has_something_describing_it(doc: Document) -> None:
    """Every figure in the report carries alt text or a caption.

    The one image that had neither is the share card,
    which is not a figure and is not in the body at all."""
    undescribed = [
        b.image.object_id
        for b in doc.blocks
        if isinstance(b, Figure) and not b.image.alt and not b.caption
    ]
    assert undescribed == []


def test_the_share_card_is_not_in_the_report(doc: Document) -> None:
    """It is a picture of the title, for whatever unfurls a link to it."""
    assert doc.card is not None
    assert doc.card.object_id == "kix.6v8dr3hm2747"
    assert doc.card.object_id not in [
        b.image.object_id for b in doc.blocks if isinstance(b, Figure)
    ]
    assert doc.card in doc.images, "still has to be downloaded to be linked"


def test_the_report_opens_with_its_hero(doc: Document) -> None:
    """Above the table of contents, which it introduces rather than follows."""
    page = report_page(doc)
    assert page.index("img-6fb0f9c4") < page.index('<nav class="toc"')
    assert page.index('property="og:image"') < page.index('<h1 id="title">')


def test_no_chip_email_reaches_any_output(doc: Document) -> None:
    """A person chip carries an email beside the name.
    The name is what the document displays and what belongs in a report;
    the address is contact information the document happens to hold,
    and publishing it would put a contributor's address on a public page.

    The fixture keeps the real addresses so this tests something.
    """
    emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", json.dumps(DOC_JSON))
    assert emails, "the fixture should still contain a chip to test against"
    for emitted in (
        HtmlEmitter().emit(doc),
        MarkdownEmitter().emit(doc),
        TypstEmitter().emit(doc),
        report_page(doc),
    ):
        for email in emails:
            assert email not in emitted, email


def test_the_chart_publishes_as_a_vector(doc: Document) -> None:
    """Docs cannot place an SVG,
    so `project_cost_comparison.svg` is pasted into the report as a raster
    and linked beside it.
    All three outputs can show the vector, so all three should."""
    vectors = [i for i in doc.images if i.vector is not None]
    assert [v.vector.title for v in vectors if v.vector] == ["project_cost_comparison.svg"]

    for emitted in (HtmlEmitter().emit(doc), MarkdownEmitter().emit(doc), TypstEmitter().emit(doc)):
        assert vectors[0].vector is not None
        assert vectors[0].vector.filename in emitted
