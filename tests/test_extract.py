"""Extraction integrity (prisma_s.extract) - pypdf text layer only, no OCR."""

from prisma_s.extract import (
    ExtractResult,
    extract_pdf,
    extract_text,
    guess_title,
    guess_year,
    looks_thin,
)


def test_pdf_page_and_word_count(make_pdf):
    pdf = make_pdf(["alpha beta gamma", "delta epsilon", "zeta"])
    res = extract_text(pdf)
    assert res.pages == 3
    assert res.backend == "pypdf"
    assert set(res.full_text.split()) == {
        "alpha", "beta", "gamma", "delta", "epsilon", "zeta"
    }
    assert res.thin is True  # 6 words over 3 pages is under the threshold
    assert res.chain == "pypdf 6w"


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


def test_looks_thin():
    assert looks_thin("", 10) is True
    assert looks_thin("only a few words here", 40) is True          # ~0.1 w/page
    assert looks_thin(" ".join(["w"] * 5000), 40) is False          # 125 w/page
    assert looks_thin("short single page", 1) is False              # too few pages to judge


def test_textless_pdf_is_flagged_not_escalated(monkeypatch, tmp_path):
    """A scan-only PDF (no text layer) is flagged for external OCR, nothing more."""
    import pypdf

    class _Empty:
        metadata = {}
        pages = [type("P", (), {"extract_text": lambda self: ""})() for _ in range(8)]

    monkeypatch.setattr(pypdf, "PdfReader", lambda *_a, **_k: _Empty())

    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    res = extract_pdf(pdf)
    assert res.backend == "pypdf"
    assert res.full_text.strip() == ""
    assert res.thin is True
    assert res.pages == 8


def test_extract_pdf_has_no_ocr_or_backend_kwargs():
    import inspect

    params = inspect.signature(extract_pdf).parameters
    assert list(params) == ["pdf_path"]
    params = inspect.signature(extract_text).parameters
    assert list(params) == ["file_path"]


def test_guess_year_prefers_first_page_text():
    md = {"/CreationDate": "D:20260101000000"}
    assert guess_year(md, "Published in 2004. Journal of Things.") == 2004


def test_guess_year_none_when_absent():
    assert guess_year({}, "no dates anywhere in this text") is None


def test_guess_title_rejects_sentinels():
    assert guess_title({"/Title": "PowerPoint Presentation"},
                       "A Real Descriptive Heading Line") == "A Real Descriptive Heading Line"
