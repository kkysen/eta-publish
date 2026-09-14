"""How a report is written, as distinct from what it says."""

from eta_publish.nodes import Document, Footnote, Paragraph, Text
from eta_publish.style import style


def written(*paragraphs: str) -> Document:
    """A document that says these paragraphs and nothing else."""
    return Document(blocks=[Paragraph(content=[Text(text=p)]) for p in paragraphs])


def cited(text: str) -> Document:
    """A document whose only words are a footnote's, which are somebody else's."""
    doc = Document()
    doc.footnotes = [
        Footnote(footnote_id="f1", number=1, content=[Paragraph(content=[Text(text=text)])])
    ]
    return doc


def warnings(doc: Document) -> list[str]:
    style(doc)
    return [str(w) for w in doc.warnings]


def test_one_space_after_a_sentence_is_not_warned_about() -> None:
    assert warnings(written("It is deep. It is also expensive.")) == []


def test_two_spaces_after_a_sentence_are_warned_about() -> None:
    found = warnings(written("It is deep.  It is also expensive."))
    assert len(found) == 1
    assert "1 space, not 2" in found[0]


def test_the_warning_shows_which_spaces_it_means() -> None:
    """The spaces themselves, drawn: quoted as spaces they are a space,
    in HTML and in the PDF alike, and the line reads as already correct."""
    found = warnings(written("It is deep.  It is also expensive."))
    assert "It is deep.\u00b7\u00b7It is also expensive." in found[0]


def test_a_closing_bracket_does_not_hide_the_gap() -> None:
    """`costs are given separately).  This` is how the real report writes one:
    the spaces come after the sentence, whatever closes the quote around it."""
    assert len(warnings(written("(costs are given separately.)  This is a Buy America cost."))) == 1


def test_three_spaces_are_counted_rather_than_rounded_to_two() -> None:
    found = warnings(written("It is deep.   It is expensive."))[0]
    assert "1 space, not 3" in found
    assert "deep.\u00b7\u00b7\u00b7It" in found


def test_two_spaces_mid_clause_are_a_different_warning() -> None:
    """`demand  requires` is a slipped finger rather than the typewriter habit,
    so it is said differently even though the characters are the same."""
    found = warnings(written("On such routes, demand  requires high frequency."))
    assert found == [
        "style: two words should be separated by 1 space, not 2: "
        "`On such routes, demand\u00b7\u00b7requires high frequency.`"
    ]


def test_indentation_is_neither_mistake() -> None:
    """A run at the start or the end of a line is not two words run together."""
    assert warnings(written("  It is deep.")) == []
    assert warnings(written("It is deep.  ")) == []


def test_a_footnote_is_read_like_the_body() -> None:
    """A footnote carries the report's own prose as often as a citation,
    and a citation is published here under this report's name too."""
    assert len(warnings(cited('Barbara Russo-Lennon, "Subway spots.  The ad blitz."'))) == 1


def test_a_closed_up_dash_is_not_warned_about() -> None:
    assert warnings(written("They are unfixable mistakes—while the debt is not.")) == []


def test_a_range_is_not_warned_about() -> None:
    """`10–20 ft` is how the reports write a range, and it is closed up already."""
    assert warnings(written("Groundwater is only 10–20 ft deep.")) == []


def test_a_spaced_em_dash_is_warned_about() -> None:
    found = warnings(written("They are unfixable mistakes — while the debt is not."))
    assert len(found) == 1
    assert "mistakes — while" in found[0]


def test_a_dash_spaced_on_one_side_is_warned_about() -> None:
    assert len(warnings(written("It is cheaper —and faster."))) == 1


def test_a_spaced_en_dash_is_warned_about() -> None:
    assert len(warnings(written("It spans 125 St, 2 – 3x the station width."))) == 1


def test_a_hyphen_is_not_a_dash() -> None:
    """`pipe-jacking` is one word, and `2 - 3` is a different thing to say."""
    assert warnings(written("The pipe-jacking at Jing'an Temple station.")) == []


def test_a_footnote_dash_is_read_like_the_body() -> None:
    assert len(warnings(cited('Barbara Russo-Lennon, "Subway spots — the ad blitz."'))) == 1


def test_the_initials_on_their_own_are_not_warned_about() -> None:
    assert warnings(written("ETA recommended reducing the scope.")) == []


def test_an_article_before_the_initials_is_warned_about() -> None:
    found = warnings(written("For the same reason, the ETA recommended reducing the scope."))
    assert len(found) == 1
    assert "`the ETA`" in found[0]
    assert "`the Effective Transit Alliance`" in found[0]


def test_a_sentence_opening_with_it_is_the_same_mistake() -> None:
    assert len(warnings(written("The ETA recommended reducing the scope."))) == 1


def test_the_name_spelled_out_keeps_its_article() -> None:
    assert warnings(written("The Effective Transit Alliance recommended reducing it.")) == []


def test_a_possessive_is_still_the_initials() -> None:
    assert len(warnings(written("Read the ETA’s response to the MTA."))) == 1


def test_a_word_beginning_with_the_initials_is_not_them() -> None:
    assert warnings(written("The ETAs quoted were all optimistic.")) == []


def test_a_footnote_saying_the_initials_is_warned_about() -> None:
    assert len(warnings(cited('Barbara Russo-Lennon, "What the ETA wants."'))) == 1


def test_the_header_is_read_like_the_body() -> None:
    """`Short:` publishes as the standfirst and `SEO Description:` as what a
    search result shows, and the header is consumed before the body walk,
    so neither is reached by walking the blocks."""
    doc = Document()
    doc.meta = {"Short": "It is deep.  It is also expensive."}
    assert len(warnings(doc)) == 1


def test_a_header_field_saying_the_initials_is_warned_about() -> None:
    doc = Document()
    doc.meta = {"SEO Description": "The ETA outlines the best practices."}
    assert len(warnings(doc)) == 1


def test_every_warning_says_it_is_about_style() -> None:
    """The rest of a document's warnings are things the build could not do,
    and these are things somebody may want to write differently,
    which is a different thing to go and fix."""
    found = warnings(written("It is deep.  The ETA said so — twice."))
    assert len(found) == 3
    assert all(w.startswith("style: ") for w in found)
