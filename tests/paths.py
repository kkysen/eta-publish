"""Where the two test corpora live.

Both are publish directories of the same shape,
so a test says which document it wants rather than how that document is stored:

    tests/fixture/reports/<slug>/doc.json   hand-written, small, fast
    site/reports/<slug>/doc.json            a real `documents.get` response

The real one is not under `tests/` at all:
it is the published site, at the top level, and the tests read it there.
It is a corpus because it is the real thing, not the other way around.

Each holds its emitted output beside its `doc.json`,
so a corpus can be rebuilt from what it already contains.
Only the image filenames need the network:
their extensions come from fetching, which is why `images.json` records them.
"""

from pathlib import Path

TESTS = Path(__file__).parent
ROOT = TESTS.parent
SLUG = "reports/digging-out-deep-hole-sas-west"

FIXTURE = TESTS / "fixture"
FIXTURE_DIR = FIXTURE / SLUG

SITE = ROOT / "site"
REAL_DIR = SITE / SLUG
