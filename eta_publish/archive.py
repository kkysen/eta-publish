"""The record of where each source the report cites has been archived.

A link is a claim about a page that is not ours and that nobody promised to
keep. The report outlives the page: `nypost.com` reorganizes, an agency retires
a PDF, a press release moves. So every source is captured once and the capture
is cited beside the original, and the record of which capture belongs to which
source is committed, because a report published in 2026 has to keep saying the
same thing in 2036.

Keyed by the original URL, never by the snapshot. A document that already cites
a `web.archive.org` URL has its link unwrapped at parse time and seeds the
record with the capture it named, so a source archived by hand and a source
archived here are the same source.

Like `images.py`, this is the side that touches the network and the filesystem;
the emitters read the result off the document and stay pure.
"""

import json
import os
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import requests

from .nodes import Archived, Document, document_url

ARCHIVES_JSON = "archives.json"

SAVE = "https://web.archive.org/save"
"""Save Page Now, which takes a URL and captures it."""

INDEX = "https://web.archive.org/cdx/search/cdx"
"""What the Wayback Machine already has, which is asked first and needs no keys.

A source somebody else already captured is a source already archived. Asking
costs nothing, spending a capture on it would take a slot from one of the pages
nothing has, and a capture already years old is better evidence of what the
page said than one taken today.

The index rather than `wayback/available`, because it can be asked for a
capture that came back `200`. The newest capture of a page that has since been
taken down is a capture of the 404, and recording that as where the source is
archived would be worse than recording nothing: the entry would say `archived`
and lead to a page saying the thing is gone.
"""

ACCESS_KEY = "SPN2_ACCESS_KEY"
SECRET_KEY = "SPN2_SECRET_KEY"
"""The archive.org keys, from `https://archive.org/account/s3.php`.

Out of the environment rather than a file in the repository, because they are
credentials and this repository is public.
"""

MAX_AT_ONCE = 2
"""How many sources to be asking about at once.

Save Page Now allows an authenticated account twelve captures in flight. Well
under it, because the index is the part that runs on every build and it is
stricter: 81 lookups four at a time answered `429` to nearly all of them, and
went on refusing single queries two seconds apart for minutes afterwards. What
that build recorded was that 72 of 81 sources were unarchived, when what had
happened was that it had been told to stop asking.
"""

PATIENCE = (5, 20, 60)
"""How long to wait before asking again, after being told to slow down.

Three tries and then the source is left for the next build. Growing, because a
rate limit that is still there after five seconds is not one more seconds will
clear; and finite, because a build should end.
"""

CAPTURE_TIMEOUT = 180
"""How long to wait for one capture before giving up on it.

Save Page Now caps a page capture at 50 seconds, and a job queued behind others
takes longer than it spends fetching. Past this the answer is that the build is
not going to get one today, which is a thing to record and move on from rather
than a thing to keep waiting for.
"""

TOO_MANY = 429
SERVER_ERROR = 500
"""Answers that are about the service rather than about the page asked for.

Told to slow down, a build records nothing: a rate limit hit on a Tuesday is
not a fact about a source, and writing it down as one would leave that source
with no archive forever.
"""

POLL_EVERY = 5


def read_archive_index(dest: Path, doc: Document) -> None:
    """Tell `doc` which of its sources already have a capture.

    Read rather than derived, and committed rather than fetched: a capture is
    an event that happened once, at a time, and nothing about the document says
    when. This is the only thing that remembers.

    An entry already on the document wins, because that one came from the
    document's own href and is what the report itself says.
    """
    index = dest / ARCHIVES_JSON
    if not index.exists():
        return
    for url, entry in json.loads(index.read_text()).items():
        doc.archives.setdefault(
            url,
            Archived(
                snapshot=entry.get("snapshot", ""),
                timestamp=entry.get("timestamp", ""),
                error=entry.get("error", ""),
            ),
        )


def write_archive_index(dest: Path, doc: Document) -> None:
    """Write back everything known about the report's sources.

    Sorted, as `images.json` is: the file is committed and compared against a
    fresh build, so any two runs that agree about the document have to write
    the same bytes.

    Only the sources this document cites are written. A record that kept every
    URL any draft ever held would grow forever and would never say which of
    them the report still stands on.
    """
    index = {}
    for url in _documents(doc):
        archived = doc.archives.get(url)
        if archived is None:
            continue
        entry = {"snapshot": archived.snapshot, "timestamp": archived.timestamp}
        if archived.error:
            entry = {"timestamp": archived.timestamp, "error": archived.error}
        index[url] = entry
    if not index:
        return
    (dest / ARCHIVES_JSON).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")


def missing(doc: Document) -> list[str]:
    """The documents nothing has tried to capture yet, in the order they are cited.

    Documents rather than sources: a fragment never reaches a server, so the
    fifteen pages of one MTA PDF the report cites are one file to capture.

    One recorded with an `error` is not among them: that one has been tried,
    and a build that submitted it again on every run would spend the rate limit
    on the pages least likely to ever answer.
    """
    return [url for url in _documents(doc) if url not in doc.archives]


def _documents(doc: Document) -> list[str]:
    """Every source as the thing that gets captured, deduplicated, in order."""
    seen: dict[str, None] = {}
    for source in doc.sources:
        seen.setdefault(document_url(source), None)
    return list(seen)


def today() -> str:
    """The date an attempt was made, for an entry that records a failure."""
    return datetime.now(UTC).strftime("%Y%m%d")


def capture(doc: Document, *, session: requests.Session | None = None) -> tuple[int, int]:
    """Archive every source of `doc` that nothing has tried yet.

    Returns how many were found already captured and how many were captured on
    request, which are different things to tell somebody about: the first costs
    nothing and needs no account, and the second is what the keys are for.

    Only the ones missing from the record: a source already captured keeps the
    capture it has, because the point of a snapshot is that it is of the page
    as the report read it, and recapturing would quietly move it forward to
    whatever the page says now.

    A capture that fails is recorded as a failure rather than left missing.
    Some of these cannot be archived at all: a Google Docs spreadsheet answers
    with a login page, and the nine `mp.weixin.qq.com` links are not reachable
    by the crawler. Left missing, every build from here to forever would submit
    them again.

    A source the service would not answer about at all is the exception, and
    stays missing. Being told to slow down is not a fact about the page, and
    recording it as one would mean a rate limit hit on a Tuesday permanently
    left a source with no archive.
    """
    wanted = missing(doc)
    if not wanted:
        return 0, 0
    http = session or requests.Session()
    # Looking up what the archive already holds needs no account, so a build
    # without keys still does the half it can: most of what a report cites is
    # already in the Wayback Machine, put there by somebody else.
    headers = _keys()

    def archive(url: str) -> tuple[Archived | None, bool]:
        return _archive(http, headers, url)

    with ThreadPoolExecutor(max_workers=MAX_AT_ONCE) as pool:
        results = list(pool.map(archive, wanted))
    # Written in document order rather than as each answer arrives, so that two
    # builds that captured the same sources write the same file.
    found = submitted = 0
    for url, (archived, already) in zip(wanted, results, strict=True):
        if archived is None:
            continue
        doc.archives[url] = archived
        if archived.error:
            continue
        if already:
            found += 1
        else:
            submitted += 1
    return found, submitted


def _keys() -> dict[str, str] | None:
    """The headers a capture request carries, or `None` if there are no keys.

    Asking for a capture needs an account; asking what is already archived does
    not. So this is a question rather than a refusal, and a build without keys
    does the half of the work that is open to it.
    """
    access, secret = os.environ.get(ACCESS_KEY), os.environ.get(SECRET_KEY)
    if not access or not secret:
        return None
    return {"Accept": "application/json", "Authorization": f"LOW {access}:{secret}"}


def have_keys() -> bool:
    """Whether this build can ask for a capture as well as look one up."""
    return _keys() is not None


def _archive(
    http: requests.Session, headers: dict[str, str] | None, url: str
) -> tuple[Archived | None, bool]:
    """One source: the capture it already has, or a new one, or why neither.

    `None` where nothing was learned: the service declined to answer, or it has
    no capture and there are no keys to ask for one. Neither is a fact about
    the page, so neither is written down, and the next build asks again.

    The second value says whether the capture was already there, which is the
    half of this that needs no account.
    """
    try:
        found = _patiently(lambda: _existing(http, url))
        if found is not None:
            return found, True
        if headers is None:
            return None, False
        return _submit(http, headers, url), False
    except Busy, requests.RequestException:
        # Nothing about the source. A read that timed out, a connection that
        # dropped, a name that would not resolve: all of them are about getting
        # to `web.archive.org`, and one of them recorded as a failed capture is
        # a source left with no archive because of a slow afternoon. The first
        # run of this wrote exactly that against
        # `en.wikipedia.org/wiki/Automatic_train_operation`, which has been
        # archived hundreds of times.
        #
        # A source is written down as uncapturable only when Save Page Now says
        # so about that URL, which `_submit` is what hears.
        return None, False


class Busy(RuntimeError):
    """The service declined to answer right now, which is not about the page."""


def _checked(response: requests.Response) -> requests.Response:
    """`response`, or `Busy` where the answer was about the service rather than the URL."""
    if response.status_code == TOO_MANY or response.status_code >= SERVER_ERROR:
        raise Busy(f"{response.status_code} from {response.url}")
    response.raise_for_status()
    return response


def _patiently[T](ask: Callable[[], T]) -> T:
    """`ask`, again after a wait if the answer was that it is being asked too much.

    The waiting is what makes the count mean anything: a source recorded as
    unarchived because the index was busy is a source that will publish saying
    so, and nothing later goes back to check.
    """
    for wait in PATIENCE:
        try:
            return ask()
        except Busy:
            time.sleep(wait)
    return ask()


def _existing(http: requests.Session, url: str) -> Archived | None:
    """The newest capture of `url` that came back `200`, if there is one.

    `200` and nothing else. A page that has been taken down still gets crawled,
    so its newest captures are of the 404, and a `warc/revisit` row carries no
    status at all because it only says the bytes had not changed since an
    earlier capture. What is wanted is the newest capture that was the page.

    That is the whole of what can be checked here. A capture that answered
    `200` with a login wall, or with a site's own "page not found", is a
    capture of a page that loaded, and nothing in the index tells it from the
    real thing.
    """
    response = _checked(
        http.get(
            INDEX,
            params={
                "url": url,
                "output": "json",
                "fl": "timestamp",
                "filter": "statuscode:200",
                # The last row is the newest, and the only one wanted: this is
                # asked once per source, and a report has 113 of them.
                "limit": "-1",
            },
            timeout=60,
        )
    )
    # A page with no capture answers with nothing at all rather than with an
    # empty list, and the first row of an answer names the fields.
    rows: list[list[str]] = response.json() if response.text.strip() else []
    if len(rows) < 2:
        return None
    stamp = str(rows[1][0])
    # Built here rather than taken as given: the record is committed and
    # compared against a fresh build byte for byte.
    return Archived(snapshot=f"https://web.archive.org/web/{stamp}/{url}", timestamp=stamp)


def _submit(http: requests.Session, headers: dict[str, str], url: str) -> Archived:
    """Ask for a capture and wait for it, or say why there is not one.

    Save Page Now answers with a job rather than a snapshot, so the wait is the
    ordinary shape of this rather than a retry.
    """
    started = _checked(http.post(SAVE, headers=headers, data={"url": url}, timeout=60))
    answer = started.json()
    job = answer.get("job_id")
    if not job:
        return Archived(timestamp=today(), error=_refused(answer))
    deadline = time.monotonic() + CAPTURE_TIMEOUT
    while time.monotonic() < deadline:
        time.sleep(POLL_EVERY)
        state = _checked(http.get(f"{SAVE}/status/{job}", headers=headers, timeout=30)).json()
        status = state.get("status")
        if status == "success" and state.get("timestamp"):
            stamp = state["timestamp"]
            return Archived(snapshot=f"https://web.archive.org/web/{stamp}/{url}", timestamp=stamp)
        if status == "error":
            return Archived(timestamp=today(), error=_refused(state))
    return Archived(timestamp=today(), error=f"no answer within {CAPTURE_TIMEOUT} seconds")


def _refused(answer: dict[str, object]) -> str:
    """What the service said, short enough to publish beside the source."""
    said = answer.get("status_ext") or answer.get("message") or answer.get("status")
    return str(said) if said else "the capture failed without saying why"
