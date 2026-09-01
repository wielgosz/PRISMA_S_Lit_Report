"""
Text extraction from PDF and DOCX files.

PDF extraction is a **per-document escalation chain**, so heavy processing is
spent only where it is needed:

    1. Primary PDF library  - PyMuPDF if the ``fast-pdf`` extra is installed,
       otherwise pypdf.
    2. Other PDF library     - tried when rung 1 returns no text, or fewer than
       ``THIN_WORDS_PER_PAGE`` words per page; the richer result is kept.
    3. OCR (PyMuPDF + Tesseract) - tried only when a document is still textless
       after the PDF libraries, and only if Tesseract is on PATH.  Disable with
       ``enable_ocr=False`` (CLI: ``--no-ocr``).

Which rung produced each document's text, and whether the chain escalated, is
recorded per document so a run stays reproducible and auditable.

DOCX extraction uses python-docx.
"""

from __future__ import annotations

import re
import shutil
import warnings
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

# A document with fewer than this many words per page is treated as
# under-extracted and the chain escalates to the other PDF library.
THIN_WORDS_PER_PAGE = 40.0
# Don't bother escalating tiny documents (cover pages, one-page forms).
_MIN_PAGES_FOR_THIN_CHECK = 2

# Resolved once: is PyMuPDF importable?  A missing optional dependency must be a
# one-time notice, not a silent per-file downgrade.  Newer PyMuPDF prefers the
# ``pymupdf`` module name; the legacy ``fitz`` alias still works but warns.
try:  # pragma: no cover - depends on the install having the extra
    try:
        import pymupdf as _fitz  # noqa: F401
    except ImportError:
        import fitz as _fitz  # noqa: F401
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
    backend: str  # "pymupdf" | "pypdf" | "ocr" | "python-docx"
    escalated: bool = False
    chain: str = ""  # human-readable trace, e.g. "pypdf 12w -> pymupdf 11040w"
    attempts: list[str] = field(default_factory=list)


def _words(text: str) -> int:
    return len(text.split())


def _looks_thin(text: str, pages: int | None) -> bool:
    n = _words(text)
    if n == 0:
        return True
    if pages and pages >= _MIN_PAGES_FOR_THIN_CHECK:
        return (n / pages) < THIN_WORDS_PER_PAGE
    return False


# ---------------------------------------------------------------------------
# PDF library rungs
# ---------------------------------------------------------------------------

def _extract_pdf_pymupdf(pdf_path: Path) -> ExtractResult:
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz

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


# Legacy alias (kept for any external callers / tests).
_extract_pdf_fitz = _extract_pdf_pymupdf


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


# ---------------------------------------------------------------------------
# OCR rung
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _ocr_available() -> bool:
    """OCR needs PyMuPDF's engine and the Tesseract binary on PATH."""
    return _HAVE_FITZ and shutil.which("tesseract") is not None


def _ocr_pdf(pdf_path: Path, lang: str = "eng", dpi: int = 200) -> ExtractResult:
    """Rasterise every page and OCR it with Tesseract via PyMuPDF."""
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz

    doc = fitz.open(str(pdf_path))
    n = doc.page_count
    out: list[str] = []
    for i in range(n):
        page = doc.load_page(i)
        tp = page.get_textpage_ocr(flags=3, language=lang, dpi=dpi, full=True)
        out.append(page.get_text("text", textpage=tp) or "")
    full = "\n".join(out)
    md = doc.metadata or {}
    return ExtractResult(
        full_text=full,
        first_text=out[0] if out else "",
        metadata={
            "/Title": md.get("title", ""),
            "/CreationDate": md.get("creationDate", ""),
            "/ModDate": md.get("modDate", ""),
        },
        pages=n,
        backend="ocr",
    )


# ---------------------------------------------------------------------------
# Chain
# ---------------------------------------------------------------------------

def _pdf_library_rungs():
    """Primary library first, then the other one (if it is installed)."""
    if _HAVE_FITZ:
        return [("pymupdf", _extract_pdf_pymupdf), ("pypdf", _extract_pdf_pypdf)]
    return [("pypdf", _extract_pdf_pypdf)]  # pymupdf not installed


def extract_pdf(
    pdf_path: Path, *, enable_ocr: bool = True, ocr_lang: str = "eng"
) -> ExtractResult:
    """Extract *pdf_path* via the escalation chain (see the module docstring)."""
    attempts: list[str] = []
    best: ExtractResult | None = None

    for name, fn in _pdf_library_rungs():
        try:
            res = fn(pdf_path)
        except Exception as exc:
            attempts.append(f"{name} error: {exc}")
            continue
        attempts.append(f"{name} {_words(res.full_text)}w")
        if best is None or _words(res.full_text) > _words(best.full_text):
            best = res
        if not _looks_thin(res.full_text, res.pages):
            break  # good enough - do not escalate

    ran_ocr = False
    if (
        enable_ocr
        and best is not None
        and _words(best.full_text) == 0
        and _ocr_available()
    ):
        ran_ocr = True
        try:
            ocr_res = _ocr_pdf(pdf_path, lang=ocr_lang)
            attempts.append(f"ocr {_words(ocr_res.full_text)}w")
            if _words(ocr_res.full_text) > _words(best.full_text):
                best = ocr_res
        except Exception as exc:
            attempts.append(f"ocr error: {exc}")

    if best is None:
        raise RuntimeError("all PDF extractors failed: " + "; ".join(attempts))

    successful = [a for a in attempts if "error" not in a]
    best.attempts = attempts
    best.chain = " -> ".join(attempts)
    best.escalated = len(successful) > 1 or ran_ocr
    return best


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

def extract_text(
    file_path: Path, *, enable_ocr: bool = True, ocr_lang: str = "eng"
) -> ExtractResult:
    """Dispatch to the correct extractor based on file extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(file_path, enable_ocr=enable_ocr, ocr_lang=ocr_lang)
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
