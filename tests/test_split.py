"""Cutting an oversized report into pastable pieces."""

import json
import re

from paths import FIXTURE_DIR

from eta_publish.emit.html import CODE_BLOCK_LIMIT, HtmlEmitter, split_at_headings
from eta_publish.parse import parse

FIXTURE = json.loads((FIXTURE_DIR / "doc.json").read_text())


def fragment() -> str:
    return HtmlEmitter().emit(parse(FIXTURE))


def test_each_piece_is_a_standalone_report_div() -> None:
    for piece in split_at_headings(fragment()):
        assert piece.count('<div class="eta-report">') == 1
        assert piece.rstrip().endswith("</div>")
        assert piece.startswith("<style>")


def test_pieces_break_at_h2_and_nowhere_else() -> None:
    pieces = split_at_headings(fragment())
    # The h3 stays with its section rather than starting a new piece.
    with_h2 = [p for p in pieces if "<h2 id=" in p]
    assert all(p.count("<h2 id=") == 1 for p in with_h2)
    assert any("<h3 id=" in p for p in with_h2)


def test_nothing_is_lost_in_the_split() -> None:
    """Every paragraph in the whole fragment survives into some piece."""
    whole = fragment()
    joined = "".join(split_at_headings(whole))
    for paragraph in re.findall(r"<p>.*?</p>", whole, re.S):
        assert paragraph in joined


def test_the_limit_matches_squarespace() -> None:
    assert CODE_BLOCK_LIMIT == 400_000
