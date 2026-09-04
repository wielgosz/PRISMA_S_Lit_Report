"""
Text extraction from PDF and DOCX files.

PDF text is read from the document's **existing text layer** with pypdf.  There
is no OCR: an image-only or scanned PDF has no text layer, and prisma-s cannot
create one.  Such files must be OCR'd with an external tool (for example
``ocrmypdf``) *before* analysis.  Every document with no text, or with
suspiciously little text for its page count, is flagged in ``Run_Metadata`` and
``run_metadata.json`` so the user knows exactly which files to re-process.

DOCX extraction uses python-docx.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

# A PDF with fewer than this many words per page almost certainly has an
# incomplete text layer (a partial scan, or vector text pypdf cannot read).
# It is flagged, not "fixed".
THIN_WORDS_PER_PAGE = 40.0
_MIN_PAGES_FOR_THIN_CHECK = 2


@dataclass
class ExtractResult:
    """Everything one document contributes to the run."""

    full_text: str
    first_text: str
    metadata: dict
    pages: int | None  # page count for PDFs; None for DOCX
    backend: str  # "pypdf" | "python-docx"
    thin: bool = False  # empty or under-extracted text layer -> needs external OCR
    chain: str = ""  # short trace, e.g. "pypdf 12183w"
    attempts: list[str] = field(default_factory=list)


def _words(text: str) -> int:
    return len(text.split())


def looks_thin(text: str, pages: int | None) -> bool:
    """True when *text* is empty, or too short for its page count."""
    n = _words(text)
    if n == 0:
        return True
    if pages and pages >= _MIN_PAGES_FOR_THIN_CHECK:
        return (n / pages) < THIN_WORDS_PER_PAGE
    return False


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def extract_pdf(pdf_path: Path) -> ExtractResult:
    """Read the text layer of *pdf_path* with pypdf (no OCR)."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    md = reader.metadata or {}
    pages: list[str] = []
    first = ""
    for i, page in enumerate(reader.pages):
        txt = page.extract_text() or ""
        if i == 0:
            first = txt
        pages.append(txt)
    full = "\n".join(pages)
    res = ExtractResult(
        full_text=full,
        first_text=first,
        metadata=dict(md),
        pages=len(pages),
        backend="pypdf",
    )
    res.thin = looks_thin(full, res.pages)
    res.attempts = [f"pypdf {_words(full)}w"]
    res.chain = res.attempts[0]
    return res


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

def extract_docx(docx_path: Path) -> ExtractResult:
    from docx import Document

    doc = Document(str(docx_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    props = doc.core_properties
    full = "\n".join(paragraphs)
    return ExtractResult(
        full_text=full,
        first_text="\n".join(paragraphs[:10]),
        metadata={
            "/Title": props.title or "",
            "/CreationDate": str(props.created or ""),
            "/ModDate": str(props.modified or ""),
        },
        pages=None,
        backend="python-docx",
        thin=(_words(full) == 0),
        chain=f"python-docx {_words(full)}w",
    )


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def extract_text(file_path: Path) -> ExtractResult:
    """Dispatch to the correct extractor based on file extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(file_path)
    if suffix == ".docx":
        return extract_docx(file_path)
    raise ValueError(f"Unsupported file type: {suffix!r}")


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------

_SENTINEL_TITLES = {
    "untitled",
    "powerpoint presentation",
    "microsoft word - document",
}


def guess_title(md: dict, first: str) -> str:
    title = str(md.get("/Title", "") or "").strip()
    if title and title.lower() not in _SENTINEL_TITLES:
        return title
    lines = [ln.strip() for ln in first.splitlines() if len(ln.strip()) > 12]
    return lines[0][:180] if lines else "Unknown"


def guess_year(md: dict, first: str) -> int | None:
    """Publication year: first-page text first, document metadata as fallback.

    Order follows ``prisma_s/data/PRISMA_keyword_protocol_v1.1.md``; metadata
    dates are unreliable because reference managers re-stamp ``/ModDate`` on
    save.  Returns ``None`` when no plausible year is found.
    """
    years = [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", first)]
    if years:
        return max(years)
    for key in ("/CreationDate", "/ModDate"):
        if md.get(key):
            m = re.search(r"(19|20)\d{2}", str(md[key]))
            if m:
                return int(m.group(0))
    return None
