"""HTML emitted for the Squarespace code block."""

import json
import re

import pytest
from paths import FIXTURE_DIR

from eta_publish.emit.html import HtmlEmitter
from eta_publish.nodes import Document
from eta_publish.parse import parse

FIXTURE = json.loads((FIXTURE_DIR / "doc.json").read_text())


@pytest.fixture
def doc() -> Document:
    parsed = parse(FIXTURE)
    parsed.image_files["io.1"] = "img-1933bef5.png"
    return parsed


@pytest.fixture
def out(doc: Document) -> str:
    return HtmlEmitter(image_base="https://assets.etany.org/sas-west", inline_css=False).emit(doc)


def test_every_footnote_has_a_matching_backlink(out: str) -> None:
    """The defect this whole tool exists to prevent: the published SAS West
    report has a footnote whose `↑` leads nowhere."""
    refs = set(re.findall(r'id="fnref(\d+)"', out))
    notes = set(re.findall(r'id="fn(\d+)"', out))
    backlinks = set(re.findall(r'href="#fnref(\d+)"', out))
    assert refs == notes == backlinks
    assert refs == {"1", "2"}


def test_ids_are_unique() -> None:
    """`fn18-return` appears twice on the published page."""
    emitted = HtmlEmitter().emit(parse(FIXTURE))
    ids = re.findall(r'id="([^"]+)"', emitted)
    assert len(ids) == len(set(ids))


def test_the_source_line_is_not_published(out: str) -> None:
    """`Source:` names the original file in Drive, for whoever assembles the
    report. It appears nowhere on the live page and must not leak."""
    assert "Source:" not in out
    assert "sas-west-036.jpg" not in out


def test_the_caption_and_credit_are_published(out: str) -> None:
    assert '<figcaption class="figure-caption">The SAS West and Phase 2 alignments.' in out
    assert '<figcaption class="figure-credit">Credit: MTA' in out


def test_images_use_the_image_base_and_resolved_extension(out: str) -> None:
    assert 'src="https://assets.etany.org/sas-west/img-1933bef5.png"' in out
    assert 'alt="SAS West alignment map"' in out


def test_the_table_of_contents_links_to_real_anchors(out: str) -> None:
    toc_html = re.findall(r'<nav class="toc".*?</nav>', out, re.S)[0]
    linked = set(re.findall(r'href="#([^"]+)"', toc_html))
    targets = set(re.findall(r'<h\d id="([^"]+)"', out))
    assert linked and linked <= targets
    assert '<a href="#the-elephants-in-the-room">The Elephants in the Room</a>' in toc_html


def test_the_table_of_contents_lists_every_heading(out: str) -> None:
    """Every heading on the page, in order, footnotes and contributors too."""
    toc_html = re.findall(r'<nav class="toc".*?</nav>', out, re.S)[0]
    linked = re.findall(r'href="#([^"]+)"', toc_html)
    targets = re.findall(r'<h\d id="([^"]+)"', out)
    assert linked == targets


def test_the_table_of_contents_indents_a_subsection(out: str) -> None:
    """A subsection sits in a list inside its section's own entry."""
    toc_html = re.findall(r'<nav class="toc".*?</nav>', out, re.S)[0]
    assert (
        '<li><a href="#the-elephants-in-the-room">The Elephants in the Room</a>\n'
        '<ul>\n<li><a href="#ground-conditions">Ground Conditions</a></li>\n'
        "</ul></li>" in toc_html
    )


def test_toc_entries_close_in_order(out: str) -> None:
    """Nesting a list inside an entry is easy to close in the wrong order."""
    toc_html = re.findall(r'<nav class="toc".*?</nav>', out, re.S)[0]
    stack: list[str] = []
    for tag in re.findall(r"</?(?:ul|li)\b", toc_html):
        if tag.startswith("</"):
            assert stack.pop() == tag.removeprefix("</")
        else:
            stack.append(tag.removeprefix("<"))
    assert not stack


def test_nested_lists_nest(out: str) -> None:
    assert "<ul><li>First point<ul><li>Nested point</li></ul></li><li>Second point</li></ul>" in out


def test_text_and_urls_are_escaped() -> None:
    """Doc text is prose, but it reaches a published page verbatim."""
    hostile = json.loads(json.dumps(FIXTURE))
    hostile["body"]["content"].append(
        {
            "paragraph": {
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "elements": [
                    {
                        "textRun": {
                            "content": "<script>alert(1)</script>\n",
                            "textStyle": {"link": {"url": 'https://x.test/?a="b'}},
                        }
                    }
                ],
            }
        }
    )
    emitted = HtmlEmitter().emit(parse(hostile))
    assert "<script>" not in emitted
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in emitted
    assert 'href="https://x.test/?a=&quot;b"' in emitted


def test_inline_css_is_optional(doc: Document) -> None:
    assert HtmlEmitter(inline_css=True).emit(doc).startswith("<style>")
    assert not HtmlEmitter(inline_css=False).emit(doc).startswith("<style>")


# Determinism across runs is covered by `test_snapshots.py`. Comparing an
# emitter with itself in one process cannot see it: hash randomization is
# fixed for the life of an interpreter, so order-dependent output matches
# itself perfectly and still differs from run to run.


def test_tables_scroll_rather_than_overflow(out: str) -> None:
    """Wide comparison tables are common in these reports, and a page that
    scrolls sideways on a phone is worse than a table that does."""
    assert '<div class="table-scroll"><table>' in out
    assert "<td><p>Grand Paris Express</p></td>" in out


def test_the_contributors_section_lists_the_public_contributors(doc: Document) -> None:
    """Alphabetically by surname, which is how etany.org credits them."""
    doc.meta["public contributors"] = "Khyber Sen, Alon Levy"
    doc.meta["private contributors"] = "Someone Unnamed"
    out = HtmlEmitter(inline_css=False).emit(doc)
    assert "<li>Alon Levy</li>\n<li>Khyber Sen</li>" in out
    assert "Someone Unnamed" not in out


def test_the_contributors_section_comes_last(doc: Document) -> None:
    """After the footnotes, which is where the published report credits them."""
    doc.meta["public contributors"] = "Khyber Sen"
    out = HtmlEmitter(inline_css=False).emit(doc)
    assert out.index('<section class="footnotes">') < out.index('<section class="contributors">')


def test_a_report_with_no_public_contributors_has_no_contributors(doc: Document) -> None:
    doc.meta.pop("public contributors", None)
    assert 'class="contributors"' not in HtmlEmitter(inline_css=False).emit(doc)


def test_the_dateline_is_the_final_due_date(doc: Document) -> None:
    """Written out, which is how etany.org dates a report."""
    doc.meta["final due date"] = "Aug 19, 2026"
    out = HtmlEmitter(inline_css=False).emit(doc)
    assert '<p class="dateline">August 19, 2026</p>' in out


def test_a_report_with_no_final_due_date_has_no_dateline(doc: Document) -> None:
    doc.meta.pop("final due date", None)
    assert 'class="dateline"' not in HtmlEmitter(inline_css=False).emit(doc)
