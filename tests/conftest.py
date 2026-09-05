import os

import pytest

# Rich draws errors in a box the width of the terminal
# and breaks anything longer than the box wherever the box ends, mid-word,
# so a test asking whether a message names a file
# would be asking it of `absent.tom` and `l` on separate lines.
# The command line keeps its formatting; only the tests read it plain.
# Set here rather than in a test:
# Typer reads this once, when it is first imported.
os.environ.setdefault("TYPER_USE_RICH", "0")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--regenerate-snapshots",
        action="store_true",
        help="overwrite the committed snapshots with current output",
    )


@pytest.fixture
def regenerate_snapshots(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--regenerate-snapshots"))


@pytest.fixture(autouse=True)
def _forget_credentials() -> None:
    """`_credentials` is worked out once per process, and a test is not a process.

    Two tests that set up different credentials would otherwise get whichever
    ran first, in whichever order the suite happened to run them.
    """
    from eta_publish.fetch import _sign_in

    _sign_in.cache_clear()
