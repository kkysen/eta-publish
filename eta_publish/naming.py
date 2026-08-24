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

_NON_SLUG = re.compile(r"[^\w\s-]")
_SEPARATORS = re.compile(r"[\s_-]+")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode()
    text = _NON_SLUG.sub("", text).strip().lower()
    return _SEPARATORS.sub("-", text) or "section"


class AnchorAllocator:
    """Assigns unique heading anchors that do not move.

    A positional counter would be wrong here. If two headings both slugify
    to `overview`, numbering them by order of appearance means inserting a
    third one earlier in the document silently reassigns `overview-2` to a
    different section, breaking anyone's link to it.

    Instead a collision is broken with a short hash of the heading's full
    text, which depends only on that heading. Colliding headings therefore
    keep their anchors no matter what happens around them.
    """

    def __init__(self) -> None:
        self._taken: dict[str, str] = {}

    def allocate(self, text: str) -> str:
        base = slugify(text)
        if self._taken.get(base) in (None, text):
            self._taken[base] = text
            return base
        anchor = f"{base}-{_short_hash(text)}"
        self._taken[anchor] = text
        return anchor


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
