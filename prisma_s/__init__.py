"""
prisma_s — PRISMA-S aligned keyword corpus analysis for systematic literature reviews.

PRISMA-S reference
------------------
This library implements corpus-analysis workflows informed by the PRISMA-S
checklist for transparent reporting of literature searches in systematic reviews.

  Rethlefsen ML, Kirtley S, Waffenschmidt S, et al.
  "PRISMA-S: an extension to the PRISMA Statement for Reporting Literature
  Searches in Systematic Reviews."
  Systematic Reviews 10, 39 (2021). https://doi.org/10.1186/s13643-020-01542-z

  Checklist and guidance: https://www.prisma-statement.org/prisma-search

Package layout
--------------
prisma_s.keywords    — versioned keyword dictionary loader
prisma_s.extract     — PDF and DOCX full-text extraction
prisma_s.search      — regex-based keyword matching engine
prisma_s.drive       — Google Drive folder ingestion
prisma_s.runner      — top-level run_analysis() orchestrator
prisma_s.compliance  — PRISMA-S 16-item compliance report builder
prisma_s.wizard      — interactive CLI setup wizard
prisma_s.cli         — argparse entry point (prisma-s command)

Quick start
-----------
>>> from prisma_s import run_analysis
>>> df = run_analysis(
...     batch_id="batch_01",
...     output_xlsx="results/batch_01.xlsx",
...     input_path="/path/to/pdfs",
... )

Or interactively from the terminal:
    prisma-s wizard
"""

__version__ = "1.2.0"
PROTOCOL_VERSION = "1.1"

from .runner import run_analysis

__all__ = ["run_analysis", "__version__", "PROTOCOL_VERSION"]
