"""
Packaging / import regression guards.

Covers the v1.3 bundled-dictionary fixes and the v1.4 lazy-import + versioning
changes.
"""

from __future__ import annotations

import subprocess
import sys

import openpyxl

from prisma_s import __version__
from prisma_s.keywords import bundled_dict_path, bundled_dict_text, load_keywords
from prisma_s.runner import run_analysis
from prisma_s.search import build_regex


def test_version_is_unified():
    assert __version__ == "1.4.0"


def test_import_prisma_s_does_not_import_pandas():
    """`prisma-s --version` must not pay the pandas import cost."""
    code = "import prisma_s, sys; print('pandas' in sys.modules)"
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert out == "False"


def test_bundled_dict_path_exists():
    p = bundled_dict_path()
    assert p.exists() and p.name == "keyword_dictionary_v1.1.csv"


def test_bundled_dict_loads_without_args():
    rows, version = load_keywords(None)
    assert version == "1.1"
    assert len(rows) > 50


def test_bundled_dict_text_first_line():
    assert bundled_dict_text().splitlines()[0].strip() == "group,term"


def test_accented_term_matches_case_insensitively():
    assert len(build_regex("ação").findall("Uma Ação e outra ação")) == 2
    assert build_regex("análisis").findall("El ANÁLISIS final") == ["ANÁLISIS"]


def test_run_analysis_smoke_uses_bundled_dict(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    from docx import Document

    d = Document()
    d.add_paragraph("This study of the Cocoa and Coffee supply chain uses Polygon data.")
    d.add_paragraph("Deforestation and traceability were assessed. Coffee again.")
    d.save(str(docs / "sample.docx"))

    out = tmp_path / "out" / "smoke.xlsx"
    df = run_analysis(batch_id="smoke", output_xlsx=out, input_path=docs, emit_citation=False)

    assert out.exists()
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Long_AllTerms", "PRISMA-S_Compliance", "Run_Metadata"]

    coffee = df[df["Term"] == "Coffee"]["Count"]
    assert not coffee.empty and int(coffee.iloc[0]) == 2
    assert (df["Count"] == 0).any()  # zero rows retained
