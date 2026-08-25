"""The document tree every emitter renders from.

This is the only intermediate representation. The Docs parser builds it,
and the HTML, Markdown, and Typst emitters each walk it independently.
Notably the HTML is not rendered from the Markdown: chaining them would
lose the figure source/caption/credit distinction, superscripts, and exact
link targets, and would create a second source of truth as soon as anyone
hand-edited the `.md`.

The tree is deliberately small. It carries what ETA reports actually use,
not a general model of what a Google Doc can express. Anything the parser
meets and cannot place here becomes a warning rather than a silent drop.
"""

from dataclasses import dataclass, field
from enum import Enum

# ---- inline content ------------------------------------------------


@dataclass(frozen=True)
class Text:
    """A run of text sharing one style.

    `sup` and `sub` are kept separate from bold/italic because footnote
    references and units both rely on them, and Typst spells them
    differently from HTML.
    """

    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    sup: bool = False
    sub: bool = False
    href: str | None = None


@dataclass(frozen=True)
class LineBreak:
    """A soft line break inside a paragraph, from Shift+Enter in Docs.

    Docs encodes these as a vertical tab inside the text run rather than as
    a paragraph boundary. Left alone they reach the published page as a raw
    control character, and they hide the convention that a `Credit:` line
    following one is a credit rather than part of the caption.
    """


@dataclass(frozen=True)
class FootnoteRef:
    """A reference to a footnote, identified by the Docs footnote id.

    Display numbering is assigned by the parser in document order, so it
    can never disagree between the reference and the definition.
    """

    footnote_id: str
    number: int


@dataclass(frozen=True)
class Crop:
    """How much of an image the document trims from each side.

    Docs stores a crop as fractions of the original, so the image file it
    serves is always the uncropped one. Nothing downstream can express this:
    Markdown has no way to crop, and a CSS crop would not reach the PDF. So
    the crop is applied to the file, which is also what the document's own
    `Uncropped Source:` lines imply is the published form.
    """

    left: float = 0.0
    right: float = 0.0
    top: float = 0.0
    bottom: float = 0.0

    @property
    def trims(self) -> bool:
        return any((self.left, self.right, self.top, self.bottom))

    @property
    def key(self) -> str:
        """Identifies this crop, so changing it renames the file."""
        if not self.trims:
            return ""
        return f"|{self.left:.6f},{self.right:.6f},{self.top:.6f},{self.bottom:.6f}"

    def box(self, width: int, height: int) -> tuple[int, int, int, int]:
        """The pixel box to keep, for an original of this size."""
        return (
            round(self.left * width),
            round(self.top * height),
            width - round(self.right * width),
            height - round(self.bottom * height),
        )


@dataclass(frozen=True)
class Vector:
    """A vector original the document names beside a rasterized copy.

    Google Docs cannot place an SVG, so a chart is pasted as a PNG and the
    real file is linked next to it on a `SVG:` line. Every output here can
    show the vector, so the raster is only ever a stand-in for the editor.
    """

    file_id: str
    """The Drive file id, which is what the API downloads by."""

    filename: str
    title: str = ""
    uri: str = ""


@dataclass(frozen=True)
class Image:
    """An inline image.

    `object_id` is the Docs `inlineObjectId`, which is stable across edits.
    Filenames derive from it rather than from a counter, so inserting one
    image into a 54-image report does not rename the other 53 or change
    their published URLs.
    """

    object_id: str
    filename: str
    alt: str = ""
    source_uri: str | None = None
    crop: Crop = field(default_factory=lambda: Crop())
    vector: Vector | None = None


Inline = Text | LineBreak | FootnoteRef | Image


# ---- block content -------------------------------------------------


@dataclass
class Paragraph:
    content: list[Inline] = field(default_factory=list)


@dataclass
class Heading:
    level: int
    """2 through 6. The document title is not a heading; it is `Document.title`."""

    anchor: str
    """Stable slug. This is a published URL, so it must not move when an
    unrelated section is added elsewhere."""

    content: list[Inline] = field(default_factory=list)


class ListKind(Enum):
    BULLET = "bullet"
    NUMBER = "number"


@dataclass
class ListItem:
    content: list[Inline] = field(default_factory=list)
    children: list[ListItem] = field(default_factory=list)


@dataclass
class List:
    kind: ListKind
    items: list[ListItem] = field(default_factory=list)


@dataclass
class Figure:
    """An image together with the lines the doc attaches to it.

    ETA reports consistently write an optional `Source:` line before the
    image and a caption and `Credit:` line after it. Keeping the three
    distinct lets HTML class them separately and lets Typst place the
    credit differently from the caption.
    """

    image: Image
    source: list[Inline] = field(default_factory=list)
    caption: list[Inline] = field(default_factory=list)
    credit: list[Inline] = field(default_factory=list)


@dataclass
class Table:
    rows: list[list[list[Block]]] = field(default_factory=list)
    """Rows of cells; each cell holds blocks."""

    header: bool = False


Block = Paragraph | Heading | List | Figure | Table


# ---- document ------------------------------------------------------


@dataclass
class Footnote:
    footnote_id: str
    number: int
    content: list[Block] = field(default_factory=list)


@dataclass
class Document:
    title: str = ""
    meta: dict[str, str] = field(default_factory=dict)
    """The doc's leading `Header` section, lowercased keys.
    Unrecognized keys are kept rather than dropped."""

    blocks: list[Block] = field(default_factory=list)
    footnotes: list[Footnote] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    image_files: dict[str, str] = field(default_factory=dict)
    """Docs object id to the filename actually written, extension included.

    Filled in by `images.download`, which is the only step that can know it.
    The Docs API describes an inline object without saying what kind of file
    it is, so the extension comes from the response; and where the document
    names a vector alongside a raster, the file written is the vector, under
    a different name entirely. Empty when images were skipped, in which case
    `image_href` falls back to the raster's name without an extension.
    """

    @property
    def contributors(self) -> list[str]:
        """The people credited on the published page, in document order.

        Read from `Public Contributors:` and from nothing else. The document
        carries a separate `Private Contributors:` field precisely so that
        some names do not publish, so no fallback to it belongs here.

        The names come from person chips, which resolve to a chip's display
        name, so this is a list of names and not of addresses.
        """
        names = self.meta.get("public contributors", "")
        return [name.strip() for name in names.split(",") if name.strip()]

    @property
    def dateline(self) -> str:
        """The publication date, as the document shows it, e.g. `Aug 19, 2026`.

        `Final Due Date:` is the date a report publishes on, and it is a date
        chip, so the string here is the one Docs renders in the document.
        It is passed through rather than reformatted: the header block is
        where the date is decided, and a longer form is a change to how every
        date reads, front matter included, rather than to this line alone.
        """
        return self.meta.get("final due date", "")

    @property
    def slug(self) -> str:
        """The published path, e.g. `/reports/digging-out-deep-hole-sas-west`."""
        return self.meta.get("url", "")

    def headings(self, level: int = 2) -> list[Heading]:
        """Headings at one level, for building a table of contents."""
        return [b for b in self.blocks if isinstance(b, Heading) and b.level == level]

    @property
    def images(self) -> list[Image]:
        """Every image in the document, in order, including inside footnotes.

        Deduplicated by `object_id`: the same image used twice is one file.
        """
        seen: dict[str, Image] = {}
        for block in _walk(self.blocks):
            for image in _images_in(block):
                seen.setdefault(image.object_id, image)
        for footnote in self.footnotes:
            for block in _walk(footnote.content):
                for image in _images_in(block):
                    seen.setdefault(image.object_id, image)
        return list(seen.values())

    def image_href(self, image: Image) -> str:
        """The filename as emitted, once a download has settled what it is."""
        return self.image_files.get(image.object_id, image.filename)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


# ---- traversal -----------------------------------------------------


def _walk(blocks: list[Block]):
    """Yield every block, descending into lists and table cells."""
    for block in blocks:
        yield block
        if isinstance(block, Table):
            for row in block.rows:
                for cell in row:
                    yield from _walk(cell)


def _images_in(block: Block) -> list[Image]:
    match block:
        case Figure():
            return [block.image]
        case Paragraph() | Heading():
            return [i for i in block.content if isinstance(i, Image)]
        case List():
            return [i for item in _items(block.items) for i in item.content if isinstance(i, Image)]
    return []


def _items(items: list[ListItem]):
    for item in items:
        yield item
        yield from _items(item.children)
