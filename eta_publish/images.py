"""Download the doc's inline images so they can be hosted somewhere stable.

Docs API `contentUri` values are short-lived, so they can never be used as
the published `src`. We pull them once at build time and write them into
`out/images/`, keyed by the deterministic names the converter assigned.
"""

from __future__ import annotations

from pathlib import Path

import requests

EXT_BY_TYPE = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


def download(images: dict[str, str], outdir: Path) -> dict[str, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for name, uri in images.items():
        resp = requests.get(uri, timeout=60)
        resp.raise_for_status()
        ext = EXT_BY_TYPE.get(resp.headers.get("content-type", "").split(";")[0], "")
        dest = outdir / (Path(name).stem + (ext or Path(name).suffix))
        dest.write_bytes(resp.content)
        written[name] = dest
    return written
