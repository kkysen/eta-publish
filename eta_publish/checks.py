"""What a report has to have before it is published.

These read a parsed document and say what is missing.
They are separate from `parse.py`, which warns about what it could not read:
a document can parse perfectly and still not be ready,
and the two questions have different answers for the same file.

Every one of these is something to fix in the document rather than in the code,
which is why they are warnings on the document
and appear both in the build log and on the site's index page.
"""

from .nodes import EMAILED, Cut, Document, Figure, Listed, Quoted, Shown, plain_text
from .parse import TODO_RE

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


SEO_LIMIT = 300
"""How long a `SEO Description:` may be.

Past this a search engine truncates it,
so the sentence that decides whether anyone clicks ends mid-word,
and the writer never sees where it was cut.
"""

MAY_BE_EMPTY = frozenset({"private contributors"})
"""Fields whose emptiness says something rather than being an omission.

A report with nobody uncredited has an empty `Private Contributors:` line,
and that is the answer, not a missing one.
Every other field empty is a line somebody meant to come back to.
"""


def check(doc: Document) -> None:
    """Warn about everything a published report should not be missing."""
    _check_figures(doc)
    _check_named(doc)
    _check_review(doc)
    _check_contributors(doc)
    _check_tracked(doc)

    if not doc.meta:
        # `parse` has already said the header is missing or empty.
        # Nine more warnings saying the same thing would bury it.
        return

    for field in REQUIRED_FIELDS:
        if field not in doc.meta:
            doc.warn("the {} section has no {} line", Shown("Header"), Shown(f"{_titled(field)}:"))
        elif field not in MAY_BE_EMPTY and not doc.meta[field].strip():
            doc.warn("the {} section leaves {} empty", Shown("Header"), Shown(f"{_titled(field)}:"))

        if TODO_RE.search(doc.meta.get(field, "")):
            # The header is consumed before the body walk that flags these,
            # so `Short: TODO` would otherwise reach the page unremarked.
            doc.warn("{} is still marked unfinished", Shown(f"{_titled(field)}:"))

    seo = doc.meta.get("seo description", "")
    if len(seo) > SEO_LIMIT:
        # The whole description, with the part that will not survive struck
        # through: which words are lost is the thing to fix.
        doc.warn(
            f"{{}} is {len(seo)} characters, over the {SEO_LIMIT} a search result shows:{{}}",
            Shown("SEO Description:"),
            Quoted(seo[:SEO_LIMIT], Cut(seo[SEO_LIMIT:])),
        )


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


def _check_contributors(doc: Document) -> None:
    """Two contributors with no comma between them, which reads as one person.

    Only detectable where an address was written beside a name,
    because the address is what says the name before it has ended.
    Two bare names run together are two words, and nothing here can tell
    those from a double-barrelled surname.
    """
    for entry in doc.meta.get("public contributors", "").split(","):
        emailed = EMAILED.search(entry)
        if emailed is not None and entry[emailed.end() :].strip():
            doc.warn(
                "the {} line reads {} as one contributor; a comma is missing after the address",
                Shown("Public Contributors:"),
                Shown(entry.strip()),
            )


def _check_figures(doc: Document) -> None:
    """Every picture is described and attributed, or says which one is not.

    Named by the file it is written as rather than by its Docs object id,
    which nothing in the document shows anybody.
    """
    for block in doc.blocks:
        if not isinstance(block, Figure):
            continue
        named = Shown(block.image.filename)
        # The template and its values together, because the two warnings differ
        # in both: one names a `Credit:` line and the other names nothing.
        for template, values, content in (
            ("the image {} has no caption", (named,), block.caption),
            ("the image {} has no {} line", (named, Shown("Credit:")), block.credit),
        ):
            if not content:
                doc.warn(template, *values)


def _check_named(doc: Document) -> None:
    """Which pictures the document never said what they are.

    A `Source:` line is what names an image, and the name is the published URL.
    Without one the URL is a hash of a Docs object id:
    it says nothing about the picture,
    and it moves if the image is ever replaced.
    A line that names no file, `Image Source` or `SVG: TODO`,
    leaves the image as unnamed as no line at all.

    One warning for all of them rather than one each:
    they are one fix repeated, seventeen times in SAS West.
    """
    unnamed = [block for block in doc.blocks if isinstance(block, Figure) and not block.image.named]
    if not unnamed:
        return
    # One to a line, each with what the report says the picture is:
    # the difficulty of fixing these is working out which picture
    # `img-6fb0f9c4` is.
    listed = Listed(*((Shown(block.image.filename), _describe(block)) for block in unnamed))
    are = "is" if len(unnamed) == 1 else "are"
    doc.warn(
        f"{plural(len(unnamed), 'image')} {are} unnamed, so each publishes under a "
        f"hash; give each a {{}} line naming its file:{{}}",
        Shown("Source:"),
        listed,
    )


TRACKING = ("utm_",)
"""Query parameters that say where a link was copied from, not what it points at.

`utm_source`, `utm_medium` and the rest are what an analytics tag looks like,
and they arrive by pasting a link out of somewhere that added them.
The prefix rather than a list of names: they are an open set by design,
and anything beginning `utm_` is one of them whatever follows.
"""


def _check_tracked(doc: Document) -> None:
    """Which sources are cited with an analytics tag still on the URL.

    Left on, it is published as part of the citation, and it says where whoever
    added the link was reading rather than anything about the page. SAS West
    cited a `masstransitmag.com` press release as `?utm_source=chatgpt.com`.

    It also costs the source its archived copy, or nearly:
    nothing had ever captured that URL with the parameter on it,
    because nothing links to it that way. The replay drops tracking parameters
    before it looks, so it found the capture anyway, and the index, which does
    not, had no row for it at all. A build before the replay landed published
    that source as `not archived` with two captures of the page sitting there.

    One warning for all of them, like `_check_named`: it is one fix repeated.
    """
    tracked = [
        source
        for source in doc.sources
        if any(f"?{tag}" in source or f"&{tag}" in source for tag in TRACKING)
    ]
    if not tracked:
        return
    listed = Listed(*((Shown(_tag(source)), " on ", Shown(source)) for source in tracked))
    doc.warn(
        f"{plural(len(tracked), 'source')} still carries the tag it was copied with; "
        f"take it off the link in the doc:{{}}",
        listed,
    )


def _tag(source: str) -> str:
    """The tracking parameters on `source`, for saying which to take off."""
    query = source.partition("?")[2].partition("#")[0]
    return "&".join(
        part for part in query.split("&") if any(part.startswith(tag) for tag in TRACKING)
    )


DESCRIPTION_LIMIT = 70
"""How much of a caption is enough to tell one picture from another."""


def _describe(block: Figure) -> str:
    """What the report says this picture is, for telling it from the others.

    The caption, because that is what a reader is told the picture is.
    Its alt text where there is no caption,
    which is what a reader who cannot see it is told instead.
    """
    description = plain_text(block.caption).strip() or block.image.alt.strip()
    if not description:
        return ""
    if len(description) > DESCRIPTION_LIMIT:
        description = description[:DESCRIPTION_LIMIT].rstrip() + "..."
    return f": {description}"


def _check_review(doc: Document) -> None:
    """Nothing is published with the editing still going on in it.

    A build resolves suggestions away and never sees comments,
    so what publishes from a document under review looks finished
    and is a snapshot of an argument nobody has finished having.

    Both counts are this tab's: the document these reports live in has eight
    tabs and 46 comments open across them, against three on the one that
    publishes, so a count for the file would be a number nobody could act on.
    """
    if doc.open_suggestions:
        doc.warn(
            f"{plural(doc.open_suggestions, 'suggestion')} still open on this tab; "
            "the build publishes the document without them, as it reads today"
        )
    if doc.open_comments:
        doc.warn(f"{plural(doc.open_comments, 'comment thread')} still open on this tab")


def plural(count: int, thing: str) -> str:
    return f"{count} {thing}" if count == 1 else f"{count} {thing}s"
