"""
Term-frequency figures.

Ports ``make_legacy_svg_bar_chart`` from the published protocol
(``protocols/v2_1/scripts/12_build_v20_output_package.py``): horizontal amber
bars (``#F0B310``), ranked by the number of corpus documents referencing a
term, a shared x-scale across the set, integer value labels, largest at the top.

* **DCF profile** (auto, when the three canonical categories are present) writes
  the guidebook's three figures with their legacy filenames.
* **Generic profile** writes one figure per category otherwise.

Both SVG and PNG are written.  If matplotlib genuinely cannot be imported a
``.txt`` placeholder is written instead and a warning is emitted -- the run does
not fail.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd

BAR_COLOR = "#F0B310"
_VALUE_COL = "number of reports referencing term"
_AXIS_LABEL = "Number of reports referencing term"

# (category, legacy filename stem, title) -- from LEGACY_FIGURE_SPECS in the source.
_DCF_SPECS = [
    ("Jurisdictional terms", "DCF_PRISMA_S_Figure_1_jurisdictional_terms",
     "Figure 1. Number of reports referencing a jurisdictional or landscape term"),
    ("Supply chain terms", "DCF_PRISMA_S_Figure_2_supply_chain_terms",
     "Figure 2. Number of reports referencing a supply chain node term"),
    ("Farm level terms", "DCF_PRISMA_S_Figure_3_farm_level_terms",
     "Figure 3. Number of reports referencing a farm level term"),
]
_DCF_CATEGORIES = {s[0] for s in _DCF_SPECS}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_") or "category"


def _placeholder(out_path: Path, msg: str) -> Path:
    out_path.with_suffix(".txt").write_text(msg + "\n", encoding="utf-8")
    return out_path.with_suffix(".txt")


def _bar_chart(sub: pd.DataFrame, stem_path: Path, title: str, shared_xlim: float) -> list[Path]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        warnings.warn("matplotlib unavailable; writing a text placeholder instead.", stacklevel=2)
        return [_placeholder(stem_path.with_suffix(".svg"), f"matplotlib unavailable; could not draw {title}")]

    data = sub.sort_values([_VALUE_COL, "term"], ascending=[False, True]).iloc[::-1]
    height = max(3.2, 0.32 * len(data) + 1.4)
    fig, ax = plt.subplots(figsize=(7.2, height))
    ax.barh(data["term"].astype(str), data[_VALUE_COL], color=BAR_COLOR, height=0.55)
    ax.set_xlim(0, shared_xlim if shared_xlim > 0 else 1)
    ax.set_xlabel(_AXIS_LABEL)
    ax.set_title(title)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for i, v in enumerate(data[_VALUE_COL].tolist()):
        ax.text(float(v) + max(shared_xlim, 1) * 0.01, i, str(int(v)), va="center", fontsize=8)
    plt.tight_layout()
    written = []
    for ext, kw in ((".svg", {}), (".png", {"dpi": 200})):
        p = stem_path.with_suffix(ext)
        fig.savefig(p, format=ext.lstrip("."), **kw)
        written.append(p)
    plt.close(fig)
    return written


def generate_figures(
    term_summary: pd.DataFrame | None, out_dir: Path, *, profile: str = "auto"
) -> list[Path]:
    """Write term-frequency figures for *term_summary* into *out_dir*.

    *term_summary* needs ``category``, ``term`` and
    ``number of reports referencing term`` columns (the D1 / flat-summary shape).
    """
    if term_summary is None or term_summary.empty or _VALUE_COL not in term_summary.columns:
        return []
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = term_summary.copy()
    ts[_VALUE_COL] = pd.to_numeric(ts[_VALUE_COL], errors="coerce").fillna(0)

    if profile == "auto":
        profile = "dcf" if _DCF_CATEGORIES <= set(ts["category"]) else "generic"

    if profile == "dcf":
        plotted = ts[ts["category"].isin(_DCF_CATEGORIES)]
        shared_xlim = float(plotted[_VALUE_COL].max() or 0) * 1.08
        written: list[Path] = []
        for category, stem, title in _DCF_SPECS:
            sub = ts[ts["category"] == category]
            written += _bar_chart(sub, out_dir / stem, title, shared_xlim)
        return written

    written = []
    shared_xlim = float(ts[_VALUE_COL].max() or 0) * 1.08
    for category in dict.fromkeys(ts["category"]):
        sub = ts[ts["category"] == category]
        written += _bar_chart(
            sub, out_dir / f"figure_{_slug(category)}",
            f"{category}: reports referencing term", shared_xlim,
        )
    return written
