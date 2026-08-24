import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--regenerate-golden",
        action="store_true",
        help="overwrite the committed golden files with current output",
    )


@pytest.fixture
def regenerate_golden(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--regenerate-golden"))
