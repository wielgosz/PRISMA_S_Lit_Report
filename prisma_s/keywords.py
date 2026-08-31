"""
Keyword dictionary loader.

The bundled default ships inside the package as
``prisma_s/data/keyword_dictionary_v1.1.csv`` (group, term columns) and is
resolved with :mod:`importlib.resources`, so it works from any install layout
(``pip install``, editable, wheel).  Users may supply their own CSV with the
same schema; the version is inferred from the filename convention
``keyword_dictionary_v{MAJOR}.{MINOR}.csv``.
"""

from __future__ import annotations

import csv
import io
import re
from importlib.resources import files
from pathlib import Path

BUNDLED_DICT_NAME = "keyword_dictionary_v1.1.csv"
BUNDLED_VERSION = "1.1"


def bundled_dict_path() -> Path:
    """Return a filesystem path to the bundled keyword dictionary.

    Valid for every normal (unzipped) install.  Prefer :func:`bundled_dict_text`
    when you only need the contents.
    """
    return Path(str(files("prisma_s").joinpath("data").joinpath(BUNDLED_DICT_NAME)))


def bundled_dict_text() -> str:
    """Return the bundled keyword dictionary CSV as UTF-8 text."""
    resource = files("prisma_s").joinpath("data").joinpath(BUNDLED_DICT_NAME)
    return resource.read_text(encoding="utf-8")


def _rows_from_reader(reader: csv.DictReader) -> list[dict]:
    rows: list[dict] = []
    for row in reader:
        term = (row.get("term") or "").strip()
        if term:
            rows.append({"group": (row.get("group") or "").strip(), "term": term})
    return rows


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
        reader = csv.DictReader(io.StringIO(bundled_dict_text()))
        return _rows_from_reader(reader), BUNDLED_VERSION

    csv_path = Path(csv_path)
    m = re.search(r"v(\d+\.\d+)", csv_path.stem)
    version = m.group(1) if m else "unknown"
    with open(csv_path, newline="", encoding="utf-8") as fh:
        return _rows_from_reader(csv.DictReader(fh)), version
