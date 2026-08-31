"""Emitters: one per output format, each walking the document tree directly.

None is layered on another:
the HTML emitter does not consume the Markdown emitter's output.
`README.md` says why.
"""

from .base import Emitter

__all__ = ["Emitter"]
