"""End-to-end orchestrator behaviour (prisma_s.runner)."""

import json
import tempfile
import zipfile
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

from prisma_s.runner import OUTPUT_COLUMNS, run_analysis


def _kw(tmp_path, *pairs):
    p = tmp_path / "kw.csv"
    p.write_text("group,term\n" + "\n".join(f"{g},{t}" for g, t in pairs), encoding="utf-8")
    return p


def test_empty_corpus_raises(tmp_path):
    (tmp_path / "docs").mkdir()
    with pytest.raises(ValueError, match="No .pdf or .docx"):
        run_analysis("b", tmp_path / "out.xlsx", input_path=tmp_path / "docs",
                     keyword_csv=_kw(tmp_path, ("C", "Coffee")), emit_citation=False)


def test_zero_term_dictionary_raises(tmp_path, make_docx):
    make_docx("some text", name="a.docx")
    kw = tmp_path / "empty.csv"
    kw.write_text("group,term\nC,\n", encoding="utf-8")
    with pytest.raises(ValueError):
        run_analysis("b", tmp_path / "out.xlsx", input_path=tmp_path,
                     keyword_csv=kw, emit_citation=False)


def test_three_sheets_and_columns(tmp_path, make_docx):
    make_docx("Coffee and Cocoa and Coffee", name="a.docx")
    out = tmp_path / "out" / "r.xlsx"
    df = run_analysis("b", out, input_path=tmp_path,
                      keyword_csv=_kw(tmp_path, ("C", "Coffee"), ("C", "Cocoa")),
                      emit_citation=False)
    assert list(df.columns) == OUTPUT_COLUMNS
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Long_AllTerms", "PRISMA-S_Compliance", "Run_Metadata"]
    counts = {r["Term"]: r["Count"] for _, r in df.iterrows()}
    assert counts["Coffee"] == 2 and counts["Cocoa"] == 1
    meta = json.loads((out.parent / "run_metadata.json").read_text())
    assert meta["documents_processed"] == 1
    assert (out.parent / "HOW_TO_CITE.txt").exists()


def test_year_is_single_dtype_with_mixed_docs(tmp_path, make_pdf):
    make_pdf(["Study from 2011 about Coffee"], name="dated.pdf")
    make_pdf(["Coffee with no year at all"], name="undated.pdf")
    out = tmp_path / "r.xlsx"
    df = run_analysis("b", out, input_path=tmp_path,
                      keyword_csv=_kw(tmp_path, ("C", "Coffee")), emit_citation=False)
    assert str(df["Year"].dtype) == "Int64"


def test_zip_temp_dir_is_cleaned(tmp_path, make_docx):
    d = make_docx("Coffee here", name="a.docx")
    archive = tmp_path / "corpus.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.write(d, "a.docx")
        z.writestr("__MACOSX/._a.docx", b"junk")
    before = set(Path(tempfile.gettempdir()).glob("prisma_s_zip_*"))
    df = run_analysis("b", tmp_path / "out.xlsx", input_path=archive,
                      keyword_csv=_kw(tmp_path, ("C", "Coffee")), emit_citation=False)
    after = set(Path(tempfile.gettempdir()).glob("prisma_s_zip_*"))
    assert before == after                      # no leak
    assert df["Document Name"].nunique() == 1   # __MACOSX entry ignored


def test_corrupt_pdf_counted_as_skipped(tmp_path, make_docx):
    make_docx("Coffee", name="good.docx")
    (tmp_path / "bad.pdf").write_bytes(b"%PDF-1.4 not really a pdf")
    out = tmp_path / "r.xlsx"
    run_analysis("b", out, input_path=tmp_path,
                 keyword_csv=_kw(tmp_path, ("C", "Coffee")), emit_citation=False)
    meta = json.loads((out.parent / "run_metadata.json").read_text())
    assert meta["documents_discovered"] == 2
    assert meta["documents_processed"] == 1
    assert meta["documents_skipped"] == 1


def test_run_metadata_has_escalated_column_and_backend_counts(tmp_path, make_docx):
    make_docx("Coffee and Cocoa", name="a.docx")
    out = tmp_path / "r.xlsx"
    run_analysis("b", out, input_path=tmp_path,
                 keyword_csv=_kw(tmp_path, ("C", "Coffee")), emit_citation=False)
    meta = pd.read_excel(out, sheet_name="Run_Metadata")
    assert "Escalated" in meta.columns
    assert meta.loc[0, "Escalated"] in (False, 0)
    summary = json.loads((out.parent / "run_metadata.json").read_text())
    assert summary["backend_counts"].get("python-docx") == 1
    assert summary["ocr_enabled"] is True
    assert summary["escalated_documents"] == []


def test_escalation_surfaces_in_run_metadata(tmp_path, monkeypatch, make_pdf):
    import prisma_s.extract as extract

    pdf = make_pdf(["one two three"], name="thin.pdf")

    def fake_pdf(path, *, enable_ocr=True, ocr_lang="eng"):
        return extract.ExtractResult(
            full_text="Coffee " * 10, first_text="Coffee", metadata={}, pages=60,
            backend="pypdf", escalated=True, chain="pymupdf 3w -> pypdf 10w",
        )

    monkeypatch.setattr(extract, "extract_pdf", fake_pdf)
    monkeypatch.setattr("prisma_s.runner.extract_text",
                        lambda p, **k: fake_pdf(p, **k) if p.suffix == ".pdf" else None)
    out = tmp_path / "r.xlsx"
    run_analysis("b", out, input_path=tmp_path,
                 keyword_csv=_kw(tmp_path, ("C", "Coffee")), emit_citation=False)
    meta = pd.read_excel(out, sheet_name="Run_Metadata")
    row = meta[meta["Document Name"] == "thin.pdf"].iloc[0]
    assert bool(row["Escalated"]) is True
    assert "escalated" in row["Status"]
    assert json.loads((out.parent / "run_metadata.json").read_text())["escalated_documents"] == ["thin.pdf"]


def test_repeated_runs_are_byte_stable(tmp_path, make_pdf):
    make_pdf(["Coffee and Cocoa on page one", "more Coffee on page two"], name="a.pdf")
    kw = _kw(tmp_path, ("C", "Coffee"), ("C", "Cocoa"))
    a = run_analysis("b", tmp_path / "a.xlsx", input_path=tmp_path, keyword_csv=kw,
                     emit_citation=False).drop(columns=["Run UTC"])
    b = run_analysis("b", tmp_path / "b.xlsx", input_path=tmp_path, keyword_csv=kw,
                     emit_citation=False).drop(columns=["Run UTC"])
    pd.testing.assert_frame_equal(a, b)
