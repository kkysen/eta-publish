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

from .nodes import Document, Shown, Where, plain_text

QUOTES_SOMEBODY_ELSE = frozenset({Where.FOOTNOTE})
"""Where the words are not ours to set.

A footnote is a citation, and a citation is an author and a headline
copied from wherever it was published. Restyling a quoted headline
misquotes it, so how it spells a thing says nothing about this report.
"""

CONTEXT = 30
"""How much of the line to show on either side of what is being warned about.

Enough to find the sentence in a document of several thousand words,
and not so much that a warning about two spaces is a paragraph.
"""


def _excerpt(text: str, start: int, end: int) -> str:
    """`text[start:end]` with enough either side of it to be found by eye."""
    before = text[max(0, start - CONTEXT) : start]
    after = text[end : end + CONTEXT]
    lead = "..." if start > len(before) else ""
    trail = "..." if end + len(after) < len(text) else ""
    return f"{lead}{before}{text[start:end]}{after}{trail}"


def _prose(doc: Document) -> Iterator[str]:
    """Every run of the document's own words, as one string each."""
    for run, where in doc.text_runs():
        if where in QUOTES_SOMEBODY_ELSE:
            continue
        yield plain_text(run)


def style(doc: Document) -> None:
    """Warn about every line written against the house style."""
    for text in _prose(doc):
        _check_sentence_spacing(doc, text)


# A sentence's terminator, whatever closes the quote or bracket around it,
# and the gap after it. The closers are `sentences.py`'s, because the two are
# answering the same question about the same prose: `separately).  This`
# ends a sentence, and the paren is not what the spaces come after.
SENTENCE_GAP = re.compile(r"""[.!?]["'”’)\]]*(?P<gap>  +)""")


def _check_sentence_spacing(doc: Document, text: str) -> None:
    """Two spaces between sentences, where the house style is one.

    It is a typewriter habit, invisible in the doc and invisible on the page:
    HTML collapses the pair and Squarespace never sees it,
    so nothing downstream reports it and the Markdown archive keeps it forever.
    """
    for match in SENTENCE_GAP.finditer(text):
        doc.warn(
            "a sentence ends with {} spaces after it, where one is the house style: {}",
            Shown(str(len(match.group("gap")))),
            Shown(_excerpt(text, match.start(), match.end())),
        )
