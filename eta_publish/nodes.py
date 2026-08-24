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

from __future__ import annotations

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
class FootnoteRef:
    """A reference to a footnote, identified by the Docs footnote id.

    Display numbering is assigned by the parser in document order, so it
    can never disagree between the reference and the definition.
    """

    footnote_id: str
    number: int


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


Inline = Text | FootnoteRef | Image


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

    @property
    def slug(self) -> str:
        """The published path, e.g. `/reports/digging-out-deep-hole-sas-west`."""
        return self.meta.get("url", "")

    def headings(self, level: int = 2) -> list[Heading]:
        """Headings at one level, for building a table of contents."""
        return [b for b in self.blocks if isinstance(b, Heading) and b.level == level]

    def warn(self, message: str) -> None:
        self.warnings.append(message)
