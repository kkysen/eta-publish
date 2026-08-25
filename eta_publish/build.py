"""The build itself: fetch, emit, compile, and the checks around them.

Separate from `__main__` because there are two entry points into the same
pipeline, `eta-publish` for one document and `eta-publish-site` for every
report the project publishes, and the second must not have to import the
first's argument parser to reuse it.
"""

import json
import sys
from pathlib import Path

from .docs_json import JsonObject
from .emit.html import HtmlEmitter, preview_page
from .emit.markdown import MarkdownEmitter
from .emit.typst import TypstEmitter
from .nodes import Document


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
