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
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from threading import Lock, RLock
from typing import IO

from rich.console import Console, Group, RenderableType
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from .nodes import Cut, Highlighted, Listed, Notice, Quoted, Shown, Span, filled

SHOWN = "cyan"
"""A value to go and find in the document, marked the way code is marked."""

CUT = "dim red strike"
"""The part of a value that will not survive, struck through.

The `~~` around it is kept as well as the strike:
not every terminal draws one, and a warning whose whole point is where a
sentence stops cannot rest on a terminal that does not.
"""

MARKED = "black on yellow"
"""The part of a value a warning is pointing at, highlighted.

Yellow because it is a highlighter, and because reverse video is whatever
the terminal's foreground happens to be: white on a white-on-black theme,
which is a mark nobody reads as one. Black on top of it rather than the
theme's own foreground, which can be too pale to sit on yellow.
"""

LINK = "underline"
"""A URL in a sentence, marked as the thing to go and open.

Underlined rather than coloured: `SHOWN` is for a value to go and find in a
document or type into a shell, and a link is neither.
The terminal is told it is a link as well, by the escape the one that supports
it uses, so a URL too long to be worth retyping can be clicked instead.
"""

UNWRAPPED = 10_000
"""The width to lay a log out at when there is no terminal to fit it to.

Wider than any warning any document can produce, which is how a width says
"do not break lines": what is being written is then a file to be searched,
and a warning searched for is one that has to be on one line to be found.
"""


_CONSOLES: dict[IO[str], Console] = {}
"""One console per stream, so everything written to a stream goes through one.

`rich` draws a bar by taking over the bottom of the screen, and it can only
do that for lines it is given: a line printed through a second console of its
own knows nothing about the bar and lands on top of it.

Kept by stream rather than one for the process, because `pytest` replaces the
stream after this module is imported, and a console built on the old one
writes where nothing is looking.
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
    kept = _CONSOLES.get(file)
    if kept is not None:
        return kept
    asked = Console(file=file, highlight=False, markup=False, emoji=False)
    if not asked.is_terminal:
        asked = Console(file=file, width=UNWRAPPED, highlight=False, markup=False, emoji=False)
    _CONSOLES[file] = asked
    return asked


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


def _sentence(
    template: str,
    values: tuple[Span | Linked, ...],
    console: Console | None,
    plain: str = "",
) -> Text:
    """One note or warning: who it is about, then what it says.

    The name is a value, marked the way `added` marks the same name it read
    off the same list: a note is a sentence with a report's name inside it,
    and a name inside a sentence is picked out or it runs into the words
    around it. A heading names a report bold and behind a ` · ` instead,
    because there the name is a field and not part of a sentence.
    It is put in front as a span of its own, like every other value here, so
    a report called `` `Draft` on 125 St `` keeps its marks and its words.
    A colon after it, not the ` · ` a heading uses: that separates the fields
    of a heading, and a note is a sentence rather than a field.
    No name at all outside a build, which is what `fetch` on its own is: there
    is one document there, and naming it says nothing the caller did not type.

    The console is asked for where the caller has none, as `write` does, and
    for the same reason: whether there is a terminal is what decides whether a
    value is coloured or left in its backticks.
    """
    console = console or for_stream()
    name = _ABOUT.get()
    spans = filled(template, values)
    if name:
        spans = (Shown(name), ": ", *spans)
    return _spans(spans, console, plain)


@dataclass(frozen=True)
class Linked:
    """A URL a message names, given to `note` where the message is written.

    Here rather than in `nodes.py` beside `Shown`, because only a terminal has
    anywhere to put a link: no emitter renders one, and widening the `Span` a
    document's warnings are made of would hand every emitter a case it has no
    answer for.
    """

    value: str


def _spans(spans: tuple[Span | Linked, ...], console: Console, plain: str = "") -> Text:
    """The inline pieces of a warning as one styled run of text.

    A `Shown` keeps its backticks where there is no colour, since that is
    then the only thing left saying where the value starts and stops.

    `plain` is the style for the words around the values, for a line that is
    written in a style of its own: a note is dim, and a value in it is the
    colour a value is and not a dim version of it, which is mud.
    """
    text = Text()
    for span in spans:
        match span:
            case Shown(value):
                text.append(value if console.is_terminal else f"`{value}`", style=SHOWN)
            case Cut(value):
                text.append(f"~~{value}~~", style=CUT)
            case Highlighted(before, marked, after):
                if console.is_terminal:
                    text.append(before, style=SHOWN)
                    text.append(marked, style=MARKED)
                    text.append(after, style=SHOWN)
                else:
                    text.append(f"`{span.value}`", style=SHOWN)
            case Linked(value):
                # Left exactly as written either way: a URL is already the
                # thing it names, so there is nothing to take out on a
                # terminal and nothing to put back off one.
                text.append(value, style=f"{LINK} link {value}" if console.is_terminal else plain)
            case _:
                text.append(span, style=plain)
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

    The reason is the text of whatever was raised, from anywhere in a build,
    and it arrives as one string with nothing saying which part of it is a
    value. So it is written as it came, backticks and all, which is what a log
    holds anyway.
    """
    heading = Text()
    heading.append("✗ ", style="bold red")
    heading.append(name, style="bold")
    return Group(heading, _hanging(Text("  "), Text(error, style="red")))


def note(template: str, *values: Span | Linked, console: Console | None = None) -> Text:
    """Something the build did differently, which is not a document's fault.

    A missing `typst`, a sign-in being asked for again, a PDF not attempted:
    nothing to go and fix in a report, and not nothing either.

    Prefixed with the report being built, because a build of a list of them
    runs several at once and writes these as they happen: a line saying three
    sources were looked up is not worth much without the report that cites
    them.

    Written as `Document.warn` writes a warning, with `{}` where a value goes
    and the value handed over as what it is: a `Shown` for a path or a command,
    a `Linked` for a URL. A message this codebase did not write, which is the
    text of an exception a tool raised, is one value and no template.
    """
    text = Text()
    text.append("· ", style="dim")
    text.append_text(_sentence(template, values, console, plain="dim"))
    return text


STEP = 10
"""How often a build with no terminal says how far along it is, as a percentage.

A bar redraws in place and costs a terminal nothing. A redirected log has no
in place, so it gets a line at every tenth instead: ten lines is a thing to
scroll past, and a hundred and nine is the log.
"""

_BAR: Progress | None = None
_BAR_LOCK = RLock()
"""The one bar a build draws, however many reports are being built at once.

`rich` draws by taking over the bottom of the screen, and two displays cannot
both have it: a second report opening its own bar is what overwrites the
first one's line and pushes everything else around. One bar with a row per
report says the same thing and is the only one drawing.
"""


def _bar(console: Console) -> Progress:
    """The build's bar, started if this is the first thing to want one."""
    global _BAR
    if _BAR is None:
        _BAR = Progress(
            # The words first, as every other line of a build reads: what is
            # happening, then how far along it is, then how long it has been.
            TextColumn("  [dim]{task.description}[/dim]"),
            BarColumn(bar_width=24),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
            # Gone once it is done, because the line that follows says the
            # same thing in the past tense and two of them is one too many.
            transient=True,
            # Redrawn where it is advanced instead, under the lock every
            # other line is written under: a timer of its own is a writer
            # nothing else can wait for.
            auto_refresh=False,
        )
        _BAR.start()
    return _BAR


def _done(task: TaskID) -> None:
    """Take that row off the bar, and the bar away when it holds no more."""
    global _BAR
    with _BAR_LOCK:
        if _BAR is None:
            return
        _BAR.remove_task(task)
        if not _BAR.tasks:
            _BAR.stop()
            _BAR = None
        else:
            _BAR.refresh()


@contextmanager
def progress(
    template: str, total: int, console: Console | None = None
) -> Iterator[Callable[[], None]]:
    """Say how far along something long is, and yield what to call as it goes.

    Checking a report against the archive is a hundred and nine questions
    to a service that
    answers in its own time, and a build that says nothing for two minutes is
    one somebody kills. What it says is the same either way; how it says it
    depends on whether anybody is watching it happen.

    The elapsed time is on the row because the count is not enough to tell a
    slow answer from a stuck one: two sources in flight and a service taking
    a minute over each is a bar that sits at 24% and is working.

    The returned callable is called from the threads doing the work,
    so what it counts is kept under a lock.
    """
    console = console or for_stream()
    counted = 0
    lock = Lock()
    said = f"{_ABOUT.get()} · {template}" if _ABOUT.get() else template
    if not console.is_terminal:
        reported = 0

        def along() -> None:
            nonlocal counted, reported
            with lock:
                counted += 1
                percent = counted * 100 // total
                if percent >= reported + STEP or counted == total:
                    reported = percent - percent % STEP
                    write(note(f"{said}: {counted} of {total}", console=console), console)

        yield along
        return

    with _BAR_LOCK:
        bar = _bar(console)
        task = bar.add_task(said, total=total)
        bar.refresh()

    def advance() -> None:
        with lock, _BAR_LOCK:
            bar.advance(task)
            bar.refresh()

    try:
        yield advance
    finally:
        _done(task)


def warning(template: str, *values: Span | Linked, console: Console | None = None) -> Text:
    """Something that went wrong and did not stop the build.

    The same mark as a document's warnings, because a reader scanning for
    what needs attention should not have to learn two.

    Takes its values as `note` does, and for the same reason.
    """
    text = Text()
    text.append("! ", style="bold yellow")
    text.append_text(_sentence(template, values, console))
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

    The console is asked for here where the caller has none of its own.
    One console per stream, kept: a bar is drawn by taking over the bottom of
    the screen, and a line written through a console that does not know about
    it lands on top of it.
    """
    if renderable is None:
        return
    console = console or for_stream()
    # Under the bar's lock, so a line is never written into the gap between
    # the bar erasing its row and drawing it again.
    with _BAR_LOCK:
        console.print(renderable, soft_wrap=not console.is_terminal)
    console.file.flush()
