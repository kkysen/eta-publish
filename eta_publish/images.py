"""Download the doc's inline images so they can be hosted somewhere stable.

The Docs API hands back short-lived `contentUri` values,
so they can never be the published `src`.
Each is fetched once at build time
and written under the deterministic filename the parser assigned.

Crops are applied here, to the file.
A Docs crop is fractions of the original and the API serves the uncropped image,
so every output would otherwise show the untrimmed picture.
Here rather than in the HTML is what makes it reach all three:
Markdown cannot express a crop, and a CSS one would never reach the PDF.

The PDF needs these same files,
so one download serves both the web and the print output.
"""

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from .naming import print_href
from .nodes import Document, Image, Shown

EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


MAX_AT_ONCE = 8
"""How many images to fetch at once.

The transfer is the whole cost: 16 MB over 29 requests,
none of which is waiting on any other.
Bounded rather than unbounded because `build_site` is already
running reports concurrently, and the two multiply.
"""

MAX_ENCODING_AT_ONCE = os.process_cpu_count() or 1
"""How many images to re-encode for print at once.

The opposite of fetching: the cost is a core's worth of decoding and encoding
each, so a thread past the cores this process may use only waits for one.
"""


def download(
    doc: Document, outdir: Path, *, session: requests.Session | None = None
) -> dict[str, Path]:
    """Fetch every image in `doc`, returning object id to written path.

    An image with a URI is always fetched, never taken from disk.
    Nothing available says whether the file already there is still the picture
    the document holds: the Docs object id survives a replacement unchanged,
    the `ETag` is the constant `"v0"` for every image, there is no
    `Last-Modified`, and a blob inside a document is not a Drive file and so
    has no checksum to ask for. The bytes are the only authority there is,
    and having them means fetching them.

    A file on disk is used only where there is no URI to check it against,
    which is a build from a saved response: those expire and are not saved.

    The fetches run together and the writes do not.
    A warning is part of the published page, so the order they are raised in
    has to be the order the document is in, whatever order the network answers.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    http = session or requests.Session()
    written: dict[str, Path] = {}

    # A saved response carries no URIs, because they expire and are not
    # committed. That is the ordinary shape of a rebuild rather than a defect
    # in any one image, so it is said once below instead of 29 times.
    no_uris = bool(doc.images) and not any(image.source_uri for image in doc.images)
    # Said afterwards rather than here, because a URI is only missed by an
    # image that needed one: a rebuild whose images are already on disk
    # downloads nothing and wants nothing.
    missing: list[str] = []

    # Why every image with a URI is fetched again, every time, and never
    # taken from the copy already on disk.
    #
    # There is no way to ask whether the picture changed. Not one of the
    # things that usually answers this answers it here, and each fails in a
    # way that looks like it works:
    #
    # The Docs object id does not change. `kix.2b6311sni148` was replaced
    # with an entirely different picture, 219589 bytes becoming 382683, and
    # came back under the same id, with no id added or removed anywhere in
    # the document. The id names a slot in the document, not what is in it.
    #
    # The `ETag` is the literal string `"v0"` for every image in the
    # document, so a conditional request is worse than none: asking for one
    # image with a different image's `ETag` returns `304 Not Modified` and an
    # empty body. `If-None-Match` here would report "unchanged" for a picture
    # that had been replaced.
    #
    # There is no `Last-Modified`, no `Content-MD5`, no `Digest`, and no
    # `x-goog-hash`. The only content-derived header is `Content-Length`,
    # which a `HEAD` will give without the body, and which a same-sized
    # replacement slips straight past.
    #
    # `Cache-Control: private, max-age=86400` is not permission to keep the
    # file for a day. It describes how long a cache may reuse a response it
    # already holds, which is a different question from whether the picture
    # is still the picture, and a different question again from how long the
    # URL keeps working: Google documents `contentUri` as having a default
    # lifetime of 30 minutes.
    #
    # Drive has all of this, and cannot help. `files.get` gives
    # `md5Checksum`, `sha1Checksum`, `sha256Checksum` and `modifiedTime` for
    # a file in Drive. An image pasted into a document is not a file in
    # Drive: it is a blob inside the document, with no id to ask about. The
    # document itself is a native Google file and has no checksums either.
    # `_fetch_vector` is the exception that proves it, because a linked chart
    # really is a Drive file.
    #
    # What Google offers instead is a content-addressed URL: the `AD_4nX...`
    # in a `contentUri` is stable across fetches of an unchanged image, which
    # is why the `ETag` can afford to be a constant. Whether it changes when
    # the bytes change is untested, and until it is tested it is not something
    # to skip a download on.
    #
    # So the bytes are the only authority, and having them means fetching
    # them. A file on disk is used only where there is no URI to check it
    # against, which is a build from a saved response, because a `contentUri`
    # is never saved.
    wanted: list[tuple[Image, str]] = []
    for image in doc.images:
        if image.vector is not None and _fetch_vector(image, outdir, doc, written):
            continue
        if image.source_uri:
            # Carried along rather than read again where it is used:
            # only here is it known not to be `None`.
            wanted.append((image, image.source_uri))
            continue
        existing = next(iter(outdir.glob(f"{image.filename}.*")), None)
        if existing is None:
            missing.append(image.object_id)
            continue
        written[image.object_id] = existing
        doc.image_files[image.object_id] = existing.name

    for image, content_type, body in _fetch_all(wanted, http):
        extension = EXTENSIONS.get(content_type)
        if extension is None:
            # Refused rather than saved under a bare stem.
            # Nothing serves a file with no extension the way an image is served,
            # and `typst` will not open one at all,
            # so the alternative is a page that looks built and has holes in it.
            raise ValueError(
                f"image {image.object_id} came back as {content_type or 'nothing'}, "
                f"which is not an image type this knows how to name; "
                f"expected one of {', '.join(sorted(EXTENSIONS))}"
            )
        dest = outdir / f"{image.filename}{extension}"
        dest.write_bytes(crop_to(image, body, doc))
        written[image.object_id] = dest
        doc.image_files[image.object_id] = dest.name

    if missing:
        if no_uris:
            doc.warn(
                "this response carries no image URIs, because they expire and are "
                "not saved; re-fetch the document to download its images"
            )
        else:
            for object_id in missing:
                doc.warn("image {} has no source URI; not downloaded", Shown(object_id))

    return written


def _fetch_all(
    wanted: list[tuple[Image, str]], http: requests.Session
) -> Iterator[tuple[Image, str, bytes]]:
    """Each image with what came back for it, in the order `wanted` is in.

    The requests overlap; what is yielded does not.
    A failure is raised as the document reaches it rather than as it happens,
    so which image is blamed does not depend on which answered first.
    """
    if not wanted:
        return
    with ThreadPoolExecutor(max_workers=min(len(wanted), MAX_AT_ONCE)) as pool:
        started = [(image, pool.submit(_fetch_one, uri, http)) for image, uri in wanted]
        for image, fetching in started:
            content_type, body = fetching.result()
            yield image, content_type, body


def _fetch_one(uri: str, http: requests.Session) -> tuple[str, bytes]:
    """One image's content type and bytes, as the server gave them.

    The content type is read here rather than guessed from the source line:
    a Docs `inlineObject` says nothing about what kind of file it is.
    """
    response = http.get(uri, timeout=60)
    response.raise_for_status()
    return response.headers.get("content-type", "").split(";")[0].strip(), response.content


def _fetch_vector(image: Image, outdir: Path, doc: Document, written: dict[str, Path]) -> bool:
    """Write the vector original, returning whether it is what gets used.

    A failure falls back to the raster rather than to nothing:
    a chart that renders slightly softer beats a report with a hole in it.
    """
    vector = image.vector
    if vector is None:
        return False

    dest = outdir / vector.filename
    if not dest.exists():
        from .fetch import FetchFailed, download_drive_file

        try:
            dest.write_bytes(download_drive_file(vector.file_id))
        except (FetchFailed, OSError) as e:
            doc.warn(
                f"could not download the vector {{}} ({e}); "
                "using the image from the document instead",
                Shown(vector.title or vector.file_id),
            )
            return False

    written[image.object_id] = dest
    doc.image_files[image.object_id] = dest.name
    return True


def crop_to(image: Image, data: bytes, doc: Document) -> bytes:
    """Trim `data` to the image's crop, returning it unchanged if there is none."""
    if not image.crop.trims:
        return data

    import io

    from PIL import Image as Pillow

    try:
        with Pillow.open(io.BytesIO(data)) as opened:
            box = image.crop.box(opened.width, opened.height)
            if box[2] <= box[0] or box[3] <= box[1]:
                doc.warn("image {} crops to nothing; left uncropped", Shown(image.object_id))
                return data
            trimmed = opened.crop(box)
            buffer = io.BytesIO()
            # Keep the format it arrived in, so the extension stays honest.
            trimmed.save(buffer, format=opened.format)
            return buffer.getvalue()
    except OSError as e:
        doc.warn(f"could not crop image {{}} ({e}); left uncropped", Shown(image.object_id))
        return data


PRINT_QUALITY = 85
"""The JPEG quality the PDF's copies are written at."""


def write_print_copies(written: dict[str, Path], dest: Path) -> dict[str, Path]:
    """Write the PDF's copy of every image, returning object id to written path.

    Every raster is re-encoded, even the few that a JPEG barely shrinks.
    What each file is called has to follow from the name it arrived under and
    nothing else: `report.typ` is committed and compared against a fresh
    build, so a name that depended on how well a picture happened to compress
    would make the committed file depend on the encoder, and a build that
    skipped the images would write a different one again.

    The cost is line art, which picks up ringing along hard edges for little
    saving. It is paid in the PDF only: `images/` keeps what the document
    holds, and that is what each picture in the PDF links to.
    """
    import shutil

    dest.mkdir(parents=True, exist_ok=True)
    copies: dict[str, Path] = {}
    if not written:
        return copies
    # Several at once, because Pillow lets go of the GIL while it decodes and
    # encodes, which is nearly all of the time a picture takes here.
    with ThreadPoolExecutor(max_workers=min(len(written), MAX_ENCODING_AT_ONCE)) as pool:
        encoded = pool.map(_for_print, written.values())
        for (object_id, path), data in zip(written.items(), encoded, strict=True):
            out = dest / print_href(path.name)
            copies[object_id] = out
            if data is None:
                shutil.copyfile(path, out)
            else:
                out.write_bytes(data)
    return copies


def _for_print(path: Path) -> bytes | None:
    """`path` re-encoded as a JPEG, at the size it arrived.

    No resolution cap. One was measured at 300 DPI across the column and
    dropped: it saved 1.9 MB of a budget with 20 MB to spare, and a PDF is
    read on a screen that zooms, where the detail it threw away is the
    detail someone is zooming in to see.

    `None` for a file that is already what the PDF wants, which the caller
    copies rather than rewrites: a vector, which has no raster to re-encode,
    and a JPEG, which would only be decoded and recompressed into a second
    generation of its own artifacts.

    Both are decided by what the file is rather than by how well it compresses,
    so the name in `PRINT_DIR` stays a function of the name it arrived under.
    """
    import io

    from PIL import Image as Pillow

    if path.suffix.lower() == ".svg":
        return None
    with Pillow.open(path) as opened:
        if opened.format == "JPEG":
            return None
        # Flattened rather than composited onto white: every alpha channel in
        # these documents compresses to under 3 KB, which is a channel that
        # says nothing, and JPEG has nowhere to put one anyway.
        buffer = io.BytesIO()
        opened.convert("RGB").save(
            buffer, "JPEG", quality=PRINT_QUALITY, optimize=True, progressive=True
        )
        return buffer.getvalue()
