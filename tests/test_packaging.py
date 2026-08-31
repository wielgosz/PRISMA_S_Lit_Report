"""
Regression tests for packaging and encoding fixes (v1.3.0).

These guard three failures seen on a clean Windows install:
  * the bundled keyword dictionary was not installed with the package;
  * a default ``prisma-s run`` crashed before writing output;
  * non-ASCII (Portuguese / Spanish) keyword terms could not be handled.
"""

from __future__ import annotations

import openpyxl
import pytest

from prisma_s import __version__
from prisma_s.keywords import bundled_dict_path, bundled_dict_text, load_keywords
from prisma_s.runner import run_analysis
from prisma_s.search import build_regex


def test_version_is_unified():
    assert __version__ == "1.3.0"


def test_bundled_dict_path_exists():
    p = bundled_dict_path()
    assert p.exists(), f"bundled dictionary missing from the install: {p}"
    assert p.name == "keyword_dictionary_v1.1.csv"


def test_bundled_dict_loads_without_args():
    rows, version = load_keywords(None)
    assert version == "1.1"
    assert len(rows) > 50
    assert {"group", "term"} <= set(rows[0])


def test_bundled_dict_text_matches_file():
    assert bundled_dict_text().splitlines()[0].strip() == "group,term"


def test_accented_term_matches_case_insensitively():
    rgx = build_regex("ação")
    assert len(rgx.findall("Uma Ação e outra ação no texto")) == 2
    assert build_regex("análisis").findall("El ANÁLISIS final") == ["ANÁLISIS"]


def _write_docx(path, text):
    from docx import Document

    doc = Document()
    for para in text.split("\n"):
        doc.add_paragraph(para)
    doc.save(str(path))


def test_run_analysis_smoke_uses_bundled_dict(tmp_path):
    """A default run (no keyword_csv) writes a valid two-sheet workbook."""
    docs = tmp_path / "docs"
    docs.mkdir()
    _write_docx(
        docs / "sample.docx",
        "This study of the Cocoa and Coffee supply chain uses Polygon data.\n"
        "Deforestation and traceability were assessed. Coffee again.",
    )
    out = tmp_path / "out" / "smoke.xlsx"

    df = run_analysis(batch_id="smoke", output_xlsx=out, input_path=docs)

    assert out.exists()
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Long_AllTerms", "PRISMA-S_Compliance"]

    coffee = df[df["Term"] == "Coffee"]["Count"]
    assert not coffee.empty and int(coffee.iloc[0]) == 2
    # zero-count rows are retained
    assert (df["Count"] == 0).any()


def test_run_analysis_accepts_utf8_keyword_csv(tmp_path):
    kw = tmp_path / "kw_pt.csv"
    kw.write_text("group,term\nPT,ação\nPT,região\nES,café\n", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    _write_docx(docs / "d.docx", "Ação de conservação na região do café.")
    out = tmp_path / "acc.xlsx"

    df = run_analysis(
        batch_id="acc", output_xlsx=out, input_path=docs, keyword_csv=kw
    )

    counts = dict(zip(df["Term"], df["Count"]))
    assert counts["ação"] == 1
    assert counts["região"] == 1
    assert counts["café"] == 1
