"""eta-publish: Google Doc -> publish-ready report HTML."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .convert import convert
from .render import write_all


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="eta-publish", description=__doc__)
    p.add_argument("doc", help="Google Doc URL or id, or a path to saved Docs API JSON")
    p.add_argument("-o", "--outdir", type=Path, default=Path("out"))
    p.add_argument(
        "--image-base",
        default="",
        help="URL prefix the published <img src> should use, e.g. https://assets.etany.org/sas-west",
    )
    p.add_argument(
        "--no-images",
        action="store_true",
        help="skip downloading inline images (HTML still references them)",
    )
    p.add_argument(
        "--site-css",
        action="store_true",
        help="omit the inline <style> block, for sites carrying REPORT_CSS in Custom CSS",
    )
    return p


def load(ref: str, outdir: Path) -> dict:
    path = Path(ref)
    if path.is_file():
        return json.loads(path.read_text())
    from .fetch import fetch_to

    outdir.mkdir(parents=True, exist_ok=True)
    return fetch_to(ref, outdir / "doc.json")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    doc_json = load(args.doc, args.outdir)
    doc = convert(doc_json, image_base=args.image_base)

    if doc.images and not args.no_images:
        from .images import download

        written = download(doc.images, args.outdir / "images")
        # Downloading resolves the real extension, so fix up the references.
        for name, dest in written.items():
            if dest.name != name:
                doc.body_html = doc.body_html.replace(name, dest.name)

    written = write_all(doc, args.outdir, inline_css=not args.site_css)

    for w in doc.warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(f"title:     {doc.title}")
    print(f"url slug:  {doc.meta.get('url', '(missing)')}")
    print(f"images:    {len(doc.images)}")
    n_footnotes = doc.footnotes_html.count('<li id="fn')
    print(f"footnotes: {n_footnotes}")
    for label, path in written.items():
        print(f"{label + ':':10} {path}  ({path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
