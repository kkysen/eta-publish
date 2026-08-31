"""The top of the document, shaped the way the real report is.

In the real doc `Header` is an `h2` while the body sections are `h1`,
and between them sit the headline,
a hero image with caption and credit, and an addendum.
A scan that runs "until the next heading of the same or higher level"
swallows all of it.
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
    """A paragraph holding only an image has no text,
    so a front-matter scan that overruns drops it without anything to warn about."""
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
    """If the headline is not TITLE-styled,
    it matches `Key: value` and is filed as metadata,
    which `title` reports as a fallback.
    What must not also happen is the image after it disappearing without a word,
    which is what a scan that runs to the next same-or-higher heading does."""
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


def test_scaffolding_before_the_header_does_not_hide_it() -> None:
    """The real doc opens with a `Draft 2` line before its `Header` heading.
    Bailing on the first text meant no front matter was found at all,
    and `URL:` and the rest landed in the body as prose."""
    doc = parse(
        {
            "title": "SAS West Feasibility Response",
            "body": {
                "content": [
                    para("Draft 2"),
                    para("Header", "HEADING_2"),
                    para("URL: /reports/digging-out-deep-hole-sas-west"),
                    para("Short: A 125 St subway should be a slam dunk."),
                    para("The Real Headline", "TITLE"),
                    para("The Elephants in the Room", "HEADING_1"),
                ]
            },
        }
    )
    assert doc.meta["url"] == "/reports/digging-out-deep-hole-sas-west"
    assert doc.meta["short"] == "A 125 St subway should be a slam dunk."
    assert doc.title == "The Real Headline"


def test_dropped_scaffolding_is_reported() -> None:
    """It is production notes rather than the report, so dropping it is right,
    but it must not leave silently."""
    doc = parse(
        {
            "title": "x",
            "body": {
                "content": [
                    para("Draft 2"),
                    para("Header", "HEADING_2"),
                    para("URL: /reports/x"),
                    para("Headline", "TITLE"),
                ]
            },
        }
    )
    assert any("Draft 2" in w for w in doc.warnings)


def test_a_document_with_no_header_section_is_left_intact() -> None:
    """The preamble scan must not eat a whole document a paragraph at a time
    when there is no `Header` heading to find."""
    doc = parse(
        {
            "title": "x",
            "body": {
                "content": [para("Just a Headline", "TITLE"), para("Body."), para("More body.")]
            },
        }
    )
    assert len([b for b in doc.blocks if isinstance(b, Paragraph)]) == 2
    assert doc.meta == {}
    assert any("no front matter found" in w for w in doc.warnings)


def test_a_headline_before_the_header_stops_the_search() -> None:
    """Past the headline the report has started,
    so there is no header to look for and nothing may be consumed."""
    doc = parse(
        {
            "title": "x",
            "body": {
                "content": [
                    para("Headline", "TITLE"),
                    para("Body."),
                    para("Header", "HEADING_2"),
                    para("URL: /reports/x"),
                ]
            },
        }
    )
    assert doc.meta == {}
    assert len(doc.blocks) == 3


def test_contributors_are_sorted_by_surname() -> None:
    """etany.org credits contributors alphabetically,
    and the field they are typed into is in whatever order people were added."""
    doc = Document(meta={"public contributors": "Khyber Sen, Alon Levy, Robert Hale"})
    assert doc.contributors == ["Robert Hale", "Alon Levy", "Khyber Sen"]


def test_a_one_word_name_sorts_on_itself() -> None:
    doc = Document(meta={"public contributors": "Zoe, Alon Levy"})
    assert doc.contributors == ["Alon Levy", "Zoe"]


def test_the_date_is_written_out() -> None:
    """etany.org writes the month out; a Docs chip renders it short."""
    assert Document(meta={"final due date": "Aug 19, 2026"}).dateline == "August 19, 2026"


def test_a_day_is_not_padded() -> None:
    assert Document(meta={"final due date": "Aug 1, 2026"}).dateline == "August 1, 2026"


def test_a_date_already_written_out_is_left_alone() -> None:
    assert Document(meta={"final due date": "August 19, 2026"}).dateline == "August 19, 2026"


def test_something_that_is_not_a_date_is_published_as_written() -> None:
    """Guessing would be worse than showing what the header block says."""
    assert Document(meta={"final due date": "when it is ready"}).dateline == "when it is ready"


def test_no_date_is_still_no_dateline() -> None:
    assert Document().dateline == ""
