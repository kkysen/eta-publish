"""The build itself: fetch, emit, compile, and the checks around them.

Separate from `__main__` so that what a build does is not tangled up with
how a command line describes it, and so the one document and the whole list
of them run the same code rather than two copies of the same order of
operations that drift apart.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from .docs_json import JsonObject
from .emit.html import HtmlEmitter, preview_page
from .emit.markdown import MarkdownEmitter
from .emit.typst import TypstEmitter
from .nodes import Document
from .parse import parse


@dataclass(frozen=True)
class BuildOptions:
    """Everything the command line can vary about one build.

    A record rather than six parameters: every one of these has to reach
    `build_one` from the argument parser, and a positional list that long is
    where a caller silently transposes two flags.
    """

    image_base: str = ""
    suggestions: str = "rejected"
    split: bool = False
    pdf: bool = True
    images: bool = True


def load(ref: str, outdir: Path, suggestions: str = "rejected") -> JsonObject:
    """Accept a saved JSON file so the pipeline can run without credentials.

    Which tab to read is part of the reference, as `?tab=` in the URL, and
    not a separate argument: a tab is named the same way here as it is in
    `reports.toml`, which is the only way it can be named there.
    """
    path = Path(ref)
    if path.is_file():
        return json.loads(path.read_text())

    from .fetch import fetch_to

    outdir.mkdir(parents=True, exist_ok=True)
    return fetch_to(ref, outdir / "doc.json", suggestions=suggestions)


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
    # Not `image_base`: see `preview_page`.
    preview.write_text(preview_page(doc))
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


def build_one(ref: str, outdir: Path, options: BuildOptions | None = None) -> tuple[Document, str]:
    """Build one report, returning it and the site-relative path it went to.

    The whole per-document order of operations lives here, and only here.
    It ran twice before, once for a single document and once per report of a
    site, which is exactly the kind of duplication that ends with images
    downloaded in one and not the other.

    A report's directory comes from its own front matter, which is inside
    the document, so the response is fetched to a staging directory and the
    destination is only known afterwards.
    """
    from .site import report_path

    options = options or BuildOptions()
    staging = outdir / ".staging"
    doc = parse(load(ref, staging, options.suggestions))
    path = report_path(doc)
    dest = outdir / path
    dest.mkdir(parents=True, exist_ok=True)

    saved = staging / "doc.json"
    if saved.exists():
        # Kept, because re-running against it needs no credentials, and it is
        # what the tests build from. It moves rather than being fetched into
        # place because where it belongs was not known until it was read.
        saved.replace(dest / "doc.json")
    if staging.is_dir() and not any(staging.iterdir()):
        staging.rmdir()

    if doc.images and options.images:
        from .images import download

        download(doc, dest / "images")

    written = emit(doc, dest, options.image_base)

    typ = written.get("report.typ")
    if typ is not None and options.pdf:
        build_pdf(typ, dest, skipped_images=not options.images and bool(doc.images))

    report = written.get("report.html")
    if report is not None:
        check_code_block_size(doc, report)
    if options.split:
        write_split(doc, dest, options.image_base)

    return doc, path
