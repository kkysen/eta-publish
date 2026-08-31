"""The type of raw Google Docs API JSON.

A paragraph element is a dict with exactly one of
`textRun`, `footnoteReference`, or `inlineObjectElement` set,
and nothing in the wire format says so.
Modeling that faithfully is a lot of machinery guarding a boundary we cross once.

So the JSON stays untyped, but says so with a name.
`fetch` and `parse` are the only modules that should mention it;
everything downstream works on the precisely typed tree in `nodes.py`.
"""

from typing import Any

type JsonObject = dict[str, Any]
