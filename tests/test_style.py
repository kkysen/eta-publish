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
    assert "two spaces" not in found[0]
    assert "`2`" in found[0]


def test_the_warning_shows_where_to_look() -> None:
    found = warnings(written("It is deep.  It is also expensive."))
    assert "It is deep.  It is also expensive." in found[0]


def test_a_closing_bracket_does_not_hide_the_gap() -> None:
    """`costs are given separately).  This` is how the real report writes one:
    the spaces come after the sentence, whatever closes the quote around it."""
    assert len(warnings(written("(costs are given separately.)  This is a Buy America cost."))) == 1


def test_three_spaces_are_counted_rather_than_rounded_to_two() -> None:
    assert "`3`" in warnings(written("It is deep.   It is expensive."))[0]


def test_two_spaces_that_end_no_sentence_are_left_alone() -> None:
    """`demand  requires` is a different mistake, and this rule is not about it."""
    assert warnings(written("On such routes, demand  requires high frequency.")) == []


def test_a_footnote_is_quoted_rather_than_written() -> None:
    """A citation is an author and a headline copied from where it was published,
    so how it spaces its sentences says nothing about this report."""
    assert warnings(cited('Barbara Russo-Lennon, "Subway spots.  The ad blitz."')) == []
