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
from datetime import UTC, datetime
from pathlib import Path

from .nodes import Archived, Document

ARCHIVES_JSON = "archives.json"


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
    for url in doc.sources:
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
    """The sources nothing has tried to capture yet, in document order.

    A source recorded with an `error` is not among them: that one has been
    tried, and a build that submitted it again on every run would spend the
    rate limit on the pages least likely to ever answer.
    """
    return [url for url in doc.sources if url not in doc.archives]


def today() -> str:
    """The date an attempt was made, for an entry that records a failure."""
    return datetime.now(UTC).strftime("%Y%m%d")
