"""What makes a set of reports a site: the list, the paths, and the index.

The per-document build lives in `build.py`.
Here is what only exists once there is more than one report,
which is the case the project is in:
ETA has published several and will publish more,
so nothing may be written in terms of *the* doc.

Each report lands under its own published path,
taken from the `URL:` line in its front matter,
so the preview URL is the published URL with a different host in front of it.
A report whose header names no URL is not published at all.
A slug of its headline would be a plausible path and not the published one,
which is a report at the wrong URL rather than a report nobody forgot.

That is one report failing, not the site:
a document that cannot be built says nothing about the next one,
so the others are still built and the exit status still reports it.
"""

import json
import sys
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .build import BuildOptions, build_one
from .emit.html import escape
from .nodes import Document

REPORTS = Path("reports.toml")
"""Which documents the site is built from, committed beside the code."""


@dataclass(frozen=True)
class Report:
    """One entry of `reports.toml`."""

    url: str
    """A Docs URL including its `?tab=` id, or a path to saved JSON."""

    name: str | None = None
    """What the document is called in Drive, which is what a build checks it against.

    Not where the report goes: that is the document's own to say.
    An entry pointing at the wrong document fails
    rather than publishing it under the heading of the one somebody meant.

    `None` is a document named on the command line, which states no expectation.
    An entry always states one, `""` included:
    a field left empty says the document is called nothing, which no document is,
    so a blank needs no rule of its own to be caught."""

    tab: str | None = None
    """What the tab in `url` is called, checked the same way.

    The `?tab=` id is opaque, so nothing about the URL says which draft it points at,
    and publishing last year's draft is the mistake nothing else can catch.

    `None` on the same terms as `name`."""


@dataclass
class Built:
    """A report that made it, and where it went."""

    report: Report
    doc: Document
    path: str
    """Site-relative directory, e.g. `reports/digging-out-deep-hole-sas-west`."""


@dataclass
class Failed:
    report: Report
    error: str


@dataclass
class Site:
    built: list[Built] = field(default_factory=list)
    failed: list[Failed] = field(default_factory=list)


def load_reports(path: Path = REPORTS) -> list[Report]:
    """Read the report list, which is TOML so it can carry comments.

    Comments matter here: a list of documents is where someone needs to say
    "this one is the 2025 rewrite, not the original".
    """
    data = tomllib.loads(path.read_text())
    entries = data.get("report", [])
    reports = []
    for entry in entries:
        url = str(entry.get("url", "")).strip()
        if not url:
            raise ValueError(f"{path}: a [[report]] entry has no `url`")
        # A string either way, never `None`: an entry states an expectation
        # whatever it says, and one that says nothing says the document is named
        # nothing, which is a disagreement like any other and needs no rule of its own.
        # `eta-publish add` is what fills these in without anyone typing them.
        reports.append(
            Report(
                url=url,
                name=str(entry.get("name", "")).strip(),
                tab=str(entry.get("tab", "")).strip(),
            )
        )
    if not reports:
        raise ValueError(f"{path}: no [[report]] entries")
    return reports


def entry_text(url: str, name: str, tab: str) -> str:
    """One `[[report]]` block, as `reports.toml` writes them.

    Built as text rather than dumped from a table
    because the file is mostly comments:
    "this one is the 2025 rewrite, not the original" is the reason it is TOML
    at all, and a round trip through `tomllib` would drop every line of it.

    The values go through `json.dumps`, which is a TOML basic string
    for anything a Drive title can hold: the same quoting, the same escapes.
    A title with a quotation mark in it is a title, not a syntax error.
    """
    return (
        "\n[[report]]\n"
        f"name = {json.dumps(name)}\n"
        f"tab = {json.dumps(tab)}\n"
        f"url = {json.dumps(url)}\n"
    )


def add_report(url: str, path: Path = REPORTS) -> Report:
    """Append the document at `url` to the report list, named as it names itself.

    `name` and `tab` are the document's own `title` and `tabTitle`,
    which is the only reason this command exists:
    they are required and required to be right,
    and a person copying two titles out of Drive by hand
    is the step that gets them wrong.
    Fetched rather than guessed from the URL,
    which carries an opaque `?tab=` id and nothing else.

    An entry whose `url` is already listed is refused rather than duplicated:
    two entries for one document publish it twice to the same path,
    and the second build silently overwrites the first.
    """
    from .build import load

    if any(report.url == url for report in load_reports(path)):
        raise ValueError(f"{path}: already lists {url}")

    document = load(url)
    name = str(document.get("title", ""))
    tab = str(document.get("tabTitle", ""))
    for field_name, value in (("name", name), ("tab", tab)):
        if not value:
            # Nothing to write down, and writing an empty one down is what
            # `load_reports` refuses. Better to say the document has no answer.
            raise ValueError(f"{url}: the document says no `{field_name}`")

    path.write_text(path.read_text().rstrip("\n") + "\n" + entry_text(url, name, tab))
    return Report(url=url, name=name, tab=tab)


def reports_from(ref: str) -> list[Report]:
    """What one command line argument means: a document, or a list of them.

    A URL is always a document.
    Only a local path can be a list, and only when named like one:
    `reports.toml` is TOML, a saved Docs response is `.json`,
    and a document reference is a URL or a bare id.
    Nothing is opened to tell them apart,
    so a typo in a filename is a missing file
    rather than a confident wrong answer about what it was.
    """
    if ref.startswith(("http://", "https://")):
        return [Report(url=ref)]
    if Path(ref).suffix == ".toml":
        return load_reports(Path(ref))
    return [Report(url=ref)]


def report_path(doc: Document) -> str:
    """Where this report goes on the site, from its own front matter.

    The leading slash is dropped because the site is a directory tree,
    and a report published at the root of a domain
    would otherwise write to the root of the filesystem.

    A path that climbs is refused for the same reason and a stronger one.
    The build writes wherever this says,
    so `URL: /../../etc` is a document choosing a directory outside the site,
    and the check that the committed site is what a build writes
    only ever looks inside `site/`, so it would not notice.

    A document that names no URL at all is refused rather than guessed at.
    A slug of the headline is a plausible path and not the published one,
    and the difference only shows up as a report sitting at the wrong URL,
    quietly, next to the ones that got theirs right.
    Both refusals are this one report's, not the site's:
    `build_site` goes on to the next.
    """
    slug = doc.slug.strip("/")
    if not slug:
        raise ValueError(
            "no `URL:` line in the `Header` section, so nothing says where this publishes; "
            "add one, as the other reports have"
        )
    if ".." in PurePosixPath(slug).parts or PurePosixPath(slug).is_absolute():
        raise ValueError(f"the `URL:` line is {doc.slug!r}, which climbs out of the site")
    return slug


def verifier(report: Report) -> Callable[[Document], None]:
    """What `build_one` calls once the document is parsed and before it is written.

    A disagreement is found after the fetch and has to stop the build before the emit,
    or a report that failed its own check leaves a directory of published files behind,
    which the next run compares against and finds nothing wrong with.

    A callback rather than the `Report` itself,
    because which entry a document was supposed to be
    is a question about `reports.toml` and not about building a document.
    """

    def verify(doc: Document) -> None:
        said = disagreements(report, doc)
        if said:
            raise ValueError("; ".join(said))

    return verify


def build_site(reports: list[Report], outdir: Path, options: BuildOptions | None = None) -> Site:
    """Build every report, keeping going when one of them cannot be built.

    A document that cannot be fetched says nothing about the next one,
    and a site missing one report beats no site at all.
    """
    site = Site()
    for report in reports:
        label = report.name or report.url
        print(f"building {label}", file=sys.stderr)
        try:
            doc, path = build_one(report.url, outdir, options, verify=verifier(report))
        except Exception as e:  # noqa: BLE001
            # Broad on purpose: a fetch, parse, disagreement, or disk failure
            # is the same decision here,
            # which is to keep going and say which report did not make it.
            print(f"failed: {label}: {e}", file=sys.stderr)
            site.failed.append(Failed(report=report, error=str(e)))
            continue
        for warning in doc.warnings:
            print(f"  warning: {warning}", file=sys.stderr)
        site.built.append(Built(report=report, doc=doc, path=path))
    return site


def disagreements(report: Report, doc: Document) -> list[str]:
    """Where `reports.toml` and the document it points at do not match.

    Only checkable here, after the fetch.
    Nothing in `reports.toml` says what the document is called
    or which of its tabs a `?tab=` id picks out,
    which is the whole reason the two can drift apart.

    Every expectation is compared, and nothing about a value exempts it.
    An entry with a blank `tab` disagrees with a document that has one,
    and an entry with a `tab` disagrees with a response that has none,
    for the same reason and by the same line of code:
    an unanswered question is not a passed check,
    and a blank is not a shorter entry.

    Only a document named straight on the command line is skipped,
    which is not an entry and holds no expectation to compare.

    Not `doc.warnings`, and not warnings at all.
    The document is fine and this file is wrong about it,
    which is nothing for the writers to fix
    and not something to publish past either:
    an entry pointing at the wrong document publishes that document
    under the heading of the one somebody meant.
    """
    checks = (
        ("calls this", report.name, "the document is named", doc.file_title),
        ("expects the tab", report.tab, "the tab is named", doc.tab_title),
    )
    return [
        f"reports.toml {said} {expected!r}, but {found_label} {found!r}"
        for said, expected, found_label, found in checks
        if expected is not None and expected != found
    ]


INDEX_CSS = """
:root { color-scheme: light dark; --fg: #1a1a1a; --bg: #fff; }
@media (prefers-color-scheme: dark) { :root { --fg: #eaeaea; --bg: #141414; } }
body { background: var(--bg); color: var(--fg); max-width: 46rem;
       margin: 0 auto; padding: 3rem 1.25rem 6rem;
       font: 17px/1.6 system-ui, sans-serif; }
h1 { font-size: 1.6rem; }
ul { list-style: none; padding: 0; }
li { margin: 2em 0; }
a { color: inherit; }
.short { opacity: .75; font-size: .95rem; }
.meta { opacity: .6; font-size: .85rem; }
.failed { border-left: 3px solid #c60; padding: .4em 1em; font-size: .9rem; }
"""


def index_page(site: Site) -> str:
    """The site's front page: every report, and anything that did not build.

    Failures are on the page, not only in the log, because the page is what people read.
    A report quietly missing from a list of four is hard to notice;
    a line saying which one failed and why is not.
    """
    items = []
    for built in site.built:
        doc = built.doc
        meta = [m for m in (doc.dateline, ", ".join(doc.contributors)) if m]
        warned = f" · {len(doc.warnings)} warning(s)" if doc.warnings else ""
        items.append(
            f'<li><a href="{escape(built.path)}/"><strong>{escape(doc.title)}</strong></a>'
            f'<div class="short">{escape(doc.meta.get("short", ""))}</div>'
            f'<div class="meta">{escape(" · ".join(meta))}{warned}</div></li>'
        )
    failures = "".join(
        f'<p class="failed">{escape(f.report.name or f.report.url)}: {escape(f.error)}</p>'
        for f in site.failed
    )
    return (
        "<!doctype html>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>ETA report previews</title>\n"
        f"<style>{INDEX_CSS}</style>\n"
        "<h1>ETA report previews</h1>\n"
        "<p>Built from the Google Docs, warnings included. "
        "Not the published pages.</p>\n"
        f"<ul>\n{''.join(items)}\n</ul>\n"
        f"{failures}"
    )
