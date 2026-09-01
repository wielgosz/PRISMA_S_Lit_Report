"""Term-frequency figures (prisma_s.figures)."""

import pandas as pd

from prisma_s.figures import generate_figures

_COL = "number of reports referencing term"


def _summary(rows):
    return pd.DataFrame(rows, columns=["category", "term", _COL])


def test_dcf_profile_writes_three_legacy_figures(tmp_path):
    df = _summary([
        ("Jurisdictional terms", "area", 102),
        ("Jurisdictional terms", "region", 97),
        ("Supply chain terms", "supplier", 65),
        ("Farm level terms", "farm", 74),
        ("AOI terms", "polygon", 27),          # present but not its own DCF figure
    ])
    written = {p.name for p in generate_figures(df, tmp_path)}
    assert written == {
        "DCF_PRISMA_S_Figure_1_jurisdictional_terms.svg",
        "DCF_PRISMA_S_Figure_1_jurisdictional_terms.png",
        "DCF_PRISMA_S_Figure_2_supply_chain_terms.svg",
        "DCF_PRISMA_S_Figure_2_supply_chain_terms.png",
        "DCF_PRISMA_S_Figure_3_farm_level_terms.svg",
        "DCF_PRISMA_S_Figure_3_farm_level_terms.png",
    }
    for name in written:
        assert (tmp_path / name).stat().st_size > 0


def test_generic_profile_one_figure_per_category(tmp_path):
    df = _summary([("AOI", "coord", 5), ("Commodity", "soy", 9), ("Commodity", "cocoa", 3)])
    written = sorted(p.name for p in generate_figures(df, tmp_path))
    assert written == [
        "figure_aoi.png", "figure_aoi.svg",
        "figure_commodity.png", "figure_commodity.svg",
    ]


def test_empty_input_writes_nothing(tmp_path):
    assert generate_figures(pd.DataFrame(), tmp_path) == []
    assert generate_figures(None, tmp_path) == []


def test_matplotlib_missing_writes_placeholder(tmp_path, monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "matplotlib" or name.startswith("matplotlib."):
            raise ImportError("no matplotlib")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    df = _summary([("Jurisdictional terms", "area", 1), ("Supply chain terms", "s", 1),
                   ("Farm level terms", "f", 1)])
    written = generate_figures(df, tmp_path)
    assert written and all(p.suffix == ".txt" for p in written)
