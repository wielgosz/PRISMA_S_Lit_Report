"""
Keyword dictionary loader.

The bundled default ships inside the package as
``prisma_s/data/keyword_dictionary_v1.1.csv`` (``group``, ``term`` columns) and
is read with :func:`bundled_dict_text`, which is safe for every install layout
including zipped ones.  Users may supply their own CSV with the same schema;
the version is inferred from the filename convention
``keyword_dictionary_v{MAJOR}.{MINOR}.csv``.

User-authored CSVs are validated on load.  A file that Excel saved with a
byte-order mark, capitalised headers, or the columns in the other order is
accepted; a file with no ``term`` column, or one that yields zero usable terms,
raises :class:`ValueError` rather than silently producing an empty analysis.
"""

from __future__ import annotations

import csv
import io
import re
from importlib.resources import files
from pathlib import Path

BUNDLED_DICT_NAME = "keyword_dictionary_v1.1.csv"
BUNDLED_VERSION = "1.1"

# Accepted header spellings, normalised to (strip + casefold).
_GROUP_KEYS = {"group", "category"}
_TERM_KEYS = {"term"}


def bundled_dict_path() -> Path:
    """Filesystem path to the bundled keyword dictionary.

    Valid for every normal (unzipped) install and used only for display.  Code
    that needs the contents should call :func:`bundled_dict_text` or
    :func:`load_keywords`, which are zip-safe.
    """
    return Path(str(files("prisma_s").joinpath("data").joinpath(BUNDLED_DICT_NAME)))


def bundled_dict_text() -> str:
    """Return the bundled keyword dictionary CSV as UTF-8 text."""
    return files("prisma_s").joinpath("data").joinpath(BUNDLED_DICT_NAME).read_text(
        encoding="utf-8"
    )


def _read_csv_text(path: Path) -> str:
    """Read *path* as text, tolerating the encodings Excel commonly writes.

    ``utf-8-sig`` transparently strips a BOM and also decodes plain UTF-8.  If
    that fails we retry the legacy Windows code page; if both fail we raise a
    :class:`ValueError` that names the file, rather than leaking a bare
    :class:`UnicodeDecodeError`.
    """
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(
        f"Could not decode {path} as UTF-8 or cp1252. "
        "Re-save the file as 'CSV UTF-8'."
    )


def _parse_rows(text: str, source: str) -> list[dict[str, str]]:
    """Parse keyword CSV *text* into ``[{'group': ..., 'term': ...}, ...]``.

    Header names are matched case-insensitively and may appear in any order;
    ``category`` is accepted as a synonym for ``group``.
    """
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []
    norm = {(name or "").strip().casefold(): name for name in fieldnames}

    term_key = next((norm[k] for k in norm if k in _TERM_KEYS), None)
    group_key = next((norm[k] for k in norm if k in _GROUP_KEYS), None)

    if term_key is None:
        raise ValueError(
            f"{source}: no 'term' column found. Header was {fieldnames!r}; "
            "expected columns 'group' (or 'category') and 'term'."
        )

    rows: list[dict[str, str]] = []
    for row in reader:
        term = (row.get(term_key) or "").strip()
        if not term:
            continue
        group = (row.get(group_key) or "").strip() if group_key else ""
        rows.append({"group": group, "term": term})

    if not rows:
        raise ValueError(
            f"{source}: 0 usable terms. Every row's '{term_key}' value was empty."
        )
    return rows


def _infer_version(csv_path: Path) -> str:
    m = re.search(r"v(\d+\.\d+)", csv_path.stem)
    return m.group(1) if m else "unknown"


def load_keywords(csv_path: str | Path | None = None) -> tuple[list[dict[str, str]], str]:
    """Load a keyword dictionary CSV and return ``(rows, version)``.

    Parameters
    ----------
    csv_path:
        Path to a CSV file with at least a ``term`` column (``group`` or
        ``category`` optional).  If *None*, the bundled
        ``keyword_dictionary_v1.1.csv`` is used.

    Returns
    -------
    rows : list[dict[str, str]]
        Each entry has keys ``"group"`` and ``"term"``.
    version : str
        Version inferred from the filename (e.g. ``"1.1"``), ``"1.1"`` for the
        bundled dictionary, or ``"unknown"``.

    Raises
    ------
    ValueError
        If the file cannot be decoded, has no ``term`` column, or yields no
        non-empty terms.
    """
    if csv_path is None:
        return _parse_rows(bundled_dict_text(), "bundled dictionary"), BUNDLED_VERSION

    csv_path = Path(csv_path)
    text = _read_csv_text(csv_path)
    return _parse_rows(text, str(csv_path)), _infer_version(csv_path)
