"""The build itself: fetch, emit, compile, and the checks around them.

Separate from `__main__` so that what a build does is not tangled up with
how a command line describes it, and so the one document and the whole list
of them run the same code rather than two copies of the same order of
operations that drift apart.
"""

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from .docs_json import JsonObject
from .emit.html import HtmlEmitter, report_page
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
IMAGES_JSON = "images.json"
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


def write_image_index(dest: Path, written: dict[str, Path]) -> None:
    """Record what each image was written as, and what is in it.

    The images are not committed, so without this the repository has no way
    to say whether a rebuild fetched the same pictures. The hash is what
    makes that checkable: a build that downloads a different image writes a
    different digest, and the diff says so.

    The filename is here because it cannot be derived. A Docs
    `inlineObject` says nothing about what kind of file it is, so `.jpg` or
    `.png` is learned by fetching, and an image with a vector original is
    written under the vector's name instead.

    The pixel size is here for the same reason. Docs says how large an
    image is placed rather than how large it is, and the crop applied on
    the way down changes the shape of the file, so the written file is the
    only thing that knows it. The HTML lays a row of figures out by it, and
    a build without the images has to be able to write the same page.

    Only written when images were downloaded. A `--no-images` build knows
    nothing about them and must not replace what a real build recorded.
    """
    index = {
        object_id: {
            "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            **_pixel_size(path),
        }
        for object_id, path in sorted(written.items())
    }
    (dest / IMAGES_JSON).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")


def _pixel_size(path: Path) -> dict[str, int]:
    """`path`'s width and height, or nothing for a file that has no pixels.

    An SVG is the file that has none: it is a drawing rather than a grid,
    and Pillow will not open one. Nothing else reads a size it did not get,
    so this stays a missing key rather than a guess.
    """
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(path) as opened:
            return {"width": opened.width, "height": opened.height}
    except OSError, UnidentifiedImageError:
        return {}


def read_image_shapes(dest: Path, doc: Document) -> None:
    """Tell `doc` how large the last build's images turned out to be.

    An image's shape is measured from the file, and the files are not
    committed, so a build that skipped the download would otherwise lay a
    row of figures out differently from the page beside it in the
    repository. The record is committed precisely so that it does not have
    to. A build that just downloaded reads back what it wrote a moment ago,
    which is the same answer by a shorter route than passing it along.

    Only the shapes. What each image was written as is `download`'s to say,
    and a build without it means the page to name the images it did not
    fetch the way a build without a record does.
    """
    index = dest / IMAGES_JSON
    if not index.exists():
        return
    for object_id, entry in json.loads(index.read_text()).items():
        if "width" in entry and "height" in entry:
            doc.image_shapes[object_id] = (entry["width"], entry["height"])


def without_content_uris(document: JsonObject) -> JsonObject:
    """The response as it is worth saving: no `contentUri` values.

    A `contentUri` is a signed URL that expires within the hour, so a saved
    one is dead on arrival: it cannot serve an image and it cannot be
    fetched again. What it can do is change on every fetch, which made a
    re-publish of an unedited document a diff in a committed file.

    Dropping them is what makes `doc.json` a record of the document. The
    parser treats an inline object with `imageProperties` as an image
    whether or not a URI came with it, so everything but the download works
    from a saved response; `images.download` says so when asked to fetch
    from one.
    """
    inline_objects = document.get("inlineObjects")
    if not inline_objects:
        return document
    stripped = dict(document)
    stripped["inlineObjects"] = {
        object_id: _without_uri(inline_object)
        for object_id, inline_object in inline_objects.items()
    }
    return stripped


def _without_uri(inline_object: JsonObject) -> JsonObject:
    properties = inline_object.get("inlineObjectProperties", {})
    embedded = properties.get("embeddedObject", {})
    if "imageProperties" not in embedded:
        return inline_object
    image_properties = {k: v for k, v in embedded["imageProperties"].items() if k != "contentUri"}
    return {
        **inline_object,
        "inlineObjectProperties": {
            **properties,
            "embeddedObject": {**embedded, "imageProperties": image_properties},
        },
    }


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
    # `index.html`, so a report directory is a page at its own URL: the site
    # serves `/reports/<slug>/` and gets the report rather than a listing of
    # files. `report.html` beside it is the fragment, which is a piece of a
    # page rather than one.
    page = outdir / "index.html"
    page.write_text(report_page(doc))
    written[page.name] = page
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
    (dest / DOC_JSON).write_text(json.dumps(without_content_uris(document), indent=2))

    if doc.images and options.images:
        from .images import download

        write_image_index(dest, download(doc, dest / IMAGE_DIR))
    read_image_shapes(dest, doc)

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
