"""
Text extraction from PDF and DOCX files.

PDF extraction tries PyMuPDF (fitz) first; falls back to PyPDF2.
DOCX extraction uses python-docx.
"""

from __future__ import annotations

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def _extract_pdf_fitz(pdf_path: Path) -> tuple[str, str, dict]:
    import fitz  # PyMuPDF
    doc = fitz.open(str(pdf_path))
    md = doc.metadata or {}
    first = doc.load_page(0).get_text("text") if doc.page_count else ""
    full = "\n".join(
        doc.load_page(i).get_text("text") or "" for i in range(doc.page_count)
    )
    return full, first, {
        "/Title": md.get("title", ""),
        "/CreationDate": md.get("creationDate", ""),
        "/ModDate": md.get("modDate", ""),
    }


def _extract_pdf_pypdf2(pdf_path: Path) -> tuple[str, str, dict]:
    from PyPDF2 import PdfReader
    reader = PdfReader(str(pdf_path))
    md = reader.metadata or {}
    pages, first = [], ""
    for i, page in enumerate(reader.pages):
        txt = page.extract_text() or ""
        if i == 0:
            first = txt
        pages.append(txt)
    return "\n".join(pages), first, dict(md)


def extract_pdf(pdf_path: Path) -> tuple[str, str, dict]:
    """Return (full_text, first_page_text, metadata_dict) for a PDF."""
    try:
        return _extract_pdf_fitz(pdf_path)
    except Exception:
        return _extract_pdf_pypdf2(pdf_path)


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

def extract_docx(docx_path: Path) -> tuple[str, str, dict]:
    """Return (full_text, first_paragraphs_text, metadata_dict) for a DOCX."""
    from docx import Document
    doc = Document(str(docx_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    full = "\n".join(paragraphs)
    first = "\n".join(paragraphs[:10])
    props = doc.core_properties
    md = {
        "/Title": props.title or "",
        "/CreationDate": str(props.created or ""),
        "/ModDate": str(props.modified or ""),
    }
    return full, first, md


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def extract_text(file_path: Path) -> tuple[str, str, dict]:
    """Dispatch to the correct extractor based on file extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(file_path)
    elif suffix == ".docx":
        return extract_docx(file_path)
    raise ValueError(f"Unsupported file type: {suffix!r}")


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------

def guess_title(md: dict, first: str) -> str:
    title = str(md.get("/Title", "") or "").strip()
    if title and title.lower() not in {
        "untitled", "powerpoint presentation", "microsoft word - document"
    }:
        return title
    lines = [ln.strip() for ln in first.splitlines() if len(ln.strip()) > 12]
    return lines[0][:180] if lines else "Unknown"


def guess_year(md: dict, first: str) -> int | str:
    for key in ("/CreationDate", "/ModDate"):
        if md.get(key):
            m = re.search(r"(19|20)\d{2}", str(md[key]))
            if m:
                return int(m.group(0))
    years = [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", first)]
    return max(years) if years else "Unknown"
