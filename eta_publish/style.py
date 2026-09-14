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

from .nodes import SPACE, Document, Highlighted, Shown, plain_text

CONTEXT = 30
"""How much of the line to show on either side of what is being warned about.

Enough to find the sentence in a document of several thousand words,
and not so much that a warning about two spaces is a paragraph.
"""


def _before(text: str, start: int) -> str:
    """What runs up to `start`, with enough of it to be found by eye."""
    lead = "..." if start > CONTEXT else ""
    return lead + text[max(0, start - CONTEXT) : start]


def _after(text: str, end: int) -> str:
    """What follows `end`, with enough of it to be found by eye."""
    trail = "..." if end + CONTEXT < len(text) else ""
    return text[end : end + CONTEXT] + trail


def _excerpt(text: str, start: int, end: int) -> str:
    """`text[start:end]` with enough either side of it to be found by eye."""
    return f"{_before(text, start)}{text[start:end]}{_after(text, end)}"


PREFIX = "style: "
"""What every warning here opens with.

A document's warnings are one list, and the rest of that list is something
the build could not do: a missing field, an unnamed image, a line nothing
read. These are things it did, correctly, that somebody may still want to
write differently, and a reader sorting the list by what to fix first
should be able to tell the two apart without reading to the end of the line.
"""


def _warn(doc: Document, template: str, *values: Shown | Highlighted) -> None:
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
        _check_street_names(doc, text)


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
        start, end = match.span("gap")
        drawn = Highlighted(_before(text, start), SPACE * len(gap), _after(text, end))
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


TYPES = {
    "Street": "St",
    "Avenue": "Av",
    "Ave": "Av",
    "Boulevard": "Blvd",
    "Place": "Pl",
    "Road": "Rd",
    "Drive": "Dr",
    "Lane": "Ln",
    "Court": "Ct",
    "Terrace": "Ter",
    "Parkway": "Pkwy",
    "Turnpike": "Tpke",
    "Plaza": "Plz",
    "Square": "Sq",
    "Expressway": "Expy",
    "Highway": "Hwy",
}
"""How the MTA writes each kind of street, and every spelling that is not it.

Its own signs, maps and announcements are where these come from:
`125 St`, `2 Av`, `Queens Blvd`, `Henry Hudson Pkwy`.
A report is about the system, so it should name a station the way the system
names it, and the reader who goes looking for the sign finds the sign.

Singular only. There is no MTA spelling of `116th and 125th Streets`,
and a rule that invents one would be worse than the one it corrects.
"""

WRITTEN = frozenset(TYPES.values())
"""The spellings that are already right, which nothing is warned about."""

NUMBER_WORDS = (
    "First",
    "Second",
    "Third",
    "Fourth",
    "Fifth",
    "Sixth",
    "Seventh",
    "Eighth",
    "Ninth",
    "Tenth",
    "Eleventh",
    "Twelfth",
)
"""The avenues whose number is a word rather than a digit.

`Second Avenue` is written out where `2 Av` is the station on it,
so a spelled-out number keeps the spelled-out kind of street beside it
and the pair is corrected the other way: towards the word, not the initials.
"""

SECOND_AVENUE_SUBWAY = "Second Avenue Subway"
"""The project, which is a name rather than a street.

The MTA's own, on every page it publishes about it, and the reports say it
constantly. The station on the line is `2 Av` and the line is this,
so the phrase is left exactly as it is written here.
"""

NOT_A_STREET = ("Rail Road",)
"""Phrases ending in what looks like a kind of street and is not one.

The Long Island Rail Road is a railroad, spelled as two words since 1876,
and `Long Island Rail Rd` is not a thing anybody has ever called it.
"""

COMMON_NOUN = "The"
"""What a name starts with when it is a phrase rather than a street.

`The Wrong Place to Scale Back` is a heading in SAS West, and `Place`,
`Square`, `Court` and `Drive` are all ordinary words as well as kinds of
street. No street is `The` anything, so this is the one that can be told
apart by reading it.
"""

ELSEWHERE = frozenset({"Nanba Road", "Heping South Street"})
"""Streets these reports name that are not in New York.

`Nanba Road` is in Shanghai and `Heping South Street` in Beijing, and neither
is a street the MTA has a spelling for: restyling them to `Nanba Rd` would be
inventing a name nothing anywhere calls it.
Nothing in the text says which city a street is in,
so a report naming another one adds it here.
"""

STREET = re.compile(
    rf"""
    (?P<name>
        (?:[A-Z][a-z]+[ ])*            # `Henry Hudson`, `Heping South`
        (?:\d+(?:st|nd|rd|th)?|[A-Z][a-z]+)  # `125th`, `2`, `Fordham`
    )
    [ ]
    (?P<kind>{"|".join(TYPES)})\b
    """,
    re.VERBOSE,
)
"""A street named the way a street is named: what it is called, then its kind.

The kind is spelled as one of the ones there is something to say about, so a
`125 St` already written that way never reaches the check at all.
Capitalized, and separated by a real space, which is what keeps a URL's
`72nd-street-station` and a filename's `96st_station` out of it.
"""


def _check_street_names(doc: Document, text: str) -> None:
    """A station or a street named some way other than the MTA's.

    The reports are about what the MTA builds, and a reader who goes looking
    for `125th Street` on a map finds `125 St`, which is the sign on the
    platform, the name in the app, and what the announcement says.
    """
    for match in STREET.finditer(text):
        name = match.group("name")
        kind = match.group("kind")
        written = f"{name} {kind}"
        if (
            written in ELSEWHERE
            or written.startswith(f"{COMMON_NOUN} ")
            or written.endswith(NOT_A_STREET)
            or text[match.start() :].startswith(SECOND_AVENUE_SUBWAY)
        ):
            continue
        correct = _mta(name, kind)
        if correct == written:
            continue
        _warn(
            doc,
            "{} is {} in MTA style: {}",
            Shown(written),
            Shown(correct),
            Highlighted(_before(text, match.start()), written, _after(text, match.end())),
        )


ORDINAL = re.compile(r"(?<=\d)(?:st|nd|rd|th)\b")


def _mta(name: str, kind: str) -> str:
    """`name` and `kind` written the way the MTA writes them.

    A spelled-out number is the one that grows rather than shrinks:
    `Second Ave` is `Second Avenue`, because that is the avenue whose
    station is `2 Av`.
    """
    if name in NUMBER_WORDS:
        spelled = next(full for full, short in TYPES.items() if short == TYPES[kind])
        return f"{name} {spelled}"
    return f"{ORDINAL.sub('', name)} {TYPES[kind]}"
