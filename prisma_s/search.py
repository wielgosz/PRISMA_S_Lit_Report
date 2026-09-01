r"""
Keyword matching engine.

Implements the PRISMA-S protocol matching rules:
  - Case-insensitive.
  - **Alphanumeric** boundaries: a term matches only when it is not flanked by
    another letter or digit.  Unlike ``\b`` this also matches terms that begin
    or end with punctuation (e.g. ``(CO2)``, ``+ve``) and does not treat ``_``
    as a word character.  See ``docs/METHOD.md``.
  - Exact phrase matching for multi-word terms, tolerant of the whitespace and
    hyphenated line breaks that PDF extraction introduces *between* words.
  - No stemming, no lemmatization.
  - Every (group, term) combination is reported, including zero counts.  A term
    that legitimately appears under two groups is counted under each.
"""

from __future__ import annotations

import re

# Separator allowed between the words of a multi-word term: ordinary whitespace,
# or a hyphenated line break ("supply-\nshed" == "supply shed").
_WORD_SEP = r"(?:\s*-\s*\n\s*|\s+)"


def build_regex(term: str) -> re.Pattern:
    r"""Compile an alphanumeric-boundary regex for *term* (single or multi-word).

    >>> bool(build_regex("(CO2)").search("emits (CO2) yearly"))
    True
    >>> build_regex("region").search("subregional") is None
    True
    """
    term = term.strip()
    if not term:
        raise ValueError("build_regex() requires a non-empty term")

    core = _WORD_SEP.join(re.escape(w) for w in term.split())
    prefix = r"(?<![A-Za-z0-9])" if term[0].isalnum() else ""
    suffix = r"(?![A-Za-z0-9])" if term[-1].isalnum() else ""
    return re.compile(prefix + core + suffix, flags=re.IGNORECASE)


def build_term_index(
    keyword_rows: list[dict[str, str]],
) -> dict[tuple[str, str], re.Pattern]:
    """Return ``{(group, term): compiled_regex}`` for every row in *keyword_rows*.

    Keyed by ``(group, term)`` so a term listed under two groups is retained
    once per group rather than silently collapsed.
    """
    index: dict[tuple[str, str], re.Pattern] = {}
    for row in keyword_rows:
        key = (row["group"], row["term"])
        if key not in index:
            index[key] = build_regex(row["term"])
    return index


def count_terms(
    text: str, term_index: dict[tuple[str, str], re.Pattern]
) -> list[dict]:
    """Return one ``{Term, Group, Count}`` dict per (group, term) in *term_index*.

    Zero counts are always included so the output matrix is complete.
    """
    return [
        {"Term": term, "Group": group, "Count": sum(1 for _ in rgx.finditer(text))}
        for (group, term), rgx in term_index.items()
    ]
