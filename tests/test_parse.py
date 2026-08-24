"""Parsing the fixture document into a tree."""

import json
from pathlib import Path

import pytest

from eta_publish.docs_json import JsonObject
from eta_publish.nodes import Document, Figure, Heading, Inline, List, ListKind, Paragraph, Text
from eta_publish.parse import Parser, parse

FIXTURE = json.loads((Path(__file__).parent / "fixture-doc.json").read_text())


@pytest.fixture
def doc() -> Document:
    return parse(FIXTURE)


def _text(content: list[Inline]) -> str:
    return "".join(i.text for i in content if isinstance(i, Text))


def _para(parser: Parser, text: str) -> list[Inline]:
    """Find the fixture paragraph containing `text` and parse its inlines."""
    for item in FIXTURE["body"]["content"]:
        para = item.get("paragraph")
        if para and text in json.dumps(para):
            return parser.inlines(para)
    raise AssertionError(f"no fixture paragraph contains {text!r}")


# ---- inline --------------------------------------------------------


def test_styles_and_links_survive() -> None:
    inlines = _para(Parser(FIXTURE), "7.7 billion")
    assert [i.text for i in inlines if isinstance(i, Text) and i.bold] == ["$7.7 billion"]
    linked = [i for i in inlines if isinstance(i, Text) and i.href]
    assert linked[0].href == "https://www.mta.info/document/196361"


def test_a_repeated_reference_keeps_its_number() -> None:
    parser = Parser(FIXTURE)
    assert parser._footnote_ref({"footnoteId": "fn.a"}).number == 1
    assert parser._footnote_ref({"footnoteId": "fn.a"}).number == 1


# ---- document ------------------------------------------------------


def test_the_headline_comes_from_the_body_not_the_filename(doc: Document) -> None:
    """The Drive filename is a working name. The real doc is called
    `SAS West Feasibility Response`, which is not what publishes."""
    assert doc.title == "Digging Out of a Very Deep Hole: Saving Billions on 125th Street"
    assert doc.title != FIXTURE["title"]


def test_a_title_containing_a_colon_is_not_eaten_as_front_matter(doc: Document) -> None:
    """`Digging Out...: Saving Billions...` matches `Key: value`, so a
    front-matter scan that does not stop at TITLE swallows the headline."""
    assert "digging out of a very deep hole" not in doc.meta
    assert doc.meta["url"] == "/reports/digging-out-deep-hole-sas-west"


def test_an_unrecognized_header_key_is_kept_and_does_not_end_the_scan(doc: Document) -> None:
    """The real doc has an `MTA SAS West Feasibility Study:` line, which a
    whitelist would have leaked into the body."""
    assert doc.meta["mta sas west feasibility study"] == "https://www.mta.info/document/196361"
    assert doc.meta["seo description"] == "Cheaper, shallower, faster."


def test_the_fixture_parses_without_warnings(doc: Document) -> None:
    assert doc.warnings == []


# ---- blocks --------------------------------------------------------


def test_block_structure(doc: Document) -> None:
    assert [type(b).__name__ for b in doc.blocks] == [
        "Heading",
        "Paragraph",
        "Figure",
        "Paragraph",
        "Heading",
        "List",
        "Paragraph",
    ]


def test_headings_carry_levels_and_anchors(doc: Document) -> None:
    headings = [b for b in doc.blocks if isinstance(b, Heading)]
    assert [(h.level, h.anchor) for h in headings] == [
        (2, "the-elephants-in-the-room"),
        (3, "ground-conditions"),
    ]


def test_a_figure_absorbs_its_source_caption_and_credit(doc: Document) -> None:
    figure = next(b for b in doc.blocks if isinstance(b, Figure))
    assert _text(figure.source) == "Source: sas-west-036.jpg"
    assert _text(figure.caption) == "The SAS West and Phase 2 alignments."
    assert _text(figure.credit) == "Credit: MTA"
    assert figure.image.alt == "SAS West alignment map"


def test_a_short_paragraph_after_a_figure_stays_a_paragraph(doc: Document) -> None:
    """Folding captions by length would swallow body text, and a report with
    54 figures has many short paragraphs following one."""
    after = doc.blocks[3]
    assert isinstance(after, Paragraph)
    assert _text(after.content) == "That is a lot of money."


def test_nested_lists_are_rebuilt_from_flat_nesting_levels(doc: Document) -> None:
    node = next(b for b in doc.blocks if isinstance(b, List))
    assert node.kind is ListKind.BULLET
    assert [_text(i.content) for i in node.items] == ["First point", "Second point"]
    assert [_text(c.content) for c in node.items[0].children] == ["Nested point"]


# ---- footnotes -----------------------------------------------------


def test_footnotes_are_numbered_in_reference_order(doc: Document) -> None:
    assert [(f.number, f.footnote_id) for f in doc.footnotes] == [(1, "fn.a"), (2, "fn.b")]


def test_footnote_bodies_are_parsed_as_blocks(doc: Document) -> None:
    body = doc.footnotes[0].content[0]
    assert isinstance(body, Paragraph)
    assert _text(body.content) == "Inflation-adjusted from the 2024 capital plan."


def test_an_unreferenced_footnote_is_reported_rather_than_numbered() -> None:
    doc_json = json.loads(json.dumps(FIXTURE))
    orphan: JsonObject = {"content": []}
    doc_json["footnotes"]["fn.orphan"] = orphan
    doc = parse(doc_json)
    assert [f.footnote_id for f in doc.footnotes] == ["fn.a", "fn.b"]
    assert any("fn.orphan" in w for w in doc.warnings)


# ---- images --------------------------------------------------------


def test_images_are_collected_with_stable_names(doc: Document) -> None:
    assert [i.object_id for i in doc.images] == ["io.1"]
    assert doc.images[0].filename.startswith("img-")


def test_a_source_line_with_no_image_is_reported_not_dropped_silently() -> None:
    doc_json = json.loads(json.dumps(FIXTURE))
    doc_json["body"]["content"].append(
        {
            "paragraph": {
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "elements": [{"textRun": {"content": "Source: orphan.jpg\n", "textStyle": {}}}],
            }
        }
    )
    doc = parse(doc_json)
    assert any("orphan.jpg" in w for w in doc.warnings)
