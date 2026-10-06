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
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from threading import Lock, Semaphore
from urllib.parse import urlsplit

import platformdirs
import requests
from pypdf import PdfReader
from pypdf.errors import PyPdfError
from requests.adapters import HTTPAdapter

from . import PACKAGE_NAME
from .checks import plural
from .nodes import UNREWRITTEN, Archived, Document, cited_page, document_url, wayback_url

ARCHIVES_JSON = "archives.json"

SAVE = "https://web.archive.org/save"
"""Save Page Now, which takes a URL and captures it."""

REPLAY = "https://web.archive.org/web"
"""The archived copies themselves, which is also the cheapest way to find one.

`REPLAY/<date>/<url>` redirects to the capture closest to that date, which is a
point lookup rather than a scan, and the capture it serves carries the status the
crawler got. So the question the index is asked can be asked here instead, in
about 200 ms rather than seconds, and the answer is about the URL this publishes.
"""

NEWEST = "2099"
"""A date nothing is archived past, so the capture closest to it is the newest."""

REDIRECT = 302
"""What the replay says when it has a capture, naming it in `Location`."""

OK = 200
"""What it says when that capture is the page rather than a wall or a 404."""

ITEM_HOST = "archive.org"
ITEM_PATH = "details"
"""An Internet Archive item: a scanned book, a recording, a piece of software.

Already archival, and by the institution that runs the Wayback Machine, which
is why it cannot be captured there: `archive.org` excludes its own pages from
the index, so every one of these answers `403` to both the index and the replay.
SAS West cites two pages of one scanned book and both published as
`not archived`, which reads as no preserved copy existing when the link is the
preserved copy.
"""

METADATA = "https://archive.org/metadata"
"""What an item says about itself, which includes the day it was added.

So these are cited the way every other source is, with a date and a link,
rather than as a special case the reader has to know how to read.
"""

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

KEYS_PAGE = "https://archive.org/account/s3.php"
"""Where the keys to ask for a capture come from."""

ACCESS_KEY = "SPN2_ACCESS_KEY"
SECRET_KEY = "SPN2_SECRET_KEY"
"""The archive.org keys, from `https://archive.org/account/s3.php`.

Out of the environment rather than a file in the repository, because they are
credentials and this repository is public.
"""

INDEX_AT_ONCE = 2
"""How many index queries to have in flight, which is the strict limit.

81 lookups four at a time answered `429` to nearly all of them, and the index
went on refusing single queries two seconds apart for minutes afterwards. What
that build recorded was that 72 of 81 sources were unarchived, when what had
happened was that it had been told to stop asking.
"""

SUBMIT_AT_ONCE = 12
"""How many captures to ask for at once, which is what the account allows.

Save Page Now gives an authenticated account twelve in flight, and a capture
is the slowest thing here: a page fetch somebody else queues, waited on for up
to `CAPTURE_TIMEOUT`. Sixteen of those two at a time is eight waits long, and
twelve at a time is two.

Asking for a thirteenth is answered rather than punished: the service says the
session limit is reached, which `_submitted` reads as being told to wait
rather than as anything about the page.
"""

REPLAY_AT_ONCE = 10
"""How many replay lookups to have in flight, and how wide the connection pool is.

Measured, over all 150 documents the five reports cite:

- 8 at once: every one answered, in 20.5 seconds.
- 10 at once: every one answered, the same answers, in 15.1 seconds.
- 32 at once: 27 answered and 123 could not connect.
- 150 at once: none answered.

Past that point `web.archive.org` stops accepting connections from the address
at all, a single request included, for a while afterwards. That is worse than a
`429`: nothing about it says to slow down, and it takes the index down with it,
since both are the same host.

Only sources without a capture are asked on a build, which is sixteen at most
today, so ten is two round trips of waiting rather than the fifteen seconds
above.
"""

_INDEXING = Semaphore(INDEX_AT_ONCE)
_SUBMITTING = Semaphore(SUBMIT_AT_ONCE)
_REPLAYING = Semaphore(REPLAY_AT_ONCE)
"""The three gates, held for the length of one question each.

A gate rather than a smaller pool: what has to be limited is the asking, and
the thread that is waiting to ask is not the thing the limit is about.

Module-wide rather than one per `capture`, because reports are built in
parallel and each one has its own pool. Eight reports with a pool of ten each
is eighty replay lookups in flight, past the point where `web.archive.org`
stops accepting connections, and a lookup that cannot connect publishes its
source as `not archived`. IBX Automation published sources that way that
had been captured weeks before, and the next build found every one.
"""

PATIENCE = (timedelta(seconds=5), timedelta(seconds=20), timedelta(minutes=1))
"""How long to wait before asking again, after being told to slow down.

Three tries and then the source is left for the next build. Growing, because a
rate limit that is still there after five seconds is not one more seconds will
clear; and finite, because a build should end.
"""

CAPTURE_TIMEOUT = timedelta(minutes=3)
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

POLL_EVERY = timedelta(seconds=5)

INDEX_LIFETIME = timedelta(days=7)
"""How long an index lookup that found nothing stands before it is asked again.

What changes a `no capture` answer is somebody else archiving the page, which
happens on the scale of weeks if it happens at all. A week of not re-asking is
20-odd lookups a build does not make, and the cost of being a week late to cite
a capture somebody else made is not a cost a reader can see.
"""


REPLAY_LIFETIME = timedelta(hours=1)
"""How long a replay lookup that found nothing stands before it is asked again.

An hour, where the index's answer stands a week, because the replay is the
half that notices a capture somebody else has just made: held back for a week,
a source would go on publishing as unarchived long after it was not.
An hour is the length of an afternoon's rebuilding, which is what this is for:
running `eta-publish all` twice in a row should not ask the same question twice.

The cost is the one the week had, an hour long instead: a capture made inside
the hour is not seen until it is up. CI restores `~/.cache/eta-publish` between
runs, this file with it, so two Pages runs inside an hour share it too.
"""

ARCHIVE_CACHE = "ETA_ARCHIVE_CACHE"
"""Where to keep the cache instead, named like `ETA_TOKEN` and for tests."""

LIFETIMES = {"index": INDEX_LIFETIME, "replay": REPLAY_LIFETIME}
"""How long a lookup of each kind that found nothing stands for."""


def archive_cache_path() -> Path:
    """Where the lookups that found nothing are remembered.

    Outside the repository and never committed, because it is not a fact about
    the report: `archives.json` says where each source is archived, and a source
    with no capture has no entry there either way. So this can expire, be
    thrown away, or be absent on a fresh clone, and the build writes the same
    `site/` regardless. That is the whole reason it is a cache and not a record.

    One file, with the index's lookups under `index` and the replay's under
    `replay`, each source by when it was asked.

    Read on each call rather than resolved once, so a test can point it
    somewhere else.
    """
    override = os.environ.get(ARCHIVE_CACHE)
    if override:
        return Path(override)
    return platformdirs.user_cache_path(PACKAGE_NAME) / "archive.json"


def _cached() -> dict[str, dict[str, str]]:
    """Each kind of lookup that found nothing, by source, by when it was asked.

    A cache nothing can read is an empty one: a truncated write, a file from an
    older layout, a directory somebody's backup tool replaced. None of them are
    worth failing a build over, because the answer to all of them is to ask the
    archive again.
    """
    try:
        loaded = json.loads(archive_cache_path().read_text())
    except OSError, ValueError:
        loaded = None
    cached: dict[str, dict[str, str]] = {kind: {} for kind in LIFETIMES}
    if not isinstance(loaded, dict):
        return cached
    for kind in LIFETIMES:
        entries = loaded.get(kind)
        if isinstance(entries, dict):
            cached[kind] = {url: str(when) for url, when in entries.items() if isinstance(url, str)}
    return cached


_REMEMBERING = Lock()
"""Held across the read and the write, because the file is one and the reports are not.

Reports are built in parallel, so three of these finish at once, and each one
reads the file, adds its own sources and writes the whole thing back. Unheld,
two that interleave leave one report's sources out of the cache, and the only
sign of it is a build that is slow again for no visible reason.

Like `_SIGNING_IN` in `fetch.py`, and for the same reason: a cache does not make
a read-modify-write atomic.
"""


def _remember(found_nothing: dict[str, list[str]]) -> None:
    """Write down that these lookups, by kind, were just made and found nothing.

    Only the ones asked about on this build are refreshed; the rest keep the
    time they had, so they expire when they were going to. Except the ones
    already expired, which are dropped: they are no longer holding anything
    back, and a file that kept every URL a draft ever cited would grow forever.

    Sorted, like every other file here, so that looking at it is possible.
    """
    if not any(found_nothing.values()):
        return
    with _REMEMBERING:
        known = {
            kind: {url: when for url, when in entries.items() if _stands(kind, when)}
            for kind, entries in _cached().items()
        }
        now = datetime.now(UTC).isoformat(timespec="seconds")
        for kind, urls in found_nothing.items():
            known[kind].update(dict.fromkeys(urls, now))
        path = archive_cache_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Written beside it and moved over it, so nothing ever reads this
            # half-written. A torn read would parse as nothing, and nothing is
            # what the next write would then build on: one interrupted write
            # would throw the whole cache away rather than one entry.
            temp = path.with_suffix(".writing")
            temp.write_text(json.dumps(known, indent=2, sort_keys=True) + "\n")
            temp.replace(path)
        except OSError:
            # A cache that cannot be written is a build that is slower than it
            # needs to be, which is not a build that should fail.
            pass


def _stands(kind: str, when: str) -> bool:
    """Whether a lookup of this kind made at `when` still stands.

    A time nothing can read was not recent, so the source is asked about
    again, which is the harmless direction. Nor was one with no zone, which
    cannot be compared with now.
    """
    try:
        asked = datetime.fromisoformat(when)
    except ValueError:
        return False
    if asked.tzinfo is None:
        return False
    return datetime.now(UTC) - asked < LIFETIMES[kind]


def _session() -> requests.Session:
    """A session holding as many connections open as there are lookups at once.

    `requests` keeps ten a host and discards the rest, so a pool wider than
    that pays a fresh TLS handshake for every request past the tenth, which
    takes longer than the `HEAD` it is for. At ten that changes nothing; it
    is here so that whoever widens `REPLAY_AT_ONCE` widens the pool with it,
    rather than finding out from a log full of discarded connections.
    """
    http = requests.Session()
    adapter = HTTPAdapter(pool_connections=REPLAY_AT_ONCE, pool_maxsize=REPLAY_AT_ONCE)
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    return http


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
        recorded = Archived(
            snapshot=entry.get("snapshot", ""),
            timestamp=entry.get("timestamp", ""),
            error=entry.get("error", ""),
            pages=entry.get("pages", 0),
        )
        cited = doc.archives.get(url)
        if cited is None:
            doc.archives[url] = recorded
        elif cited.timestamp == recorded.timestamp and not cited.pages:
            # The same capture, so the record's count of its pages is still
            # true of it. The document names the capture and nothing more.
            doc.archives[url] = replace(cited, pages=recorded.pages)


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
        entry: dict[str, str | int] = {
            "snapshot": archived.snapshot,
            "timestamp": archived.timestamp,
        }
        if archived.error:
            entry = {"timestamp": archived.timestamp, "error": archived.error}
        if archived.pages:
            entry["pages"] = archived.pages
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


def capture(
    doc: Document,
    *,
    session: requests.Session | None = None,
    along: Callable[[], None] | None = None,
) -> tuple[int, int]:
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

    `along` is called once per source as the answer arrives, for a build that
    wants to say how far along it is: this is the slowest thing a build does,
    and it is slow in a way nothing here controls.

    A source the service would not answer about at all is the exception, and
    stays missing. Being told to slow down is not a fact about the page, and
    recording it as one would mean a rate limit hit on a Tuesday permanently
    left a source with no archive.
    """
    http = session or _session()
    # Looking up what the archive already holds needs no account, so a build
    # without keys still does the half it can: most of what a report cites is
    # already in the Wayback Machine, put there by somebody else.
    headers = _keys()
    wanted = missing(doc)
    if not wanted:
        return 0, 0
    pdfs = pdfs_cited(doc)
    # Only a build with no keys defers anything, the index's answer for a week
    # and the replay's for an hour: one with keys submits a source the replay
    # found nothing for, which records an answer either way.
    cached = _cached() if headers is None else {"index": {}, "replay": {}}

    def archive(url: str) -> Lookup:
        return _archive(
            http,
            headers,
            url,
            pdf=url in pdfs,
            index=not _stands("index", cached["index"].get(url, "")),
            replay=not _stands("replay", cached["replay"].get(url, "")),
        )

    pool = ThreadPoolExecutor(max_workers=REPLAY_AT_ONCE)
    asked = [pool.submit(archive, url) for url in wanted]
    try:
        if along is not None:
            # As each answer arrives rather than as the list is read back:
            # the results are read in document order, which says nothing
            # about when the service answered.
            for _ in as_completed(asked):
                along()
        results = [answer.result() for answer in asked]
    except KeyboardInterrupt:
        # Cancelled and not waited on. Every request here has a timeout in
        # the tens of seconds, so waiting is a minute of a build that has
        # been told to stop, and the person who said so says it again and
        # again into what looks like nothing happening.
        pool.shutdown(wait=False, cancel_futures=True)
        raise Stopped(
            f"asked about {sum(answer.done() for answer in asked)} of "
            f"{plural(len(wanted), 'source')}, and was waiting on "
            + ", ".join(url for url, answer in zip(wanted, asked, strict=True) if answer.running())
        ) from None
    pool.shutdown()
    # Written in document order rather than as each answer arrives, so that two
    # builds that captured the same sources write the same file.
    found = submitted = 0
    for url, result in zip(wanted, results, strict=True):
        if result.archived is None:
            continue
        doc.archives[url] = result.archived
        if result.archived.error:
            continue
        if result.already:
            found += 1
        else:
            submitted += 1
    answered = list(zip(wanted, results, strict=True))
    _remember(
        {
            "index": [url for url, result in answered if result.unindexed],
            "replay": [url for url, result in answered if result.unserved],
        }
    )
    unanswered = [url for url, result in answered if result.unanswered]
    if unanswered:
        raise Unanswered(
            f"could not ask the archive about {plural(len(unanswered), 'source')}, "
            "so they would publish as not archived; build again: " + ", ".join(unanswered)
        )
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


@dataclass(frozen=True)
class Lookup:
    """What asking about one source came to.

    `archived` is what to write down, and `None` where nothing was learned.
    `already` says the capture was there to be found, which is the half of this
    that needs no account.

    `unindexed` is the third case and the reason this is not a pair: the index
    answered, and the answer was that there is no capture. That is worth
    remembering for a week so the next build does not ask again, and it is not
    the same as an answer that never came.
    """

    archived: Archived | None = None
    already: bool = False
    unindexed: bool = False
    unserved: bool = False
    """The replay was asked and served nothing, which stands for an hour."""
    unanswered: bool = False
    """The archive could not be asked at all, so nothing is known either way."""


def _archive(
    http: requests.Session,
    headers: dict[str, str] | None,
    url: str,
    *,
    pdf: bool = False,
    index: bool = True,
    replay: bool = True,
) -> Lookup:
    """One source: the capture it already has, or a new one, or why neither."""
    try:
        item = _item(url)
        if item is not None:
            # Nothing to look up and nothing to ask for: it is already archived,
            # and asking the Wayback Machine about it only ever answers `403`.
            return Lookup(_patiently(lambda: _added(http, url, item)), already=True)
        found = _patiently(lambda: _existing(http, url, pdf=pdf, index=index, replay=replay))
        if found is not None:
            return Lookup(found, already=True)
        if headers is None:
            # `unindexed` only where the index was the one that said so. Where it
            # was held back, this build learned nothing, and writing today's
            # date would renew the entry on every build and expire it never.
            return Lookup(unindexed=index, unserved=replay)
        return Lookup(_patiently(lambda: _submit(http, headers, url)))
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
        #
        # Not remembered either, for the same reason: a cache of this would be a
        # week of not asking about a page nothing ever learned anything about.
        #
        # Nor published: `capture` stops the build over it, because the source
        # would otherwise publish as `not archived`, which is a claim about it.
        return Lookup(unanswered=True)


class Unanswered(RuntimeError):
    """The archive could not be asked about some sources, so the build stops.

    Published anyway, those sources would read `not archived`, and a build an
    hour later that got through would publish something different from the
    same document. Stopping keeps the build saying the same thing every time
    it says anything, and the next one asks again.
    """


class Busy(RuntimeError):
    """The service declined to answer right now, which is not about the page."""


class Stopped(KeyboardInterrupt):
    """Somebody stopped the build, and this says what it was waiting on.

    A `KeyboardInterrupt` still, so nothing treats it as a failure of the
    report: what a run that was told to stop should print is where it had
    got to, not a traceback through the machinery that was waiting.
    """


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

    A connection that was refused or a read that timed out is waited out the
    same way: `web.archive.org` refuses connections rather than answering `429`
    when it is asked too much at once, so that is being told to slow down too.
    Not every `RequestException`, though: an `HTTPError` is an answer.
    """
    for wait in PATIENCE:
        try:
            return ask()
        except Busy, requests.ConnectionError, requests.Timeout:
            time.sleep(wait.total_seconds())
    return ask()


def _existing(
    http: requests.Session,
    url: str,
    *,
    pdf: bool = False,
    index: bool = True,
    replay: bool = True,
) -> Archived | None:
    """The newest capture of `url` that is the page, if there is one.

    Asked of the replay first and of the index only if that did not answer.
    Both answer the same question; the index is the one that can be asked it
    exactly, and it is twenty to sixty times slower.

    `index` is what the cache holds back, and only that. The replay runs on
    every build for every source: it costs about half a second, and it is the
    half that finds a capture somebody else has just made. Held back, a source
    would go on publishing as unarchived for a week after its capture appeared,
    and a build checking its own work could not see what a fresh one would.
    That is not a theory: `masstransitmag.com`'s press release was published as
    `not archived` because this machine had cached the older answer, and CI,
    which had no cache, found the capture and failed the check.
    """
    # `replay` is the hour's cache, and holds back the replay for that long only.
    served = _replayed(http, url, pdf=pdf) if replay else None
    if served is not None:
        return served
    return _indexed(http, url, pdf=pdf) if index else None


def _replayed(http: requests.Session, url: str, *, pdf: bool = False) -> Archived | None:
    """`_served`, asked while holding `_REPLAYING`."""
    with _REPLAYING:
        return _served(http, url, pdf=pdf)


def _served(http: requests.Session, url: str, *, pdf: bool = False) -> Archived | None:
    """The newest capture, if the archive serves it as the page.

    Two `HEAD`s where the index takes one query, and still far cheaper: the
    replay answers in about 200 ms of server time because it is a point lookup,
    where a `statuscode` filter over a URL's whole row set took 0.5s to 31s,
    varying 50-fold for the same query asked three times running.

    The first `HEAD` asks the replay for the capture closest to a date nothing
    is archived past, which is the newest one, and reads the timestamp out of
    the redirect. The second asks for that capture at the URL this would
    publish, rather than at the one the redirect names: those differ over
    percent-encoding, and the point is to check the link a reader will click.

    `200` there is the answer the index is asked for, arrived at the other way
    round. Stricter in one way: the index says a crawler once logged `200`,
    while this says the archived URL serves the page now. Looser in another: a
    `warc/revisit` capture carries no status in the index and so is filtered
    out, but the replay resolves it and serves it, and it is a later crawl of
    bytes that had not changed. `hsr.ca.gov`'s 2026 business plan is one, five
    weeks newer than the newest row the index would allow and the same digest.

    `None` where the capture is not the page: taken down, paywalled, a login
    wall. The NYT's 125th Street piece is captured daily and the newest replays
    `403`. Then the index is asked, because the newest capture that *was* the
    page is a different question and only the index can answer it.

    For a `pdf`, also `None` where the capture is not one, whatever its status.
    `transitcosts.com` answers some crawls of `TCP_Final_Report.pdf` with a
    "One moment, please..." bot check, and Save Page Now archived that as `200`.
    """
    landed = _checked_service(
        http.head(f"{REPLAY}/{NEWEST}/{url}", timeout=30, allow_redirects=False)
    )
    if landed.status_code != REDIRECT:
        # No capture at all, or none the replay will serve. Either way this is
        # not the answer, and the index is asked rather than trusted to agree.
        return None
    stamp = _stamp(landed.headers.get("location", ""))
    if stamp is None:
        return None
    snapshot = f"{REPLAY}/{stamp}/{url}"
    served = _checked_service(http.head(snapshot, timeout=60, allow_redirects=False))
    if served.status_code != OK:
        return None
    if pdf and not served.headers.get("content-type", "").startswith(PDF_TYPE):
        return None
    return Archived(snapshot=snapshot, timestamp=stamp)


def _item(url: str) -> str | None:
    """The identifier of the Internet Archive item `url` points into, if it is one.

    `archive.org/details/<identifier>` and anything under it: the two SAS West
    citations are two pages of one book, so the identifier is the third segment
    however much path follows it.

    Read out of the parsed URL rather than matched: the host has to be that host
    and not one ending in it, and `details` has to be a whole segment.
    """
    parsed = urlsplit(url)
    if parsed.hostname != ITEM_HOST:
        return None
    segments = parsed.path.strip("/").split("/")
    if len(segments) < 2 or segments[0] != ITEM_PATH:
        return None
    return segments[1] or None


def _added(http: requests.Session, url: str, identifier: str) -> Archived | None:
    """`url` as its own archived copy, dated the day the item was added.

    An item has no capture and so no capture date, but it has the day it
    arrived, which is the same kind of fact: the day this copy started existing
    where the report points. `publicdate` where there is no `addeddate`, which
    is the day it became readable and is the nearest thing left.

    The URL as cited, not the item's front page: `.../page/34/mode/2up` is the
    page the claim is about, and the whole point of citing the archive is
    landing on it.

    `None` where the item says neither, or would not say: that is a build that
    learned nothing rather than a source with no archive, so it is asked again.
    """
    answer = _checked(http.get(f"{METADATA}/{identifier}", timeout=30)).json()
    if not isinstance(answer, dict):
        return None
    metadata = answer.get("metadata")
    if not isinstance(metadata, dict):
        # An identifier nothing holds answers `{}` rather than saying so.
        return None
    for field in ("addeddate", "publicdate"):
        stamp = _fourteen(str(metadata.get(field, "")))
        if stamp is not None:
            return Archived(snapshot=url, timestamp=stamp)
    return None


def _fourteen(said: str) -> str | None:
    """`2023-05-04 00:51:39` as the 14 digits the record is written in.

    Whatever an item writes that is not a date is not one: these are typed by
    hand often enough that a `0000-00-00` is a thing that happens.
    """
    digits = "".join(character for character in said if character.isdigit())
    if len(digits) < 8:
        return None
    try:
        datetime.strptime(digits[:8], "%Y%m%d")
    except ValueError:
        return None
    return (digits + "000000")[:14]


def _stamp(location: str) -> str | None:
    """The 14 digits naming the capture in a replay redirect, if they are there.

    `/web/<stamp>/<url>`, where the stamp may carry a modifier: `id_` asks for
    the capture raw, and the digits in front of it are the same capture.
    """
    segments = urlsplit(location).path.strip("/").split("/")
    if len(segments) < 2 or segments[0] != "web":
        return None
    stamp = segments[1][:14]
    return stamp if len(stamp) == 14 and stamp.isdigit() else None


def _checked_service(response: requests.Response) -> requests.Response:
    """`response`, or `Busy` if the answer was about the service.

    Unlike `_checked`, every other status is handed back rather than raised on:
    a `403` or a `404` from the replay is an answer about the capture, and the
    caller's next move is to ask the index rather than to give up.
    """
    if response.status_code == TOO_MANY or response.status_code >= SERVER_ERROR:
        raise Busy(f"{response.status_code} from {response.url}")
    return response


def _indexed(http: requests.Session, url: str, *, pdf: bool = False) -> Archived | None:
    """The newest capture of `url` that the index says came back `200`.

    `200` and nothing else. A page that has been taken down still gets crawled,
    so its newest captures are of the 404, and a `warc/revisit` row carries no
    status at all because it only says the bytes had not changed since an
    earlier capture. What is wanted is the newest capture that was the page.

    That is the whole of what can be checked here. A capture that answered
    `200` with a login wall, or with a site's own "page not found", is a
    capture of a page that loaded, and nothing in the index tells it from the
    real thing. Except by type: for a `pdf`, only a capture that was one.

    Under `_INDEXING`, which is the limit this whole module is careful about:
    it is held for this question and not for the replay lookup that came first.
    """
    with _INDEXING:
        return _index_answer(http, url, pdf=pdf)


def _index_answer(http: requests.Session, url: str, *, pdf: bool = False) -> Archived | None:
    """What the index said, asked for while holding the gate."""
    response = _checked(
        http.get(
            INDEX,
            params={
                "url": url,
                "output": "json",
                "fl": "timestamp",
                "filter": ["statuscode:200", *([f"mimetype:{PDF_TYPE}"] if pdf else [])],
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
    with _SUBMITTING:
        return _submitted(http, headers, url)


def _submitted(http: requests.Session, headers: dict[str, str], url: str) -> Archived:
    """Ask for the capture and wait for it, while holding the gate."""
    started = _checked(http.post(SAVE, headers=headers, data={"url": url}, timeout=60))
    answer = started.json()
    job = answer.get("job_id")
    if not job:
        refused = _refused(answer)
        if SESSION_LIMIT in refused:
            # Being told the account already has twelve captures going is a
            # fact about the build, not about the page: recorded as a failure
            # it would leave this source with no archive forever.
            raise Busy(refused)
        return Archived(timestamp=today(), error=refused)
    deadline = time.monotonic() + CAPTURE_TIMEOUT.total_seconds()
    while time.monotonic() < deadline:
        time.sleep(POLL_EVERY.total_seconds())
        state = _checked(http.get(f"{SAVE}/status/{job}", headers=headers, timeout=30)).json()
        status = state.get("status")
        if status == "success" and state.get("timestamp"):
            stamp = state["timestamp"]
            return Archived(snapshot=f"https://web.archive.org/web/{stamp}/{url}", timestamp=stamp)
        if status == "error":
            return Archived(timestamp=today(), error=_refused(state))
    return Archived(
        timestamp=today(), error=f"no answer within {CAPTURE_TIMEOUT.total_seconds():.0f} seconds"
    )


SESSION_LIMIT = "session"
"""What the service says when the account already has twelve captures going.

`error:user-session-limit`, which is the one refusal that is about how fast
this build is asking rather than about the page it asked for.
"""


def _refused(answer: dict[str, object]) -> str:
    """What the service said, short enough to publish beside the source."""
    said = answer.get("status_ext") or answer.get("message") or answer.get("status")
    return str(said) if said else "the capture failed without saying why"


PDF_TYPE = "application/pdf"


def pdfs_cited(doc: Document) -> set[str]:
    """The documents `doc` cites as PDFs: by page, or by a `.pdf` path.

    These are the ones whose capture has to be a PDF to be a capture of them.
    `mta.info/document/179396` has no extension and is a PDF all the same,
    which only its `#page=` says.
    """
    return {
        document_url(source)
        for source in doc.sources
        if cited_page(source) is not None or urlsplit(source).path.lower().endswith(".pdf")
    }


COUNT_AT_ONCE = 4
"""How many PDFs are downloaded at once to count their pages.

Fewer than the lookups, because these are whole files rather than `HEAD`s,
and some of what the reports cite runs to hundreds of pages and tens of MB.
"""


def count_pages(doc: Document, session: requests.Session | None = None) -> int:
    """Record how many pages each PDF cited by page has, returning how many were counted.

    Counted from the capture, asked for raw, because that is the file the
    archived link opens and a capture never changes, so one count stands for
    good. A source whose capture failed is counted live, and one nothing has
    tried to capture yet is left until something has, since its entry is what
    the count is recorded on.

    A capture that turns out not to be a PDF is dropped from the record, so
    that the next lookup finds one that is. Every capture recorded before
    lookups checked the type was accepted on its status alone, and that is how
    `TCP_Final_Report.pdf` came to be archived as a bot check.

    A download that failed is left uncounted rather than recorded: it is not a
    fact about the document.
    """
    wanted = [
        url
        for url in dict.fromkeys(
            document_url(source) for source in doc.sources if cited_page(source) is not None
        )
        if url in doc.archives and not doc.archives[url].pages
    ]
    if not wanted:
        return 0
    http = session or _session()

    def count(url: str) -> int | None:
        archived = doc.archives[url]
        if archived.snapshot and not archived.error:
            return _pages(http, wayback_url(archived.timestamp, url, modifier=UNREWRITTEN))
        return _pages(http, url)

    with ThreadPoolExecutor(max_workers=COUNT_AT_ONCE) as pool:
        counted = list(pool.map(count, wanted))
    for url, pages in zip(wanted, counted, strict=True):
        if pages:
            doc.archives[url] = replace(doc.archives[url], pages=pages)
        elif pages == 0 and doc.archives[url].snapshot:
            del doc.archives[url]
    return sum(1 for pages in counted if pages)


PDF_MAGIC = b"%PDF"
"""What every PDF starts with, and what a login wall or an error page does not."""


def _pages(http: requests.Session, url: str) -> int | None:
    """The pages of the PDF at `url`: 0 if it is not one, `None` if it could not be fetched."""
    try:
        response = _patiently(lambda: _checked(http.get(url, timeout=120)))
    except requests.RequestException, Busy:
        return None
    if not response.content.startswith(PDF_MAGIC):
        return 0
    try:
        return len(PdfReader(BytesIO(response.content)).pages)
    except PyPdfError:
        return 0
