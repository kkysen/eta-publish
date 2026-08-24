"""The top of the document, shaped the way the real report is.

In the real doc `Header` is an `h2` while the body sections are `h1`, and
between them sit the headline, a hero image with caption and credit, and an
addendum. A scan that runs "until the next heading of the same or higher
level" swallows all of it.
"""

import pytest

from eta_publish.docs_json import JsonObject
from eta_publish.nodes import Document, Figure, Inline, Paragraph, Text
from eta_publish.parse import parse


def _text(content: list[Inline]) -> str:
    return "".join(i.text for i in content if isinstance(i, Text))


def para(text: str, style: str = "NORMAL_TEXT") -> JsonObject:
    return {
        "paragraph": {
            "paragraphStyle": {"namedStyleType": style},
            "elements": [{"textRun": {"content": text + "\n", "textStyle": {}}}],
        }
    }


def image_para() -> JsonObject:
    return {
        "paragraph": {
            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
            "elements": [{"inlineObjectElement": {"inlineObjectId": "io.hero"}}],
        }
    }


REAL_SHAPE: JsonObject = {
    "title": "SAS West Feasibility Response",
    "body": {
        "content": [
            para("Header", "HEADING_2"),  # deeper than the body sections
            para("Project Manager: Khyber Sen"),
            para("URL: /reports/digging-out-deep-hole-sas-west"),
            para("MTA SAS West Feasibility Study: https://www.mta.info/document/196361"),
            para("Digging Out of a Very Deep Hole: Saving Billions on 125th Street", "TITLE"),
            image_para(),
            para("Composite image of the MTA's station diagram."),
            para("Credit: MTA, ETA (Blair Lorenzo)"),
            para("Addendum: clarifying text was added on August 21, 2026."),
            para("The Elephants in the Room", "HEADING_1"),
            para("On paper, this should be a slam dunk."),
        ]
    },
    "inlineObjects": {
        "io.hero": {
            "inlineObjectProperties": {
                "embeddedObject": {
                    "description": "Composite of the station diagram",
                    "imageProperties": {"contentUri": "https://example.invalid/hero"},
                }
            }
        }
    },
    "footnotes": {},
    "lists": {},
}


@pytest.fixture
def doc() -> Document:
    return parse(REAL_SHAPE)


def test_the_header_section_ends_at_the_headline(doc: Document) -> None:
    assert set(doc.meta) == {"project manager", "url", "mta sas west feasibility study"}
    assert "addendum" not in doc.meta


def test_the_headline_is_the_title(doc: Document) -> None:
    assert doc.title == "Digging Out of a Very Deep Hole: Saving Billions on 125th Street"


def test_the_hero_image_survives(doc: Document) -> None:
    """A paragraph holding only an image has no text, so a front-matter scan
    that overruns drops it without anything to warn about."""
    figures = [b for b in doc.blocks if isinstance(b, Figure)]
    assert len(figures) == 1
    assert figures[0].image.object_id == "io.hero"
    assert [i.object_id for i in doc.images] == ["io.hero"]


def test_the_hero_caption_and_credit_survive(doc: Document) -> None:
    figure = next(b for b in doc.blocks if isinstance(b, Figure))
    assert _text(figure.caption) == "Composite image of the MTA's station diagram."
    assert _text(figure.credit) == "Credit: MTA, ETA (Blair Lorenzo)"


def test_the_addendum_stays_body_text(doc: Document) -> None:
    """It matches `Key: value`, so an overrunning scan files it as metadata,
    but it is prose on the published page."""
    paragraphs = [
        "".join(i.text for i in b.content if isinstance(i, Text))
        for b in doc.blocks
        if isinstance(b, Paragraph)
    ]
    assert "Addendum: clarifying text was added on August 21, 2026." in paragraphs


def test_prose_ends_the_header_section_even_without_a_headline() -> None:
    doc = parse(
        {
            "title": "x",
            "body": {
                "content": [
                    para("Header", "HEADING_2"),
                    para("URL: /reports/x"),
                    para("This is body prose, not a key."),
                ]
            },
        }
    )
    assert set(doc.meta) == {"url"}
    assert len(doc.blocks) == 1


def test_an_unstyled_headline_still_does_not_swallow_the_hero_image() -> None:
    """If the headline is not TITLE-styled, it matches `Key: value` and is
    filed as metadata, which `title` reports as a fallback. What must not
    also happen is the image after it disappearing without a word, which is
    what a scan that runs to the next same-or-higher heading does."""
    unstyled = {
        **REAL_SHAPE,
        "body": {
            "content": [
                para("Header", "HEADING_2"),
                para("URL: /reports/digging-out-deep-hole-sas-west"),
                para("Digging Out of a Very Deep Hole: Saving Billions on 125th Street"),
                image_para(),
                para("The Elephants in the Room", "HEADING_1"),
            ]
        },
    }
    doc = parse(unstyled)
    assert [i.object_id for i in doc.images] == ["io.hero"]
    assert any("TITLE-styled" in w for w in doc.warnings)
