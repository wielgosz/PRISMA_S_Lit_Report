"""
Console encoding helper.

On Windows the default console encoding is often a legacy code page (cp1252),
which raises ``UnicodeEncodeError`` when the tool prints non-ASCII text -- e.g.
accented terms from a Portuguese or Spanish keyword dictionary, or box-drawing
characters in the wizard.  Calling :func:`enable_utf8_console` once at CLI
start-up reconfigures stdout/stderr to UTF-8 so printing never crashes.

This is a no-op on interpreters/streams that do not support ``reconfigure``
(Python < 3.7, or already-wrapped streams); callers should not rely on it and
should still avoid emitting characters the terminal font cannot display.
"""

from __future__ import annotations

import sys


def enable_utf8_console() -> None:
    """Best-effort switch of stdout/stderr to UTF-8 with lossy fallback."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass
