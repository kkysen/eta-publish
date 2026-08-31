"""Deterministic names for things that become published URLs.

Heading anchors and image filenames both end up in URLs
that outlive any one regeneration.
If either moves because something unrelated changed elsewhere,
links from outside rot and the committed Markdown fills with diff noise.

So both derive from the content they name, never from position.
"""

import hashlib
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable

from pymdownx.slugs import slugify as _slugify

IMAGE_DIR = "images"
"""The directory a build writes images into, relative to the report.

Here rather than spelled out in each of the four places that must agree.
Serving them from somewhere else is an emitter's `image_base`,
which is a decision about hosting rather than about a build.
"""

# What a filename may keep: a dot is as much a part of a name as a letter,
# and `-` and `_` are what people join names with.
_NON_FILENAME = re.compile(r"[^\w.-]")
# A source line's extension names the format rather than the picture,
# and the one that publishes is whatever the download fetches,
# so it is dropped and the real one appended.
_ASSET_EXTENSION = re.compile(r"\.(?:jpe?g|png|gif|webp|svg|pdf|tiff?|heic)$", re.IGNORECASE)


# GitHub's rule for a heading anchor, from `pymdown-extensions` rather than rewritten here.
# The two agreeing today is no reason to keep a second copy:
# they agree until a heading has an accent in it,
# and then whichever copy is wrong is wrong in published URLs.
# This is what MkDocs Material publishes GitHub-style slugs with.
#
# `github-slugger`, the dedicated PyPI port, cannot be imported on a current Python:
# it carries the JavaScript regex as lone surrogates, a `UnicodeEncodeError` on import.
_github_slug = _slugify(case="lower")


def slugify(text: str) -> str:
    """`text` as a heading anchor, by the rule Markdown uses for one.

    The same report publishes as HTML and as Markdown,
    and a link to a section must mean the same in both,
    so the rule is not ours to choose:
    lowercase, punctuation dropped, `-` and `_` kept, one hyphen per space,
    non-ASCII letters left alone. That is what GitHub renders an anchor as.

    Not the rule a filename gets.
    A heading is a sentence, and every separator in its anchor is one we invented;
    a filename is a name somebody chose, and `_ascii_name` keeps it.
    """
    return _github_slug(text, "-") or "section"


def _ascii_name(name: str) -> str:
    """A filename as close to `name` as a URL can carry it.

    Every character that cannot appear becomes one underscore, and nothing else moves:
    runs are not collapsed, case is not folded, and a dot stays where it was.
    `SAS West - Tunnel Profile - pg 18.screenshot`
    publishes under a name its author would recognize,
    which is the whole reason for reading the source line.
    """
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode()
    return _NON_FILENAME.sub("_", _ASSET_EXTENSION.sub("", name.strip()))


class AnchorAllocator:
    """Assigns heading anchors that depend only on the heading's own text.

    Two-pass on purpose.
    Handing the bare slug to whichever heading claims it first and suffixing the rest
    is still positional:
    if two headings slugify alike and their order changes between drafts,
    both anchors move.

    So the constructor takes every heading text up front,
    works out which base slugs more than one distinct heading would claim,
    and suffixes *all* claimants of those.
    An anchor is then a function of its own text
    plus the set of headings it collides with, and reordering cannot touch it.

    `overrides` maps heading text to an explicit anchor,
    for headings whose published URL already exists and must not change.

    `reserved` holds ids the emitters generate themselves, such as `footnotes`.
    A heading titled "Footnotes" would otherwise collide with it,
    producing the duplicate id that is one of the three defects on the live page.
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


def content_anchor(prefix: str, text: str) -> str:
    """An id for a block that has no name of its own, from what it says.

    Paragraphs, tables, and lists carry no identifier and no title to slugify,
    but they still want to be linkable:
    a report this long is quoted a paragraph at a time.

    Hashing what the block says rather than counting where it sits
    is the difference between two failures.
    Numbering means inserting a paragraph
    silently repoints every link after it in that section at the wrong text.
    Hashing means editing a paragraph breaks links to that paragraph,
    loudly, and to nothing else.
    """
    return f"{prefix}-{_short_hash(text)}"


def image_filename(object_id: str, extension: str = "", crop_key: str = "", name: str = "") -> str:
    """Name an image after the file the document says it came from.

    A `Source:` line is the document saying which file this is,
    which makes it usable as a name where a caption is not:
    a caption gets rewritten in copy-editing,
    and a position changes whenever anything is inserted above it.
    Editing a source line does move a published URL,
    which is the cost of readable names.

    An image with no source line keeps the name it always had:
    its Docs object id, hashed.
    The id is stable across edits, so inserting an image cannot rename its neighbours.

    The crop is part of the name because it is part of the file.
    Recropping produces a different published image,
    and without this it would keep the old name and the old cached file.
    So a named image that is cropped carries the hash too,
    which is also what tells two crops of one source file apart.
    An uncropped image is named as it was.

    The extension is filled in once the download settles the real content type.
    """
    base = _ascii_name(name)
    # A name of nothing but separators names nothing.
    if not base.strip("_.-"):
        return f"img-{_short_hash(object_id + crop_key)}{extension}"
    if crop_key:
        base = f"{base}-{_short_hash(object_id + crop_key)}"
    return f"{base}{extension}"


def image_filenames(claims: Iterable[tuple[str, str, str]]) -> dict[str, str]:
    """A filename for each image, given every claim in the document.

    A claim is an object id, a crop key, and the name the document gave the image,
    empty for the images it named nothing.
    Allocated knowing all of them for the reason `AnchorAllocator` is:
    two images whose source lines name the same file
    would otherwise be told apart by which came first,
    and reordering the report would move a published URL.

    So both keep the name and carry the hash too,
    the same way a crop is told from its original.
    The name is still the useful half:
    `96st-station-a1b2c3d4` says what the file is,
    where `img-a1b2c3d4` says only that it is an image.
    """
    claims = list(claims)
    claimants: dict[str, set[str]] = defaultdict(set)
    for object_id, crop_key, name in claims:
        claimants[image_filename(object_id, crop_key=crop_key, name=name)].add(object_id)
    ambiguous = {base for base, ids in claimants.items() if len(ids) > 1}

    names: dict[str, str] = {}
    for object_id, crop_key, name in claims:
        plain = image_filename(object_id, crop_key=crop_key, name=name)
        # `crop_key` alone would make the name distinct;
        # asking for it here says why:
        # the two images claim to be the same file, and only the hash can disagree.
        names[object_id] = (
            image_filename(object_id, crop_key=crop_key or object_id, name=name)
            if plain in ambiguous
            else plain
        )
    return names


def _short_hash(value: str, length: int = 8) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]
