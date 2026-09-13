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
def _forget_credentials(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """`_credentials` is worked out once per process, and a test is not a process.

    Two tests that set up different credentials would otherwise get whichever
    ran first, in whichever order the suite happened to run them.

    Opening a browser is then refused outright, for every test but a `network`
    one. `_sign_in` ends at `InstalledAppFlow.run_local_server`, which opens a
    browser and waits for a redirect that is never coming: a test that reaches
    it does not fail, it hangs, and the suite hangs with it. A test reaching
    that is one that missed something it meant to stub, so say which one and
    say it immediately.

    Refused there rather than at `_sign_in`, which has a branch that reads
    credentials the environment names and is worth a test of its own.
    """
    import eta_publish.fetch as fetch

    fetch._sign_in.cache_clear()
    if "network" in request.keywords:
        return

    from google_auth_oauthlib.flow import InstalledAppFlow

    def refused(self: object, *args: object, **kwargs: object) -> object:
        raise AssertionError(
            f"{request.node.name} would open a browser to sign in to Google; "
            "stub what it calls, or mark it `network`"
        )

    monkeypatch.setattr(InstalledAppFlow, "run_local_server", refused)


@pytest.fixture(autouse=True)
def _fresh_lookup_cache(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A cache of the person's own builds is not a fixture.

    `archive.to_ask` skips a source looked up in the last week and not found, and
    the file saying which those are lives in the person's cache directory. Left
    alone, a suite run after a real build would be told to skip the very lookups
    the test set up an answer for, and would pass or fail depending on what the
    machine happened to have done that week.
    """
    from eta_publish.archive import ARCHIVE_CACHE

    monkeypatch.setenv(
        ARCHIVE_CACHE, str(tmp_path_factory.mktemp("cache") / "archive-lookups.json")
    )
