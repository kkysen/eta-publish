"""`eta-publish`: Google Docs in, a publishable site out.

One document or the whole list of them, the same way.
The single argument is either a document
(a Docs URL, an id, or a saved response)
or a `.toml` list of them, defaulting to `reports.toml`.
Each report lands under the path its own front matter gives it,
with an index listing them.

Both defaults name the committed thing,
so `eta-publish` with no arguments rebuilds the site as it ships.

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

# `Option` and `Argument` stay qualified:
# both are ordinary words a document tool can expect to want for its own things.
# The rest are distinctive enough to import.
import typer
from typer import BadParameter, Exit, Typer

from .build import BuildOptions
from .site import build_site, index_page, reports_from


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
        typer.Argument(
            metavar="DOC",
            help="a Google Doc URL (including its `?tab=` id), an id, saved "
            "Docs API JSON, or a `.toml` list of reports",
        ),
    ] = "reports.toml",
    outdir: Annotated[
        Path,
        typer.Option("-o", "--outdir", help="where the site is written; `site/` is published"),
    ] = Path("site"),
    suggestions: Annotated[
        Suggestions,
        typer.Option(help="how to resolve open suggestions; rejected is what the doc says now"),
    ] = Suggestions.REJECTED,
    split: Annotated[
        bool,
        typer.Option(help="write the HTML as numbered pieces cut at h2, for oversized reports"),
    ] = False,
    images: Annotated[
        bool, typer.Option(help="download the images; the output references them either way")
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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
