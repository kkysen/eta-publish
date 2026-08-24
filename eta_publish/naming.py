"""Deterministic names for things that become published URLs.

Heading anchors and image filenames both end up in URLs that outlive any
one regeneration. If either can move because something unrelated changed
elsewhere in the document, two things break: links from outside rot, and
the committed Markdown fills with diff noise that a human has to read past.

So both are derived from the content they name, never from position.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable

_NON_SLUG = re.compile(r"[^\w\s-]")
_SEPARATORS = re.compile(r"[\s_-]+")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode()
    text = _NON_SLUG.sub("", text).strip().lower()
    return _SEPARATORS.sub("-", text) or "section"


class AnchorAllocator:
    """Assigns heading anchors that depend only on the heading's own text.

    Allocation is two-pass on purpose. The tempting approach, handing the
    bare slug to whichever heading claims it first and suffixing the rest,
    is still positional: if two headings slugify alike and their order
    changes between drafts, both of their anchors move.

    So the constructor is given every heading text up front, works out
    which base slugs more than one distinct heading would claim, and
    suffixes *all* claimants of those. A heading's anchor is then a pure
    function of its own text plus the set of headings it collides with,
    and reordering cannot touch it.

    `overrides` maps heading text to an explicit anchor, for headings whose
    published URL already exists and must not change.

    `reserved` holds ids the emitters generate themselves, such as the
    `footnotes` section. A heading actually titled "Footnotes" would
    otherwise collide with it, producing exactly the duplicate id that is
    one of the three defects on the live page.
    """

    def __init__(
        self,
        heading_texts: Iterable[str] = (),
        overrides: dict[str, str] | None = None,
        reserved: Iterable[str] = (),
    ) -> None:
        self.overrides = overrides or {}
        self.reserved = frozenset(reserved)
        claimants: dict[str, set[str]] = defaultdict(set)
        for text in heading_texts:
            if text not in self.overrides:
                claimants[slugify(text)].add(text)
        self._ambiguous = {base for base, texts in claimants.items() if len(texts) > 1}

    def allocate(self, text: str) -> str:
        if text in self.overrides:
            return self.overrides[text]
        base = slugify(text)
        if base in self._ambiguous or base in self.reserved:
            return f"{base}-{_short_hash(text)}"
        return base


def image_filename(object_id: str, extension: str = "") -> str:
    """Name an image after its Docs object id.

    The id is stable across edits, so inserting an image cannot rename the
    ones around it. It is opaque rather than descriptive, which is the
    trade we want: a descriptive name would have to come from position or
    from a caption, and both of those change.

    The extension is filled in once the image is downloaded and its real
    content type is known.
    """
    return f"img-{_short_hash(object_id)}{extension}"


def _short_hash(value: str, length: int = 8) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]
