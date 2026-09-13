"""How a build says what it did, in a terminal.

A build's log is read while it is running, by whoever is going to go and fix
what it names, so it is laid out for that: one heading per report, its
warnings under it, and the values a warning is about picked out from the
words around them.

The rendering is separate from the warnings themselves.
`Notice` is built in `nodes.py` out of `Shown`, `Cut`, `Quoted` and `Listed`,
and its `str` is the plain markup that a redirected log holds and that the
tests assert against. This module is a second reader of the same parts:
nothing here changes what a warning says, only how it sits on the screen.

`rich`, which `typer` already brings, rather than escape sequences written
here: which terminals honour `NO_COLOR`, how wide one is, and where a line
of styled text may be broken are all questions with a right answer somebody
has already had to get right.
It is named in `pyproject.toml` all the same, because a dependency of a
dependency is not a promise.

Colour and wrapping are for a terminal only.
Piped into a file, into `less`, or into `pytest`'s capture, each warning is
written plain and whole on one line, so a log that is going to be searched
holds no escape sequences to search past and no line broken mid-sentence.
"""

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import IO

from rich.console import Console, Group, RenderableType
from rich.table import Table
from rich.text import Text

from .nodes import Cut, Listed, Notice, Quoted, Shown, Span

SHOWN = "cyan"
"""A value to go and find in the document, marked the way code is marked."""

CUT = "dim red strike"
"""The part of a value that will not survive, struck through.

The `~~` around it is kept as well as the strike:
not every terminal draws one, and a warning whose whole point is where a
sentence stops cannot rest on a terminal that does not.
"""

UNWRAPPED = 10_000
"""The width to lay a log out at when there is no terminal to fit it to.

Wider than any warning any document can produce, which is how a width says
"do not break lines": what is being written is then a file to be searched,
and a warning searched for is one that has to be on one line to be found.
"""


def for_stream(stream: IO[str] | None = None) -> Console:
    """How to write to that stream.

    `rich` decides colour, from the stream, `NO_COLOR`, `FORCE_COLOR` and the
    rest, and decides the width from the terminal where there is one.
    Asked first with nothing set, because whether there is a terminal is the
    thing that decides what to set.

    Everything `rich` would read out of a string is off: every style here is
    given to `Text` rather than spelled in square brackets, so a report
    called `Report [Draft] on 125 St` is a title and not a style tag that
    does not exist, and a document that writes `:construction:` in a line
    warned about keeps its colon and its word.
    """
    file = stream or sys.stderr
    asked = Console(file=file, highlight=False, markup=False, emoji=False)
    if asked.is_terminal:
        return asked
    return Console(file=file, width=UNWRAPPED, highlight=False, markup=False, emoji=False)


_ABOUT: ContextVar[str | None] = ContextVar("about", default=None)
"""Which report the build is in the middle of, for the notes it writes.

A context variable rather than an argument threaded through the build, because
every one of these notes is written from somewhere that has no idea which
report it is building: a sign-in asked for again in `fetch`, a `typst` that is
not installed, a count of sources looked up in the archive. Passing a name
down to each of them means passing it through everything in between, which is
most of the build, to be used by a handful of lines.

Attribution belongs in `note` and `warning` for the same reason.
A caller that has to remember to say which report it is writing about is a
caller that will not, and the one which forgets is the one whose line gets
read on a build of fourteen reports at once.

Set for the duration of one report, in the worker that builds it, so a note
written by a pooled thread is attributed to the report that thread is on and
not to the one it was on last.
"""


@contextmanager
def about(name: str) -> Iterator[None]:
    """Attribute everything written inside this to `name`.

    Reset on the way out rather than left set: the threads that build reports
    are reused, and a label left behind is a note about the next report under
    the name of the last one.
    """
    token = _ABOUT.set(name)
    try:
        yield
    finally:
        _ABOUT.reset(token)


def _said(said: str) -> str:
    """`said`, with the report it is about in front of it where there is one.

    A colon, not the ` · ` a heading uses: that separates the three fields of
    a heading, and a note is a sentence rather than a field.
    Nothing at all outside a build, which is what `fetch` on its own is: there
    is one document there, and naming it says nothing the caller did not type.
    """
    name = _ABOUT.get()
    return f"{name}: {said}" if name else said


def _spans(spans: tuple[Span, ...], console: Console) -> Text:
    """The inline pieces of a warning as one styled run of text.

    A `Shown` keeps its backticks where there is no colour, since that is
    then the only thing left saying where the value starts and stops.
    """
    text = Text()
    for span in spans:
        match span:
            case Shown(value):
                text.append(value if console.is_terminal else f"`{value}`", style=SHOWN)
            case Cut(value):
                text.append(f"~~{value}~~", style=CUT)
            case _:
                text.append(span)
    return text


def _hanging(prefix: Text, body: Text) -> Table:
    """`prefix`, then `body` wrapped in the column the prefix leaves.

    A grid of two cells rather than an indented block, so a warning too long
    for the terminal comes back under its own first word rather than under
    the mark that says a new warning has started.
    Also so a line that fits ends where its words do: an indented block is
    padded out to the width of the terminal, and a log of trailing spaces is
    one nobody can paste anywhere.
    A line too long to fit is padded to the column it wraps inside, which is
    only ever on a terminal: off one there is no width to exceed.
    """
    grid = Table.grid()
    grid.add_column()
    grid.add_column(overflow="fold")
    grid.add_row(prefix, body)
    return grid


def notice(about: Notice, console: Console, indent: str = "  ") -> RenderableType:
    """One warning, laid out.

    The sentence first, then anything the warning set apart: a `Quoted` value
    on its own lines, a `Listed` one line for each thing.
    Both are indented past the sentence, so a list of seventeen images reads
    as belonging to the warning above it rather than as seventeen more.
    """
    sentence: list[Span] = []
    apart: list[RenderableType] = []
    inner = indent + "    "
    for part in about.parts:
        match part:
            case Quoted(spans):
                apart.append(_hanging(Text(inner), _spans(spans, console)))
            case Listed(items):
                apart.extend(
                    _hanging(Text(f"{inner}• ", style="dim"), _spans(item, console))
                    for item in items
                )
            case _:
                sentence.append(part)
    said = _hanging(Text(f"{indent}! ", style="bold yellow"), _spans(tuple(sentence), console))
    return Group(said, *apart)


def built(name: str, path: str, warnings: list[Notice], console: Console) -> RenderableType:
    """One report that was built, where it went, and everything in it to fix.

    Where it went belongs on this line rather than in a list of its own at the
    end: the list was written before there was a heading to put the path on,
    and it named each report by its headline where this names it by its entry
    in `reports.toml`, so the two read as being about different reports.

    Separated by a mark and not by spaces alone.
    On a terminal the colour is what says one field has ended and the next
    begun; piped into a file there is no colour left to say it, and three
    fields with two spaces between them are one field.
    """
    heading = Text()
    heading.append("✓ ", style="bold green")
    heading.append(path, style=SHOWN)
    heading.append(" · ", style="dim")
    heading.append(name, style="bold")
    if warnings:
        heading.append(" · ", style="dim")
        heading.append(f"{len(warnings)} warning{'' if len(warnings) == 1 else 's'}", "yellow")
    return Group(heading, *(notice(warning, console) for warning in warnings))


def failed(name: str, error: str) -> RenderableType:
    """One report that was not built, and the reason, which is the message.

    Said here rather than counted here and explained elsewhere: a failure
    named twice, once with its reason and once without, is one failure read
    twice.
    """
    heading = Text()
    heading.append("✗ ", style="bold red")
    heading.append(name, style="bold")
    return Group(heading, _hanging(Text("  "), Text(error, style="red")))


def note(said: str) -> Text:
    """Something the build did differently, which is not a document's fault.

    A missing `typst`, a sign-in being asked for again, a PDF not attempted:
    nothing to go and fix in a report, and not nothing either.

    Prefixed with the report being built, because a build of a list of them
    runs several at once and writes these as they happen: a line saying three
    sources were looked up is not worth much without the report that cites
    them.
    """
    text = Text()
    text.append("· ", style="dim")
    text.append(_said(said), style="dim")
    return text


def warning(said: str) -> Text:
    """Something that went wrong and did not stop the build.

    The same mark as a document's warnings, because a reader scanning for
    what needs attention should not have to learn two.
    """
    text = Text()
    text.append("! ", style="bold yellow")
    text.append(_said(said))
    return text


def added(reports: Path, name: str, tab: str, console: Console) -> Text:
    """What `eta-publish add` wrote into the list.

    Both values back, because both were read off the document rather than
    typed, and reading them back is the only way anybody sees what they are.
    """
    text = Text()
    text.append("✓ ", style="bold green")
    text.append_text(_spans((f"{reports}: added ", Shown(name), ", tab ", Shown(tab)), console))
    return text


def summary(built_count: int, failed_count: int, warning_count: int) -> Text:
    """The one line to read if only one line is read.

    Nothing is counted that is not there: `0 failed` printed after every
    successful build teaches people to skip the line that says a build failed.
    """
    line = Text(f"{built_count} built", style="" if failed_count else "green")
    if warning_count:
        line.append(" · ", "dim").append(
            f"{warning_count} warning{'' if warning_count == 1 else 's'}", "yellow"
        )
    if failed_count:
        line.append(" · ", "dim").append(f"{failed_count} failed", "bold red")
    return line


def write(renderable: RenderableType | None, console: Console | None = None) -> None:
    """Print that, wrapped to the terminal or left alone where there is none.

    Flushed as it is written: a build says things on both streams, and a
    redirected one held back in a buffer arrives after the other, which puts
    the summary above the paths it is summarising.

    The console is asked for here where the caller has none of its own, and
    asked for each time rather than kept: it holds the stream it was built
    with, and `pytest` replaces the stream after this module is imported.
    """
    if renderable is None:
        return
    console = console or for_stream()
    console.print(renderable, soft_wrap=not console.is_terminal)
    console.file.flush()
