"""`eta-publish`: a Google Doc in, a publishable report out."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build import build_pdf, check_code_block_size, emit, load, write_split
from .parse import parse


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="eta-publish", description=__doc__)
    p.add_argument(
        "doc",
        help="a Google Doc URL or id, or a path to saved Docs API JSON",
    )
    p.add_argument("-o", "--outdir", type=Path, default=Path("out"))
    p.add_argument(
        "--tab",
        help="Docs tab id; defaults to the `?tab=` in the URL. Multi-tab "
        "documents refuse to guess, and list their tabs.",
    )
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
    args = build_parser().parse_args(argv)
    from .fetch import FetchFailed, TabNotFound

    try:
        doc = parse(load(args.doc, args.outdir, args.tab, args.suggestions))
    except (TabNotFound, FetchFailed) as e:
        print(f"eta-publish: {e}", file=sys.stderr)
        return 2
    except NotImplementedError as e:
        # The parser is still being filled in; say so plainly rather than
        # handing the user a traceback.
        print(f"eta-publish: not implemented yet: {e}", file=sys.stderr)
        return 2

    if doc.images and not args.no_images:
        from .images import download

        download(doc, args.outdir / "images")

    written = emit(doc, args.outdir, args.image_base)

    typ = written.get("report.typ")
    if typ is not None and not args.no_pdf:
        build_pdf(typ, args.outdir, skipped_images=args.no_images and bool(doc.images))

    report = written.get("report.html")
    if report is not None:
        check_code_block_size(doc, report)
    if args.split:
        for part in write_split(doc, args.outdir, args.image_base):
            written[part.name] = part

    for warning in doc.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(f"title:     {doc.title}")
    print(f"url:       {doc.slug or '(missing)'}")
    print(f"footnotes: {len(doc.footnotes)}")
    for name, path in sorted(written.items()):
        print(f"  {name:14} {path.stat().st_size:>9,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
