"""
Text normalisation for the v1.3 canonicalisation workflow.

Mirrors the frozen-text step of the published protocol
(`protocols/v2_1/scripts/freeze_extract_text_corpus.py::normalize_text`):
NFC Unicode, LF line endings, trailing whitespace stripped per line. Nothing
more — no de-hyphenation, no internal-whitespace collapse — so that strict
single-space variant matching stays comparable to the paper.

Applied to each document's text in **registry (v1.3) mode only**; the flat
(v1.1) path is left untouched so its counts stay identical to v1.4.
"""

from __future__ import annotations

import unicodedata


def normalize_text(text: str) -> str:
    """NFC-normalise, convert CRLF/CR to LF, strip trailing whitespace per line."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n"))
