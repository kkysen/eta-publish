"""Inline parsing is implemented; block assembly is not yet."""

import json
from pathlib import Path

import pytest

from eta_publish.nodes import FootnoteRef, Image, Inline, Text
from eta_publish.parse import Parser

FIXTURE = json.loads((Path(__file__).parent / "fixture-doc.json").read_text())


def _para(parser: Parser, text: str) -> list[Inline]:
    """Find the fixture paragraph containing `text` and parse its inlines."""
    for item in FIXTURE["body"]["content"]:
        para = item.get("paragraph")
        if para and text in json.dumps(para):
            return parser.inlines(para)
    raise AssertionError(f"no fixture paragraph contains {text!r}")


def test_styles_and_links_survive():
    inlines = _para(Parser(FIXTURE), "7.7 billion")
    bold = [i for i in inlines if isinstance(i, Text) and i.bold]
    assert [b.text for b in bold] == ["$7.7 billion"]
    linked = [i for i in inlines if isinstance(i, Text) and i.href]
    assert linked[0].href == "https://www.mta.info/document/196361"


def test_footnotes_are_numbered_in_document_order():
    parser = Parser(FIXTURE)
    first = [i for i in _para(parser, "7.7 billion") if isinstance(i, FootnoteRef)]
    second = [i for i in _para(parser, "100 ft deep") if isinstance(i, FootnoteRef)]
    assert (first[0].number, second[0].number) == (1, 2)


def test_a_repeated_reference_keeps_its_number():
    parser = Parser(FIXTURE)
    a = parser._footnote_ref({"footnoteId": "fn.a"})
    again = parser._footnote_ref({"footnoteId": "fn.a"})
    assert a.number == again.number


def test_image_filename_comes_from_the_object_id():
    parser = Parser(FIXTURE)
    image = parser._image({"inlineObjectId": "io.1"})
    assert isinstance(image, Image)
    assert image.filename.startswith("img-")
    assert image.alt == "SAS West alignment map"


def test_block_assembly_is_not_implemented_yet():
    with pytest.raises(NotImplementedError):
        Parser(FIXTURE).parse()
