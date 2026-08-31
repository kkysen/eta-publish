"""Emitters: one per output format, each walking the document tree directly.

None of these is layered on another.
In particular the HTML emitter does not consume the Markdown emitter's output;
see `README.md` for why.
"""

from .base import Emitter

__all__ = ["Emitter"]
