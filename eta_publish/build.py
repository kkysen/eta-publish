"""The build itself: fetch, emit, compile, and the checks around them."""

import hashlib
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .checks import check
from .docs_json import JsonObject
from .emit.html import HtmlEmitter, report_page
from .emit.markdown import MarkdownEmitter
from .emit.typst import TypstEmitter
from .naming import ASSET_DIR, IMAGE_DIR
from .nodes import Document, Shown
from .parse import parse, read_review


@dataclass(frozen=True)
class BuildOptions:
    """Everything the command line can vary about one build.

    A record rather than six parameters:
    all of these have to reach `build_one` from the argument parser,
    and a positional list that long is where a caller transposes two flags.
    """

    suggestions: str = "rejected"
    split: bool = False
    images: bool = True
    offline: bool = False
    """Whether to rebuild from the responses a previous build saved.

    No credentials, no network, and no way to notice a document that changed.
    A rebuild of what is committed, for a change to this code rather than to a doc.
    """

    comments: bool = True
    """Whether to ask how many comment threads are open.

    The one expensive question a build asks: it is a text export of the whole
    document rather than an API call, and it costs more than fetching the
    document does. Left unasked, the last answer stands, the way it already
    does for the service account that cannot ask it at all.
    """


DOC_JSON = "doc.json"
IMAGES_JSON = "images.json"
"""The saved API response, written by every build beside its outputs."""


def load(
    ref: str,
    suggestions: str = "rejected",
    comments: bool = True,
    cached: Path | None = None,
) -> JsonObject:
    """Resolve a reference to the document it names.

    A saved response can be the file itself or the directory holding it,
    so whatever a previous run produced can be handed straight back
    without knowing the filename inside it.

    Which tab to read is part of the reference, as `?tab=` in the URL,
    which is the only way it can be named in `reports.toml`.
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

    return fetch(ref, suggestions=suggestions, comments=comments, cached=cached)


REVIEW_KEYS = ("openSuggestions", "openComments")
"""What the fetch records about the editing still open on a document.

Left out of the response entirely when the account could not read it,
which is not the same as there being none.
"""


def carry_over_review(document: JsonObject, saved: Path) -> None:
    """Keep the last answer about suggestions and comments where this run has none.

    Reading suggestions needs edit access,
    and reading comments needs an export the service account is refused,
    which is what rebuilds the site in CI.
    Without this it would write a page saying nothing is open,
    differ from the committed one, and fail the check that the two match
    over something no document changed.
    A stale count beats a wrong one.
    """
    previous: JsonObject = {}
    if saved.is_file():
        try:
            previous = json.loads(saved.read_text())
        except OSError, ValueError:
            previous = {}
    for key in REVIEW_KEYS:
        if key not in document and key in previous:
            document[key] = previous[key]


def write_split(doc: Document, outdir: Path) -> list[Path]:
    """One file per piece, named so paste order is obvious."""
    emitter = HtmlEmitter(image_base=IMAGE_DIR)
    pieces = [emitter.join(emitter.wrapped(group)) for group in emitter.groups(doc)]
    written = []
    for n, piece in enumerate(pieces, start=1):
        dest = outdir / f"report.part{n:02d}.html"
        dest.write_text(piece)
        written.append(dest)
    return written


def write_image_index(dest: Path, written: dict[str, Path]) -> None:
    """Record what each image was written as, and what is in it.

    The images are not committed,
    so without this nothing says whether a rebuild fetched the same pictures.

    The filename is here because it cannot be derived:
    a Docs `inlineObject` says nothing about what kind of file it is,
    so `.jpg` or `.png` is learned by fetching.

    The pixel size is here because only the written file knows it:
    Docs says how large an image is placed, not how large it is,
    and the crop applied on the way down changes the shape of the file.
    The HTML lays a row of figures out by it,
    and a build without the images has to write the same page.

    Only written when images were downloaded:
    a `--no-images` build knows nothing about them
    and must not replace what a real build recorded.

    A download that turned up nothing is the same thing arrived at differently,
    and is why an empty result is refused rather than written.
    The caller only asks when the document has images,
    so nothing to record means none of them could be fetched,
    and recording that would erase the one file
    that says which pictures a complete build wrote.
    """
    if not written and (dest / IMAGES_JSON).exists():
        return
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

    An SVG has none: it is a drawing rather than a grid, and Pillow will not open one.
    Nothing else reads a size it did not get,
    so this stays a missing key rather than a guess.
    """
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(path) as opened:
            return {"width": opened.width, "height": opened.height}
    except OSError, UnidentifiedImageError:
        return {}


def has_its_images(dest: Path) -> bool:
    """Whether the last build's image files are still beside its response.

    The images are not committed and the response is,
    so a fresh checkout has a saved response describing pictures that are not there.
    Reusing that response is what makes the build write a page with no images in it:
    a saved `contentUri` expires within the hour and so is never saved,
    which leaves the download nothing to fetch from
    and the emitters no filename to write.

    Asked of `images.json` rather than of the directory,
    because only the index says which files a complete build wrote.
    An index that is missing or unreadable is not evidence that anything is gone,
    so it reads as present and the build goes on to answer the question itself.
    """
    try:
        recorded = json.loads((dest / IMAGES_JSON).read_text())
    except OSError, ValueError:
        return True
    return all((dest / IMAGE_DIR / entry["file"]).exists() for entry in recorded.values())


def check_images_written(dest: Path, doc: Document) -> None:
    """Refuse a build that emits a path to a picture it did not write.

    Every emitter asks `image_href` where an image went,
    and it answers with the raster's bare stem for an image nothing downloaded.
    That reaches the page as `src="images/img-d4734d4b"`,
    which no browser serves as an image and `typst` will not open at all.

    Caught here rather than left to whatever notices it downstream.
    A missing file surfaced as a `typst` warning and a diff against the
    committed site, which says a rebuild disagrees with what was published
    and not that this build has holes in it.
    Only asked of a build that meant to have the images:
    a `--no-images` run is not publishing this page.
    """
    absent = sorted(
        doc.image_href(image)
        for image in doc.images
        if not (dest / IMAGE_DIR / doc.image_href(image)).is_file()
    )
    if absent:
        raise ValueError(
            f"{len(absent)} of {len(doc.images)} images were not written, "
            f"so the page would link pictures that are not there: {', '.join(absent)}"
        )


def read_image_shapes(dest: Path, doc: Document) -> None:
    """Tell `doc` how large the last build's images turned out to be.

    A shape is measured from the file, and the files are not committed,
    so a build that skipped the download would otherwise lay a row of figures
    out differently from the page beside it in the repository.

    Only the shapes: what each image was written as is `download`'s to say.
    """
    index = dest / IMAGES_JSON
    if not index.exists():
        return
    for object_id, entry in json.loads(index.read_text()).items():
        if "width" in entry and "height" in entry:
            doc.image_shapes[object_id] = (entry["width"], entry["height"])


def without_content_uris(document: JsonObject) -> JsonObject:
    """The response as it is worth saving: no `contentUri` values.

    A `contentUri` is a signed URL that expires within the hour,
    so a saved one is dead on arrival and changes on every fetch,
    which made re-publishing an unedited document a diff in a committed file.

    The parser treats an inline object with `imageProperties` as an image
    whether or not a URI came with it,
    so everything but the download works from a saved response.
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


# The stylesheets and the script every report page shares, and the formatter
# each is read by. Written once per build rather than into each page.
SHARED_ASSETS = (
    "page.css",
    "report.css",
    "report.js",
)


def write_assets(siteroot: Path) -> list[Path]:
    """The one copy of what every report page links.

    Written as they are; `format.tree` lays out and checks the whole build
    afterwards, these among the rest.
    """
    from .assets import read

    dest = siteroot / ASSET_DIR
    dest.mkdir(parents=True, exist_ok=True)
    written = []
    for name in SHARED_ASSETS:
        path = dest / name
        path.write_text(read(name))
        written.append(path)
    return written


def asset_base(path: str) -> str:
    """`ASSET_DIR` as seen from a report at `path`, which says how deep it is.

    Relative rather than rooted at `/`, because the site is served from
    wherever Pages puts it and a report's own `URL:` decides its depth.
    """
    return "/".join([".."] * len(PurePosixPath(path).parts) + [ASSET_DIR])


def emit(doc: Document, outdir: Path, assets: str = ASSET_DIR) -> dict[str, Path]:
    """Run each emitter,
    reporting the ones not yet implemented rather than failing the whole build for them."""
    outdir.mkdir(parents=True, exist_ok=True)
    emitters = {
        "report.html": HtmlEmitter(image_base=IMAGE_DIR),
        "report.md": MarkdownEmitter(),
        "report.typ": TypstEmitter(),
    }
    written: dict[str, Path] = {}
    # `index.html`, so a report directory is a page at its own URL:
    # `/reports/<slug>/` serves the report rather than a listing of files.
    # `report.html` beside it is the fragment, a piece of a page rather than one.
    page = outdir / "index.html"
    page.write_text(report_page(doc, asset_base=assets))
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
    """Say something before a paste fails, not after.

    Asked once the tree has been formatted, because that is what the file
    will be when it is pasted: laying it out adds around an eighth to it,
    and a limit checked against the bytes before that is not the limit.
    """
    from .emit.html import CODE_BLOCK_LIMIT, CODE_BLOCK_WARN

    size = report.stat().st_size
    if size > CODE_BLOCK_LIMIT:
        doc.warn(
            f"{report.name} is {size:,} bytes, over Squarespace's "
            f"{CODE_BLOCK_LIMIT:,} byte code block limit; "
            "split it at h2 boundaries with {}",
            Shown("--split"),
        )
    elif size > CODE_BLOCK_WARN:
        doc.warn(
            f"{report.name} is {size:,} bytes, within Squarespace's "
            f"{CODE_BLOCK_LIMIT:,} byte limit but large enough that the editor "
            "may be slow to save it"
        )


def build_pdf(source: Path, outdir: Path, skipped_images: bool) -> Path | None:
    """Compile the report PDF, reporting rather than failing the whole build.

    The `.typ` is written either way,
    so a missing `typst` or a compile error costs the PDF and nothing else.
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


def build_one(
    ref: str,
    outdir: Path,
    options: BuildOptions | None = None,
    verify: Callable[[Document], None] | None = None,
    cached: Path | None = None,
) -> tuple[Document, str]:
    """Build one report, returning it and the site-relative path it went to.

    The whole per-document order of operations lives here, and only here.

    Where a report goes comes from its own front matter, inside the document,
    so the destination is unknown until the document has been read.
    That is why the response is not written on the way in:
    it is saved into the report's directory afterwards,
    whether it came from the API or from a previous build.

    `verify` is the caller's chance to say this is not the document it meant,
    given the parsed document and called before anything is written.

    `cached` is the response the last build of this report saved, if there is one.
    It is not read unless Drive says the document has not been edited since,
    which is a cheaper question than any of the ones it saves asking.
    """
    from .site import report_path

    options = options or BuildOptions()
    document = load(ref, options.suggestions, options.comments, cached)
    doc = parse(document)
    if verify is not None:
        # Before the first directory is made,
        # so a wrong answer leaves no report's worth of files behind.
        verify(doc)
    path = report_path(doc)
    dest = outdir / path
    dest.mkdir(parents=True, exist_ok=True)

    # Before the checks, which warn about what it says,
    # and before the response is written, which is what the next build reads.
    carry_over_review(document, dest / DOC_JSON)
    read_review(doc, document)
    check(doc)

    # Sorted, as `images.json` is: this file is committed and compared against
    # a fresh build, so any two runs that agree about the document have to
    # write the same bytes, which insertion order does not promise.
    (dest / DOC_JSON).write_text(
        json.dumps(without_content_uris(document), indent=2, sort_keys=True)
    )

    if doc.images and options.images:
        from .images import download

        write_image_index(dest, download(doc, dest / IMAGE_DIR))
    read_image_shapes(dest, doc)
    if doc.images and options.images:
        check_images_written(dest, doc)

    # Written here rather than once per site, so that building a single
    # report produces a page with everything it links.
    write_assets(outdir)
    written = emit(doc, dest, asset_base(path))

    typ = written.get("report.typ")
    if typ is not None:
        build_pdf(typ, dest, skipped_images=not options.images and bool(doc.images))

    if options.split:
        write_split(doc, dest)

    return doc, path
