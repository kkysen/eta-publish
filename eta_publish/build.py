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
from .naming import IMAGE_DIR
from .nodes import Document
from .parse import parse


@dataclass(frozen=True)
class BuildOptions:
    """Everything the command line can vary about one build.

    A record rather than six parameters: every one of these has to reach
    `build_one` from the argument parser, and a positional list that long is
    where a caller silently transposes two flags.
    """

    suggestions: str = "rejected"
    split: bool = False
    images: bool = True


DOC_JSON = "doc.json"
"""The saved API response, written by every build beside its outputs."""


def load(ref: str, suggestions: str = "rejected") -> JsonObject:
    """Resolve a reference to the document it names.

    A saved response can be given as the file itself or as the directory
    holding it, because a build writes `doc.json` into the report's own
    directory: whatever a previous run produced can be handed straight back
    without anyone having to know the filename inside it. That is what lets
    a test run the whole pipeline with no network at all.

    Which tab to read is part of the reference, as `?tab=` in the URL, and
    not a separate argument: a tab is named the same way here as it is in
    `reports.toml`, which is the only way it can be named there.
    """
    path = Path(ref)
    if path.is_dir():
        saved = path / DOC_JSON
        if not saved.is_file():
            raise FileNotFoundError(f"{path} holds no {DOC_JSON}; is it a report directory?")
        return json.loads(saved.read_text())
    if path.is_file():
        return json.loads(path.read_text())

    from .fetch import fetch

    return fetch(ref, suggestions=suggestions)


def write_split(doc: Document, outdir: Path) -> list[Path]:
    """One file per piece, named so paste order is obvious."""
    from .emit.html import HtmlEmitter, split_at_headings

    fragment = HtmlEmitter(image_base=IMAGE_DIR).emit(doc)
    pieces = split_at_headings(fragment)
    written = []
    for n, piece in enumerate(pieces, start=1):
        dest = outdir / f"report.part{n:02d}.html"
        dest.write_text(piece)
        written.append(dest)
    return written


def emit(doc: Document, outdir: Path) -> dict[str, Path]:
    """Run each emitter, reporting the ones not yet implemented rather than
    failing the whole build for them."""
    outdir.mkdir(parents=True, exist_ok=True)
    emitters = {
        "report.html": HtmlEmitter(image_base=IMAGE_DIR),
        "report.md": MarkdownEmitter(),
        "report.typ": TypstEmitter(),
    }
    written: dict[str, Path] = {}
    preview = outdir / "preview.html"
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

    Where a report goes comes from its own front matter, which is inside
    the document, so nothing about the destination is known until the
    document has been read. That is why the response is not written on the
    way in: it is saved into the report's directory afterwards, whether it
    arrived from the API or from a previous build, so what one run wrote is
    always what the next can be handed.
    """
    from .site import report_path

    options = options or BuildOptions()
    document = load(ref, options.suggestions)
    doc = parse(document)
    path = report_path(doc)
    dest = outdir / path
    dest.mkdir(parents=True, exist_ok=True)
    (dest / DOC_JSON).write_text(json.dumps(document, indent=2))

    if doc.images and options.images:
        from .images import download

        download(doc, dest / IMAGE_DIR)

    written = emit(doc, dest)

    typ = written.get("report.typ")
    if typ is not None:
        build_pdf(typ, dest, skipped_images=not options.images and bool(doc.images))

    report = written.get("report.html")
    if report is not None:
        check_code_block_size(doc, report)
    if options.split:
        write_split(doc, dest)

    return doc, path
