"""The type of raw Google Docs API JSON.

The Docs API returns deeply nested, weakly specified objects: a paragraph
element is a dict with exactly one of `textRun`, `footnoteReference`, or
`inlineObjectElement` set, and nothing in the wire format says so. Modeling
that faithfully would be a large amount of machinery guarding a boundary we
cross once.

So the JSON stays untyped by design, but says so with a name. `fetch` and
`parse` are the only modules that should mention it; everything downstream
works on the tree in `nodes.py`, which is precisely typed.
"""

from __future__ import annotations

from typing import Any

type JsonObject = dict[str, Any]
