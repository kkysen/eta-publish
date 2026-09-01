"""What a report has to have before it is published."""

import json

import pytest
from paths import FIXTURE_DIR

from eta_publish.checks import REQUIRED_FIELDS, check
from eta_publish.nodes import Document
from eta_publish.parse import parse

FIXTURE = json.loads((FIXTURE_DIR / "doc.json").read_text())


@pytest.fixture
def doc() -> Document:
    parsed = parse(FIXTURE)
    parsed.warnings.clear()
    parsed.meta = {field: "something" for field in REQUIRED_FIELDS}
    return parsed


def test_a_complete_header_is_not_warned_about(doc: Document) -> None:
    check(doc)
    assert doc.warnings == []


def test_a_missing_field_is_named(doc: Document) -> None:
    """By name, rather than as a list of nine:
    a warning naming one line is a line to go and add."""
    del doc.meta["discussion channel"]
    check(doc)
    assert doc.warnings == ["the `Header` section has no `Discussion Channel:` line"]


def test_seo_is_spelled_the_way_the_document_spells_it(doc: Document) -> None:
    del doc.meta["seo description"]
    check(doc)
    assert "`SEO Description:`" in doc.warnings[0]


def test_an_empty_field_is_not_a_filled_one(doc: Document) -> None:
    doc.meta["url"] = "   "
    check(doc)
    assert doc.warnings == ["the `Header` section leaves `URL:` empty"]


def test_an_empty_private_list_is_an_answer(doc: Document) -> None:
    """A report with nobody uncredited has an empty line, and that is the answer."""
    doc.meta["private contributors"] = ""
    check(doc)
    assert doc.warnings == []


def test_a_document_with_no_header_is_left_to_the_parser(doc: Document) -> None:
    """`parse` has already said so; nine more warnings would bury it."""
    doc.meta.clear()
    check(doc)
    assert doc.warnings == []
