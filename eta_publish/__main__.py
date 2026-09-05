"""`eta-publish`: Google Docs in, a publishable site out.

One document or the whole list of them, the same way.
The single argument is either a document
(a Docs URL, an id, or a saved response)
or a `.toml` list of them, defaulting to `reports.toml`.
Each report lands under the path its own front matter gives it,
with an index listing them.

Both defaults name the committed thing,
so `eta-publish` with no arguments rebuilds the site as it ships.

`eta-publish add <url>` writes the next entry of that list,
reading the two names it has to carry off the document itself.

One argument rather than many:
building several documents at once is what a list is for,
and a list is a file that can be committed, reviewed, and commented
rather than a shell line that is right once.

There is no separate single-document mode.
A publish of one report is a publish of a list with one entry,
which keeps the common case and the real case on the same code.
"""

import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from typer import Argument, BadParameter, Exit, Option, Typer

from .build import BuildOptions
from .site import REPORTS, add_report, build_site, index_page, reports_from


class Suggestions(StrEnum):
    """How to resolve the document's open suggestions.

    An enum, so `--suggestions` cannot be handed a mode the API does not have.
    """

    REJECTED = "rejected"
    ACCEPTED = "accepted"


app = Typer(context_settings={"help_option_names": ["-h", "--help"]})


@app.command(help=__doc__)
def publish(
    doc: Annotated[
        str,
        Argument(
            metavar="DOC",
            help="a Google Doc URL (including its `?tab=` id), an id, saved "
            "Docs API JSON, or a `.toml` list of reports",
        ),
    ] = "reports.toml",
    outdir: Annotated[
        Path,
        Option("-o", "--outdir", help="where the site is written; `site/` is published"),
    ] = Path("site"),
    suggestions: Annotated[
        Suggestions,
        Option(help="how to resolve open suggestions; rejected is what the doc says now"),
    ] = Suggestions.REJECTED,
    split: Annotated[
        bool,
        Option(help="write the HTML as numbered pieces cut at h2, for oversized reports"),
    ] = False,
    images: Annotated[
        bool, Option(help="download the images; the output references them either way")
    ] = True,
) -> None:
    try:
        reports = reports_from(doc)
    except (OSError, ValueError) as e:
        # Typer's own wording for a bad argument, because that is what it is.
        raise BadParameter(str(e), param_hint="DOC") from e

    site = build_site(
        reports,
        outdir,
        BuildOptions(suggestions=str(suggestions), split=split, images=images),
    )

    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "index.html").write_text(index_page(site))

    for built in site.built:
        print(f"  {built.path}  {built.doc.title}")
    for failure in site.failed:
        print(f"  failed: {failure.report.name or failure.report.url}", file=sys.stderr)
    # Non-zero when anything failed, even though the rest of the site was written,
    # so an unattended run cannot fail quietly.
    if site.failed:
        raise Exit(code=1)


add_app = Typer(context_settings={"help_option_names": ["-h", "--help"]})


@add_app.command()
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

    `name` and `tab` are required and required to be right,
    and copying two titles out of Drive by hand is the step that gets them wrong,
    so they are read off the document rather than typed.
    """
    try:
        added = add_report(url, reports)
    except (OSError, ValueError) as e:
        raise BadParameter(str(e), param_hint="URL") from e
    print(f"{reports}: added {added.name!r}, tab {added.tab!r}")


def main() -> None:
    """`add` is the one subcommand; anything else is a publish.

    Not two commands on one Typer app,
    which would make every publish say `publish` first:
    `eta-publish <url>` is what the README documents
    and `eta-publish` alone is what the workflow runs,
    and neither is worth breaking to give `add` a tidier home.
    """
    if sys.argv[1:2] == ["add"]:
        add_app(sys.argv[2:], prog_name="eta-publish add")
        return
    app()


if __name__ == "__main__":
    main()
