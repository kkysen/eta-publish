"""Download the doc's inline images so they can be hosted somewhere stable.

The Docs API hands back short-lived `contentUri` values,
so they can never be the published `src`.
We fetch each once at build time
and write it under the deterministic filename the parser assigned.

Crops are applied here, to the file.
A Docs crop is stored as fractions of the original
and the API serves the uncropped image,
so every output would otherwise show the untrimmed picture.
Doing it here rather than in the HTML is what makes it reach all three:
Markdown cannot express a crop at all, and a CSS one would never reach the PDF.

These same files are what the PDF needs,
so one download serves both the web and the print output,
and one upload to whatever host serves both.
"""

from pathlib import Path

import requests

from .nodes import Document, Image

EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


def download(
    doc: Document, outdir: Path, *, session: requests.Session | None = None
) -> dict[str, Path]:
    """Fetch every image in `doc`, returning object id to written path.

    Images already on disk are left alone.
    The filename depends only on the Docs object id,
    so a re-run after an unrelated edit re-downloads nothing.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    http = session or requests.Session()
    written: dict[str, Path] = {}

    # A saved response carries no URIs at all, because they expire and are not committed.
    # That is the ordinary shape of a rebuild rather than a defect in any one image,
    # so it is said once here instead of 29 times below,
    # and the remedy is a fetch rather than an edit to the document.
    no_uris = bool(doc.images) and not any(image.source_uri for image in doc.images)
    if no_uris:
        doc.warn(
            "this response carries no image URIs, because they expire and are "
            "not saved; re-fetch the document to download its images"
        )

    for image in doc.images:
        if image.vector is not None and _fetch_vector(image, outdir, doc, written):
            continue

        existing = next(iter(outdir.glob(f"{image.filename}.*")), None)
        if existing is not None:
            written[image.object_id] = existing
            doc.image_files[image.object_id] = existing.name
            continue
        if not image.source_uri:
            if not no_uris:
                doc.warn(f"image {image.object_id} has no source URI; not downloaded")
            continue

        response = http.get(image.source_uri, timeout=60)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        extension = EXTENSIONS.get(content_type)
        if extension is None:
            doc.warn(
                f"image {image.object_id} has unexpected content type {content_type!r}; "
                "saved without an extension"
            )
            extension = ""

        dest = outdir / f"{image.filename}{extension}"
        dest.write_bytes(crop_to(image, response.content, doc))
        written[image.object_id] = dest
        doc.image_files[image.object_id] = dest.name

    return written


def _fetch_vector(image: Image, outdir: Path, doc: Document, written: dict[str, Path]) -> bool:
    """Write the vector original, returning whether it is what gets used.

    A failure here falls back to the raster rather than to nothing:
    the document still holds a perfectly good picture,
    and a chart that renders slightly softer beats a report with a hole in it.
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
                f"could not download the vector {vector.title or vector.file_id} "
                f"({e}); using the image from the document instead"
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
                doc.warn(f"image {image.object_id} crops to nothing; left uncropped")
                return data
            trimmed = opened.crop(box)
            buffer = io.BytesIO()
            # Keep the format it arrived in, so the extension stays honest.
            trimmed.save(buffer, format=opened.format)
            return buffer.getvalue()
    except OSError as e:
        doc.warn(f"could not crop image {image.object_id} ({e}); left uncropped")
        return data
