"""`eta-publish`: Google Docs in, a publishable site out.

Three commands, because there are three things to do:

    eta-publish all             every report in `reports.toml`, into `site/`
    eta-publish one <doc>       one document, wherever you point it
    eta-publish add <url>       write that document's entry into the list

`all` is what the workflow runs and what the committed site is built from.
`one` is for a document before it is on the list,
and takes a Docs URL, a bare id, or a saved Docs response.

Both build the same way and write the same index,
so the common case and the real case stay on the same code.
Each report lands under the path its own front matter gives it.
"""

import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from typer import Argument, BadParameter, Exit, Option, Typer

from . import console, format
from .build import BuildOptions, check_code_block_size
from .site import REPORTS, Report, Site, add_report, build_site, index_page, load_reports


class Suggestions(StrEnum):
    """How to resolve the document's open suggestions.

    An enum, so `--suggestions` cannot be handed a mode the API does not have.
    """

    REJECTED = "rejected"
    ACCEPTED = "accepted"


app = Typer(context_settings={"help_option_names": ["-h", "--help"]}, help=__doc__)

Outdir = Annotated[
    Path,
    Option("-o", "--outdir", help="where the site is written; `site/` is published"),
]
Suggested = Annotated[
    Suggestions,
    Option("--suggestions", help="how to resolve open suggestions; rejected is what the doc says"),
]
Split = Annotated[
    bool,
    Option(help="write the HTML as numbered pieces cut at h2, for oversized reports"),
]
Images = Annotated[
    bool,
    Option(help="download the images; the output references them either way"),
]
Offline = Annotated[
    bool,
    Option(help="rebuild from the responses saved by the last build; no network"),
]
Comments = Annotated[
    bool,
    Option(help="ask how many comment threads are open; the slowest thing a build does"),
]
"""The options `all` and `one` share, spelled once,
so two commands that build the same way offer the same switches."""


@app.command(name="all")
def build_all(
    reports: Annotated[
        Path,
        Argument(metavar="LIST", help="a `.toml` list of reports"),
    ] = REPORTS,
    outdir: Outdir = Path("site"),
    suggestions: Suggested = Suggestions.REJECTED,
    split: Split = False,
    images: Images = True,
    comments: Comments = True,
    offline: Offline = False,
) -> None:
    """Build every report in a list, into a site with an index.

    Both defaults name the committed thing,
    so `eta-publish all` with no arguments rebuilds the site as it ships.
    """
    try:
        listed = load_reports(reports)
    except (OSError, ValueError) as e:
        # Typer's own wording for a bad argument, because that is what it is.
        raise BadParameter(str(e), param_hint="LIST") from e
    publish(listed, outdir, suggestions, split, images, comments, offline)


@app.command(name="one")
def build_one_report(
    doc: Annotated[
        str,
        Argument(
            metavar="DOC",
            help="a Google Doc URL (including its `?tab=` id), an id, or saved Docs API JSON",
        ),
    ],
    outdir: Outdir = Path("site"),
    suggestions: Suggested = Suggestions.REJECTED,
    split: Split = False,
    images: Images = True,
    comments: Comments = True,
) -> None:
    """Build one document, before it is on the list or instead of it.

    The report has no entry, so there is nothing saying what it should be called
    and nothing to hold it up against: what the document says, it publishes as.
    """
    publish([Report(url=doc)], outdir, suggestions, split, images, comments)


def publish(
    reports: list[Report],
    outdir: Path,
    suggestions: Suggestions,
    split: bool,
    images: bool,
    comments: bool,
    offline: bool = False,
) -> None:
    """Build these reports and write the index over them.

    One document and a whole list end here alike.
    A publish of one report is a publish of a list with one entry,
    down to the index page, which is the page that says what failed.
    """
    site = build_site(
        reports,
        outdir,
        BuildOptions(
            suggestions=str(suggestions),
            split=split,
            images=images,
            comments=comments,
            offline=offline,
        ),
    )

    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "index.html").write_text(index_page(site))

    # Once, over everything just written, rather than per file as it was
    # written: `biome` costs far more to start than to run.
    format.tree(outdir)

    # After the formatting, which is what decides how big the file to paste is.
    for built in site.built:
        report = outdir / built.path / "report.html"
        if report.exists():
            check_code_block_size(built.doc, report)

    report_outcome(site)


def report_outcome(site: Site) -> None:
    """Where the site was written, and one line saying how the build went.

    The paths on stdout, because they are the answer to what was just built
    and the thing somebody pipes somewhere.
    Each failure has already been said, with the reason, as it happened:
    repeating the names here without their reasons would only be the same
    list read a second time, so this counts them instead.
    """
    console.write(
        console.paths([(built.path, built.doc.title) for built in site.built]),
        console.for_stream(sys.stdout),
    )
    console.write(
        console.summary(
            len(site.built),
            len(site.failed),
            sum(len(built.doc.warnings) for built in site.built),
        ),
        console.for_stream(),
    )
    # Non-zero when anything failed, even though the rest of the site was written,
    # so an unattended run cannot fail quietly.
    if site.failed:
        raise Exit(code=1)


@app.command()
def add(
    url: Annotated[
        str,
        Argument(metavar="URL", help="a Google Doc URL, including the `?tab=` id to publish"),
    ],
    reports: Annotated[
        Path,
        Option("-r", "--reports", help="the list to append to"),
    ] = REPORTS,
) -> None:
    """Append a document to `reports.toml`, named as the document names itself.

    `name` and `tab` have to be right, and copying two titles out of Drive by hand
    is the step that gets them wrong, so they are read off the document rather than typed.
    """
    try:
        added = add_report(url, reports)
    except (OSError, ValueError, LookupError, RuntimeError) as e:
        # `LookupError` and `RuntimeError` are `TabNotFound` and `FetchFailed`,
        # which only this command can raise: a fetch that fails inside
        # `build_site` is one report's failure there.
        # `TabNotFound` carries the list of tabs to pick from, which is the
        # answer to a URL pasted without its `?tab=` id.
        raise BadParameter(str(e), param_hint="URL") from e
    out = console.for_stream(sys.stdout)
    console.write(console.added(reports, added.name or "", added.tab or "", out), out)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
