"""The shape every emitter shares.

Emitters are pure: tree in, string out.
Nothing here touches the network or the filesystem,
so an emitter can be tested against a fixture tree without credentials.
"""

import re
from abc import ABC, abstractmethod
from collections.abc import Callable

from ..nodes import (
    Block,
    Document,
    Figure,
    FootnoteRef,
    Heading,
    Image,
    Inline,
    LineBreak,
    List,
    Paragraph,
    Table,
    Text,
)

WARNING_MARKUP = re.compile(r"`(?P<code>[^`]*)`|~~(?P<cut>[^~]+)~~")
# `*` and not `+` for the code span, so an empty one is a span and not two
# stray backticks. A warning about a value that is not there has to show that
# it is not there, and an empty marked span is what that looks like:
# on a page a code span carries a background and a little padding,
# so an empty one is a small box with nothing in it,
# which reads as the empty string it is reporting.
"""The little markup a warning is written in, spelled as Markdown spells it.

A warning names a field, a file, or a line, and marks it with backticks
the way the rest of this project writes prose.
It strikes through the part of a value that will not survive,
which is the difference between telling somebody a string is too long
and showing them where it stops.

Each output renders both the way that output spells them,
rather than showing a reader a stray backtick or a pair of tildes.
"""


QUOTED_LINE = "> "
"""How a warning quotes the document, which is how Markdown quotes anything.

A value the warning is about is shown rather than described,
and shown as a quotation so that it is not read as more of the sentence.
"""


BULLET_LINE = "- "
"""How a warning lists the things it is about, which is how Markdown lists anything.

A warning naming one thing says it in the sentence.
A warning naming seventeen lists them,
because seventeen names run together are not a list anybody reads.
"""


def warning_markup(
    message: str,
    *,
    code: Callable[[str], str],
    cut: Callable[[str], str],
    text: Callable[[str], str],
    quote: Callable[[str], str] | None = None,
    bullets: Callable[[list[str]], str] | None = None,
) -> str:
    """`message` rendered: its marked spans, its quoted and listed lines, the rest as `text`.

    A quoted or listed line is rendered whole, after its spans are,
    so that a quotation of a value keeps whatever is marked inside it.
    Consecutive listed lines are handed over together,
    because a list is one thing rather than a run of them.
    """
    out: list[str] = []
    pending: list[str] = []

    def flush() -> None:
        if pending and bullets is not None:
            out.append(bullets(pending.copy()))
        pending.clear()

    for line in message.split("\n"):
        if bullets is not None and line.startswith(BULLET_LINE):
            pending.append(_spans(line.removeprefix(BULLET_LINE), code, cut, text))
            continue
        flush()
        quoted = quote is not None and line.startswith(QUOTED_LINE)
        rendered = _spans(line.removeprefix(QUOTED_LINE) if quoted else line, code, cut, text)
        out.append(quote(rendered) if quoted and quote is not None else rendered)
    flush()
    return "".join(out)


def _spans(
    line: str,
    code: Callable[[str], str],
    cut: Callable[[str], str],
    text: Callable[[str], str],
) -> str:
    out = []
    position = 0
    for match in WARNING_MARKUP.finditer(line):
        out.append(text(line[position : match.start()]))
        marked = match.group("code")
        out.append(code(marked) if marked is not None else cut(match.group("cut")))
        position = match.end()
    out.append(text(line[position:]))
    return "".join(out)


# The line a report introduces its contributors with.
# The header block names who they are; this says what naming them means.
CONTRIBUTORS_NOTE = (
    "We wish to acknowledge the following ETA members who contributed to "
    "this report, and without whose hard work it would not be possible:"
)


class Emitter(ABC):
    """Walks a `Document` and returns source in one output format.

    Every node kind is an abstract method, so adding one
    fails loudly in every emitter rather than being skipped by one.

    `list_` carries a trailing underscore because a method named `list`
    would shadow the builtin throughout the class body,
    and every `list[...]` annotation in this file would resolve to the method.
    """

    extension: str = ""

    separator: str = "\n"
    """What `join` puts between blocks.

    A newline is enough for HTML, where the tags say where a block ends.
    A format whose blocks are separated by a blank line says so here,
    rather than by writing `join` again.
    """

    def __init__(self) -> None:
        # Set by `emit`, the only entry point.
        # Node methods read it for document-wide context, so calling one directly fails.
        self.doc = Document()

    def emit(self, doc: Document) -> str:
        self.doc = doc
        return self.document(doc)

    # ---- dispatch ---------------------------------------------------

    def blocks(self, blocks: list[Block]) -> str:
        return self.join([self.block(b) for b in blocks])

    def block(self, node: Block) -> str:
        match node:
            case Heading():
                return self.heading(node)
            case Paragraph():
                return self.paragraph(node)
            case List():
                return self.list_(node)
            case Figure():
                return self.figure(node)
            case Table():
                return self.table(node)

    def inlines(self, content: list[Inline]) -> str:
        return "".join(self.inline(i) for i in content)

    def inline(self, node: Inline) -> str:
        match node:
            case Text():
                return self.text(node)
            case LineBreak():
                return self.line_break(node)
            case FootnoteRef():
                return self.footnote_ref(node)
            case Image():
                return self.image(node)

    # ---- overridable ------------------------------------------------

    def join(self, parts: list[str]) -> str:
        return self.separator.join(p for p in parts if p)

    @abstractmethod
    def document(self, doc: Document) -> str: ...

    @abstractmethod
    def heading(self, node: Heading) -> str: ...

    @abstractmethod
    def paragraph(self, node: Paragraph) -> str: ...

    @abstractmethod
    def list_(self, node: List) -> str: ...

    @abstractmethod
    def figure(self, node: Figure) -> str: ...

    @abstractmethod
    def table(self, node: Table) -> str: ...

    @abstractmethod
    def text(self, node: Text) -> str: ...

    @abstractmethod
    def line_break(self, node: LineBreak) -> str: ...

    @abstractmethod
    def footnote_ref(self, node: FootnoteRef) -> str: ...

    @abstractmethod
    def image(self, node: Image) -> str: ...
