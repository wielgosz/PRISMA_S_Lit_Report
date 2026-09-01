r"""
Keyword matching engine.

Matching rules (shared by both dictionary shapes):
  - Case-insensitive.
  - **Alphanumeric** boundaries: a term matches only when it is not flanked by
    another letter or digit.  Unlike ``\b`` this also matches terms that begin
    or end with punctuation (e.g. ``(CO2)``, ``+ve``) and does not treat ``_``
    as a word character.

Whitespace between the words of a multi-word term:
  - ``strict=False`` (flat / v1.1 path): tolerant of arbitrary whitespace and a
    hyphenated line break, to cope with raw PDF extraction.
  - ``strict=True`` (registry / v1.3 path): a literal single space, matching the
    published protocol's ``compile_variant_pattern``.  The registry path
    normalises text first (see ``prisma_s.normalize``), so the strict rule is
    both faithful and safe.

Roll-up (registry path): each ``canonical_term`` owns one or more
``search_variant`` patterns; a document's count for the canonical term is the
sum of its variant counts.
"""

from __future__ import annotations

import re

# Separator between words of a multi-word term in lenient mode: whitespace, or a
# hyphenated line break ("supply-\nshed" == "supply shed").
_WORD_SEP = r"(?:\s*-\s*\n\s*|\s+)"


def build_regex(term: str, *, strict: bool = False) -> re.Pattern:
    r"""Compile an alphanumeric-boundary regex for *term*.

    >>> bool(build_regex("(CO2)").search("emits (CO2) yearly"))
    True
    >>> build_regex("region").search("subregional") is None
    True
    >>> build_regex("supply shed", strict=True).search("supply  shed") is None
    True
    """
    term = term.strip()
    if not term:
        raise ValueError("build_regex() requires a non-empty term")

    if strict:
        core = re.escape(term)
    else:
        core = _WORD_SEP.join(re.escape(w) for w in term.split())
    prefix = r"(?<![A-Za-z0-9])" if term[0].isalnum() else ""
    suffix = r"(?![A-Za-z0-9])" if term[-1].isalnum() else ""
    return re.compile(prefix + core + suffix, flags=re.IGNORECASE)


# ---------------------------------------------------------------------------
# Flat (v1.1) path
# ---------------------------------------------------------------------------

def build_term_index(
    keyword_rows: list[dict[str, str]],
) -> dict[tuple[str, str], re.Pattern]:
    """Return ``{(group, term): compiled_regex}`` for every row in *keyword_rows*."""
    index: dict[tuple[str, str], re.Pattern] = {}
    for row in keyword_rows:
        key = (row["group"], row["term"])
        if key not in index:
            index[key] = build_regex(row["term"])
    return index


def count_terms(
    text: str, term_index: dict[tuple[str, str], re.Pattern]
) -> list[dict]:
    """One ``{Term, Group, Count}`` per (group, term); zero counts included."""
    return [
        {"Term": term, "Group": group, "Count": sum(1 for _ in rgx.finditer(text))}
        for (group, term), rgx in term_index.items()
    ]


# ---------------------------------------------------------------------------
# Registry (v1.3) path
# ---------------------------------------------------------------------------

def build_registry_index(kw, *, strict: bool = True) -> list[dict]:
    """Compile the variant patterns for a :class:`~prisma_s.keywords.KeywordDictionary`.

    Returns an ordered list of
    ``{"category", "term_id", "canonical_term", "include_in_visuals",
       "variants": [(variant, compiled_regex), ...]}``.
    """
    index: list[dict] = []
    for category, term_id, canonical, variants, iv in kw.canonical_terms():
        index.append(
            {
                "category": category,
                "term_id": term_id,
                "canonical_term": canonical,
                "include_in_visuals": iv,
                "variants": [(v, build_regex(v, strict=strict)) for v in variants],
            }
        )
    return index


def count_registry(text: str, registry_index: list[dict]) -> list[dict]:
    """One row per canonical term: summed count plus the per-variant breakdown.

    Keys: ``Category, Term ID, Canonical Term, Variants Included,
    Variant Counts, Count, Referenced``.
    """
    out: list[dict] = []
    for entry in registry_index:
        variant_counts = {
            v: sum(1 for _ in rgx.finditer(text)) for v, rgx in entry["variants"]
        }
        total = sum(variant_counts.values())
        out.append(
            {
                "Category": entry["category"],
                "Term ID": entry["term_id"],
                "Canonical Term": entry["canonical_term"],
                "Variants Included": "; ".join(v for v, _ in entry["variants"]),
                "Variant Counts": variant_counts,
                "Count": total,
                "Referenced": 1 if total > 0 else 0,
            }
        )
    return out
