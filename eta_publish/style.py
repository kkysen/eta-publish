"""How a report is written, as distinct from what it says.

`parse.py` warns about what it could not read and `checks.py` about what a
report has not got. These read prose that parsed cleanly and is complete,
and say it is spelled against the house style: the same sentence,
set the way every other report sets it.

Each is a fix in the document rather than in the build,
so each is a warning on the document like the others,
and none of them rewrites anything on the way out.
Spelling the reports alike is the writer's, so the build says where to look
rather than quietly making the reports agree.
"""

import re
from collections.abc import Iterator

from .nodes import Document, Shown, plain_text

CONTEXT = 30
"""How much of the line to show on either side of what is being warned about.

Enough to find the sentence in a document of several thousand words,
and not so much that a warning about two spaces is a paragraph.
"""


def _excerpt(text: str, start: int, end: int, shown: str | None = None) -> str:
    """`text[start:end]` with enough either side of it to be found by eye.

    `shown` stands in for the part being warned about, for a warning whose
    subject cannot be seen where it is quoted: two spaces are one space in
    every output but the log, so an excerpt of them says nothing by itself.
    """
    before = text[max(0, start - CONTEXT) : start]
    after = text[end : end + CONTEXT]
    lead = "..." if start > len(before) else ""
    trail = "..." if end + len(after) < len(text) else ""
    middle = text[start:end] if shown is None else shown
    return f"{lead}{before}{middle}{after}{trail}"


PREFIX = "style: "
"""What every warning here opens with.

A document's warnings are one list, and the rest of that list is something
the build could not do: a missing field, an unnamed image, a line nothing
read. These are things it did, correctly, that somebody may still want to
write differently, and a reader sorting the list by what to fix first
should be able to tell the two apart without reading to the end of the line.
"""


def _warn(doc: Document, template: str, *values: Shown) -> None:
    """Warn about how something is written, said as one of these rather than
    as one of the document's other warnings."""
    doc.warn(PREFIX + template, *values)


def _prose(doc: Document) -> Iterator[str]:
    """Every run of the document's own words, as one string each.

    Footnotes included. They carry the report's own prose as often as they
    carry a citation, and a citation copied from where it was published is
    published here too, under this report's name and in its house style.

    The header is read alongside the body rather than left out of this.
    `text_runs` walks the blocks, and the header was consumed before those
    existed, so a `Short:` or `SEO Description:` written against the style
    would otherwise be the one piece of prose nothing here reads,
    and it is the piece that publishes as the standfirst
    and as what a search result shows.
    """
    yield from doc.meta.values()
    for run, _ in doc.text_runs():
        yield plain_text(run)


def style(doc: Document) -> None:
    """Warn about every line written against the house style."""
    for text in _prose(doc):
        _check_spacing(doc, text)
        _check_dash_spacing(doc, text)
        _check_organization_name(doc, text)


GAP = re.compile(r"(?<=\S)(?P<gap>  +)(?=\S)")
"""Two or more spaces with a word either side of them.

A word either side because a run at the start or the end of a line
is indentation or something left trailing, which is neither of the two
mistakes here and would be described wrongly by both.
"""

ENDS_A_SENTENCE = re.compile(r"""[.!?]["'”’)\]]*$""")
"""What comes before a gap that separates two sentences.

The terminator and whatever closes the quote or bracket around it.
The closers are `sentences.py`'s, because the two are answering the same
question about the same prose: `separately).  This` ends a sentence,
and the paren is not what the spaces come after.
"""


SPACE = "\u00b7"
"""What one of the offending spaces is shown as.

A space is the one thing a warning cannot quote: HTML collapses the pair,
`typst` sets it as one, and the reader is shown a line that looks correct
and told it is not. The middle dot is what an editor draws a space with,
and it is in the excerpt only, so the words either side are still the
document's own to search for.
"""


def _check_spacing(doc: Document, text: str) -> None:
    """A gap of more than one space, described by what sits either side of it.

    Between sentences it is the typewriter habit, and mid-clause it is a
    slipped finger: the same characters, but one is how somebody was taught
    to type and the other is a typo, so they are not one warning.

    Neither is visible anywhere somebody would catch it.
    The doc shows one space either way, HTML collapses the run, and
    Squarespace never sees it, so nothing downstream reports either one
    and the Markdown archive keeps both forever.
    """
    for match in GAP.finditer(text):
        gap = match.group("gap")
        drawn = Shown(_excerpt(text, match.start("gap"), match.end("gap"), SPACE * len(gap)))
        if ENDS_A_SENTENCE.search(text[: match.start("gap")]):
            _warn(doc, f"a sentence should end with 1 space, not {len(gap)}: {{}}", drawn)
        else:
            _warn(doc, f"two words should be separated by 1 space, not {len(gap)}: {{}}", drawn)


DASHES = "—–"
"""The two dashes that set a phrase off, em and en.

Not the hyphen: `pipe-jacking` is one word and `10-15` is somebody
reaching for an en dash, which is a different thing to say about a line.
"""

SPACED_DASH = re.compile(rf"(?: +[{DASHES}]|[{DASHES}] +)")


def _check_dash_spacing(doc: Document, text: str) -> None:
    """A dash with a space on either side of it, where the house style has none.

    The reports already write it closed up, in every one of the fourteen
    dashes SAS West and IBX have between them. A spaced one arrives by pasting
    from somewhere that sets them open, and the one paragraph set the other way
    is visible on the page next to the rest.
    """
    for match in SPACED_DASH.finditer(text):
        _warn(
            doc,
            "a dash is written with a space beside it, and the house style closes it up: {}",
            Shown(_excerpt(text, match.start(), match.end())),
        )


SPELLED_OUT = "the Effective Transit Alliance"
"""The name written out, which does take an article.

Only the initials go bare, so a line spelling the name out is already right
and this rule has nothing to say about it.
"""

ARTICLED = re.compile(r"\bthe[ \u00a0]+(?=ETA\b)", re.IGNORECASE)
"""An article before the initials, which is what is being warned about.

The initials themselves are left to the sentence: `ETA recommended` and
`ETA members` are how both reports write it, and the only thing wrong with
`the ETA` is the word in front. Case-insensitively, because a sentence
opening `The ETA` is the same mistake as one saying it mid-line.
"""


def _check_organization_name(doc: Document, text: str) -> None:
    """`the ETA`, where the initials are written on their own.

    It is the name rather than a description of one, the way somebody writes
    `NASA said` and not `the NASA said`, and both reports already say
    `ETA recommended` and `ETA members` in the places they say it at all.
    Spelled out it does take the article, which is why this looks only at
    the initials.
    """
    for match in ARTICLED.finditer(text):
        _warn(
            doc,
            "{} is written {}; it is {} on its own, and {} spelled out: {}",
            Shown("ETA"),
            Shown(text[match.start() : match.end() + len("ETA")]),
            Shown("ETA"),
            Shown(SPELLED_OUT),
            Shown(_excerpt(text, match.start(), match.end() + len("ETA"))),
        )
