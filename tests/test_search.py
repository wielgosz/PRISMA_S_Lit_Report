"""
Tests for the keyword matching engine (prisma_s.search).

These tests encode the PRISMA-S protocol rules so that any future change
to the matching logic can be validated for protocol compliance.
"""

import pytest
from prisma_s.search import build_regex, build_term_index, count_terms


def _index(*terms_with_groups):
    """Helper: build a term index from (group, term) pairs."""
    rows = [{"group": g, "term": t} for g, t in terms_with_groups]
    return build_term_index(rows)


# ---------------------------------------------------------------------------
# Core matching rules
# ---------------------------------------------------------------------------

def test_single_word_match():
    idx = _index(("AOI", "Coordinate"))
    result = count_terms("Coordinate measurement systems use coordinate data.", idx)
    assert result[0]["Count"] == 2


def test_case_insensitive():
    idx = _index(("Supply Chain Node", "Farm"))
    result = count_terms("The farm and FARM and Farm.", idx)
    assert result[0]["Count"] == 3


def test_no_partial_substring_match():
    """'Soy' must NOT match inside 'Soybean'."""
    idx = _index(("Commodity", "Soy"))
    result = count_terms("Soybean production increased. Soy exports rose.", idx)
    assert result[0]["Count"] == 1


def test_multiword_phrase():
    idx = _index(("Supply Chain Node", "Supply shed"))
    result = count_terms(
        "The supply shed was identified as a key node. Supply shed mapping.", idx
    )
    assert result[0]["Count"] == 2


def test_zero_count_always_returned():
    """Every term must appear in the output even with zero matches."""
    idx = _index(("AOI", "isochrone"))
    result = count_terms("No relevant content here.", idx)
    assert len(result) == 1
    assert result[0]["Count"] == 0


def test_multiword_flexible_whitespace():
    """Multi-word terms should match across a single line-break (OCR artefact)."""
    idx = _index(("AOI", "region of origin"))
    result = count_terms("The region\nof origin was documented.", idx)
    assert result[0]["Count"] == 1


def test_multiple_terms_independent():
    idx = _index(("Commodity", "Coffee"), ("Commodity", "Cocoa"))
    text = "Coffee exports grew, but Cocoa and coffee output fell."
    result = {r["Term"]: r["Count"] for r in count_terms(text, idx)}
    assert result["Coffee"] == 2
    assert result["Cocoa"] == 1


def test_group_preserved_in_output():
    idx = _index(("AOI", "Polygon"))
    result = count_terms("Draw a Polygon around the area.", idx)
    assert result[0]["Group"] == "AOI"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_text_returns_zero():
    idx = _index(("Commodity", "Wheat"))
    result = count_terms("", idx)
    assert result[0]["Count"] == 0


def test_punctuation_boundary():
    """Term at sentence end (followed by '.') should still match."""
    idx = _index(("Supply Chain Node", "Mill"))
    result = count_terms("Sent to the Mill.", idx)
    assert result[0]["Count"] == 1


# ---------------------------------------------------------------------------
# v1.4: alphanumeric boundaries, duplicates, metacharacters
# ---------------------------------------------------------------------------

def test_term_starting_with_punctuation_matches():
    idx = _index(("Emissions", "(CO2)"))
    result = count_terms("annual (CO2) emissions and more (CO2) here", idx)
    assert result[0]["Count"] == 2


def test_term_with_leading_plus_matches():
    idx = _index(("Sign", "+ve"))
    assert count_terms("a +ve result", idx)[0]["Count"] == 1


def test_underscore_is_a_boundary_not_a_word_char():
    """\\b would fail this; alphanumeric boundaries treat '_' as a separator."""
    idx = _index(("X", "data"))
    assert count_terms("raw_data_set", idx)[0]["Count"] == 1


def test_regex_metacharacters_are_literal():
    idx = _index(("X", "a.b"))
    result = {r["Term"]: r["Count"] for r in count_terms("a.b but not axb", idx)}
    assert result["a.b"] == 1


def test_duplicate_term_in_two_groups_counted_twice():
    idx = _index(("A", "Coffee"), ("B", "Coffee"))
    rows = count_terms("Coffee and more Coffee", idx)
    assert len(rows) == 2
    assert {(r["Group"], r["Count"]) for r in rows} == {("A", 2), ("B", 2)}


def test_hyphenated_line_break_in_phrase():
    idx = _index(("Node", "supply shed"))
    assert count_terms("the supply-\nshed here", idx)[0]["Count"] == 1


def test_build_regex_rejects_empty():
    with pytest.raises(ValueError):
        build_regex("   ")


# ---------------------------------------------------------------------------
# v1.5: strict matching + registry roll-up
# ---------------------------------------------------------------------------

def test_strict_requires_a_single_space():
    rgx = build_regex("supply shed", strict=True)
    assert rgx.search("the supply shed here") is not None
    assert rgx.search("supply  shed") is None
    assert rgx.search("supply\nshed") is None


def test_strict_still_has_alphanumeric_boundaries():
    assert build_regex("area", strict=True).search("catchment area near") is not None
    assert build_regex("area", strict=True).search("areation") is None


class _KW:
    is_registry = True

    def __init__(self, rows):
        self._rows = rows

    def canonical_terms(self):
        out, idx = [], {}
        for cat, tid, canon, var, iv in self._rows:
            if (tid, canon) not in idx:
                idx[(tid, canon)] = len(out)
                out.append((cat, tid, canon, [], iv))
            out[idx[(tid, canon)]][3].append(var)
        return out


def test_registry_rollup_sums_variants():
    from prisma_s.search import build_registry_index, count_registry

    kw = _KW([
        ("C", "T1", "cooperative", "cooperative", True),
        ("C", "T1", "cooperative", "coop", True),
        ("C", "T2", "mill", "mill", True),
    ])
    idx = build_registry_index(kw)
    rows = {r["Canonical Term"]: r for r in count_registry("a coop and a cooperative; no M", idx)}
    assert rows["cooperative"]["Count"] == 2
    assert rows["cooperative"]["Referenced"] == 1
    assert rows["cooperative"]["Variant Counts"] == {"cooperative": 1, "coop": 1}
    assert rows["mill"]["Count"] == 0 and rows["mill"]["Referenced"] == 0
