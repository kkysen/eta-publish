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


@pytest.fixture(autouse=True)
def impatient(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ask once and take the answer.

    A real build waits and asks again, because being told to slow down is not
    an answer. A test that did would spend 85 seconds finding that out.
    """
    monkeypatch.setattr(archive, "PATIENCE", ())


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
    assert archive.capture(doc, session=Answering(429)) == (0, 0)
    assert doc.archives == {}
    assert missing(doc) == ["https://a.example/1"]


def test_a_capture_somebody_else_already_made_is_used(keyed: None) -> None:
    doc = cites("https://a.example/1")
    session = Answering(200, [["timestamp"], ["20240503123456"]])
    assert archive.capture(doc, session=session) == (1, 0)
    assert doc.archives["https://a.example/1"].timestamp == "20240503123456"


def test_a_server_error_is_not_recorded_as_a_fact_about_the_source(keyed: None) -> None:
    doc = cites("https://a.example/1")
    assert archive.capture(doc, session=Answering(503)) == (0, 0)
    assert doc.archives == {}


def test_without_keys_what_is_already_archived_is_still_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Looking one up needs no account; only asking for a new one does."""
    monkeypatch.delenv(archive.ACCESS_KEY, raising=False)
    monkeypatch.delenv(archive.SECRET_KEY, raising=False)
    doc = cites("https://a.example/1")
    found, submitted = archive.capture(
        doc, session=Answering(200, [["timestamp"], ["20240503123456"]])
    )
    assert (found, submitted) == (1, 0)
    assert doc.archives["https://a.example/1"].timestamp == "20240503123456"


def test_without_keys_a_source_with_no_capture_is_left_for_a_build_that_can_ask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(archive.ACCESS_KEY, raising=False)
    monkeypatch.delenv(archive.SECRET_KEY, raising=False)
    doc = cites("https://a.example/1")
    assert archive.capture(doc, session=Answering(200, [["timestamp"]])) == (0, 0)
    assert doc.archives == {}
    assert missing(doc) == ["https://a.example/1"]


# ---- asking the replay before the index ------------------------------


class Replaying(requests.Session):
    """A replay that has `captures`, newest last, each with the status it serves.

    The index answers separately, from `rows`, so a test can say what each of
    the two would say and check which one was believed.
    """

    def __init__(self, captures: list[tuple[str, int]], rows: object = None) -> None:
        super().__init__()
        self.captures = captures
        self.rows = rows
        self.index_asked = 0

    @override
    def request(self, method: object, url: object, *args: object, **kwargs: object):
        response = requests.Response()
        response.url = str(url)
        asked = str(url)
        if asked.startswith(archive.INDEX):
            self.index_asked += 1
            response.status_code = 200
            response._content = json.dumps(self.rows or [["timestamp"]]).encode()
            return response
        if not self.captures:
            response.status_code = 404
            return response
        stamp, status = self.captures[-1]
        if f"/web/{archive.NEWEST}/" in asked:
            response.status_code = 302
            response.headers["location"] = f"{archive.REPLAY}/{stamp}/whatever"
            return response
        response.status_code = status
        return response


def test_a_capture_the_replay_serves_is_taken_without_asking_the_index(keyed: None) -> None:
    """Two `HEAD`s at 200 ms beat one query that took 0.5s to 31s."""
    doc = cites("https://a.example/1")
    session = Replaying([("20240503123456", 200)])
    assert archive.capture(doc, session=session) == (1, 0)
    assert doc.archives["https://a.example/1"].timestamp == "20240503123456"
    assert session.index_asked == 0


def test_the_snapshot_is_the_url_this_publishes(keyed: None) -> None:
    """Built from the timestamp, not taken from the redirect.

    The two differ over percent-encoding, and the record is committed and
    compared against a fresh build byte for byte.
    """
    doc = cites("https://a.example/1")
    archive.capture(doc, session=Replaying([("20240503123456", 200)]))
    assert doc.archives["https://a.example/1"].snapshot == (
        "https://web.archive.org/web/20240503123456/https://a.example/1"
    )


def test_a_capture_that_is_not_the_page_falls_back_to_the_index(keyed: None) -> None:
    """The NYT's newest capture replays `403`, and the newest that was the page
    is a different question only the index can answer."""
    doc = cites("https://a.example/1")
    session = Replaying([("20260913083748", 403)], rows=[["timestamp"], ["20260101035028"]])
    assert archive.capture(doc, session=session) == (1, 0)
    assert doc.archives["https://a.example/1"].timestamp == "20260101035028"
    assert session.index_asked == 1


def test_no_capture_at_all_is_confirmed_with_the_index(
    keyed: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A `404` from the replay is not taken as the answer.

    Nothing is written down without the index saying so, because `not archived`
    is what a report publishes.
    """
    refused = Archived(timestamp="20260913", error="no")

    def refuse(*args: object) -> Archived:
        return refused

    monkeypatch.setattr(archive, "_submit", refuse)
    doc = cites("https://a.example/1")
    session = Replaying([])
    archive.capture(doc, session=session)
    assert session.index_asked == 1


# ---- not asking again about the same nothing -------------------------


class Counting(Answering):
    """An `Answering` that says how many requests it was sent."""

    def __init__(self, status: int, body: object = None) -> None:
        super().__init__(status, body)
        self.asked = 0

    @override
    def request(self, *args: object, **kwargs: object) -> requests.Response:
        self.asked += 1
        return super().request(*args, **kwargs)


@pytest.fixture
def unkeyed(monkeypatch: pytest.MonkeyPatch) -> None:
    """No keys, which is the case the cache is for."""
    monkeypatch.delenv(archive.ACCESS_KEY, raising=False)
    monkeypatch.delenv(archive.SECRET_KEY, raising=False)


def test_a_source_with_no_capture_is_not_looked_up_again_the_same_week(unkeyed: None) -> None:
    """The slow half of a build, spent to write down the same nothing twice."""
    doc = cites("https://a.example/1")
    session = Counting(200, [["timestamp"]])
    archive.capture(doc, session=session)
    asked = session.asked
    assert asked
    archive.capture(cites("https://a.example/1"), session=session)
    assert session.asked == asked, "asked again inside the week"


def test_it_is_looked_up_again_once_the_week_is_up(
    unkeyed: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    doc = cites("https://a.example/1")
    session = Counting(200, [["timestamp"]])
    archive.capture(doc, session=session)
    asked = session.asked
    monkeypatch.setattr(archive, "LOOKUP_CACHE_DAYS", 0)
    archive.capture(cites("https://a.example/1"), session=session)
    assert session.asked > asked


def test_what_the_cache_holds_back_is_still_counted_as_unarchived(unkeyed: None) -> None:
    """The count a person reads is how many sources have no capture.

    Not how many were asked about today: a build that said `0 sources` because
    it skipped them all would be reporting on its own cache.
    """
    doc = cites("https://a.example/1")
    archive.capture(doc, session=Answering(200, [["timestamp"]]))
    again = cites("https://a.example/1")
    archive.capture(again, session=Answering(200, [["timestamp"]]))
    assert missing(again) == ["https://a.example/1"]


def test_being_told_to_slow_down_is_not_cached(unkeyed: None) -> None:
    """Nothing was learned, so there is nothing to remember for a week."""
    doc = cites("https://a.example/1")
    session = Counting(429)
    archive.capture(doc, session=session)
    asked = session.asked
    archive.capture(cites("https://a.example/1"), session=session)
    assert session.asked > asked


def test_with_keys_nothing_is_held_back(keyed: None) -> None:
    """A source with no capture is submitted, so it leaves `missing` either way.

    So a build that has keys asks about it however recently one without them
    looked, and the capture gets made rather than waiting out the week.
    """
    archive._remember_nothing(["https://a.example/1"])
    assert archive.to_ask(cites("https://a.example/1")) == ["https://a.example/1"]


def test_a_cache_that_cannot_be_read_is_an_empty_one(
    unkeyed: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A truncated write is a slower build, not a failed one."""
    broken = tmp_path / "archive-lookups.json"
    broken.write_text("{not json")
    monkeypatch.setenv(archive.ARCHIVE_CACHE, str(broken))
    session = Counting(200, [["timestamp"]])
    archive.capture(cites("https://a.example/1"), session=session)
    assert session.asked


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
    session = Answering(200, [["timestamp"], ["20240503123456"]])
    assert archive.capture(doc, session=session) == (1, 0)


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


def test_a_page_of_a_pdf_is_asked_for_raw() -> None:
    """The ordinary Wayback URL for a PDF is an HTML page carrying the toolbar,
    so `#page=50` lands on a wrapper that has no page 50."""
    doc = cites("https://a.example/report.pdf#page=50")
    doc.archives["https://a.example/report.pdf"] = Archived(
        snapshot="https://web.archive.org/web/20240503123456/https://a.example/report.pdf",
        timestamp="20240503123456",
    )
    archived = doc.archived("https://a.example/report.pdf#page=50")
    assert archived is not None
    assert archived.snapshot == (
        "https://web.archive.org/web/20240503123456id_/https://a.example/report.pdf#page=50"
    )


def test_an_anchor_in_a_page_is_left_on_the_ordinary_capture() -> None:
    """An HTML capture is the document itself, toolbar and rewritten assets included."""
    doc = cites("https://a.example/article#grades")
    doc.archives["https://a.example/article"] = Archived(
        snapshot="https://web.archive.org/web/20240503123456/https://a.example/article",
        timestamp="20240503123456",
    )
    archived = doc.archived("https://a.example/article#grades")
    assert archived is not None
    assert archived.snapshot == (
        "https://web.archive.org/web/20240503123456/https://a.example/article#grades"
    )


def test_a_request_that_never_arrived_says_nothing_about_the_source(keyed: None) -> None:
    """A read timeout is about reaching `web.archive.org`, not about the page.

    Recorded as a failed capture it would leave that source with no archive
    for good, which is what happened to a Wikipedia article that has been
    captured hundreds of times.
    """

    class Timing(requests.Session):
        @override
        def request(self, *args: object, **kwargs: object) -> requests.Response:
            raise requests.Timeout("read timed out")

    doc = cites("https://a.example/1")
    assert archive.capture(doc, session=Timing()) == (0, 0)
    assert doc.archives == {}
    assert missing(doc) == ["https://a.example/1"]


def test_being_told_to_slow_down_is_asked_again(
    keyed: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two `429`s and then an answer, which is the shape a real build meets."""
    monkeypatch.setattr(archive, "PATIENCE", (0, 0, 0))
    answers = [429, 429, 200]

    class Relenting(requests.Session):
        @override
        def request(self, *args: object, **kwargs: object) -> requests.Response:
            response = requests.Response()
            response.status_code = answers.pop(0) if answers else 200
            response.url = "https://web.archive.org/asked"
            response._content = json.dumps([["timestamp"], ["20240503123456"]]).encode()
            return response

    doc = cites("https://a.example/1")
    assert archive.capture(doc, session=Relenting()) == (1, 0)
    assert doc.archives["https://a.example/1"].timestamp == "20240503123456"
