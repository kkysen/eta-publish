"""Where the two test corpora live.

Both are publish directories of the same shape, so a test says which
document it wants rather than how that document is stored:

    fixture/reports/<slug>/doc.json   hand-written, small, fast
    real/reports/<slug>/doc.json      an actual `documents.get` response

Each holds its emitted output beside its `doc.json`, which is what
`eta-publish <that directory>` produces, so a corpus can be rebuilt from
what it already contains. Only the image filenames need the network: their
extensions come from fetching the images, which is why `images.json`
records them for the real one.
"""

from pathlib import Path

TESTS = Path(__file__).parent
SLUG = "reports/digging-out-deep-hole-sas-west"

FIXTURE = TESTS / "fixture"
FIXTURE_DIR = FIXTURE / SLUG

REAL_SITE = TESTS / "real"
REAL_DIR = REAL_SITE / SLUG
