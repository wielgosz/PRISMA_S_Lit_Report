"""Keyword-dictionary loading (prisma_s.keywords) - flat and registry shapes."""

import pytest

from prisma_s.keywords import bundled_dict_text, load_keywords, resolve_dict_arg


def _write(path, text, encoding="utf-8"):
    path.write_bytes(text.encode(encoding))
    return path


# ---- bundled dictionaries -------------------------------------------------

def test_default_is_the_v13_registry():
    kw = load_keywords(None)
    assert kw.is_registry is True
    assert kw.version == "1.3"
    assert kw.n_canonical == 98
    assert kw.n_variants == 194
    cats = {c[0] for c in kw.canonical_terms()}
    assert {"Jurisdictional terms", "Supply chain terms", "Farm level terms",
            "AOI terms"} <= cats


def test_canonical_terms_group_variants():
    kw = load_keywords(None)
    by_name = {c[2]: c for c in kw.canonical_terms()}
    _, _, _, variants, iv = by_name["GPS coordinate"]
    assert variants[0] == "GPS coordinate" and "coordinate" in variants
    assert iv is True


def test_bundled_11_is_flat():
    kw = load_keywords("bundled:1.1")
    assert kw.is_registry is False
    assert kw.version == "1.1"
    assert kw.n_terms > 100
    assert set(kw.flat_rows[0]) == {"group", "term"}


@pytest.mark.parametrize("arg,expected", [
    (None, ("bundled", "keyword_dictionary_v1.3.csv")),
    ("bundled:1.3", ("bundled", "keyword_dictionary_v1.3.csv")),
    ("bundled:1.1", ("bundled", "keyword_dictionary_v1.1.csv")),
    ("some/path.csv", ("path", "some/path.csv")),
])
def test_resolve_dict_arg(arg, expected):
    assert resolve_dict_arg(arg) == expected


# ---- user CSVs: flat ----------------------------------------------------

def test_flat_bom_and_reversed_headers(tmp_path):
    p = _write(tmp_path / "kw.csv", "term,group\r\nCoffee,Commodity\r\n", "utf-8-sig")
    kw = load_keywords(p)
    assert kw.is_registry is False
    assert kw.flat_rows == [{"group": "Commodity", "term": "Coffee"}]


def test_flat_missing_term_column_raises(tmp_path):
    p = _write(tmp_path / "kw.csv", "group,keyword\nCommodity,Coffee\n")
    with pytest.raises(ValueError, match="keyword"):
        load_keywords(p)


def test_flat_zero_terms_raises(tmp_path):
    p = _write(tmp_path / "kw.csv", "group,term\nCommodity,\n")
    with pytest.raises(ValueError):
        load_keywords(p)


def test_cp1252_fallback(tmp_path):
    p = _write(tmp_path / "kw.csv", "group,term\nX,caf\xe9\n", "cp1252")
    kw = load_keywords(p)
    assert kw.flat_rows[0]["term"] == "caf\xe9"


# ---- user CSVs: registry ---------------------------------------------------

def test_registry_detection_and_active_filter(tmp_path):
    p = _write(tmp_path / "reg.csv",
               "category,term_id,canonical_term,search_variant,active,include_in_visuals\n"
               "Cat,T1,alpha,alpha,yes,yes\n"
               "Cat,T1,alpha,alfa,yes,yes\n"
               "Cat,T2,beta,beta,no,yes\n")
    kw = load_keywords(p)
    assert kw.is_registry is True
    assert kw.n_canonical == 1                      # beta dropped (active=no)
    _, _, _, variants, _ = kw.canonical_terms()[0]
    assert variants == ["alpha", "alfa"]


def test_registry_include_in_visuals(tmp_path):
    p = _write(tmp_path / "reg.csv",
               "category,term_id,canonical_term,search_variant,include_in_visuals\n"
               "Cat,T1,alpha,alpha,no\n")
    kw = load_keywords(p)
    assert kw.canonical_terms()[0][4] is False


def test_bundled_text_matches_file_load(tmp_path):
    p = _write(tmp_path / "keyword_dictionary_v1.3.csv", bundled_dict_text())
    from_file = load_keywords(p)
    assert from_file.n_canonical == load_keywords(None).n_canonical
