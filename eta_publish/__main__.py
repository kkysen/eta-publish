"""`eta-publish`: Google Docs in, a publishable site out.

One document or the whole list of them, the same way. The single argument
is either a document (a Docs URL, an id, or a saved response) or a `.toml`
list of them, and it defaults to `reports.toml`. Each report lands under
the path its own front matter gives it, with an index listing them.

One argument rather than many: building several documents at once is what
a list is for, and a list is a file that can be committed, reviewed, and
commented rather than a shell line that is right once.

There is no separate single-document mode. A publish of one report is a
publish of a list with one entry in it, and keeping that true means the
common case and the real case run the same code.
"""

import argparse
import sys
from pathlib import Path

from .build import BuildOptions
from .site import build_site, index_page, reports_from


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="eta-publish", description=__doc__)
    p.add_argument(
        "doc",
        nargs="?",
        default="reports.toml",
        metavar="DOC",
        help="a Google Doc URL (including its `?tab=` id), an id, saved Docs "
        "API JSON, or a `.toml` list of reports (default: reports.toml)",
    )
    p.add_argument("-o", "--outdir", type=Path, default=Path("out"))
    p.add_argument(
        "--image-base",
        default="",
        help="URL prefix for published images, e.g. https://assets.etany.org/sas-west",
    )
    p.add_argument(
        "--suggestions",
        choices=("rejected", "accepted"),
        default="rejected",
        help="how to resolve open suggestions (default: rejected, i.e. what the doc says now)",
    )
    p.add_argument(
        "--split",
        action="store_true",
        help="write the HTML as numbered pieces cut at h2, for reports over the code block limit",
    )
    p.add_argument(
        "--no-pdf",
        action="store_true",
        help="write the Typst source but do not compile it",
    )
    p.add_argument(
        "--no-images",
        action="store_true",
        help="skip downloading images; the output still references them",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        reports = reports_from(args.doc)
    except (OSError, ValueError) as e:
        parser.error(str(e))

    options = BuildOptions(
        image_base=args.image_base,
        suggestions=args.suggestions,
        split=args.split,
        pdf=not args.no_pdf,
        images=not args.no_images,
    )
    site = build_site(reports, args.outdir, options)

    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "index.html").write_text(index_page(site))

    for built in site.built:
        print(f"  {built.path}  {built.doc.title}")
    for failure in site.failed:
        print(f"  failed: {failure.report.name or failure.report.url}", file=sys.stderr)
    # Non-zero when anything failed, even though the rest of the site was
    # written, so an unattended run cannot fail quietly.
    return 1 if site.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
