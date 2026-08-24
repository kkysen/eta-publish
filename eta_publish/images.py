"""Download the doc's inline images so they can be hosted somewhere stable.

The Docs API hands back short-lived `contentUri` values, so they can never
be the published `src`. We fetch each once at build time and write it under
the deterministic filename the parser assigned.

These same files are what the PDF needs, so one download serves both the
web and the print output, and one upload to whatever host serves both.
"""

from __future__ import annotations

from pathlib import Path

import requests

EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


def download(doc, outdir: Path, *, session: requests.Session | None = None) -> dict[str, Path]:
    """Fetch every image in `doc`, returning object id to written path.

    Images already on disk are left alone. The filename depends only on the
    Docs object id, so a re-run after an unrelated edit re-downloads nothing.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    http = session or requests.Session()
    written: dict[str, Path] = {}

    for image in doc.images:
        existing = next(iter(outdir.glob(f"{image.filename}.*")), None)
        if existing is not None:
            written[image.object_id] = existing
            continue
        if not image.source_uri:
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
        dest.write_bytes(response.content)
        written[image.object_id] = dest

    return written
