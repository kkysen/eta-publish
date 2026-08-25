"""Building more than one report into one site.

The single-document path is covered everywhere else. What matters here is
what only appears with several: where each report lands, that one failure
does not take the others with it, and that the index says so.
"""

import json
from pathlib import Path

import pytest

from eta_publish.build import BuildOptions
from eta_publish.nodes import Document
from eta_publish.parse import parse
from eta_publish.site import (
    Built,
    Failed,
    Report,
    Site,
    build_site,
    index_page,
    load_reports,
    report_path,
)

FIXTURE = json.loads((Path(__file__).parent / "fixture-doc.json").read_text())


@pytest.fixture
def doc() -> Document:
    return parse(FIXTURE)


def test_a_report_is_published_at_the_path_its_header_names(doc: Document) -> None:
    doc.meta["url"] = "/reports/digging-out-deep-hole-sas-west"
    assert report_path(doc) == "reports/digging-out-deep-hole-sas-west"


def test_a_report_with_no_url_falls_back_to_its_title_and_says_so(doc: Document) -> None:
    """A missing `URL:` is a line to add to the document. It must not take
    the other reports down, and it must not pass unmentioned."""
    doc.meta.pop("url", None)
    doc.title = "Digging Out of a Very Deep Hole"
    assert report_path(doc) == "digging-out-of-a-very-deep-hole"
    assert any("no `URL:`" in w for w in doc.warnings)


def test_an_absolute_url_cannot_escape_the_site_root(doc: Document) -> None:
    """`/reports/x` is a published path, not a filesystem one; joined
    unstripped it would write to the root of the disk."""
    doc.meta["url"] = "/reports/x"
    assert not Path(report_path(doc)).is_absolute()


def test_reports_are_read_from_the_list(tmp_path: Path) -> None:
    path = tmp_path / "reports.toml"
    path.write_text(
        '[[report]]\nname = "SAS West"\nurl = "https://example.invalid/a"\n'
        '\n[[report]]\nurl = "https://example.invalid/b"\n'
    )
    assert load_reports(path) == [
        Report(url="https://example.invalid/a", name="SAS West"),
        Report(url="https://example.invalid/b"),
    ]


def test_an_entry_without_a_url_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "reports.toml"
    path.write_text('[[report]]\nname = "Nameless"\n')
    with pytest.raises(ValueError, match="no `url`"):
        load_reports(path)


def test_the_project_list_parses() -> None:
    """The committed one, so a typo in it fails here rather than in CI."""
    reports = load_reports()
    assert reports
    assert all(
        "?tab=" in r.url or "&tab=" in r.url or not r.url.startswith("http") for r in reports
    )


def test_one_failure_does_not_stop_the_others(tmp_path: Path) -> None:
    good = tmp_path / "good.json"
    good.write_text(json.dumps(FIXTURE))
    # Unreadable rather than absent: a path that does not exist is taken for
    # a document reference and would reach for the network, and the test
    # suite never does that.
    broken = tmp_path / "broken.json"
    broken.write_text("{not json")
    reports = [
        Report(url=str(broken), name="gone"),
        Report(url=str(good), name="fine"),
    ]
    site = build_site(reports, tmp_path / "site", BuildOptions(images=False, pdf=False))
    assert [f.report.name for f in site.failed] == ["gone"]
    assert [b.report.name for b in site.built] == ["fine"]
    assert (tmp_path / "site" / site.built[0].path / "preview.html").exists()


def test_the_index_lists_what_built_and_what_did_not(doc: Document) -> None:
    site = Site(
        built=[Built(report=Report(url="u", name="SAS West"), doc=doc, path="reports/sas-west")],
        failed=[Failed(report=Report(url="u2", name="Next"), error="not found")],
    )
    page = index_page(site)
    assert 'href="reports/sas-west/"' in page
    assert doc.title in page
    assert "Next: not found" in page
