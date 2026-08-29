"""Conventions found in the real SAS West document.

Everything here was read off the actual doc and checked against the
published page, rather than guessed from the fixture.
"""

import pytest

from eta_publish.docs_json import JsonObject
from eta_publish.emit.html import HtmlEmitter
from eta_publish.emit.typst import TypstEmitter
from eta_publish.nodes import Document, Figure, Heading, Inline, Paragraph, Text
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


def build(content: list[JsonObject], alt: str = "", crop: JsonObject | None = None) -> Document:
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
                            "imageProperties": {
                                "contentUri": "https://x.invalid/1",
                                "cropProperties": crop or {},
                            },
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
    from eta_publish.emit.html import report_page

    doc = build(
        [
            para("Header", "HEADING_2"),
            para("SEO Description (300 char limit): Cheaper and shallower."),
            para("Headline", "TITLE"),
        ]
    )
    assert 'content="Cheaper and shallower."' in report_page(doc)


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


# ---- found by running against the real document ---------------------


def test_a_qualified_source_line_is_still_editorial() -> None:
    """The real report writes `Source:`, `Uncropped Source:`, and
    `[Image Source](...)`. All three appear zero times on the published
    page, against 26 occurrences of `Credit:`."""
    for label in ("Source:", "Uncropped Source:", "Cropped Source:"):
        doc = build(
            [
                para("Header", "HEADING_2"),
                para("URL: /reports/x"),
                para("Headline", "TITLE"),
                para(f"{label} sas-west-036.jpg"),
                image(),
                para("A caption."),
            ]
        )
        figure = next(b for b in doc.blocks if isinstance(b, Figure))
        assert label in text_of(figure.source), label
        assert not [b for b in doc.blocks if isinstance(b, Paragraph)], label
        assert label not in HtmlEmitter().emit(doc), label


def test_an_image_styled_as_a_heading_becomes_a_figure() -> None:
    """The real doc has one, from inserting an image while a heading style
    was active. Treated as a heading it produced an empty one, whose anchor
    is a published URL, and buried the image inside it."""
    doc = build(
        [
            para("Header", "HEADING_2"),
            para("URL: /reports/x"),
            para("Headline", "TITLE"),
            para("Tail Tracks", "HEADING_2"),
            {
                "paragraph": {
                    "paragraphStyle": {"namedStyleType": "HEADING_3"},
                    "elements": [{"inlineObjectElement": {"inlineObjectId": "io.1"}}],
                }
            },
        ]
    )
    assert [b.anchor for b in doc.blocks if isinstance(b, Heading)] == ["tail-tracks"]
    assert len([b for b in doc.blocks if isinstance(b, Figure)]) == 1
    assert any("styled as a heading" in w for w in doc.warnings)


def test_unfinished_text_is_reported() -> None:
    """The real doc contains `TODO insert PSD image, maybe JFK AirTrain?`,
    which the human publisher removed by hand. Nothing removes it here, so
    the least the build can do is say it is there."""
    doc = build(
        [
            para("Header", "HEADING_2"),
            para("URL: /reports/x"),
            para("Headline", "TITLE"),
            para("TODO insert PSD image, maybe JFK AirTrain?"),
        ]
    )
    assert any("unfinished text" in w for w in doc.warnings)


def test_chart_asset_placeholders_are_editorial() -> None:
    """`SVG:` and `PNG:` name a chart file for whoever assembles the page.
    The published report carries real download links instead."""
    doc = build(
        [
            para("Header", "HEADING_2"),
            para("URL: /reports/x"),
            para("Headline", "TITLE"),
            image(),
            para("Station length as a percentage of platform length."),
            para("SVG: station-length.svg"),
        ]
    )
    assert "SVG:" not in HtmlEmitter().emit(doc)
    assert not [b for b in doc.blocks if isinstance(b, Paragraph)]


def test_an_undescribed_image_is_reported() -> None:
    doc = build(
        [
            para("Header", "HEADING_2"),
            para("URL: /reports/x"),
            para("Headline", "TITLE"),
            image(),
        ]
    )
    assert any("no alt text and no caption" in w for w in doc.warnings)


def test_a_soft_line_break_separates_a_caption_from_its_credit() -> None:
    """The hero image's caption and credit are one paragraph split by
    Shift+Enter, which Docs encodes as a vertical tab inside the run."""
    doc = build(
        [
            para("Header", "HEADING_2"),
            para("URL: /reports/x"),
            para("Headline", "TITLE"),
            image(),
            para("Composite image of the station diagram.\v\vCredit: MTA, ETA"),
        ]
    )
    figure = next(b for b in doc.blocks if isinstance(b, Figure))
    assert text_of(figure.caption) == "Composite image of the station diagram."
    assert text_of(figure.credit) == "Credit: MTA, ETA"


def test_soft_line_breaks_do_not_reach_the_output_as_control_characters() -> None:
    doc = build(
        [
            para("Header", "HEADING_2"),
            para("URL: /reports/x"),
            para("Headline", "TITLE"),
            para("One line.\vAnother line."),
        ]
    )
    for emitted in (HtmlEmitter().emit(doc), TypstEmitter().emit(doc)):
        assert "\v" not in emitted
    assert "One line.<br>Another line." in HtmlEmitter().emit(doc)


def _svg_doc(mime: str = "image/svg+xml", uri: str = "https://drive.google.com/open?id=ABC123"):
    return build(
        [
            para("Header", "HEADING_2"),
            para("URL: /reports/x"),
            para("Headline", "TITLE"),
            image(),
            {
                "paragraph": {
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "elements": [
                        {"textRun": {"content": "SVG: ", "textStyle": {}}},
                        {
                            "richLink": {
                                "richLinkProperties": {
                                    "title": "chart.svg",
                                    "uri": uri,
                                    "mimeType": mime,
                                }
                            }
                        },
                    ],
                }
            },
            para("A bar graph comparing costs."),
        ]
    )


def test_a_linked_svg_becomes_the_figure_file() -> None:
    """Docs cannot place an SVG, so a chart is pasted as a raster and the
    real file linked beside it. Every output here can show the vector."""
    figure = next(b for b in _svg_doc().blocks if isinstance(b, Figure))
    assert figure.image.vector is not None
    assert figure.image.vector.file_id == "ABC123"
    assert figure.image.vector.filename.endswith(".svg")


def test_the_svg_line_is_still_not_published() -> None:
    doc = _svg_doc()
    assert "SVG:" not in HtmlEmitter().emit(doc)
    assert "drive.google.com" not in HtmlEmitter().emit(doc)


def test_a_source_line_that_links_no_vector_leaves_the_raster() -> None:
    """`SVG: TODO`, which the real report also contains, is a note."""
    doc = build(
        [
            para("Header", "HEADING_2"),
            para("URL: /reports/x"),
            para("Headline", "TITLE"),
            image(),
            para("SVG: TODO"),
        ]
    )
    figure = next(b for b in doc.blocks if isinstance(b, Figure))
    assert figure.image.vector is None


def test_a_non_vector_link_is_not_mistaken_for_one() -> None:
    figure = next(b for b in _svg_doc(mime="image/png").blocks if isinstance(b, Figure))
    assert figure.image.vector is None


def test_a_cropped_figure_keeps_its_raster() -> None:
    """The crop is expressed in pixels of the rasterized copy, so it cannot
    be carried over to the vector."""
    doc = build(
        [
            para("Header", "HEADING_2"),
            para("URL: /reports/x"),
            para("Headline", "TITLE"),
            image(),
            para("SVG: chart.svg"),
        ],
        crop={"offsetLeft": 0.1},
    )
    figure = next(b for b in doc.blocks if isinstance(b, Figure))
    assert figure.image.crop.trims


# ---- italicized section names are links ------------------------------


def runs(*pieces: tuple[str, bool]) -> JsonObject:
    """A paragraph of text runs, each either italic or not."""
    return {
        "paragraph": {
            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
            "elements": [
                {"textRun": {"content": text, "textStyle": {"italic": True} if italic else {}}}
                for text, italic in pieces
            ],
        }
    }


def linked(doc: Document) -> list[tuple[str, str | None]]:
    para = next(b for b in doc.blocks if isinstance(b, Paragraph))
    return [(t.text, t.href) for t in para.content if isinstance(t, Text)]


def test_an_italicized_section_name_becomes_a_link() -> None:
    """Docs cannot link to a heading in the same document, so the report
    italicizes the section's name and means a link by it."""
    doc = parse(
        {
            "title": "A report",
            "body": {
                "content": [
                    para("Station Depth", "HEADING_2"),
                    runs(("See ", False), ("Station Depth", True), (" for more.\n", False)),
                ]
            },
            "footnotes": {},
            "lists": {},
        }
    )
    assert linked(doc) == [
        ("See ", None),
        ("Station Depth", "#station-depth"),
        (" for more.", None),
    ]


def test_the_italics_come_off_once_it_is_a_link() -> None:
    doc = parse(
        {
            "title": "A report",
            "body": {
                "content": [
                    para("Fire Code", "HEADING_2"),
                    runs(("Fire Code", True)),
                ]
            },
            "footnotes": {},
            "lists": {},
        }
    )
    para_node = next(b for b in doc.blocks if isinstance(b, Paragraph))
    assert [t.italic for t in para_node.content if isinstance(t, Text)] == [False]


def test_a_reference_can_precede_the_section_it_names() -> None:
    """The report links to `Station Depth` long before reaching it."""
    doc = parse(
        {
            "title": "A report",
            "body": {
                "content": [
                    runs(("as suggested in ", False), ("Station Depth", True)),
                    para("Station Depth", "HEADING_2"),
                ]
            },
            "footnotes": {},
            "lists": {},
        }
    )
    assert linked(doc)[1] == ("Station Depth", "#station-depth")


def test_a_name_split_across_runs_still_matches() -> None:
    """Docs splits a run wherever styling changes, mid-name included."""
    doc = parse(
        {
            "title": "A report",
            "body": {
                "content": [
                    para("Tail Tracks", "HEADING_2"),
                    runs(("Tail ", True), ("Tracks", True)),
                ]
            },
            "footnotes": {},
            "lists": {},
        }
    )
    assert [href for _, href in linked(doc)] == ["#tail-tracks", "#tail-tracks"]


def test_case_and_spacing_are_forgiven() -> None:
    doc = parse(
        {
            "title": "A report",
            "body": {
                "content": [
                    para("Ruling Grade", "HEADING_2"),
                    runs(("ruling  grade", True)),
                ]
            },
            "footnotes": {},
            "lists": {},
        }
    )
    assert linked(doc) == [("ruling  grade", "#ruling-grade")]


def test_italics_that_name_no_section_stay_italics() -> None:
    """The real report italicizes `and` and `tens of billions` for emphasis."""
    doc = parse(
        {
            "title": "A report",
            "body": {
                "content": [
                    para("Fire Code", "HEADING_2"),
                    runs(("tens of billions", True)),
                ]
            },
            "footnotes": {},
            "lists": {},
        }
    )
    para_node = next(b for b in doc.blocks if isinstance(b, Paragraph))
    text = next(t for t in para_node.content if isinstance(t, Text))
    assert text.italic and text.href is None


def test_an_italicized_link_is_left_alone() -> None:
    """Already a link, and to somewhere the author chose."""
    doc = parse(
        {
            "title": "A report",
            "body": {
                "content": [
                    para("Fire Code", "HEADING_2"),
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                            "elements": [
                                {
                                    "textRun": {
                                        "content": "Fire Code",
                                        "textStyle": {
                                            "italic": True,
                                            "link": {"url": "https://nfpa.test/130"},
                                        },
                                    }
                                }
                            ],
                        }
                    },
                ]
            },
            "footnotes": {},
            "lists": {},
        }
    )
    assert linked(doc) == [("Fire Code", "https://nfpa.test/130")]


def test_a_section_named_before_its_colon_still_matches() -> None:
    """`Appendix A: Freedom Tunnel` is referred to as `Appendix A`, which is
    how the live page links it."""
    doc = parse(
        {
            "title": "A report",
            "body": {
                "content": [
                    para("Appendix A: Freedom Tunnel", "HEADING_2"),
                    runs(("see ", False), ("Appendix A", True)),
                ]
            },
            "footnotes": {},
            "lists": {},
        }
    )
    assert linked(doc)[1] == ("Appendix A", "#appendix-a-freedom-tunnel")


def test_the_full_name_wins_over_a_shortened_one() -> None:
    """A heading actually called `Appendix A` keeps its own anchor."""
    doc = parse(
        {
            "title": "A report",
            "body": {
                "content": [
                    para("Appendix A", "HEADING_2"),
                    para("Appendix A: Freedom Tunnel", "HEADING_2"),
                    runs(("Appendix A", True)),
                ]
            },
            "footnotes": {},
            "lists": {},
        }
    )
    assert linked(doc) == [("Appendix A", "#appendix-a")]
