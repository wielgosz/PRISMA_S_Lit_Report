"""
Text extraction from PDF and DOCX files.

PDF extraction uses **pypdf** by default.  If the optional ``fast-pdf`` extra is
installed (``pip install prisma-s-lit-review[fast-pdf]``) PyMuPDF is used
instead for higher-fidelity text; the backend actually used is recorded per
document so a run stays reproducible and auditable.

DOCX extraction uses python-docx.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

# Resolved once: is PyMuPDF importable?  A missing optional dependency must be a
# one-time notice, not a silent per-file downgrade.
try:  # pragma: no cover - depends on the install having the extra
    import fitz  # noqa: F401  (PyMuPDF)

    _HAVE_FITZ = True
except Exception:  # ImportError, or a broken build
    _HAVE_FITZ = False


@dataclass
class ExtractResult:
    """Everything one document contributes to the run."""

    full_text: str
    first_text: str
    metadata: dict
    pages: int | None  # page count for PDFs; None for DOCX
    backend: str  # "pymupdf" | "pypdf" | "python-docx"


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def _extract_pdf_fitz(pdf_path: Path) -> ExtractResult:
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf_path))
    md = doc.metadata or {}
    n = doc.page_count
    first = doc.load_page(0).get_text("text") if n else ""
    full = "\n".join(doc.load_page(i).get_text("text") or "" for i in range(n))
    return ExtractResult(
        full_text=full,
        first_text=first,
        metadata={
            "/Title": md.get("title", ""),
            "/CreationDate": md.get("creationDate", ""),
            "/ModDate": md.get("modDate", ""),
        },
        pages=n,
        backend="pymupdf",
    )


def _extract_pdf_pypdf(pdf_path: Path) -> ExtractResult:
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
    return ExtractResult(
        full_text="\n".join(pages),
        first_text=first,
        metadata=dict(md),
        pages=len(pages),
        backend="pypdf",
    )


def extract_pdf(pdf_path: Path) -> ExtractResult:
    """Extract a PDF with PyMuPDF if available, otherwise pypdf.

    Data errors (corrupt file, encrypted, no text layer) propagate to the
    caller so the document can be recorded as skipped.
    """
    if _HAVE_FITZ:
        try:
            return _extract_pdf_fitz(pdf_path)
        except Exception as exc:  # a data error in this specific file
            warnings.warn(
                f"PyMuPDF failed on {pdf_path.name} ({exc!r}); retrying with pypdf",
                stacklevel=2,
            )
    return _extract_pdf_pypdf(pdf_path)


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

def extract_docx(docx_path: Path) -> ExtractResult:
    from docx import Document

    doc = Document(str(docx_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    props = doc.core_properties
    return ExtractResult(
        full_text="\n".join(paragraphs),
        first_text="\n".join(paragraphs[:10]),
        metadata={
            "/Title": props.title or "",
            "/CreationDate": str(props.created or ""),
            "/ModDate": str(props.modified or ""),
        },
        pages=None,
        backend="python-docx",
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
