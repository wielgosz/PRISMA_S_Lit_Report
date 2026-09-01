"""Citation text loading (prisma_s.citation)."""

import pytest

from prisma_s.citation import LANGS, all_citations, citation_text


@pytest.mark.parametrize("lang", list(LANGS))
def test_each_language_loads(lang):
    text = citation_text(lang)
    assert "World Resources Institute" in text
    assert "wielgosz" in text.lower()


def test_unknown_language_raises():
    with pytest.raises(ValueError):
        citation_text("fr")


def test_all_citations_has_three_blocks():
    combined = all_citations()
    for label in LANGS.values():
        assert label in combined
    assert combined.count("World Resources Institute") == 3
