"""What makes a set of reports a site: the list, the paths, and the index.

The per-document build lives in `build.py`. What is here is everything that
only exists once there is more than one report, which is the case the
project is actually in: ETA has published several and will publish more, so
nothing may be written in terms of *the* doc.

Each report lands under its own published path, taken from the `URL:` line
in its front matter, so a preview of
`/reports/digging-out-deep-hole-sas-west` sits at that path on the site too
and the preview URL is the published URL with a different host in front of
it. A report whose header names no URL falls back to a slug of its title,
with a warning: that is a missing front matter line to fix in the document,
not a reason to fail the build for the reports either side of it.

One failing report does not stop the others, for the same reason. A fetch
can fail for reasons that have nothing to do with the other documents, and
a site missing one report beats no site at all. The exit status still
reports it.
"""

import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .build import BuildOptions, build_one
from .emit.html import escape
from .naming import slugify
from .nodes import Document

REPORTS = Path("reports.toml")
"""Which documents the site is built from, committed beside the code.

A list in the repository rather than a workflow input: what the site
publishes is a fact about the project, it belongs in review and in history,
and adding the next report should be a pull request rather than something
typed into a form and forgotten.
"""


@dataclass(frozen=True)
class Report:
    """One entry of `reports.toml`."""

    url: str
    """A Docs URL including its `?tab=` id, or a path to saved JSON."""

    name: str = ""
    """Only for messages; the site path comes from the document itself."""


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

    Comments matter here: a list of documents is exactly the place someone
    needs to say "this one is the 2025 rewrite, not the original".
    """
    data = tomllib.loads(path.read_text())
    entries = data.get("report", [])
    reports = []
    for entry in entries:
        url = str(entry.get("url", "")).strip()
        if not url:
            raise ValueError(f"{path}: a [[report]] entry has no `url`")
        reports.append(Report(url=url, name=str(entry.get("name", "")).strip()))
    if not reports:
        raise ValueError(f"{path}: no [[report]] entries")
    return reports


def report_path(doc: Document) -> str:
    """Where this report goes on the site, from its own front matter.

    The leading slash is dropped because the site is a directory tree, and
    a report published at the root of a domain would otherwise write to the
    root of the filesystem.
    """
    slug = doc.slug.strip("/")
    if slug:
        return slug
    fallback = slugify(doc.title) if doc.title else "report"
    doc.warn(
        f"no `URL:` in the header, so this is published at /{fallback}, "
        "which is a guess; add the line to the document"
    )
    return fallback


def build_site(reports: list[Report], outdir: Path, options: BuildOptions | None = None) -> Site:
    """Build every report, keeping going when one of them cannot be built.

    Failing late rather than at the first error is the only behavior that
    makes sense for a list: a document that cannot be fetched says nothing
    about the next one, and a site missing one report beats no site at all.
    With a single report it costs nothing, since there is nothing after it
    to salvage.
    """
    site = Site()
    for report in reports:
        label = report.name or report.url
        print(f"building {label}", file=sys.stderr)
        try:
            doc, path = build_one(report.url, outdir, options)
        except Exception as e:  # noqa: BLE001
            # Deliberately broad: a fetch failure, a parse failure, and a
            # disk failure are all the same decision here, which is to keep
            # going and say which report did not make it.
            print(f"failed: {label}: {e}", file=sys.stderr)
            site.failed.append(Failed(report=report, error=str(e)))
            continue
        for warning in doc.warnings:
            print(f"  warning: {warning}", file=sys.stderr)
        site.built.append(Built(report=report, doc=doc, path=path))
    return site


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

    Failures are on the page rather than only in the log because the page is
    what someone looks at. A report quietly missing from a list of four is
    hard to notice; a line saying which one failed and why is not.
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
