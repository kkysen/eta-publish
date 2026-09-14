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

import re
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import override

# ---- inline content ------------------------------------------------


@dataclass(frozen=True)
class Archived:
    """Where a snapshot of one source lives, or why there is none.

    `snapshot` and `timestamp` are the capture; `error` is a capture that was
    tried and did not happen, which is a third state and not the absence of one.
    A source nothing has ever tried is simply missing from the record, and a
    later build submits it; one recorded here with an `error` is one a later
    build already knows the answer for, and so does not submit again and again
    forever. Some URLs cannot be archived at all: a page behind a login, and
    every `mp.weixin.qq.com` link the reports cite.
    """

    snapshot: str = ""
    timestamp: str = ""
    """When the snapshot was taken, as the 14 digits Wayback writes, or the
    date the attempt failed."""
    error: str = ""

    @property
    def date(self) -> str:
        """The capture written out, e.g. `May 3, 2024`.

        A reader checking a source against the page it cites is asking when the
        report read it, and 14 digits is not an answer anyone reads.
        Whatever does not parse as a date is shown as it is, which is the same
        choice `dateline` makes and for the same reason.
        """
        return _long_date(self.timestamp[:8])


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

    named: bool = False
    """Whether the document said which file this is, in a `Source:` line.

    Not a question the filename can answer: an image with no name publishes
    under `img-` and a hash, and a `Source:` line is free to name a file
    called `img-something.jpg`."""

    alt: str = ""
    source_uri: str | None = None
    crop: Crop = field(default_factory=lambda: Crop())
    vector: Vector | None = None


Inline = Text | LineBreak | FootnoteRef | Image


def plain_text(content: list[Inline]) -> str:
    """Inline content with every mark dropped, for reading rather than rendering.

    A table of contents entry, the file a `Source:` line names,
    the caption an image borrows when Docs gave it no description:
    each wants what the run says, not how it is set.
    A break, a footnote reference, and an image say nothing in a line,
    so each contributes nothing.
    """
    return "".join(i.text for i in content if isinstance(i, Text))


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


SLOT = "{}"
"""Where a warning's template takes a value.

Templates are written here rather than read from a document,
so nothing a report says can be mistaken for one.
"""


def filled[T](template: str, values: tuple[T, ...]) -> tuple[str | T, ...]:
    """`template` split at its `{}`, with `values` in their places.

    The words and the values stay separate spans rather than becoming one
    string, because that is what lets each of them be rendered as what it is:
    a value is coloured, or quoted, or struck through, and words are words.
    Interpolating first and looking for the values again afterwards is the
    other way round, and it has to guess.

    Shared by a document's warnings and by the log's own notes, so both say a
    value the same way and neither has to be read twice.
    """
    said = template.split(SLOT)
    if len(said) != len(values) + 1:
        raise ValueError(f"{template!r} has {len(said) - 1} {SLOT} for {len(values)} values")
    parts: list[str | T] = [said[0]]
    for value, rest in zip(values, said[1:], strict=True):
        parts.append(value)
        parts.append(rest)
    return tuple(part for part in parts if part != "")


@dataclass(frozen=True)
class Shown:
    """A value a warning shows rather than says.

    A field name, a filename, a line quoted back.
    Emitters mark it the way they mark code, because it is something exact
    to go and find rather than words being spoken.
    """

    value: str


@dataclass(frozen=True)
class Cut:
    """The part of a value that will not survive.

    Struck through, which is the difference between telling somebody
    a string is too long and showing them where it stops.
    """

    value: str


@dataclass(frozen=True)
class Quoted:
    """A value given a line of its own.

    Long enough that running it into the sentence would leave the reader
    unsure where the sentence ended and the document began.
    """

    spans: tuple[Span, ...]

    def __init__(self, *spans: Span) -> None:
        object.__setattr__(self, "spans", spans)


@dataclass(frozen=True)
class Listed:
    """One line for each of the things a warning is about.

    A warning naming one thing says it in the sentence.
    A warning naming seventeen lists them,
    because seventeen names run together are not a list anybody reads.
    """

    items: tuple[tuple[Span, ...], ...]

    def __init__(self, *items: tuple[Span, ...]) -> None:
        object.__setattr__(self, "items", items)


type Span = str | Shown | Cut
type Part = Span | Quoted | Listed


@dataclass(frozen=True)
class Notice:
    """One warning, in the pieces it is made of.

    Not a marked-up string: a warning is built here and rendered by three
    emitters, and marking it up at one end to recover it by parser at the
    other is how a filename with a backtick in it came out the far end
    having re-paired the spans around it.

    `str` writes the markup and nothing reads it:
    it is what the log prints and what a test asserts against.
    """

    parts: tuple[Part, ...]

    @override
    def __str__(self) -> str:
        return "".join(_written(part) for part in self.parts)


def _written(part: Part) -> str:
    """One part as the log writes it, which is how this project writes prose."""
    match part:
        case Shown(value):
            return f"`{value}`"
        case Cut(value):
            return f"~~{value}~~"
        case Quoted(spans):
            return "\n> " + "".join(_written(span) for span in spans)
        case Listed(items):
            return "".join("\n- " + "".join(_written(span) for span in item) for item in items)
        case _:
            return part


@dataclass
class Document:
    title: str = ""

    file_title: str = ""
    """What the document is called in Drive, which is not what it is called here.

    The headline is the report's title; this is the working name it is filed under,
    and the only thing `reports.toml` can be checked against."""

    open_suggestions: int = 0
    """Suggestions still open on the tab this was read from.

    Recorded by the fetch, because the response a build reads has them resolved away.
    Zero for a response saved before the fetch counted them, which cannot be helped:
    the count is not in the file to be read."""

    open_comments: int = 0
    """Comment threads still open on this tab.

    Zero where the fetch could not read them, which is not the same as none:
    the count is carried over from the last build that could."""

    tab_title: str = ""
    """What the tab this was read from is called.

    A `?tab=` id is opaque, so it is not something a person can check by reading it.
    This is the same choice written in words."""
    meta: dict[str, str] = field(default_factory=dict)
    """The doc's leading `Header` section, lowercased keys.
    Unrecognized keys are kept rather than dropped."""

    has_header: bool = False
    """Whether the document had a `Header` section for `meta` to be read from.

    Not the same as an empty `meta`, which is also what a `Header` section
    holding no `Key: value` lines leaves behind.
    The two are different mistakes and want different things said about them:
    a missing section is usually one whose heading is styled as body text,
    where an empty one is a section nobody filled in."""

    blocks: list[Block] = field(default_factory=list)
    footnotes: list[Footnote] = field(default_factory=list)
    warnings: list[Notice] = field(default_factory=list)

    card: Image | None = None
    """A wide image with the title set into it,
    placed above the headline for whatever links to the report to show as a thumbnail.

    Not part of the report, so not in `blocks`: it publishes as `og:image` and nowhere else."""

    image_files: dict[str, str] = field(default_factory=dict)
    """Docs object id to the filename actually written, extension included.

    Only fetching can know it:
    a Docs `inlineObject` says nothing about what kind of file it is,
    and a vector named alongside a raster is written under a different name entirely.
    `images.download` fills this in as it writes each file,
    and a build that skips the download reads it back from `images.json`,
    which every build that downloaded left behind and which such a build requires.

    An image missing from here is one nothing has ever written,
    and `image_href` refuses to name it rather than guessing at a stem.
    """

    image_shapes: dict[str, tuple[int, int]] = field(default_factory=dict)
    """Docs object id to the pixel size of the file actually written.

    From the same record as `image_files`, and for the same reason:
    Docs says how large an image is placed, not how large it is,
    and the crop applied here changes the shape of the file without the document knowing.
    An SVG has no pixel size to read, so it is one this is empty for.
    """

    archives: dict[str, Archived] = field(default_factory=dict)
    """Source URL to the snapshot of it, keyed by the original and never by the
    snapshot.

    Filled in from `archive.json`, which is committed, and added to by a build
    that submits the sources not yet in it. A document whose own href already
    points at a snapshot seeds this at parse time, so a link written by hand as
    an archive is one already archived rather than one to archive again.
    """

    @property
    def hero(self) -> Figure | None:
        """The figure a report opens with, if it opens with one.

        The document puts it under the headline,
        so it belongs there rather than after a table of contents it should be introducing.

        Recognized by position: nothing else in these reports leads with a figure,
        and when one does and does not mean it,
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

        Read from `Public Contributors:` and nothing else:
        the document carries a separate `Private Contributors:` field
        so that some names do not publish.

        Where Docs cannot resolve a person chip to a display name it renders
        as the address, and the field is written `Alon Levy (alon@example.org)`
        with the name typed and the chip beside it.
        A byline is names, so the address is dropped.

        Sorted, because `etany.org` credits contributors alphabetically
        and the field they are typed into is in whoever-was-added-when order.
        """
        names = self.meta.get("public contributors", "")
        listed = [_named(name) for name in names.split(",")]
        return sorted((name for name in listed if name), key=_by_surname)

    @property
    def dateline(self) -> str:
        """The publication date, written out, e.g. `August 19, 2026`.

        The field is a date chip,
        so the document holds whatever short form Docs renders, `Aug 19, 2026`,
        where `etany.org` writes the month out.

        Anything that does not parse as a date is published exactly as written:
        guessing would be worse than showing what the header says.
        """
        return _long_date(self.meta.get("publish due date", ""))

    @property
    def phase(self) -> str:
        """Where the report is in its own process, when that is worth saying.

        `published` is the state every reader of a published report is looking at,
        so it is the one phase that goes unmentioned.
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
        for block in self._every_block():
            for image in _images_in(block):
                seen.setdefault(image.object_id, image)
        return list(seen.values())

    @property
    def sources(self) -> list[str]:
        """Every external link the report cites, in the order it cites them.

        Deduplicated by URL, first use first, the way `images` deduplicates by
        object id: one page cited six times is one source, and renumbering it
        because a later section cites it again would renumber everything after.

        Document order and nothing else decides the numbering. Reading it off
        the archive record instead would make the numbers a property of which
        captures happened to have succeeded, and an offline build against a
        partial record would renumber the whole report.
        """
        seen: dict[str, None] = {}
        for block in self._every_block():
            for href in _links_in(block):
                if is_source(href):
                    seen.setdefault(href, None)
        return list(seen)

    def archived(self, source: str) -> Archived | None:
        """Where `source` is archived, with its own fragment put back.

        The record is keyed by the document, so a capture is shared by every
        page of it the report cites. The fragment goes back on the way out,
        which is what makes the archived copy of a claim about page 28 open on
        page 28 rather than on the cover.

        A `#page=` citation is served raw, because the ordinary Wayback URL for
        a PDF is not the PDF. It is an HTML page carrying the capture toolbar
        with the file inside it, so the browser applies `#page=50` to that
        wrapper, which has no page 50, and the reader gets the cover. Asked for
        with `id_`, the same capture comes back as the PDF itself and the
        viewer opens where the citation meant. Measured in a browser, on the
        `R211 Tech Spec.pdf` capture the report already cites: `50 / 819`.

        Only for those. An HTML capture is the archived document itself, so an
        anchor in it already resolves, and the ordinary URL is the one that
        keeps the toolbar and serves the page's images and stylesheets from the
        archive rather than from a live site that may no longer have them.
        """
        base, hash_, fragment = source.partition("#")
        found = self.archives.get(base)
        if found is None or not found.snapshot or not hash_:
            return found
        snapshot = found.snapshot
        if fragment.startswith(PDF_PAGE):
            snapshot = RAW.sub(r"\1id_/", snapshot, count=1)
        return replace(found, snapshot=f"{snapshot}{hash_}{fragment}")

    @property
    def source_uses(self) -> dict[str, int]:
        """How many times each source is cited, which is how many backlinks it has."""
        uses: dict[str, int] = {}
        for block in self._every_block():
            for href in _links_in(block):
                if is_source(href):
                    uses[href] = uses.get(href, 0) + 1
        return uses

    @property
    def figures(self) -> list[Figure]:
        """Every figure in the document, in order, footnotes included.

        Unlike `images`, not the share card:
        it is a picture of the title rather than a figure of the report.
        """
        return [b for b in self._every_block() if isinstance(b, Figure)]

    def _every_block(self) -> Iterator[Block]:
        """Every block of the report, then every block of its footnotes.

        The body first, because that is the order the document is read in.
        Descends into lists and table cells,
        so nothing is missed for sitting inside something else.
        """
        yield from _walk(self.blocks)
        for footnote in self.footnotes:
            yield from _walk(footnote.content)

    def image_href(self, image: Image) -> str:
        """The filename as emitted, which is the name of the file that was written.

        There is no answer for an image nothing wrote.
        The stem is not one: an extension is learned by fetching,
        so `images/img-d4734d4b` is a path no browser serves as an image
        and `typst` will not open at all,
        and a page that links one is a page with a hole in it
        that nothing downstream reports as this.
        """
        written = self.image_files.get(image.object_id)
        if written is None:
            raise ValueError(
                f"image {image.object_id} was never written, so nothing says what it "
                f"is called; an extension is learned by fetching, and `{image.filename}` "
                f"without one is not a picture anything can serve"
            )
        return written

    def image_aspect(self, image: Image) -> float | None:
        """The written file's width over its height, if that was recorded."""
        size = self.image_shapes.get(image.object_id)
        if size is None or not size[1]:
            return None
        return size[0] / size[1]

    def warn(self, template: str, *values: Part) -> None:
        """Warn, with `{}` in `template` wherever a value goes.

        The template is written here and the values come from the document,
        which is why they are handed over separately rather than formatted in:
        a value is never read as markup, whatever it happens to contain.
        """
        self.warnings.append(Notice(filled(template, values)))


# What a Docs date chip can render, most likely first.
# A chip is a real date, so this is a short list of ways to write one
# rather than an attempt at parsing dates in general.
DATE_FORMATS = ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%Y%m%d")


def _long_date(text: str) -> str:
    """`Aug 19, 2026` written out, or `text` unchanged if it is not a date."""
    for fmt in DATE_FORMATS:
        try:
            date = datetime.strptime(text, fmt).date()
        except ValueError:
            continue
        return f"{date:%B} {date.day}, {date.year}"
    return text


def addressed(entry: str) -> tuple[str, str] | None:
    """One listed contributor split around the address written beside their name.

    The name, and whatever was written after the closing bracket,
    which is a second contributor whose comma is missing.
    `None` where the entry carries no address, which is the ordinary case:
    a resolved person chip is a name and nothing else.

    Docs writes an address beside a name when it cannot resolve a person chip
    to a display name: the chip renders as the address,
    so the name is typed and the chip put beside it.
    The name is the half worth publishing, and `etany.org` credits names.

    Not an address by any standard, deliberately:
    a bracketed run with no spaces and something either side of an `@`.
    What is being recognized is the Docs spelling, not an email,
    and a stricter reading would drop a name
    over an address this has no business having an opinion about.
    """
    name, bracket, rest = entry.partition("(")
    if not bracket:
        return None
    address, closed, after = rest.partition(")")
    address = address.strip()
    local, at, domain = address.partition("@")
    if not closed or not at or not local or not domain:
        return None
    if any(character.isspace() for character in address):
        return None
    return name.strip(), after.strip()


def _named(entry: str) -> str:
    """One listed contributor, as a byline writes them."""
    found = addressed(entry)
    if found is None:
        return entry.strip()
    name, after = found
    return f"{name} {after}".strip()


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


def _walk(blocks: list[Block]) -> Iterator[Block]:
    """Yield every block, descending into lists and table cells."""
    for block in blocks:
        yield block
        if isinstance(block, Table):
            for row in block.rows:
                for cell in row:
                    yield from _walk(cell)


SNAPSHOT = re.compile(
    r"^https?://web\.archive\.org/web/(\d{4,14})[a-z_]*/(?P<url>https?://.+)$",
    re.IGNORECASE,
)
"""A Wayback URL, as the timestamp it was taken at and the page it is of.

The digits are followed by a modifier on some of these, `id_` for the
unrewritten original and `im_` for an image, which says how Wayback serves the
capture rather than which capture it is.
"""


def unwrap_snapshot(href: str) -> tuple[str, Archived | None]:
    """A link split into the page it is of and the capture it is, if it is one.

    A report that cites `web.archive.org/web/.../nypost.com/...` has already
    done by hand what this does: the source is the Post article, and the
    snapshot is the capture already named. Left wrapped it would be a source of
    its own, keyed in the record under a URL that is itself the answer, and the
    same article cited bare elsewhere would be a second source saying the same
    thing.
    """
    found = SNAPSHOT.match(href)
    if found is None:
        return href, None
    stamp, url = found.group(1), found.group("url")
    # Rebuilt rather than kept as written, so that a capture cited with a
    # modifier and the same capture cited without one are one snapshot.
    # Of the document rather than of the page of it named here, because that is
    # what a capture is, and `Document.archived` puts the fragment back.
    document = document_url(url)
    return url, Archived(
        snapshot=f"https://web.archive.org/web/{stamp}/{document}", timestamp=stamp
    )


PDF_PAGE = "page="
"""The fragment a link to a page of a PDF carries.

An instruction to the PDF viewer rather than an anchor in a document, which is
why it is the one fragment the ordinary Wayback URL swallows.
"""

RAW = re.compile(r"(https?://web\.archive\.org/web/\d{4,14})/")
"""Where the modifier goes in a Wayback URL, between the timestamp and the page.

`id_` is the one that says to serve the capture as it was rather than rewritten
and wrapped.
"""


def document_url(url: str) -> str:
    """A link's address without its fragment, which is the thing that is archived.

    A fragment never reaches a server. `#page=28` is an instruction to the PDF
    viewer once the file has arrived, and `#:~:text=` is one to the browser, so
    fifteen citations of fifteen pages of one MTA PDF are fifteen citations of
    one document and one capture of it. Asking for fifteen would spend fifteen
    of the day's captures on the same file and get fifteen snapshots of it,
    taken at fifteen moments.
    """
    return url.partition("#")[0]


def is_source(href: str | None) -> bool:
    """Whether a link is a citation of something outside the report.

    An anchor is a place in this page, `mailto:` is a person, and `etany.org`
    is the site the report is published on: none of the three is a source that
    can go away, and archiving the site into itself would say nothing.
    """
    if not href:
        return False
    if not href.startswith(("http://", "https://")):
        return False
    return "etany.org" not in href


def _links_in(block: Block) -> list[str]:
    """Every href the block's own inlines carry, in order."""
    match block:
        case Figure():
            # `Figure.source` is left out: it names the original file in Drive
            # for whoever assembles the report, no emitter publishes it, and a
            # Sources entry for a link nothing on the page points at is an
            # entry whose way back into the text does not exist.
            return _hrefs(block.caption) + _hrefs(block.credit)
        case Paragraph() | Heading():
            return _hrefs(block.content)
        case List():
            return [href for item in _items(block.items) for href in _hrefs(item.content)]
    return []


def _hrefs(content: list[Inline]) -> list[str]:
    return [i.href for i in content if isinstance(i, Text) and i.href]


def _images_in(block: Block) -> list[Image]:
    match block:
        case Figure():
            return [block.image]
        case Paragraph() | Heading():
            return [i for i in block.content if isinstance(i, Image)]
        case List():
            return [i for item in _items(block.items) for i in item.content if isinstance(i, Image)]
    return []


def _items(items: list[ListItem]) -> Iterator[ListItem]:
    for item in items:
        yield item
        yield from _items(item.children)
