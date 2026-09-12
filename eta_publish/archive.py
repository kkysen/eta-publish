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
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import requests

from .nodes import Archived, Document, document_url

ARCHIVES_JSON = "archives.json"

SAVE = "https://web.archive.org/save"
"""Save Page Now, which takes a URL and captures it."""

AVAILABLE = "https://archive.org/wayback/available"
"""What the Wayback Machine already has, which is asked first and costs nothing.

A source somebody else already captured is a source already archived. Spending
a capture on it would take a slot from one of the pages nothing has.
"""

ACCESS_KEY = "SPN2_ACCESS_KEY"
SECRET_KEY = "SPN2_SECRET_KEY"
"""The archive.org keys, from `https://archive.org/account/s3.php`.

Out of the environment rather than a file in the repository, because they are
credentials and this repository is public.
"""

MAX_AT_ONCE = 4
"""How many captures to have in flight at once.

Save Page Now allows an authenticated account twelve. Well under it, because a
capture is a crawl of somebody else's site: the limit is what the service will
tolerate, and this is what a build should ask of it.
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


class NoCredentials(RuntimeError):
    """No archive.org keys, so nothing can be submitted."""


def capture(doc: Document, *, session: requests.Session | None = None) -> int:
    """Archive every source of `doc` that nothing has tried yet, and say how many.

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
        return 0
    http = session or requests.Session()
    headers = _authorization()

    def archive(url: str) -> Archived | None:
        return _archive(http, headers, url)

    with ThreadPoolExecutor(max_workers=MAX_AT_ONCE) as pool:
        results = list(pool.map(archive, wanted))
    # Written in document order rather than as each answer arrives, so that two
    # builds that captured the same sources write the same file.
    for url, archived in zip(wanted, results, strict=True):
        if archived is not None:
            doc.archives[url] = archived
    return sum(1 for archived in results if archived is not None and not archived.error)


def _authorization() -> dict[str, str]:
    """The headers every request carries, or `NoCredentials` saying what is missing."""
    access, secret = os.environ.get(ACCESS_KEY), os.environ.get(SECRET_KEY)
    if not access or not secret:
        raise NoCredentials(
            f"no archive.org keys in the environment, so no source was submitted; "
            f"set {ACCESS_KEY} and {SECRET_KEY} from https://archive.org/account/s3.php"
        )
    return {"Accept": "application/json", "Authorization": f"LOW {access}:{secret}"}


def _archive(http: requests.Session, headers: dict[str, str], url: str) -> Archived | None:
    """One source: the capture it already has, or a new one, or why neither.

    `None` where the service said nothing about the page: it is not an answer,
    so it is not recorded, and the next build asks again.
    """
    try:
        found = _existing(http, headers, url)
        if found is not None:
            return found
        return _submit(http, headers, url)
    except Busy:
        return None
    except requests.RequestException as e:
        return Archived(timestamp=today(), error=_said(e))


class Busy(RuntimeError):
    """The service declined to answer right now, which is not about the page."""


def _checked(response: requests.Response) -> requests.Response:
    """`response`, or `Busy` where the answer was about the service rather than the URL."""
    if response.status_code == TOO_MANY or response.status_code >= SERVER_ERROR:
        raise Busy(f"{response.status_code} from {response.url}")
    response.raise_for_status()
    return response


def _existing(http: requests.Session, headers: dict[str, str], url: str) -> Archived | None:
    """The capture the Wayback Machine already holds, if it holds one."""
    response = _checked(http.get(AVAILABLE, params={"url": url}, headers=headers, timeout=30))
    closest = response.json().get("archived_snapshots", {}).get("closest", {})
    if not closest.get("available") or not closest.get("timestamp"):
        return None
    # Rebuilt from the timestamp rather than taken as given: what comes back
    # carries whichever scheme and host the service felt like, and the record
    # is compared against a fresh build byte for byte.
    stamp = closest["timestamp"]
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


def _said(error: requests.RequestException) -> str:
    """A failed request as one line, because this reaches the published page."""
    return " ".join(str(error).split())[:200] or error.__class__.__name__
