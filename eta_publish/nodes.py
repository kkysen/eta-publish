"""The document tree every emitter renders from.

The only intermediate representation:
the parser builds it, and each emitter walks it independently.
The HTML is not rendered from the Markdown,
which would lose the figure source/caption/credit distinction,
superscripts, and exact link targets,
and would create a second source of truth the moment anyone edited the `.md`.

It carries what ETA reports use, not what a Google Doc can express.
Anything the parser cannot place here becomes a warning rather than a silent drop.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# ---- inline content ------------------------------------------------


@dataclass(frozen=True)
class Text:
    """A run of text sharing one style.

    `sup` and `sub` are separate from bold/italic
    because footnote references and units rely on them,
    and Typst spells them differently from HTML.
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

    Docs encodes these as a vertical tab inside the text run
    rather than as a paragraph boundary.
    Left alone they reach the published page as a raw control character,
    and they hide that a `Credit:` line following one
    is a credit rather than part of the caption.
    """


@dataclass(frozen=True)
class FootnoteRef:
    """A reference to a footnote, identified by the Docs footnote id.

    The parser numbers these in document order,
    so a reference and its definition cannot disagree.
    """

    footnote_id: str
    number: int


@dataclass(frozen=True)
class Crop:
    """How much of an image the document trims from each side.

    Docs stores a crop as fractions of the original,
    so the file it serves is always the uncropped one.
    Nothing downstream can express this:
    Markdown has no way to crop, and a CSS crop would not reach the PDF.
    So the crop is applied to the file,
    which is what the document's own `Uncropped Source:` lines imply anyway.
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
        """Changing this renames the file."""
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

    Google Docs cannot place an SVG,
    so a chart is pasted as a PNG and the real file linked beside it on an `SVG:` line.
    Every output here can show the vector,
    so the raster is only a stand-in for the editor.
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
    Filenames derive from it rather than from a counter,
    so inserting one image into a 54-image report
    does not rename the other 53 or move their published URLs.
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
    """2 through 6. The title is not a heading; it is `Document.title`."""

    anchor: str
    """A published URL, so it must not move
    when an unrelated section is added elsewhere."""

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

    ETA reports write an optional `Source:` line before the image,
    and a caption and `Credit:` line after it.
    Keeping the three distinct lets HTML class them separately
    and lets Typst place the credit differently from the caption.
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

    file_title: str = ""
    """What the document is called in Drive, which is not what it is called here.

    The headline is the report's title; this is the working name it is filed under,
    and the only thing `reports.toml` can be checked against."""

    tab_title: str = ""
    """What the tab this was read from is called.

    A `?tab=` id is opaque, so it is not something a person can check by reading it.
    This is the same choice written in words."""
    meta: dict[str, str] = field(default_factory=dict)
    """The doc's leading `Header` section, lowercased keys.
    Unrecognized keys are kept rather than dropped."""

    blocks: list[Block] = field(default_factory=list)
    footnotes: list[Footnote] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    card: Image | None = None
    """A wide image with the title set into it,
    placed above the headline for whatever links to the report to show as a thumbnail.

    Not part of the report, so not in `blocks`: it publishes as `og:image` and nowhere else."""

    image_files: dict[str, str] = field(default_factory=dict)
    """Docs object id to the filename actually written, extension included.

    Only `images.download` can know it.
    A Docs `inlineObject` says nothing about what kind of file it is,
    so the extension comes from the response,
    and a vector named alongside a raster is written under a different name entirely.
    Empty when images were skipped,
    where `image_href` falls back to the raster's name without an extension.
    """

    image_shapes: dict[str, tuple[int, int]] = field(default_factory=dict)
    """Docs object id to the pixel size of the file actually written.

    From the same record as `image_files`, and for the same reason:
    Docs says how large an image is placed, not how large it is,
    and the crop applied here changes the shape of the file without the document knowing.
    An SVG has no pixel size to read, so it is one this is empty for.
    """

    @property
    def hero(self) -> Figure | None:
        """The figure a report opens with, if it opens with one.

        The document puts it under the headline,
        so it belongs there rather than after a table of contents it should be introducing.
        This is the title page, and a title page is a title and a picture.

        Recognized by position, which is what the document already says.
        Nothing else in these reports leads with a figure;
        when one does and does not mean it,
        that is when a `Hero:` line earns its place beside `Source:` and `Credit:`.
        """
        first = self.blocks[0] if self.blocks else None
        return first if isinstance(first, Figure) else None

    @property
    def body(self) -> list[Block]:
        """Everything after the hero, which is the report proper."""
        return self.blocks[1:] if self.hero is not None else self.blocks

    @property
    def contributors(self) -> list[str]:
        """The people credited on the published page, by surname.

        Read from `Public Contributors:` and nothing else.
        The document carries a separate `Private Contributors:` field
        so that some names do not publish, so no fallback to it belongs here.

        The names come from person chips, which resolve to a display name,
        so this is names and not addresses.

        Sorted, because etany.org credits contributors alphabetically
        and the field they are typed into is in whoever-was-added-when order.
        """
        names = self.meta.get("public contributors", "")
        listed = [name.strip() for name in names.split(",") if name.strip()]
        return sorted(listed, key=_by_surname)

    DATE_FIELDS = ("publish due date", "final due date")
    """What the header has called the publication date, newest name first.

    The field was renamed in the document and the rename was silent:
    the date simply stopped appearing, because nothing here reads a name it
    was not told. Both are accepted so that neither a document that has been
    renamed nor a response saved before the rename loses its date."""

    @property
    def dateline(self) -> str:
        """The publication date, written out, e.g. `August 19, 2026`.

        The field is a date chip,
        so the document holds whatever short form Docs renders, `Aug 19, 2026`.
        etany.org writes the month out,
        and a published date is not the place to abbreviate three letters.

        Anything that does not parse as a date is published exactly as written:
        guessing would be worse than showing what the header says.
        """
        for name in self.DATE_FIELDS:
            if self.meta.get(name):
                return _long_date(self.meta[name])
        return ""

    @property
    def phase(self) -> str:
        """Where the report is in its own process, when that is worth saying.

        `published` is the state every reader of a published report is looking at,
        so it is the one phase that goes unmentioned:
        a banner saying `published` on a published page tells nobody anything.
        Anything else is a draft of some kind reaching someone,
        and that is exactly what they need to be told.
        """
        phase = self.meta.get("phase", "").strip()
        return "" if phase.casefold() == "published" else phase

    @property
    def slug(self) -> str:
        """The published path, e.g. `/reports/digging-out-deep-hole-sas-west`."""
        return self.meta.get("url", "")

    def headings(self, level: int | None = None) -> list[Heading]:
        """Every heading in order, or only those at one level.

        The title is not among them: it is `Document.title`, not a block,
        so a table of contents over these never lists the report itself.
        """
        return [
            b for b in self.blocks if isinstance(b, Heading) and (level is None or b.level == level)
        ]

    @property
    def images(self) -> list[Image]:
        """Every image in the document, in order, including inside footnotes.

        Deduplicated by `object_id`: the same image used twice is one file.

        The share card is among them even though it is not in `blocks`:
        `og:image` is a URL like any other and needs the file to be there.
        """
        seen: dict[str, Image] = {}
        if self.card is not None:
            seen[self.card.object_id] = self.card
        for block in _walk(self.blocks):
            for image in _images_in(block):
                seen.setdefault(image.object_id, image)
        for footnote in self.footnotes:
            for block in _walk(footnote.content):
                for image in _images_in(block):
                    seen.setdefault(image.object_id, image)
        return list(seen.values())

    @property
    def figures(self) -> list[Figure]:
        """Every figure in the document, in order, footnotes included.

        Unlike `images`, not the share card:
        it is a picture of the title rather than a figure of the report.
        """
        blocks = list(_walk(self.blocks))
        blocks += [b for note in self.footnotes for b in _walk(note.content)]
        return [b for b in blocks if isinstance(b, Figure)]

    def image_href(self, image: Image) -> str:
        """The filename as emitted, once a download has settled what it is."""
        return self.image_files.get(image.object_id, image.filename)

    def image_aspect(self, image: Image) -> float | None:
        """The written file's width over its height, if that was recorded."""
        size = self.image_shapes.get(image.object_id)
        if size is None or not size[1]:
            return None
        return size[0] / size[1]

    def warn(self, message: str) -> None:
        self.warnings.append(message)


# What a Docs date chip can render, most likely first.
# A chip is a real date, so this is a short list of ways to write one
# rather than an attempt at parsing dates in general.
DATE_FORMATS = ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y")


def _long_date(text: str) -> str:
    """`Aug 19, 2026` written out, or `text` unchanged if it is not a date."""
    for fmt in DATE_FORMATS:
        try:
            date = datetime.strptime(text, fmt).date()
        except ValueError:
            continue
        return f"{date:%B} {date.day}, {date.year}"
    return text


def _by_surname(name: str) -> tuple[str, str]:
    """Sort key for a person's name: last word first, then the whole name.

    The last word is the surname for every name these reports have carried,
    and a display name is all the document gives us.
    It guesses wrong for a surname written in more than one word,
    `van der Berg` sorting under `Berg`, which is wrong quietly and in one place.
    Casefolded so `de Vries` and `De Vries` land together.
    """
    return (name.split()[-1].casefold(), name.casefold())


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
