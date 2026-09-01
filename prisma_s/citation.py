"""
"How to cite" / attribution text, in English, Brazilian Portuguese, and Spanish.

The text lives in ``prisma_s/data/citation/{en,pt_br,es}.md`` and is read via
:mod:`importlib.resources` so it ships with the package.  ``prisma-s cite``
prints it; a run prints all three blocks when it finishes and also writes
``HOW_TO_CITE.txt`` next to the results.
"""

from __future__ import annotations

from importlib.resources import files

LANGS: dict[str, str] = {
    "en": "English",
    "pt-br": "Português (Brasil)",
    "es": "Español",
}

_FILES = {"en": "en.md", "pt-br": "pt_br.md", "es": "es.md"}


def citation_text(lang: str = "en") -> str:
    """Return the citation block for *lang* (``en`` | ``pt-br`` | ``es``)."""
    key = lang.lower().replace("_", "-")
    if key not in _FILES:
        raise ValueError(f"Unknown language {lang!r}; choose from {sorted(_FILES)}.")
    resource = (
        files("prisma_s").joinpath("data").joinpath("citation").joinpath(_FILES[key])
    )
    return resource.read_text(encoding="utf-8").strip()


def all_citations() -> str:
    """Return the three citation blocks joined with language separators."""
    parts = []
    for key, label in LANGS.items():
        bar = "=" * 70
        parts.append(f"{bar}\n{label}\n{bar}\n\n{citation_text(key)}")
    return "\n\n\n".join(parts)
