"""What makes a set of reports a site: the list, the paths, and the index.

The per-document build lives in `build.py`.
Here is what only exists once there is more than one report.

Each report lands under its own published path,
taken from the `URL:` line in its front matter,
so the preview URL is the published URL with a different host in front of it.
A report whose header names no URL is not published at all,
since a slug of its headline would be a plausible path and not the published one.
Nor is one with no `Header` section for a URL to be named in.

That is one report failing, not the site:
the others are still built and the exit status still reports it.
"""

import json
import sys
import tomllib
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import htpy
from markupsafe import Markup

from .assets import read
from .build import DOC_JSON, BuildOptions, build_one
from .emit.html import Piece, lines, markup, tag
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

    `None` is a document named on the command line, which states no expectation.
    An entry always states one, `""` included:
    a field left empty says the document is called nothing, which no document is."""

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
        # whatever it says, and one that says nothing says the document is
        # named nothing, which is a disagreement like any other.
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
    they are required to be right, and a person copying two titles out of
    Drive by hand is the step that gets them wrong.

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
            # Writing an empty one down is what `load_reports` refuses.
            raise ValueError(f"{url}: the document says no `{field_name}`")

    path.write_text(path.read_text().rstrip("\n") + "\n" + entry_text(url, name, tab))
    return Report(url=url, name=name, tab=tab)


def saved_responses(outdir: Path) -> dict[tuple[str, str], Path]:
    """Every response a previous build wrote under `outdir`, by document and tab.

    A report's directory is named after its own `URL:` line, which is a path
    and not an id, so nothing about `reports.toml` says where a given entry's
    last response was written. Reading the responses is what joins the two,
    which is why each records the `documentId` and `tabId` it came from.

    Scanned once for a whole build rather than per report:
    a site is a directory of them, and each answer is the same walk.
    """
    found: dict[tuple[str, str], Path] = {}
    for saved in sorted(outdir.glob(f"*/*/{DOC_JSON}")) + sorted(outdir.glob(f"*/{DOC_JSON}")):
        try:
            document = json.loads(saved.read_text())
        except OSError, ValueError:
            # Not a saved response, whatever else it is.
            continue
        key = (str(document.get("documentId", "")), str(document.get("tabId", "")))
        if all(key):
            found.setdefault(key, saved.parent)
    return found


def saved_for(report: Report, saved: dict[tuple[str, str], Path]) -> Path | None:
    """Where the last build of `report` wrote its response, if it is still there."""
    from .fetch import parse_ref

    doc_id, tab = parse_ref(report.url)
    return saved.get((doc_id, tab or ""))


def report_path(doc: Document) -> str:
    """Where this report goes on the site, from its own front matter.

    The leading slash is dropped because the site is a directory tree,
    and a report published at the root of a domain
    would otherwise write to the root of the filesystem.

    A path that climbs is refused for the same reason and a stronger one:
    `URL: /../../etc` is a document choosing a directory outside the site,
    and the check that the committed site is what a build writes
    only ever looks inside `site/`, so it would not notice.

    A document that names no URL at all is refused rather than guessed at,
    since a slug of the headline is a plausible path and not the published one.
    That is two refusals rather than one, because it is two mistakes:
    a `Header` section with no `URL:` line in it,
    and no `Header` section at all, which is what a document has
    when its `Header` line is styled as body text rather than as a heading.
    Naming the one that happened is the difference between
    a line to go and add and a line to go and restyle.

    All three refusals are this one report's, not the site's:
    `build_site` goes on to the next.
    """
    slug = doc.slug.strip("/")
    if not slug and not doc.has_header:
        raise ValueError(
            "no `Header` section, so nothing says where this publishes; "
            "add one, styling its heading as a heading rather than as body text"
        )
    if not slug:
        raise ValueError(
            "no `URL:` line in the `Header` section, so nothing says where this publishes; "
            "add one, as the other reports have"
        )
    if ".." in PurePosixPath(slug).parts or PurePosixPath(slug).is_absolute():
        raise ValueError(f"the `URL:` line is `{doc.slug}`, which climbs out of the site")
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


def source(report: Report, previous: Path | None, options: BuildOptions) -> str:
    """What to build this report from: the document, or the last response saved for it.

    A report with no saved response cannot be built offline,
    and neither can one saved with its suggestions resolved the other way.
    Saying so is better than fetching one document
    in a run that was asked not to fetch anything.
    """
    if not options.offline:
        return report.url
    if previous is None:
        raise ValueError(
            f"nothing saved under the output directory for {report.url}; "
            "build it once with a fetch before building it offline"
        )
    # A fetch would notice this and go and get the other one.
    # Offline cannot, so it says so rather than publishing the document
    # read the way the last build happened to read it.
    saved_as = str(json.loads((previous / DOC_JSON).read_text()).get("suggestions", ""))
    if saved_as != options.suggestions:
        raise ValueError(
            f"what is saved for {report.url} has its suggestions {saved_as or 'unrecorded'}, "
            f"and this build wants them {options.suggestions}; "
            "reading the document the other way needs a fetch"
        )
    return str(previous)


MAX_AT_ONCE = 8
"""How many reports to build at once.

A build is almost entirely waiting on Google, so these overlap well.
A ceiling rather than one thread a report, because the calls are rate limited
at the other end and thirty asking at once is a way to be told to wait.
"""


def build_site(reports: list[Report], outdir: Path, options: BuildOptions | None = None) -> Site:
    """Build every report, keeping going when one of them cannot be built.

    A document that cannot be fetched says nothing about the next one,
    and a site missing one report beats no site at all.

    Several at a time, because nearly all of a build is waiting for a reply.
    Each carries its own HTTP client the whole way down, which is not tidiness
    but a requirement: the client under the Google libraries is `httplib2`,
    and one shared across threads takes the interpreter down in the allocator
    rather than raising anything.

    Reported in the order the list gives rather than the order they finish,
    which also means the first one's warnings are printed
    while the rest are still running.
    """
    options = options or BuildOptions()
    # Always, not only offline: a fetch reuses one too, when Drive says
    # the document behind it has not been edited since it was written.
    saved = saved_responses(outdir)
    site = Site()

    def build(report: Report) -> tuple[Document, str]:
        previous = saved_for(report, saved)
        return build_one(
            source(report, previous, options),
            outdir,
            options,
            verify=verifier(report),
            cached=previous / DOC_JSON if previous is not None else None,
        )

    with ThreadPoolExecutor(max_workers=max(1, min(len(reports), MAX_AT_ONCE))) as pool:
        started = [(report, pool.submit(build, report)) for report in reports]
        for report, building in started:
            label = report.name or report.url
            try:
                doc, path = building.result()
            except Exception as e:
                # Broad on purpose: a fetch, parse, disagreement, or disk failure
                # is the same decision here,
                # which is to keep going and say which report did not make it.
                print(f"failed: {label}: {e}", file=sys.stderr)
                site.failed.append(Failed(report=report, error=str(e)))
                continue
            print(f"built {label}", file=sys.stderr)
            for warning in doc.warnings:
                print(f"  warning: {warning}", file=sys.stderr)
            site.built.append(Built(report=report, doc=doc, path=path))
    return site


def disagreements(report: Report, doc: Document) -> list[str]:
    """Where `reports.toml` and the document it points at do not match.

    Only checkable here, after the fetch:
    nothing in `reports.toml` says what the document is called
    or which of its tabs a `?tab=` id picks out.

    Every expectation is compared, and nothing about a value exempts it:
    an unanswered question is not a passed check,
    and a blank is not a shorter entry.
    Only a document named straight on the command line is skipped,
    which is not an entry and holds no expectation to compare.

    Not warnings: the document is fine and this file is wrong about it,
    which is nothing for the writers to fix
    and not something to publish past either.
    """
    checks = (
        ("calls this", report.name, "the document is named", doc.file_title),
        ("expects the tab", report.tab, "the tab is named", doc.tab_title),
    )
    return [
        f"reports.toml {said} `{expected}`, but {found_label} `{found}`"
        for said, expected, found_label, found in checks
        if expected is not None and expected != found
    ]


INDEX_CSS = read("index.css")


def index_page(site: Site) -> str:
    """The site's front page: every report, and anything that did not build.

    Failures are on the page, not only in the log, because the page is what people read.
    A report quietly missing from a list of four is hard to notice;
    a line saying which one failed and why is not.
    """
    entries: list[Piece] = []
    for built in site.built:
        doc = built.doc
        meta = [m for m in (doc.dateline, ", ".join(doc.contributors)) if m]
        warned = f" · {len(doc.warnings)} warning(s)" if doc.warnings else ""
        entries.append(
            tag.li[
                tag.a(href=f"{built.path}/")[tag.strong[doc.title]],
                tag.div(class_="short")[doc.meta.get("short", "")],
                tag.div(class_="meta")[" · ".join(meta), warned],
            ]
        )
    failures = [
        tag.p(class_="failed")[f"{f.report.name or f.report.url}: {f.error}"] for f in site.failed
    ]
    page: list[Piece] = [
        htpy.meta(charset="utf-8"),
        htpy.meta(name="viewport", content="width=device-width, initial-scale=1"),
        tag.title["ETA report previews"],
        tag.style[Markup(f"\n{INDEX_CSS}")],
        tag.h1["ETA report previews"],
        tag.p["Built from the Google Docs, warnings included. Not the published pages."],
        tag.ul["\n", lines(entries), "\n"],
        *failures,
    ]
    return markup([Markup("<!doctype html>"), "\n", lines(page), "\n"])
