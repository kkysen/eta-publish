"""Deterministic names for things that become published URLs.

Heading anchors and image filenames both end up in URLs that outlive any
one regeneration. If either can move because something unrelated changed
elsewhere in the document, two things break: links from outside rot, and
the committed Markdown fills with diff noise that a human has to read past.

So both are derived from the content they name, never from position.
"""

import hashlib
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable

IMAGE_DIR = "images"
"""The directory a build writes images into, relative to the report.

Every output refers to them by this name, and the download writes them
under it, so it lives here rather than being spelled out in each of the
four places that has to agree with the other three. Serving them from
somewhere else is what an emitter's `image_base` is for, and is a decision
about hosting rather than about a build.
"""

_NON_SLUG = re.compile(r"[^\w\s-]")
_SEPARATORS = re.compile(r"[\s_-]+")


def slugify(text: str) -> str:
    """`text` as one lowercase word, joined by the separators it already
    used.

    An underscore is left as an underscore. It is a legal character in a
    URL and it is one the name was written with, so turning it into a
    hyphen edits a name this is supposed to be carrying: `96st_station` is
    what the document calls that file.

    A run is still one separator, which is what makes ` - ` and `_ ` and a
    double space each come out as a single character rather than as three.
    The run keeps the character it was written with, and a hyphen wins a
    run that holds both, because that is the one a reader of a URL expects.
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode()
    text = _NON_SLUG.sub("", text).strip().lower()
    return _SEPARATORS.sub(_separator, text) or "section"


def _separator(run: re.Match[str]) -> str:
    return "_" if "_" in run.group() and "-" not in run.group() else "-"


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


def content_anchor(prefix: str, text: str) -> str:
    """An id for a block that has no name of its own, from what it says.

    Paragraphs, tables, and lists carry no identifier in the Docs API and
    no title to slugify, but they still want to be linkable: a report this
    long is quoted a paragraph at a time.

    Hashing what the block says rather than counting where it sits is the
    same trade the rest of this module makes, and here it is the difference
    between two failures. Numbering paragraphs means inserting one silently
    repoints every link after it in that section at the wrong text. Hashing
    means editing a paragraph breaks links to that paragraph, loudly, and
    to nothing else.
    """
    return f"{prefix}-{_short_hash(text)}"


# The file extensions a source line writes, which name the format rather
# than the picture. `sas-west-036.jpg` and `sas-west-036.png` are the same
# image exported twice, and the extension the published file gets is the
# one the download learns, so the one written here is dropped.
_ASSET_EXTENSION = re.compile(r"\.(?:jpe?g|png|gif|webp|svg|pdf|tiff?|heic)$", re.IGNORECASE)


def image_filename(object_id: str, extension: str = "", crop_key: str = "", name: str = "") -> str:
    """Name an image after the file the document says it came from.

    A `Source:` line is the document stating which file this is, which is
    what makes it usable as a name where a caption is not: a caption
    describes the picture and gets rewritten in copy-editing, and a
    position changes whenever anything is inserted above it. Editing a
    source line does move a published URL, and that is the cost of the
    names being readable at all.

    Most images are given no source line, and those keep the name they
    always had: their Docs object id, hashed. The id is stable across
    edits, so inserting an image cannot rename the ones around it.

    The crop is part of the name because it is part of the file. Recropping
    in the document produces a different published image, and without this
    it would keep the old name and the old cached file. So a named image
    that is cropped carries the hash too, which is also what tells two
    crops of one source file apart. An uncropped image is named as it was.

    The extension is filled in once the image is downloaded and its real
    content type is known.
    """
    base = slugify(_ASSET_EXTENSION.sub("", name).replace(".", " ")) if name.strip() else ""
    if not base or base == "section":
        return f"img-{_short_hash(object_id + crop_key)}{extension}"
    if crop_key:
        base = f"{base}-{_short_hash(object_id + crop_key)}"
    return f"{base}{extension}"


def image_filenames(claims: Iterable[tuple[str, str, str]]) -> dict[str, str]:
    """A filename for each image, given every claim in the document.

    A claim is an object id, a crop key, and the name the document gave the
    image, which is empty for the images it named nothing. Allocated
    knowing all of them for the reason `AnchorAllocator` is: two images
    whose source lines name the same file would otherwise be told apart by
    which came first, and reordering the report would move a published URL.

    So both of them keep the name and carry the hash as well, which is the
    same way a crop is told from its original. The name is still the useful
    half: `96st-station-a1b2c3d4` says what the file is, where
    `img-a1b2c3d4` says only that it is an image.
    """
    claims = list(claims)
    claimants: dict[str, set[str]] = defaultdict(set)
    for object_id, crop_key, name in claims:
        claimants[image_filename(object_id, crop_key=crop_key, name=name)].add(object_id)
    ambiguous = {base for base, ids in claimants.items() if len(ids) > 1}

    names: dict[str, str] = {}
    for object_id, crop_key, name in claims:
        plain = image_filename(object_id, crop_key=crop_key, name=name)
        # `crop_key` on its own would be enough to make the name distinct,
        # and asking for it here is what says why: the two images say they
        # are the same file, and only the hash can disagree.
        names[object_id] = (
            image_filename(object_id, crop_key=crop_key or object_id, name=name)
            if plain in ambiguous
            else plain
        )
    return names


def _short_hash(value: str, length: int = 8) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]
