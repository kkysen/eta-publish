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
    add_report,
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


def test_a_report_with_no_url_is_refused(doc: Document) -> None:
    """A slug of the headline is a plausible path and not the published one,
    so guessing one publishes the report at the wrong URL, quietly."""
    doc.meta.pop("url", None)
    doc.title = "Digging Out of a Very Deep Hole"
    with pytest.raises(ValueError, match="no `URL:` line"):
        report_path(doc)


def test_an_absolute_url_cannot_escape_the_site_root(doc: Document) -> None:
    """`/reports/x` is a published path, not a filesystem one;
    joined unstripped it would write to the root of the disk."""
    doc.meta["url"] = "/reports/x"
    assert not Path(report_path(doc)).is_absolute()


def test_reports_are_read_from_the_list(tmp_path: Path) -> None:
    path = tmp_path / "reports.toml"
    path.write_text(
        '[[report]]\nname = "SAS West"\ntab = "Draft 2"\nurl = "https://example.invalid/a"\n'
        '\n[[report]]\nname = "IBX"\ntab = "Live version"\nurl = "https://example.invalid/b"\n'
    )
    assert load_reports(path) == [
        Report(url="https://example.invalid/a", name="SAS West", tab="Draft 2"),
        Report(url="https://example.invalid/b", name="IBX", tab="Live version"),
    ]


@pytest.mark.parametrize("blank", ["name", "tab"])
def test_an_entry_that_names_nothing_disagrees_like_any_other(tmp_path: Path, blank: str) -> None:
    """A blank field needs no rule of its own: no document is named nothing,
    so the comparison that catches a wrong name catches a missing one."""
    saved = tmp_path / "doc.json"
    saved.write_text(json.dumps({**FIXTURE, "tabTitle": "Draft 2"}))
    fields = {"name": "Digging Out of a Very Deep Hole", "tab": "Draft 2"}
    fields[blank] = ""
    site = build_site(
        [Report(url=str(saved), **fields)], tmp_path / "site", BuildOptions(images=False)
    )
    assert not site.built
    assert "''" in site.failed[0].error


def test_an_entry_without_a_url_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "reports.toml"
    path.write_text('[[report]]\nname = "Nameless"\n')
    with pytest.raises(ValueError, match="no `url`"):
        load_reports(path)


def test_add_names_an_entry_from_the_document(tmp_path: Path) -> None:
    """The whole point of the command: the two names come off the document,
    not off a person reading them out of Drive."""
    saved = tmp_path / "doc.json"
    saved.write_text(json.dumps({**FIXTURE, "title": "IBX Automation", "tabTitle": "Live version"}))
    path = tmp_path / "reports.toml"
    path.write_text('# a comment worth keeping\n\n[[report]]\nname = "A"\ntab = "B"\nurl = "u"\n')

    added = add_report(str(saved), path)
    assert added == Report(url=str(saved), name="IBX Automation", tab="Live version")
    assert "# a comment worth keeping" in path.read_text()
    assert load_reports(path)[-1] == added


def test_add_refuses_a_document_already_listed(tmp_path: Path) -> None:
    """Two entries for one document publish it twice to one path,
    and the second build overwrites the first."""
    path = tmp_path / "reports.toml"
    path.write_text('[[report]]\nname = "A"\ntab = "B"\nurl = "u"\n')
    with pytest.raises(ValueError, match="already lists"):
        add_report("u", path)


def test_add_refuses_a_document_that_names_no_tab(tmp_path: Path) -> None:
    """It cannot write down an answer the document does not give,
    and writing an empty one down is what `load_reports` refuses."""
    saved = tmp_path / "doc.json"
    saved.write_text(json.dumps({**FIXTURE, "title": "Titled", "tabTitle": ""}))
    path = tmp_path / "reports.toml"
    path.write_text('[[report]]\nname = "A"\ntab = "B"\nurl = "u"\n')
    with pytest.raises(ValueError, match="no `tab`"):
        add_report(str(saved), path)
    assert len(load_reports(path)) == 1


def test_add_says_which_tabs_there_are_when_the_url_names_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A URL pasted without its `?tab=` id is the mistake this command exists
    to survive, and the answer is the list of tabs `TabNotFound` carries,
    not the traceback it used to be printed as."""
    from typer.testing import CliRunner

    from eta_publish import build
    from eta_publish.__main__ import add_app
    from eta_publish.fetch import TabNotFound

    def no_tab(ref: str, suggestions: str = "rejected") -> object:
        raise TabNotFound("this document has 2 tabs; pass the URL including\n  t.a  Live version")

    monkeypatch.setattr(build, "load", no_tab)
    path = tmp_path / "reports.toml"
    path.write_text('[[report]]\nname = "A"\ntab = "B"\nurl = "u"\n')

    result = CliRunner().invoke(add_app, ["https://example.invalid/d/x", "-r", str(path)])
    assert result.exit_code != 0
    assert "t.a  Live version" in result.output
    assert len(load_reports(path)) == 1


def test_a_title_with_a_quotation_mark_stays_one_string(tmp_path: Path) -> None:
    saved = tmp_path / "doc.json"
    saved.write_text(json.dumps({**FIXTURE, "title": 'The "Deep Hole" Report', "tabTitle": "D2"}))
    path = tmp_path / "reports.toml"
    path.write_text('[[report]]\nname = "A"\ntab = "B"\nurl = "u"\n')
    add_report(str(saved), path)
    assert load_reports(path)[-1].name == 'The "Deep Hole" Report'


def test_the_project_list_parses() -> None:
    """The committed one, so a typo in it fails here rather than in CI."""
    reports = load_reports()
    assert reports
    assert all(
        "?tab=" in r.url or "&tab=" in r.url or not r.url.startswith("http") for r in reports
    )


def test_one_failure_does_not_stop_the_others(tmp_path: Path) -> None:
    # Named as the entry below names it, and with a tab title to confirm:
    # this test is about a fetch failure, not about a wrong entry.
    good = tmp_path / "good.json"
    good.write_text(json.dumps({**FIXTURE, "tabTitle": "Draft 2"}))
    # Unreadable rather than absent:
    # a path that does not exist is taken for a document reference
    # and would reach for the network, and the test suite never does that.
    broken = tmp_path / "broken.json"
    broken.write_text("{not json")
    reports = [
        Report(url=str(broken), name="gone", tab="Draft 2"),
        Report(url=str(good), name="Digging Out of a Very Deep Hole", tab="Draft 2"),
    ]
    site = build_site(reports, tmp_path / "site", BuildOptions(images=False))
    assert [f.report.name for f in site.failed] == ["gone"]
    assert [b.report.name for b in site.built] == ["Digging Out of a Very Deep Hole"]
    assert (tmp_path / "site" / site.built[0].path / "index.html").exists()


def test_a_wrong_entry_leaves_no_files_behind(tmp_path: Path) -> None:
    """A report that failed its own check must not leave a published directory:
    the next run compares against it and finds nothing wrong."""
    saved = tmp_path / "doc.json"
    saved.write_text(json.dumps({**FIXTURE, "tabTitle": "Draft 2"}))
    out = tmp_path / "site"
    site = build_site(
        [Report(url=str(saved), name="Some Other Document", tab="Draft 2")],
        out,
        BuildOptions(images=False),
    )
    assert not site.built
    assert "the document is named" in site.failed[0].error
    assert not list(out.rglob("report.html"))


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
    path.write_text('[[report]]\nname = "A"\ntab = "B"\nurl = "https://example.invalid/a"\n')
    assert reports_from(str(path)) == [Report(url="https://example.invalid/a", name="A", tab="B")]


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


def test_a_response_that_names_no_tab_cannot_confirm_one(tmp_path: Path) -> None:
    """A `?tab=` id names a draft and says nothing about which,
    so a response with no `tabTitle` leaves the entry's one question unanswered,
    and an unanswered question is not a passed check."""
    saved = tmp_path / "doc.json"
    assert "tabTitle" not in FIXTURE
    saved.write_text(json.dumps(FIXTURE))
    site = build_site(
        [Report(url=str(saved), name="Digging Out of a Very Deep Hole", tab="Draft 1")],
        tmp_path / "site",
        BuildOptions(images=False),
    )
    assert not site.built
    assert "the tab is named ''" in site.failed[0].error


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
    with pytest.raises(ValueError, match="climbs out of the site"):
        report_path(doc)
