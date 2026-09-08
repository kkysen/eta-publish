"""Lay out and check what a build wrote: the HTML, the CSS, the JavaScript.

The emitter's job is what the page says; this is where it sits on the line.
What is emitted is committed and read as a diff, and a paragraph on one line
reports a corrected word as a changed paragraph.

One entry point, `tree`, over the finished output directory. There is no
second way to format a page: two of them would have to agree byte for byte,
and nothing would notice the day they stopped.

`biome` rather than a formatter written here: whether a line break is safe
in HTML is a question about which elements are inline, and getting it wrong
welds two words together on the page. A stylesheet and a script embedded in
the page are formatted as a stylesheet and a script, which no HTML-only
formatter does.
"""

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

    Asked once, and for the path rather than by running `mise x` per call:
    `mise` re-reads the pin every time it is asked.
    """
    try:
        result = subprocess.run(
            ["mise", "which", "biome"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        raise MiseMissing(
            "`mise` is not on PATH, so `biome` could not be resolved and "
            "nothing was formatted. Install it from https://mise.jdx.dev, "
            "then rerun."
        ) from e
    if result.returncode != 0:
        raise MiseMissing(
            "`mise` has not installed the `biome` that `mise.toml` pins, so "
            "the HTML was not formatted. Run `mise install`, then rerun.\n"
            f"{result.stderr.strip()}"
        )
    return result.stdout.strip()


PASSES = 4
"""How many times `tree` may run before it gives up on settling."""


class LintFailed(RuntimeError):
    pass


def tree(root: Path) -> None:
    """Lay out and check everything under `root` that `biome` reads.

    One run over the whole build rather than one per file. `biome` takes
    about 40ms to start and a few milliseconds to do the work, so a site
    formatted a file at a time spends nearly all of its time launching
    processes. It lays out the saved API responses too, which changes how
    they are punctuated and not what they say.

    Repeated until it reports nothing left to fix, for the reason `_format`
    runs more than once over one page.
    """
    for _ in range(PASSES):
        result = subprocess.run(
            [biome(), "format", "--write", *FLAGS, str(root)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"biome format failed:\n{result.stderr.strip()}")
        # What `biome` says it rewrote, rather than a walk of the tree
        # comparing timestamps: it is the one doing the counting.
        if "Fixed" not in result.stdout:
            break
    else:
        raise RuntimeError(f"biome format did not settle under {root} in {PASSES} passes")
    result = subprocess.run(
        [biome(), "lint", "--error-on-warnings", str(root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise LintFailed(f"biome lint failed:\n{result.stderr.strip()}")
