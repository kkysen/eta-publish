"""Conventions found in the real SAS West document.

Everything here was read off the actual doc and checked against the
published page, rather than guessed from the fixture.
"""

from __future__ import annotations

import pytest

from eta_publish.docs_json import JsonObject
from eta_publish.emit.html import HtmlEmitter
from eta_publish.emit.typst import TypstEmitter
from eta_publish.nodes import Document, Figure, Inline, Paragraph, Text
from eta_publish.parse import parse


def para(text: str, style: str = "NORMAL_TEXT") -> JsonObject:
    return {
        "paragraph": {
            "paragraphStyle": {"namedStyleType": style},
            "elements": [{"textRun": {"content": text + "\n", "textStyle": {}}}],
        }
    }


def image(object_id: str = "io.1") -> JsonObject:
    return {
        "paragraph": {
            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
            "elements": [{"inlineObjectElement": {"inlineObjectId": object_id}}],
        }
    }


def build(content: list[JsonObject], alt: str = "") -> Document:
    return parse(
        {
            "title": "SAS West Feasibility Response",
            "body": {"content": content},
            "footnotes": {},
            "lists": {},
            "inlineObjects": {
                "io.1": {
                    "inlineObjectProperties": {
                        "embeddedObject": {
                            "description": alt,
                            "imageProperties": {"contentUri": "https://x.invalid/1"},
                        }
                    }
                }
            },
        }
    )


def text_of(content: list[Inline]) -> str:
    return "".join(i.text for i in content if isinstance(i, Text))


# ---- `[Image Source](...)` -----------------------------------------

APPENDIX = [
    para("Header", "HEADING_2"),
    para("URL: /reports/x"),
    para("Headline", "TITLE"),
    image(),
    para("A photo inside the Freedom Tunnel, showing room for 4 tracks."),
    para("[Image Source](https://www.flickr.com/photo_download.gne?id=4490800374)"),
    para("[Credit: Logan Hicks](https://www.flickr.com/photos/loganhicks/4490800374/)"),
    para("The Freedom Tunnel was formerly the 4-track West Side Line."),
]


@pytest.fixture
def appendix() -> Document:
    return build(APPENDIX)


def test_image_source_lines_attach_to_the_figure(appendix: Document) -> None:
    """The doc writes `Source: <file>` before an image in the body and
    `[Image Source](<url>)` after the caption in the appendices. Both are
    editorial; neither appears on the published page."""
    figure = next(b for b in appendix.blocks if isinstance(b, Figure))
    assert "Image Source" in text_of(figure.source)
    assert text_of(figure.caption).startswith("A photo inside the Freedom Tunnel")
    assert "Credit: Logan Hicks" in text_of(figure.credit)


def test_image_source_does_not_become_a_paragraph(appendix: Document) -> None:
    paragraphs = [text_of(b.content) for b in appendix.blocks if isinstance(b, Paragraph)]
    assert paragraphs == ["The Freedom Tunnel was formerly the 4-track West Side Line."]


@pytest.mark.parametrize("emitter", [HtmlEmitter(), TypstEmitter()], ids=["html", "typst"])
def test_image_source_never_reaches_a_published_output(
    emitter: HtmlEmitter | TypstEmitter, appendix: Document
) -> None:
    """`Image Source` appears zero times on the live page."""
    out = emitter.emit(appendix)
    assert "Image Source" not in out
    assert "flickr.com/photo_download" not in out
    assert "Credit: Logan Hicks" in out


# ---- front matter keys ---------------------------------------------


def test_a_parenthetical_note_is_not_part_of_the_key() -> None:
    """The doc writes `SEO Description (300 char limit):`, and a lookup for
    `seo description` finds nothing unless the note is stripped."""
    doc = build(
        [
            para("Header", "HEADING_2"),
            para("SEO Description (300 char limit): Cheaper and shallower."),
            para("Headline", "TITLE"),
        ]
    )
    assert doc.meta["seo description"] == "Cheaper and shallower."


def test_the_description_reaches_the_preview() -> None:
    from eta_publish.emit.html import preview_page

    doc = build(
        [
            para("Header", "HEADING_2"),
            para("SEO Description (300 char limit): Cheaper and shallower."),
            para("Headline", "TITLE"),
        ]
    )
    assert 'content="Cheaper and shallower."' in preview_page(doc)


# ---- alt text -------------------------------------------------------


def test_the_caption_becomes_alt_text_when_docs_has_none(appendix: Document) -> None:
    """On the live page the caption appears twice: as the image's `alt` and
    as visible small text beneath it."""
    figure = next(b for b in appendix.blocks if isinstance(b, Figure))
    assert figure.image.alt == "A photo inside the Freedom Tunnel, showing room for 4 tracks."


def test_a_real_description_wins_over_the_caption() -> None:
    doc = build(APPENDIX, alt="Four tracks under Riverside Park")
    figure = next(b for b in doc.blocks if isinstance(b, Figure))
    assert figure.image.alt == "Four tracks under Riverside Park"
