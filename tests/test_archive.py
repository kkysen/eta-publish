"""What the report cites, and the record of where each of those is archived."""

import json
from pathlib import Path
from typing import override

import pytest
import requests

from eta_publish import archive
from eta_publish.archive import (
    ARCHIVES_JSON,
    missing,
    read_archive_index,
    write_archive_index,
)
from eta_publish.nodes import (
    Archived,
    Document,
    Figure,
    Image,
    Paragraph,
    Text,
    unwrap_snapshot,
)


def cites(*hrefs: str) -> Document:
    """A document whose body is one paragraph of links."""
    return Document(blocks=[Paragraph(content=[Text(text=href, href=href) for href in hrefs])])


# ---- what counts as a source ----------------------------------------


def test_sources_are_external_links_in_document_order() -> None:
    doc = cites("https://b.example/2", "https://a.example/1")
    assert doc.sources == ["https://b.example/2", "https://a.example/1"]


def test_a_source_cited_twice_is_one_source_and_keeps_its_first_place() -> None:
    doc = cites("https://a.example/1", "https://b.example/2", "https://a.example/1")
    assert doc.sources == ["https://a.example/1", "https://b.example/2"]
    assert doc.source_uses == {"https://a.example/1": 2, "https://b.example/2": 1}


def test_anchors_addresses_and_the_site_itself_are_not_sources() -> None:
    doc = cites(
        "#fn3",
        "mailto:someone@example.org",
        "https://www.etany.org/reports/something",
        "https://a.example/1",
    )
    assert doc.sources == ["https://a.example/1"]


def test_a_figures_source_line_is_not_a_source() -> None:
    """It names the file in Drive, and no published output points at it."""
    figure = Figure(
        image=Image(object_id="kix.1", filename="img-1"),
        source=[Text(text="drive", href="https://drive.google.com/file/d/1/view")],
        caption=[Text(text="cited", href="https://a.example/1")],
    )
    assert Document(blocks=[figure]).sources == ["https://a.example/1"]


# ---- a link the document already wrote as a snapshot ------------------


def test_a_wayback_link_is_the_page_it_is_of() -> None:
    original, archived = unwrap_snapshot(
        "https://web.archive.org/web/20240503123456/https://nypost.com/a"
    )
    assert original == "https://nypost.com/a"
    assert archived == Archived(
        snapshot="https://web.archive.org/web/20240503123456/https://nypost.com/a",
        timestamp="20240503123456",
    )


def test_a_modifier_on_the_timestamp_is_not_a_different_capture() -> None:
    plain, _ = unwrap_snapshot("https://web.archive.org/web/20240503123456/https://nypost.com/a")
    with_modifier, archived = unwrap_snapshot(
        "https://web.archive.org/web/20240503123456id_/https://nypost.com/a"
    )
    assert with_modifier == plain
    assert archived is not None
    assert archived.snapshot.endswith("/web/20240503123456/https://nypost.com/a")


def test_an_ordinary_link_is_left_alone() -> None:
    assert unwrap_snapshot("https://nypost.com/a") == ("https://nypost.com/a", None)


# ---- the record -------------------------------------------------------


def test_the_record_round_trips(tmp_path: Path) -> None:
    doc = cites("https://a.example/1")
    doc.archives["https://a.example/1"] = Archived(
        snapshot="https://web.archive.org/web/20240503123456/https://a.example/1",
        timestamp="20240503123456",
    )
    write_archive_index(tmp_path, doc)

    read = cites("https://a.example/1")
    read_archive_index(tmp_path, read)
    assert read.archives == doc.archives


def test_the_record_is_sorted_so_two_builds_write_the_same_bytes(tmp_path: Path) -> None:
    """The file is committed and compared against a fresh build."""
    doc = cites("https://b.example/2", "https://a.example/1")
    for url in doc.sources:
        doc.archives[url] = Archived(snapshot=f"snap {url}", timestamp="20240503123456")
    write_archive_index(tmp_path, doc)
    written = json.loads((tmp_path / ARCHIVES_JSON).read_text())
    assert list(written) == sorted(written)


def test_only_what_the_report_still_cites_is_written(tmp_path: Path) -> None:
    """A URL a draft dropped is not something the report stands on any more."""
    doc = cites("https://a.example/1")
    doc.archives["https://dropped.example/"] = Archived(snapshot="snap", timestamp="20240503")
    doc.archives["https://a.example/1"] = Archived(snapshot="snap", timestamp="20240503")
    write_archive_index(tmp_path, doc)
    assert list(json.loads((tmp_path / ARCHIVES_JSON).read_text())) == ["https://a.example/1"]


def test_what_the_document_itself_says_wins_over_the_record(tmp_path: Path) -> None:
    doc = cites("https://a.example/1")
    doc.archives["https://a.example/1"] = Archived(snapshot="recorded", timestamp="20200101")
    write_archive_index(tmp_path, doc)

    fresh = cites("https://a.example/1")
    fresh.archives["https://a.example/1"] = Archived(snapshot="from the doc", timestamp="20260101")
    read_archive_index(tmp_path, fresh)
    assert fresh.archives["https://a.example/1"].snapshot == "from the doc"


def test_a_failed_capture_is_not_tried_again() -> None:
    doc = cites("https://a.example/1", "https://b.example/2")
    doc.archives["https://a.example/1"] = Archived(timestamp="20260101", error="cannot be captured")
    assert missing(doc) == ["https://b.example/2"]


# ---- what the service says --------------------------------------------


@pytest.fixture
def keyed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keys in the environment, so these test the capture rather than their absence."""
    monkeypatch.setenv(archive.ACCESS_KEY, "access")
    monkeypatch.setenv(archive.SECRET_KEY, "secret")


class Answering(requests.Session):
    """A session that answers every request with one canned status and body."""

    def __init__(self, status: int, body: object = None) -> None:
        super().__init__()
        self.status = status
        self.body = body

    @override
    # The signature is narrowed on purpose: nothing here reads the arguments.
    def request(self, *args: object, **kwargs: object) -> requests.Response:
        response = requests.Response()
        response.status_code = self.status
        response.url = "https://archive.org/asked"
        response._content = json.dumps(self.body or {}).encode()
        return response


def test_being_told_to_slow_down_is_not_an_answer_about_the_page(keyed: None) -> None:
    """A rate limit leaves the source missing, so the next build asks again."""
    doc = cites("https://a.example/1")
    captured = archive.capture(doc, session=Answering(429))
    assert captured == 0
    assert doc.archives == {}
    assert missing(doc) == ["https://a.example/1"]


def test_a_capture_somebody_else_already_made_is_used(keyed: None) -> None:
    doc = cites("https://a.example/1")
    session = Answering(
        200,
        {
            "archived_snapshots": {
                "closest": {"available": True, "timestamp": "20240503123456"},
            }
        },
    )
    assert archive.capture(doc, session=session) == 1
    assert doc.archives["https://a.example/1"].timestamp == "20240503123456"


def test_a_server_error_is_not_recorded_as_a_fact_about_the_source(keyed: None) -> None:
    doc = cites("https://a.example/1")
    assert archive.capture(doc, session=Answering(503)) == 0
    assert doc.archives == {}


def test_without_keys_nothing_is_submitted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(archive.ACCESS_KEY, raising=False)
    monkeypatch.delenv(archive.SECRET_KEY, raising=False)
    doc = cites("https://a.example/1")
    with pytest.raises(archive.NoCredentials):
        archive.capture(doc, session=Answering(200))
    assert doc.archives == {}


# ---- a link to a page of a PDF ---------------------------------------


def test_pages_of_one_pdf_are_one_document_to_capture() -> None:
    """A fragment never reaches a server, so there is one file to ask for."""
    doc = cites(
        "https://a.example/report.pdf#page=28",
        "https://a.example/report.pdf#page=5",
        "https://a.example/report.pdf",
    )
    assert len(doc.sources) == 3
    assert missing(doc) == ["https://a.example/report.pdf"]


def test_every_page_of_a_pdf_shares_the_one_capture(keyed: None) -> None:
    doc = cites("https://a.example/report.pdf#page=28", "https://a.example/report.pdf#page=5")
    session = Answering(
        200,
        {"archived_snapshots": {"closest": {"available": True, "timestamp": "20240503123456"}}},
    )
    assert archive.capture(doc, session=session) == 1


def test_the_archived_copy_opens_on_the_page_that_was_cited() -> None:
    doc = cites("https://a.example/report.pdf#page=28")
    doc.archives["https://a.example/report.pdf"] = Archived(
        snapshot="https://web.archive.org/web/20240503123456/https://a.example/report.pdf",
        timestamp="20240503123456",
    )
    archived = doc.archived("https://a.example/report.pdf#page=28")
    assert archived is not None
    assert archived.snapshot.endswith("/https://a.example/report.pdf#page=28")


def test_a_hand_written_snapshot_of_a_page_is_recorded_as_the_document() -> None:
    original, archived = unwrap_snapshot(
        "https://web.archive.org/web/20240503123456/https://a.example/report.pdf#page=50"
    )
    assert original == "https://a.example/report.pdf#page=50"
    assert archived is not None
    assert archived.snapshot == (
        "https://web.archive.org/web/20240503123456/https://a.example/report.pdf"
    )
