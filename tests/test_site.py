"""Building more than one report into one site.

The single-document path is covered everywhere else.
What matters here is what only appears with several:
where each report lands,
that one failure does not take the others with it,
and that the index says so.
"""

import json
from pathlib import Path

import pytest
from paths import FIXTURE_DIR

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
    reports_from,
)

FIXTURE = json.loads((FIXTURE_DIR / "doc.json").read_text())


@pytest.fixture
def doc() -> Document:
    return parse(FIXTURE)


def test_a_report_is_published_at_the_path_its_header_names(doc: Document) -> None:
    doc.meta["url"] = "/reports/digging-out-deep-hole-sas-west"
    assert report_path(doc) == "reports/digging-out-deep-hole-sas-west"


def test_a_report_with_no_url_falls_back_to_its_title_and_says_so(doc: Document) -> None:
    """A missing `URL:` is a line to add to the document.
    It must not take the other reports down, and it must not pass unmentioned."""
    doc.meta.pop("url", None)
    doc.title = "Digging Out of a Very Deep Hole"
    assert report_path(doc) == "digging-out-of-a-very-deep-hole"
    assert any("no `URL:`" in w for w in doc.warnings)


def test_an_absolute_url_cannot_escape_the_site_root(doc: Document) -> None:
    """`/reports/x` is a published path, not a filesystem one;
    joined unstripped it would write to the root of the disk."""
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
    # Unreadable rather than absent:
    # a path that does not exist is taken for a document reference
    # and would reach for the network, and the test suite never does that.
    broken = tmp_path / "broken.json"
    broken.write_text("{not json")
    reports = [
        Report(url=str(broken), name="gone"),
        Report(url=str(good), name="fine"),
    ]
    site = build_site(reports, tmp_path / "site", BuildOptions(images=False))
    assert [f.report.name for f in site.failed] == ["gone"]
    assert [b.report.name for b in site.built] == ["fine"]
    assert (tmp_path / "site" / site.built[0].path / "index.html").exists()


def test_the_index_lists_what_built_and_what_did_not(doc: Document) -> None:
    site = Site(
        built=[Built(report=Report(url="u", name="SAS West"), doc=doc, path="reports/sas-west")],
        failed=[Failed(report=Report(url="u2", name="Next"), error="not found")],
    )
    page = index_page(site)
    assert 'href="reports/sas-west/"' in page
    assert doc.title in page
    assert "Next: not found" in page


def test_a_url_is_a_document_even_when_it_ends_in_toml() -> None:
    """Only a local path can name a list.
    A URL is a document, whatever it is spelled like,
    so a Drive link can never be mistaken for a roster."""
    ref = "https://docs.google.com/document/d/abc/edit?tab=t.1"
    assert reports_from(ref) == [Report(url=ref)]
    assert reports_from("https://example.invalid/reports.toml") == [
        Report(url="https://example.invalid/reports.toml")
    ]


def test_a_toml_path_is_a_list(tmp_path: Path) -> None:
    path = tmp_path / "more.toml"
    path.write_text('[[report]]\nurl = "https://example.invalid/a"\n')
    assert reports_from(str(path)) == [Report(url="https://example.invalid/a")]


def test_a_saved_response_is_a_document(tmp_path: Path) -> None:
    saved = tmp_path / "doc.json"
    saved.write_text("{}")
    assert reports_from(str(saved)) == [Report(url=str(saved))]


def test_only_one_document_or_list_at_a_time() -> None:
    """Building several at once is what a list is for,
    and a list is a file that can be reviewed
    rather than a shell line that is right once."""
    from typer.testing import CliRunner

    from eta_publish.__main__ import app

    result = CliRunner().invoke(app, ["one.toml", "two.toml"])
    assert result.exit_code != 0


def test_a_missing_list_is_reported_as_a_bad_argument(tmp_path: Path) -> None:
    """Not a traceback:
    naming a file that is not there is a typo, and the message should read like one."""
    from typer.testing import CliRunner

    from eta_publish.__main__ import app

    absent = tmp_path / "absent.toml"
    result = CliRunner().invoke(app, [str(absent)])
    assert result.exit_code != 0
    assert str(absent) in result.output


def test_a_report_directory_is_a_document(tmp_path: Path) -> None:
    """A build writes `doc.json` beside its outputs,
    so what one run wrote is what the next can be handed,
    with no network and no knowing the filename inside it."""
    from typer.testing import CliRunner

    from eta_publish.__main__ import app

    result = CliRunner().invoke(
        app, [str(FIXTURE_DIR), "-o", str(tmp_path / "site"), "--no-images"]
    )
    assert result.exit_code == 0, result.output
    built = tmp_path / "site" / "reports" / "digging-out-deep-hole-sas-west"
    assert (built / "report.md").is_file()
    assert (built / "doc.json").is_file()


def test_a_directory_without_a_saved_response_says_so(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from eta_publish.__main__ import app

    (tmp_path / "empty").mkdir()
    result = CliRunner().invoke(app, [str(tmp_path / "empty"), "-o", str(tmp_path / "site")])
    assert result.exit_code != 0
    assert "doc.json" in result.output


def test_a_name_that_is_not_the_documents_is_warned_about(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`reports.toml` names each report, and only the fetch knows if it is right."""
    saved = tmp_path / "doc.json"
    saved.write_text(json.dumps(FIXTURE))
    build_site(
        [Report(url=str(saved), name="SAS West")],
        tmp_path / "site",
        BuildOptions(images=False),
    )
    warning = capsys.readouterr().err
    assert "reports.toml calls this 'SAS West'" in warning
    assert repr(FIXTURE["title"]) in warning


def test_the_documents_own_name_is_not_warned_about(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    saved = tmp_path / "doc.json"
    saved.write_text(json.dumps(FIXTURE))
    build_site(
        [Report(url=str(saved), name=str(FIXTURE["title"]))],
        tmp_path / "site",
        BuildOptions(images=False),
    )
    assert "reports.toml calls this" not in capsys.readouterr().err


def test_a_tab_that_is_not_the_documents_is_warned_about(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A `?tab=` id says nothing a reader can check, so the title is what is checked."""
    saved = tmp_path / "doc.json"
    saved.write_text(json.dumps(FIXTURE | {"tabTitle": "Draft 2"}))
    build_site(
        [Report(url=str(saved), tab="Draft 1")],
        tmp_path / "site",
        BuildOptions(images=False),
    )
    warning = capsys.readouterr().err
    assert "reports.toml expects the tab 'Draft 1'" in warning
    assert "'Draft 2'" in warning


def test_a_response_saved_before_tabs_were_recorded_is_not_warned_about(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A response with no `tabTitle` cannot disagree, and must not be said to.

    Every response saved before the fetch started recording one is such a file,
    and they are what an offline build reads.
    """
    saved = tmp_path / "doc.json"
    assert "tabTitle" not in FIXTURE
    saved.write_text(json.dumps(FIXTURE))
    build_site(
        [Report(url=str(saved), tab="Draft 1")],
        tmp_path / "site",
        BuildOptions(images=False),
    )
    assert "reports.toml" not in capsys.readouterr().err


def test_an_entry_that_names_neither_is_not_warned_about(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Both fields are optional: an entry says as much as whoever wrote it wanted."""
    saved = tmp_path / "doc.json"
    saved.write_text(json.dumps(FIXTURE))
    build_site([Report(url=str(saved))], tmp_path / "site", BuildOptions(images=False))
    assert "reports.toml" not in capsys.readouterr().err


def test_a_url_that_climbs_out_of_the_site_is_refused(doc: Document) -> None:
    """The build writes wherever this says, and the committed-site check
    only ever looks inside `site/`, so a climb would leave no trace there."""
    doc.title = "Digging Out of a Very Deep Hole"
    doc.meta["url"] = "/../../../../tmp/pwned"
    assert report_path(doc) == "digging-out-of-a-very-deep-hole"
    assert any("climbs out of the site" in w for w in doc.warnings)
