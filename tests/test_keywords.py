"""
Keyword-dictionary loading (prisma_s.keywords).

These guard the v1.4 rule that a user-authored CSV either loads correctly or
fails loudly - never a silent empty analysis.
"""

import pytest

from prisma_s.keywords import bundled_dict_path, bundled_dict_text, load_keywords


def _write(path, text, encoding="utf-8"):
    path.write_bytes(text.encode(encoding))
    return path


def test_bundled_loads_without_args():
    rows, version = load_keywords(None)
    assert version == "1.1"
    assert len(rows) > 50
    assert set(rows[0]) == {"group", "term"}


def test_bundled_text_matches_load(tmp_path):
    p = _write(tmp_path / "keyword_dictionary_v1.1.csv", bundled_dict_text())
    from_file, _ = load_keywords(p)
    from_bundle, _ = load_keywords(None)
    assert from_file == from_bundle


def test_bom_group_term(tmp_path):
    p = _write(tmp_path / "kw.csv", "group,term\r\nCommodity,Coffee\r\n", "utf-8-sig")
    rows, _ = load_keywords(p)
    assert rows == [{"group": "Commodity", "term": "Coffee"}]


def test_bom_term_group_reversed(tmp_path):
    p = _write(tmp_path / "kw.csv", "term,group\r\nCoffee,Commodity\r\nCocoa,Commodity\r\n", "utf-8-sig")
    rows, _ = load_keywords(p)
    assert [r["term"] for r in rows] == ["Coffee", "Cocoa"]
    assert all(r["group"] == "Commodity" for r in rows)


def test_capitalised_headers(tmp_path):
    p = _write(tmp_path / "kw.csv", "Group,Term\nCommodity,Coffee\n")
    rows, _ = load_keywords(p)
    assert rows == [{"group": "Commodity", "term": "Coffee"}]


def test_category_alias_for_group(tmp_path):
    p = _write(tmp_path / "kw.csv", "category,term\nJurisdictional,region\n")
    rows, _ = load_keywords(p)
    assert rows == [{"group": "Jurisdictional", "term": "region"}]


def test_cp1252_file_is_readable_or_named_error(tmp_path):
    p = _write(tmp_path / "kw.csv", "group,term\nComodete,café\n", "cp1252")
    rows, _ = load_keywords(p)  # utf-8-sig fails -> cp1252 retry succeeds
    assert rows[0]["term"] == "café"


def test_missing_term_column_raises_with_headers(tmp_path):
    p = _write(tmp_path / "kw.csv", "group,keyword\nCommodity,Coffee\n")
    with pytest.raises(ValueError) as exc:
        load_keywords(p)
    assert "keyword" in str(exc.value)


def test_zero_terms_raises(tmp_path):
    p = _write(tmp_path / "kw.csv", "group,term\nCommodity,\nCommodity,   \n")
    with pytest.raises(ValueError):
        load_keywords(p)


def test_bundled_dict_path_exists():
    assert bundled_dict_path().exists()
