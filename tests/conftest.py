import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--regenerate-snapshots",
        action="store_true",
        help="overwrite the committed snapshots with current output",
    )


@pytest.fixture
def regenerate_snapshots(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--regenerate-snapshots"))
