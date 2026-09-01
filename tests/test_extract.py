"""Extraction integrity (prisma_s.extract)."""

import prisma_s.extract as extract
from prisma_s.extract import extract_text, guess_title, guess_year


def test_pdf_page_and_word_count(make_pdf):
    pdf = make_pdf(["alpha beta gamma", "delta epsilon", "zeta"])
    res = extract_text(pdf)
    assert res.pages == 3
    assert res.backend in {"pypdf", "pymupdf"}
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


def test_pymupdf_import_failure_falls_back(monkeypatch, make_pdf, recwarn):
    monkeypatch.setattr(extract, "_HAVE_FITZ", True)

    def boom(_):
        raise ImportError("no fitz")

    monkeypatch.setattr(extract, "_extract_pdf_fitz", boom)
    res = extract_text(make_pdf(["fallback text here"]))
    assert res.backend == "pypdf"
    assert any("pypdf" in str(w.message) for w in recwarn.list)


def test_guess_year_prefers_first_page_text():
    md = {"/CreationDate": "D:20260101000000"}
    assert guess_year(md, "Published in 2004. Journal of Things.") == 2004


def test_guess_year_none_when_absent():
    assert guess_year({}, "no dates anywhere in this text") is None


def test_guess_title_rejects_sentinels():
    assert guess_title({"/Title": "PowerPoint Presentation"},
                       "A Real Descriptive Heading Line") == "A Real Descriptive Heading Line"
