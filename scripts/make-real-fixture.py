#!/usr/bin/env python
"""Build `tests/real/` from a fetched Docs API response.

    uv run eta-publish <doc-url> -o out
    uv run scripts/make-real-fixture.py out/doc.json

The response is committed as fetched. Person smart chips carry an email
address beside the name, which stays: it is already in this repository on
every commit's author line, so removing it from one file would be theatre.
What does matter is that no *output* carries it, which
`tests/test_real_document.py` asserts.

Image extensions are recorded separately because they are only knowable by
downloading each image, and the test that reads them does not use the
network.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REAL = Path(__file__).resolve().parent.parent / "tests" / "real"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2

    source = Path(argv[1])
    doc_json = json.loads(source.read_text())

    REAL.mkdir(parents=True, exist_ok=True)
    (REAL / "sas-west.doc.json").write_text(json.dumps(doc_json, indent=2) + "\n")

    # Extensions, from whatever was downloaded next to the response.
    images = source.parent / "images"
    if images.is_dir():
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from eta_publish.parse import parse

        by_stem = {i.filename: i.object_id for i in parse(doc_json).images}
        mapping = {by_stem[p.stem]: p.suffix for p in sorted(images.iterdir()) if p.stem in by_stem}
        (REAL / "sas-west.images.json").write_text(
            json.dumps(mapping, indent=2, sort_keys=True) + "\n"
        )
        print(f"recorded {len(mapping)} image extensions")
    else:
        print(f"no {images}, keeping the existing image extensions")

    print("now run: uv run pytest --regenerate-golden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
