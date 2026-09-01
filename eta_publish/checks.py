"""What a report has to have before it is published.

These read a parsed document and say what is missing.
They are separate from `parse.py`, which warns about what it could not read:
a document can parse perfectly and still not be ready,
and the two questions have different answers for the same file.

Every one of these is something to fix in the document rather than in the code,
which is why they are warnings on the document
and appear both in the build log and on the site's index page.
"""

from .nodes import Document

REQUIRED_FIELDS = (
    "project manager",
    "phase",
    "discussion channel",
    "publish due date",
    "public contributors",
    "private contributors",
    "url",
    "short",
    "seo description",
)
"""Every line the `Header` section is expected to carry, in the order it writes them.

A missing one is warned about by name rather than as a list of nine,
because a warning naming one line is a line to go and add
and a warning naming nine is a paragraph nobody reads twice.
"""


MAY_BE_EMPTY = frozenset({"private contributors"})
"""Fields whose emptiness says something rather than being an omission.

A report with nobody uncredited has an empty `Private Contributors:` line,
and that is the answer, not a missing one.
Every other field empty is a line somebody meant to come back to.
"""


def check(doc: Document) -> None:
    """Warn about everything a published report should not be missing."""
    if not doc.meta:
        # `parse` has already said the header is missing or empty.
        # Nine more warnings saying the same thing would bury it.
        return

    for field in REQUIRED_FIELDS:
        if field not in doc.meta:
            doc.warn(f"the `Header` section has no `{_titled(field)}:` line")
        elif field not in MAY_BE_EMPTY and not doc.meta[field].strip():
            doc.warn(f"the `Header` section leaves `{_titled(field)}:` empty")


ACRONYMS = frozenset({"seo", "url"})
"""Words the header writes in capitals, which `str.title` would not."""


def _titled(field: str) -> str:
    """A header key as the document writes it: `seo description` is `SEO Description`.

    The keys are lowercased on the way in, so that a document writing `Url:`
    and one writing `URL:` are the same field.
    They are written back out the way the document asks for them,
    because the warning is telling somebody which line to go and look at.
    """
    return " ".join(
        word.upper() if word in ACRONYMS else word.capitalize() for word in field.split()
    )
