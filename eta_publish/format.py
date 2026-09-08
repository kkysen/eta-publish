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

# Pinned, because the output is committed and a formatter that changes its
# mind between versions rewrites every report without a report changing.
VERSION = "2.3.14"

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


class BiomeMissing(RuntimeError):
    pass


def command() -> list[str]:
    """`biome`, however this machine has it.

    On `PATH` first, because a build runs the formatter once per output and
    `npx` resolves the package each time it is asked.
    """
    binary = shutil.which("biome")
    if binary is not None:
        return [binary]
    npx = shutil.which("npx")
    if npx is not None:
        return [npx, "--yes", f"@biomejs/biome@{VERSION}"]
    raise BiomeMissing(
        "`biome` is not on PATH and neither is `npx`, so the HTML could not be "
        f"formatted. Install it with `mise use -g biome@{VERSION}` or "
        "`npm i -g @biomejs/biome`, then rerun."
    )


def html(source: str) -> str:
    """`source`, formatted.

    Read from standard input and named rather than written to a file:
    the name is how `biome` knows it is looking at HTML,
    and the build has nowhere it wants a copy of the unformatted page.
    """
    result = subprocess.run(  # noqa: S603
        [*command(), "format", "--stdin-file-path=report.html", *FLAGS],
        input=source,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"biome format failed:\n{result.stderr.strip()}")
    return result.stdout
