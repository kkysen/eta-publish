"""Compile the emitted Typst source into the report PDF.

Typst is an external binary rather than a Python dependency, so this is best-effort:
if it is not installed the `.typ` is still written
and the build reports what to install,
instead of failing everything for the sake of one output.
"""

import shutil
import subprocess
from importlib import resources
from pathlib import Path

TEMPLATE = "template.typ"


class TypstMissing(RuntimeError):
    pass


def install_template(outdir: Path) -> Path:
    """Write the house style next to the emitted source, every build.

    It is a package asset rather than something the emitter writes,
    so that editing how reports look means editing Typst rather than a Python string.

    Overwritten rather than kept, because an output directory is build output:
    it is rebuilt from the document on every run,
    and `site/` is gitignored precisely because nothing in it is edited by hand.
    Keeping an existing copy meant a change to the house style
    reached a directory that had ever been built once, never,
    and the PDF was compiled against a template several versions old without saying so.
    """
    dest = outdir / TEMPLATE
    source = resources.files("eta_publish.assets").joinpath(TEMPLATE)
    dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def compile_pdf(source: Path, dest: Path | None = None) -> Path:
    """Run `typst compile` on `source`, returning the PDF path."""
    typst = shutil.which("typst")
    if typst is None:
        raise TypstMissing(
            "`typst` is not on PATH, so the PDF was not built. "
            "Install it with `mise use -g typst` or from https://typst.app/, "
            "then rerun. The `.typ` source has already been written."
        )
    dest = dest or source.with_suffix(".pdf")
    result = subprocess.run(  # noqa: S603
        [typst, "compile", "--root", str(source.parent), str(source), str(dest)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"typst compile failed:\n{result.stderr.strip()}")
    return dest
