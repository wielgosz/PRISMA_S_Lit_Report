"""Extraction integrity and the per-document escalation chain (prisma_s.extract)."""

import prisma_s.extract as extract
from prisma_s.extract import ExtractResult, extract_pdf, extract_text, guess_title, guess_year


def test_pdf_page_and_word_count(make_pdf):
    pdf = make_pdf(["alpha beta gamma", "delta epsilon", "zeta"])
    res = extract_text(pdf)
    assert res.pages == 3
    assert res.backend in {"pypdf", "pymupdf", "ocr"}
    assert set(res.full_text.split()) == {
        "alpha", "beta", "gamma", "delta", "epsilon", "zeta"
    }


def test_extraction_is_deterministic(make_pdf):
    pdf = make_pdf(["one two three four", "five six"])
    a = extract_text(pdf)
    b = extract_text(pdf)
    assert (a.full_text, a.pages) == (b.full_text, b.pages)


def test_docx_has_no_page_count(make_docx):
    res = extract_text(make_docx("hello world\nsecond line"))
    assert res.pages is None
    assert res.backend == "python-docx"
    assert "second line" in res.full_text


def _fake(words, pages, backend):
    def _fn(_p, *args, **kwargs):
        return ExtractResult(
            full_text=" ".join(["w"] * words),
            first_text="w",
            metadata={},
            pages=pages,
            backend=backend,
        )

    return _fn


def test_chain_escalates_from_thin_primary_to_richer_secondary(monkeypatch, tmp_path):
    monkeypatch.setattr(extract, "_HAVE_FITZ", True)
    monkeypatch.setattr(extract, "_extract_pdf_pymupdf", _fake(10, 60, "pymupdf"))  # thin
    monkeypatch.setattr(extract, "_extract_pdf_pypdf", _fake(6000, 60, "pypdf"))    # rich
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    res = extract_pdf(pdf)
    assert res.backend == "pypdf"
    assert res.escalated is True
    assert "pymupdf 10w -> pypdf 6000w" in res.chain


def test_chain_stops_at_primary_when_not_thin(monkeypatch, tmp_path):
    monkeypatch.setattr(extract, "_HAVE_FITZ", True)
    calls = []
    monkeypatch.setattr(extract, "_extract_pdf_pymupdf", _fake(5000, 50, "pymupdf"))
    monkeypatch.setattr(
        extract, "_extract_pdf_pypdf",
        lambda p: calls.append(p) or _fake(1, 50, "pypdf")(p),
    )
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    res = extract_pdf(pdf)
    assert res.backend == "pymupdf" and res.escalated is False
    assert calls == []  # secondary never invoked


def test_ocr_rung_runs_only_when_still_textless(monkeypatch, tmp_path):
    monkeypatch.setattr(extract, "_HAVE_FITZ", True)
    monkeypatch.setattr(extract, "_extract_pdf_pymupdf", _fake(0, 12, "pymupdf"))
    monkeypatch.setattr(extract, "_extract_pdf_pypdf", _fake(0, 12, "pypdf"))
    monkeypatch.setattr(extract, "_ocr_available", lambda: True)
    monkeypatch.setattr(extract, "_ocr_pdf", _fake(400, 12, "ocr"))
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    res = extract_pdf(pdf)
    assert res.backend == "ocr" and res.escalated is True
    assert "ocr 400w" in res.chain


def test_ocr_skipped_when_disabled(monkeypatch, tmp_path):
    monkeypatch.setattr(extract, "_HAVE_FITZ", True)
    monkeypatch.setattr(extract, "_extract_pdf_pymupdf", _fake(0, 12, "pymupdf"))
    monkeypatch.setattr(extract, "_extract_pdf_pypdf", _fake(0, 12, "pypdf"))
    monkeypatch.setattr(extract, "_ocr_available", lambda: True)
    monkeypatch.setattr(extract, "_ocr_pdf", _fake(400, 12, "ocr"))
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    res = extract_pdf(pdf, enable_ocr=False)
    assert res.backend in {"pymupdf", "pypdf"}
    assert res.full_text == ""


def test_guess_year_prefers_first_page_text():
    md = {"/CreationDate": "D:20260101000000"}
    assert guess_year(md, "Published in 2004. Journal of Things.") == 2004


def test_guess_year_none_when_absent():
    assert guess_year({}, "no dates anywhere in this text") is None


def test_guess_title_rejects_sentinels():
    assert guess_title({"/Title": "PowerPoint Presentation"},
                       "A Real Descriptive Heading Line") == "A Real Descriptive Heading Line"
