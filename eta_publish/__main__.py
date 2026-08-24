"""`eta-publish`: a Google Doc in, a publishable report out."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .docs_json import JsonObject
from .emit.html import HtmlEmitter
from .emit.markdown import MarkdownEmitter
from .emit.typst import TypstEmitter
from .nodes import Document
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
        "--no-images",
        action="store_true",
        help="skip downloading images; the output still references them",
    )
    return p


def load(
    ref: str, outdir: Path, tab: str | None = None, suggestions: str = "rejected"
) -> JsonObject:
    """Accept a saved JSON file so the pipeline can run without credentials."""
    path = Path(ref)
    if path.is_file():
        return json.loads(path.read_text())

    from .fetch import fetch_to

    outdir.mkdir(parents=True, exist_ok=True)
    return fetch_to(ref, outdir / "doc.json", tab, suggestions)


def emit(doc: Document, outdir: Path, image_base: str) -> dict[str, Path]:
    """Run each emitter, reporting the ones not yet implemented rather than
    failing the whole build for them."""
    outdir.mkdir(parents=True, exist_ok=True)
    emitters = {
        "report.html": HtmlEmitter(image_base=image_base),
        "report.md": MarkdownEmitter(),
        "report.typ": TypstEmitter(),
    }
    written: dict[str, Path] = {}
    for name, emitter in emitters.items():
        try:
            source = emitter.emit(doc)
        except NotImplementedError as e:
            print(f"skipped {name}: not implemented ({e})", file=sys.stderr)
            continue
        dest = outdir / name
        dest.write_text(source)
        written[name] = dest
    return written


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    from .fetch import TabNotFound

    try:
        doc = parse(load(args.doc, args.outdir, args.tab, args.suggestions))
    except TabNotFound as e:
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
