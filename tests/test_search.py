"""
Tests for the keyword matching engine (prisma_s.search).

These tests encode the PRISMA-S protocol rules so that any future change
to the matching logic can be validated for protocol compliance.
"""

import pytest
from prisma_s.search import build_term_index, count_terms


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
