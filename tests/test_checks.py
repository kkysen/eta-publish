"""What a report has to have before it is published."""

import json
from dataclasses import replace

import pytest
from paths import FIXTURE_DIR

from eta_publish.checks import REQUIRED_FIELDS, check
from eta_publish.nodes import Document, Figure, Image, Text
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


def test_an_seo_description_over_the_limit_shows_what_is_cut(doc: Document) -> None:
    """Which words are lost is the thing to fix,
    and a count of characters over does not say which they are."""
    doc.meta["seo description"] = "x" * 300 + " and this is lost"
    check(doc)
    assert doc.warnings == [
        "`SEO Description:` is 317 characters, over the 300 a search result shows:\n> "
        + "x" * 300
        + "~~ and this is lost~~"
    ]


def test_an_seo_description_at_the_limit_is_fine(doc: Document) -> None:
    doc.meta["seo description"] = "x" * 300
    check(doc)
    assert doc.warnings == []


def figure(*, caption: bool = True, credit: bool = True, named: bool = True) -> Figure:
    return Figure(
        image=Image(object_id="io.9", filename="a-diagram", named=named),
        caption=[Text(text="What it shows.")] if caption else [],
        credit=[Text(text="Credit: MTA")] if credit else [],
    )


def test_a_figure_with_both_is_not_warned_about(doc: Document) -> None:
    doc.blocks = [figure()]
    check(doc)
    assert doc.warnings == []


def test_an_uncaptioned_figure_is_named_by_its_file(doc: Document) -> None:
    """The Docs object id is not something the document shows anybody."""
    doc.blocks = [figure(caption=False)]
    check(doc)
    assert doc.warnings == ["the image `a-diagram` has no caption"]


def test_an_unattributed_figure_is_flagged(doc: Document) -> None:
    """These reports run other people's diagrams on nearly every page."""
    doc.blocks = [figure(credit=False)]
    check(doc)
    assert doc.warnings == ["the image `a-diagram` has no `Credit:` line"]


def test_a_figure_missing_both_says_both(doc: Document) -> None:
    doc.blocks = [figure(caption=False, credit=False)]
    check(doc)
    assert len(doc.warnings) == 2


def test_an_unfinished_header_line_is_flagged(doc: Document) -> None:
    """The body walk never sees the header: it is consumed before that walk begins."""
    doc.meta["short"] = "TODO write this"
    check(doc)
    assert doc.warnings == ["`Short:` is still marked unfinished"]


def test_open_suggestions_are_flagged(doc: Document) -> None:
    """A build resolves them away, so what publishes looks finished and is not."""
    doc.open_suggestions = 3
    check(doc)
    assert doc.warnings == [
        "3 suggestions still open on this tab; "
        "the build publishes the document without them, as it reads today"
    ]


def test_one_open_comment_is_not_called_comments(doc: Document) -> None:
    doc.open_comments = 1
    check(doc)
    assert doc.warnings == ["1 comment thread still open on this tab"]


def test_a_document_under_no_review_says_nothing(doc: Document) -> None:
    check(doc)
    assert doc.warnings == []


def test_an_unnamed_image_is_flagged(doc: Document) -> None:
    """Without a `Source:` line the published URL is a hash of a Docs object id."""
    doc.blocks = [figure(named=False)]
    check(doc)
    assert doc.warnings == [
        "1 image is unnamed, so each publishes under a hash; "
        "give each a `Source:` line naming its file:\n- `a-diagram`: What it shows."
    ]


def test_an_unnamed_image_falls_back_to_its_alt_text(doc: Document) -> None:
    """A picture with no caption still has to be told apart from the others."""
    bare = figure(caption=False, named=False)
    bare.image = replace(bare.image, alt="A cross-section of the station box")
    doc.blocks = [bare]
    check(doc)
    listed = doc.warnings[-1].split("\n")[-1]
    assert listed == "- `a-diagram`: A cross-section of the station box"


def test_an_image_a_human_named_img_is_not_unnamed(doc: Document) -> None:
    """`img-` is what an unnamed image is called,
    and also a name a `Source:` line is free to give one."""
    named = figure()
    named.image = replace(named.image, filename="img-of-the-tunnel", named=True)
    doc.blocks = [named]
    check(doc)
    assert doc.warnings == []
