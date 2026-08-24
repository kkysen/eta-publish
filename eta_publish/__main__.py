"""`eta-publish`: a Google Doc in, a publishable report out."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .docs_json import JsonObject
from .emit.html import HtmlEmitter, preview_page
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


def write_split(doc: Document, outdir: Path, image_base: str) -> list[Path]:
    """One file per piece, named so paste order is obvious."""
    from .emit.html import HtmlEmitter, split_at_headings

    fragment = HtmlEmitter(image_base=image_base).emit(doc)
    pieces = split_at_headings(fragment)
    written = []
    for n, piece in enumerate(pieces, start=1):
        dest = outdir / f"report.part{n:02d}.html"
        dest.write_text(piece)
        written.append(dest)
    return written


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
    preview = outdir / "preview.html"
    preview.write_text(preview_page(doc, image_base))
    written[preview.name] = preview
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


def check_code_block_size(doc: Document, report: Path) -> None:
    """Say something before a paste fails, not after."""
    from .emit.html import CODE_BLOCK_LIMIT, CODE_BLOCK_WARN

    size = report.stat().st_size
    if size > CODE_BLOCK_LIMIT:
        doc.warn(
            f"{report.name} is {size:,} bytes, over Squarespace's "
            f"{CODE_BLOCK_LIMIT:,} byte code block limit; "
            "split it at h2 boundaries with `--split`"
        )
    elif size > CODE_BLOCK_WARN:
        doc.warn(
            f"{report.name} is {size:,} bytes, within Squarespace's "
            f"{CODE_BLOCK_LIMIT:,} byte limit but large enough that the editor "
            "may be slow to save it"
        )


def build_pdf(source: Path, outdir: Path, skipped_images: bool) -> Path | None:
    """Compile the report PDF, reporting rather than failing the whole build.

    The `.typ` is already written either way, so a missing `typst` or a
    compile error costs the PDF and nothing else.
    """
    from .pdf import TypstMissing, compile_pdf, install_template

    if skipped_images:
        print(
            "note: skipping the PDF because images were not downloaded; "
            "Typst embeds them from disk, so it needs the real files",
            file=sys.stderr,
        )
        return None

    install_template(outdir)
    try:
        return compile_pdf(source)
    except TypstMissing as e:
        print(f"note: {e}", file=sys.stderr)
    except RuntimeError as e:
        print(f"warning: {e}", file=sys.stderr)
    return None


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
