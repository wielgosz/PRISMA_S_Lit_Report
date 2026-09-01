"""
Keyword dictionary loader.

Two dictionary shapes are supported and auto-detected:

* **Registry (v1.3, the default)** -- columns ``category``, ``canonical_term``,
  ``search_variant`` (plus optional ``term_id``, ``active``,
  ``include_in_visuals``).  Many explicit ``search_variant`` rows roll up to one
  ``canonical_term``; per-document counts are summed across a canonical term's
  variants.  The bundled default is ``prisma_s/data/keyword_dictionary_v1.3.csv``
  (98 canonical terms).

* **Flat (v1.1)** -- columns ``group`` (or ``category``) and ``term``.  Every
  row is an independent term.  Selected with ``--keywords bundled:1.1`` or by
  supplying a matching CSV.

User CSVs are validated on load: a file with a byte-order mark, capitalised
headers, or the columns in another order is accepted; a file that cannot be
decoded, has no usable key column, or yields zero rows raises ``ValueError``
rather than silently producing an empty analysis.  The version is inferred from
the filename convention ``keyword_dictionary_v{MAJOR}.{MINOR}.csv``.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path

BUNDLED_DEFAULT_NAME = "keyword_dictionary_v1.3.csv"
BUNDLED_V11_NAME = "keyword_dictionary_v1.1.csv"
BUNDLED_VERSION = "1.3"  # version of the default bundled dictionary

# Header spellings, normalised to (strip + casefold).
_GROUP_KEYS = {"group", "category"}
_TERM_KEYS = {"term"}
_CANONICAL_KEYS = {"canonical_term", "canonical term"}
_VARIANT_KEYS = {"search_variant", "search variant", "variant"}


@dataclass
class KeywordDictionary:
    """A loaded keyword dictionary, flat or registry."""

    version: str
    is_registry: bool
    flat_rows: list[dict[str, str]] = field(default_factory=list)
    registry_rows: list[dict[str, str]] = field(default_factory=list)

    # -- flat helpers ----------------------------------------------------------
    @property
    def n_terms(self) -> int:
        return self.n_canonical if self.is_registry else len(self.flat_rows)

    # -- registry helpers ----------------------------------------------------
    @property
    def n_canonical(self) -> int:
        return len({(r["term_id"], r["canonical_term"]) for r in self.registry_rows})

    @property
    def n_variants(self) -> int:
        return len(self.registry_rows)

    def canonical_terms(self) -> list[tuple[str, str, str, list[str], bool]]:
        """``[(category, term_id, canonical_term, [variants], include_in_visuals)]``.

        Order follows first appearance in the CSV; variants are de-duplicated
        keeping order.
        """
        out: list[tuple[str, str, str, list[str], bool]] = []
        index: dict[tuple[str, str], int] = {}
        for r in self.registry_rows:
            key = (r["term_id"], r["canonical_term"])
            if key not in index:
                index[key] = len(out)
                out.append(
                    (r["category"], r["term_id"], r["canonical_term"], [],
                     r["include_in_visuals"] == "yes")
                )
            variants = out[index[key]][3]
            if r["search_variant"] not in variants:
                variants.append(r["search_variant"])
        return out


# ---------------------------------------------------------------------------
# Bundled-resource access
# ---------------------------------------------------------------------------

def bundled_dict_path(name: str = BUNDLED_DEFAULT_NAME) -> Path:
    """Filesystem path to a bundled dictionary (display only; may not be zip-safe)."""
    return Path(str(files("prisma_s").joinpath("data").joinpath(name)))


def bundled_dict_text(name: str = BUNDLED_DEFAULT_NAME) -> str:
    """Return a bundled dictionary CSV as UTF-8 text (zip-safe)."""
    return (
        files("prisma_s").joinpath("data").joinpath(name).read_text(encoding="utf-8")
    )


def resolve_dict_arg(arg: str | Path | None) -> tuple[str, str]:
    """Map a ``--keywords`` value to ``(kind, value)``.

    ``None`` / ``"bundled:1.3"`` -> the default bundled registry;
    ``"bundled:1.1"`` -> the bundled flat dictionary; anything else -> a path.
    """
    if arg is None:
        return "bundled", BUNDLED_DEFAULT_NAME
    s = str(arg).strip()
    if s.lower() in ("bundled:1.3", "bundled", "bundled:default"):
        return "bundled", BUNDLED_DEFAULT_NAME
    if s.lower() in ("bundled:1.1", "bundled:v1.1"):
        return "bundled", BUNDLED_V11_NAME
    return "path", s


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _read_csv_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(
        f"Could not decode {path} as UTF-8 or cp1252. Re-save it as 'CSV UTF-8'."
    )


def _norm_header(fieldnames: list[str]) -> dict[str, str]:
    return {(name or "").strip().casefold(): name for name in fieldnames}


def _parse_flat(text: str, source: str, version: str) -> KeywordDictionary:
    reader = csv.DictReader(io.StringIO(text))
    norm = _norm_header(reader.fieldnames or [])
    term_key = next((norm[k] for k in norm if k in _TERM_KEYS), None)
    group_key = next((norm[k] for k in norm if k in _GROUP_KEYS), None)
    if term_key is None:
        raise ValueError(
            f"{source}: no 'term' column found. Header was {reader.fieldnames!r}; "
            "expected 'group' (or 'category') and 'term'."
        )
    rows: list[dict[str, str]] = []
    for row in reader:
        term = (row.get(term_key) or "").strip()
        if not term:
            continue
        group = (row.get(group_key) or "").strip() if group_key else ""
        rows.append({"group": group, "term": term})
    if not rows:
        raise ValueError(f"{source}: 0 usable terms (every '{term_key}' value was empty).")
    return KeywordDictionary(version=version, is_registry=False, flat_rows=rows)


def _parse_registry(text: str, source: str, version: str) -> KeywordDictionary:
    reader = csv.DictReader(io.StringIO(text))
    norm = _norm_header(reader.fieldnames or [])
    cat_k = next((norm[k] for k in norm if k in _GROUP_KEYS), None)
    can_k = next((norm[k] for k in norm if k in _CANONICAL_KEYS), None)
    var_k = next((norm[k] for k in norm if k in _VARIANT_KEYS), None)
    id_k = norm.get("term_id")
    active_k = norm.get("active")
    iv_k = next((norm[k] for k in norm if k in {"include_in_visuals", "include in visuals"}), None)

    rows: list[dict[str, str]] = []
    seen_ids: dict[str, str] = {}
    for row in reader:
        if active_k and (row.get(active_k) or "yes").strip().casefold() != "yes":
            continue
        variant = (row.get(var_k) or "").strip()
        canonical = (row.get(can_k) or "").strip()
        if not variant or not canonical:
            continue
        term_id = (row.get(id_k) or "").strip() if id_k else ""
        if not term_id:
            term_id = seen_ids.setdefault(canonical, f"TERM-{len(seen_ids) + 1:04d}")
        rows.append(
            {
                "category": (row.get(cat_k) or "").strip() if cat_k else "",
                "term_id": term_id,
                "canonical_term": canonical,
                "search_variant": variant,
                "include_in_visuals": "yes"
                if not iv_k or (row.get(iv_k) or "yes").strip().casefold() == "yes"
                else "no",
            }
        )
    if not rows:
        raise ValueError(f"{source}: 0 usable rows (no active canonical_term/search_variant pairs).")
    return KeywordDictionary(version=version, is_registry=True, registry_rows=rows)


def _looks_like_registry(text: str) -> bool:
    first_line = text.splitlines()[0] if text else ""
    norm = {c.strip().casefold() for c in first_line.split(",")}
    return bool(norm & _CANONICAL_KEYS) and bool(norm & _VARIANT_KEYS)


def _infer_version(csv_path: Path) -> str:
    m = re.search(r"v(\d+\.\d+)", csv_path.stem)
    return m.group(1) if m else "custom"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def load_keywords(arg: str | Path | None = None) -> KeywordDictionary:
    """Load a keyword dictionary, auto-detecting the flat vs registry shape.

    *arg* is a ``--keywords`` value: ``None`` / ``"bundled:1.3"`` for the default
    registry, ``"bundled:1.1"`` for the flat dictionary, or a path to a CSV.
    """
    kind, value = resolve_dict_arg(arg)
    if kind == "bundled":
        text = bundled_dict_text(value)
        version = "1.1" if value == BUNDLED_V11_NAME else BUNDLED_VERSION
        source = f"bundled dictionary ({value})"
    else:
        path = Path(value)
        text = _read_csv_text(path)
        version = _infer_version(path)
        source = str(path)

    if _looks_like_registry(text):
        return _parse_registry(text, source, version)
    return _parse_flat(text, source, version)
