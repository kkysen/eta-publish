"""Lay out the emitted HTML, and the CSS and JavaScript inside it.

The emitter's job is what the page says; this is where it sits on the line.
Both outputs are committed and read as diffs, and a paragraph on one line
reports a corrected word as a changed paragraph.

`biome` rather than a formatter written here: whether a line break is safe
in HTML is a question about which elements are inline, and getting it wrong
welds two words together on the page. A stylesheet and a script embedded in
the page are formatted as a stylesheet and a script, which no HTML-only
formatter does.
"""

import shutil
import subprocess
from functools import cache
from pathlib import Path

# `mise` reads the pin from the nearest `mise.toml`, which is this one,
# whatever directory the build was started from.
ROOT = Path(__file__).parent.parent

FLAGS = (
    # HTML formatting is off by default in this version.
    "--html-formatter-enabled=true",
    # As the stylesheets and the script in `assets/` are already written.
    "--indent-style=space",
    # Every space in the prose is one somebody typed, so none of them move.
    #
    # The default reads the whitespace the way CSS does and breaks a long
    # line where the rendering would not notice, which is right for most
    # tags and wrong for a footnote reference: `biome` 2.3.14 will break
    # between a sentence and the `<sup>` welded to its full stop, and that
    # newline renders as a space between the two. It puts the `>` on the
    # next line to avoid exactly that around a `<span>`, so this is a gap
    # in which elements it counts as inline rather than a missing idea.
    #
    # Under `strict` it uses that same trick everywhere and moves nothing.
    # The markup is uglier where a line has to wrap mid-tag; the page is
    # correct, and the page is what publishes.
    "--html-formatter-whitespace-sensitivity=strict",
)


class MiseMissing(RuntimeError):
    pass


@cache
def biome() -> str:
    """The `biome` that `mise.toml` pins.

    Through `mise` rather than off `PATH`, so that pin is the only answer to
    which version runs. The output is committed, and a different `biome`
    would rewrite every report without a report having changed: reading that
    diff, `check-committed-site.sh` says the documents changed, which would
    not be true and points at Google Docs instead of at an installed binary.

    Asked once, and for the path rather than by running `mise x` per page:
    `mise` re-reads the pin every time it is asked, and a build formats a
    page per report while the tests format far more, so that resolution is
    most of what running the formatter would cost.
    """
    mise = shutil.which("mise")
    if mise is None:
        raise MiseMissing(
            "`mise` is not on PATH, so `biome` could not be resolved and the "
            "HTML was not formatted. Install it from https://mise.jdx.dev, "
            "then rerun."
        )
    result = subprocess.run(  # noqa: S603
        [mise, "which", "biome"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise MiseMissing(
            "`mise` has not installed the `biome` that `mise.toml` pins, so "
            "the HTML was not formatted. Run `mise install`, then rerun.\n"
            f"{result.stderr.strip()}"
        )
    return result.stdout.strip()


def html(source: str) -> str:
    """`source`, formatted.

    Read from standard input and named rather than written to a file:
    the name is how `biome` knows it is looking at HTML,
    and the build has nowhere it wants a copy of the unformatted page.
    """
    result = subprocess.run(  # noqa: S603
        [biome(), "format", "--stdin-file-path=report.html", *FLAGS],
        input=source,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"biome format failed:\n{result.stderr.strip()}")
    return result.stdout
