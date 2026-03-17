"""
Keyword matching engine.

Implements the PRISMA-S protocol matching rules:
  - Case-insensitive
  - Exact word boundaries (no partial substring matching)
  - Exact phrase matching for multi-word terms (whitespace-flexible)
  - No stemming, no lemmatization
  - All document x term combinations are returned, including zero counts
"""

from __future__ import annotations

import re


def build_regex(term: str) -> re.Pattern:
    """Compile a word-boundary regex for *term* (single or multi-word)."""
    if " " in term:
        # Allow any whitespace between words to handle line-breaks in OCR text
        pat = r"\b" + r"\s+".join(re.escape(w) for w in term.split()) + r"\b"
    else:
        pat = r"\b" + re.escape(term) + r"\b"
    return re.compile(pat, flags=re.IGNORECASE)


def build_term_index(keyword_rows: list[dict]) -> dict[str, tuple[str, re.Pattern]]:
    """Return ``{term: (group, compiled_regex)}`` for every row in *keyword_rows*."""
    index: dict[str, tuple[str, re.Pattern]] = {}
    for row in keyword_rows:
        term = row["term"]
        if term not in index:
            index[term] = (row["group"], build_regex(term))
    return index


def count_terms(text: str, term_index: dict) -> list[dict]:
    """Return one ``{Term, Group, Count}`` dict per term in *term_index*.

    Zero counts are always included so the output matrix is complete.
    """
    return [
        {"Term": term, "Group": group, "Count": len(rgx.findall(text))}
        for term, (group, rgx) in term_index.items()
    ]
