"""
Keyword dictionary loader.

The bundled default is keywords/keyword_dictionary_v1.1.csv (group, term columns).
Users may supply their own CSV with the same schema; the version is inferred from
the filename convention  keyword_dictionary_v{MAJOR}.{MINOR}.csv.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

# Path to the bundled keyword dictionary relative to this file's package root
_KEYWORDS_DIR = Path(__file__).parent.parent / "keywords"
BUNDLED_DICT_NAME = "keyword_dictionary_v1.1.csv"
BUNDLED_VERSION = "1.1"


def load_keywords(csv_path: str | Path | None = None) -> tuple[list[dict], str]:
    """Load a keyword dictionary CSV and return (rows, version).

    Parameters
    ----------
    csv_path:
        Path to a CSV file with at least ``group`` and ``term`` columns.
        If *None*, the bundled ``keyword_dictionary_v1.1.csv`` is used.

    Returns
    -------
    rows : list[dict]
        Each entry has keys ``"group"`` and ``"term"``.
    version : str
        Version string inferred from the filename (e.g. ``"1.1"``), or
        ``"unknown"`` if the filename does not match the convention.
    """
    if csv_path is None:
        csv_path = _KEYWORDS_DIR / BUNDLED_DICT_NAME
        version = BUNDLED_VERSION
    else:
        csv_path = Path(csv_path)
        m = re.search(r"v(\d+\.\d+)", csv_path.stem)
        version = m.group(1) if m else "unknown"

    rows: list[dict] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            term = (row.get("term") or "").strip()
            if term:
                rows.append({"group": (row.get("group") or "").strip(), "term": term})

    return rows, version
