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
    # the guidebook citation appears once per language block
    assert combined.count("deforestation- and conversion-free (DCF)") == 3


def test_citation_does_not_overclaim_wri_licence():
    """The v1.3 dictionary / protocol licence must be stated as pending, not CC BY."""
    for lang in LANGS:
        text = citation_text(lang).lower()
        assert "pending" in text or "pendente" in text or "pendiente" in text
        assert "open-data-commitment" in text  # WRI data-policy link present
