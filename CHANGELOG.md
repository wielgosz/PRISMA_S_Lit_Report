# Changelog

All notable changes to this project will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.0] - 2026-08-31

### Fixed (correctness)
- A user keyword CSV saved from Excel (byte-order mark, capitalised headers, or
  `term,group` column order) is now parsed correctly. A CSV with no `term`
  column, or that yields zero terms, raises `ValueError` instead of silently
  writing an empty workbook. `category` is accepted as a synonym for `group`.
- An empty run (no documents, all extractions failed) no longer produces a
  `(0, 0)` DataFrame; the frame always has the documented columns, and
  `run_analysis` raises with an actionable message when there is nothing to do.
- Matching now uses **alphanumeric boundaries** (`(?<![A-Za-z0-9]) ... (?![A-Za-z0-9])`)
  instead of `\b`: terms that start or end with punctuation (`(CO2)`, `+ve`)
  match, `_` is treated as a separator, and multi-word phrases tolerate a
  hyphenated line break between words. A term listed under two groups is now
  counted under each rather than silently dropped.
- `guess_year` takes the first-page text year first and the document metadata
  date only as a fallback (matching the protocol spec); returns `None` when
  absent, so the `Year` column is a single nullable `Int64` dtype.
- `.zip` input no longer leaks a full corpus copy into the temp directory;
  `__MACOSX/` and `._*` entries are ignored.
- The `PRISMA-S_Compliance` sheet no longer contains statements that are false
  at runtime: it references the real `Run_Metadata` sheet, and the multi-lingual
  note is formatted from the dictionary version actually used.
- The compliance document count is the number of documents **processed**, not
  discovered.
- `token.json` (Drive OAuth) is written `0600`; a failed token refresh falls
  back to interactive consent instead of aborting the run.

### Added
- `Run_Metadata` sheet + `run_metadata.json`: per-document extraction backend,
  page / word / character counts, and status; run-level discovered / processed /
  skipped totals. This is the artifact for checking extraction completeness.
- `prisma-s cite [--lang en|pt-br|es|all]`; the trilingual "How to cite" block
  is printed when a run finishes (suppress with `--no-citation`) and written to
  `HOW_TO_CITE.txt` beside the results.
- `LICENSE` (MIT, code), `LICENSE-CC-BY-4.0.txt` + `prisma_s/data/DATA_LICENSE.md`
  (CC BY 4.0 for the dictionary, protocol spec, figures, and docs), and
  `CITATION.cff` with the associated WRI guidebook as the preferred citation.
- `docs/USAGE.md` and `docs/METHOD.md` (each protocol rule paired with its code);
  `prisma_s/py.typed`.
- Regression tests: `test_keywords.py`, `test_runner.py`, `test_extract.py`,
  `test_cli.py`, `test_cite.py`, and additions to `test_search.py`; synthetic
  multi-page PDF fixtures via `reportlab` (dev extra). `--doctest-modules` on.

### Changed
- **Default PDF backend is now pypdf** (BSD). PyMuPDF (AGPL-3.0) moves to an
  optional extra: `pip install "prisma-s-lit-review[fast-pdf]"`. The backend
  used is recorded per document.
- Dependency bounds added (`pandas>=2.0,<3`, `openpyxl>=3.1,<4`); 3.13 classifier
  added.
- `prisma_s/__init__.py` no longer imports pandas at import time (`run_analysis`
  is a lazy re-export); `__version__` / `PROTOCOL_VERSION` moved to a
  dependency-free `prisma_s/_version.py`.
- Version 1.4.0.

### Removed
- `scripts/keyword_corpus_analysis.py` — a pre-package monolith that duplicated
  the extraction / matching logic and carried a third copy of the keyword list.

### Deferred to 1.5
- Term-frequency figures (port of the desktop-runner SVG spec), the v1.3
  canonicalization dictionary (variant roll-up) as the default, Tkinter folder
  pickers, `prisma-s template`, dated run-output folders.

---

## [1.3.0] - 2026-08-31

### Fixed
- `prisma-s run` with no `--keywords` no longer crashes with `No such file or directory: .../keywords/keyword_dictionary_v1.1.csv`. The bundled dictionary and the locked protocol spec now ship inside the package at `prisma_s/data/` and are resolved with `importlib.resources`.
- Console output is forced to UTF-8 at CLI start-up, fixing `'charmap' codec can't encode character` on legacy Windows code pages (the `->` in the run summary, the wizard's rule characters) and making accented keyword dictionaries (Portuguese, Spanish) safe to print.
- `git clone` on Windows no longer fails with "Filename too long": paths under `desktop_runner/` and `protocols/` were shortened (longest 161 -> 106 chars) and the redundant 11 MB `archive_zips/` was removed.

### Added
- `install.ps1` / `install.sh` - locate a usable Python (skipping broken embedded interpreters), build a virtual environment at a short stable path, and install the package.
- `INSTALL.md` with install and troubleshooting guidance; `.gitattributes` pinning shell-script line endings.

### Changed
- Package version unified at 1.3.0 and sourced from `prisma_s.__version__` via `[tool.setuptools.dynamic]` (was `pyproject` 1.1.0 vs package 1.2.0).
- `README.md` now leads with the installable package; the Supply Chain Data Review Protocol / Desktop Runner material moved to a separate section.

---

## [1.2.0] — 2026-03-17

### Added
- `prisma-s wizard` — interactive CLI that prompts for search terms, source
  location (Drive URL or local path), batch ID, and output folder before running
- `prisma_s/wizard.py` — full wizard implementation with step-by-step prompts;
  supports manual term entry, bundled dictionary, or custom CSV
- `prisma_s/compliance.py` — full PRISMA-S 16-item checklist (Rethlefsen et al.
  2021; https://doi.org/10.1186/s13643-020-01542-z) with per-item status
  (APPLIED / PARTIAL / NOT_APPLICABLE / NOT_APPLIED) and runtime-injected notes
- Second Excel sheet `PRISMA-S_Compliance` written to every output workbook —
  documents which PRISMA-S search reporting items were addressed and which were not
- `drive.parse_folder_id()` — accepts full Drive folder URLs
  (`https://drive.google.com/drive/folders/...`) in addition to bare folder IDs,
  in both `prisma-s wizard` and `prisma-s run --drive-folder`
- Comprehensive package-level docstring in `prisma_s/__init__.py` referencing
  the PRISMA-S statement and linking to all submodules

### Changed
- Package version bumped to 1.2.0
- `prisma-s run --drive-folder` now accepts full Drive URLs as well as folder IDs
- README updated with `prisma-s wizard` as the recommended entry point

---

## [1.1.0] — 2026-03-17

### Added
- `prisma_s` installable Python package with CLI (`prisma-s run`)
- Google Drive integration — download PDFs and DOCX files from a Drive folder by folder ID
- DOCX support via `python-docx` (previously PDF-only)
- Keyword dictionary loaded from versioned CSV (`keywords/keyword_dictionary_v1.1.csv`) — no longer hardcoded
- Reproducibility columns in every output row: `Protocol Version`, `Keyword Dict Version`, `Run UTC`, `Source Ref`
- `Group` column in output (AOI / Commodity / Supply Chain Node)
- `pyproject.toml` for pip-installable packaging
- Test suite (`tests/test_search.py`) encoding all PRISMA-S protocol matching rules
- Comprehensive README with Google Drive setup guide and replication instructions

### Changed
- Output columns extended: `Group` added; reproducibility metadata columns added
- Package now reads keyword dictionary from CSV rather than a hardcoded list

### Retained
- `scripts/keyword_corpus_analysis.py` — original standalone script kept for reference

---

## [1.0.0] — 2026-03-16

### Added
- Initial standalone script `keyword_corpus_analysis.py`
- Hardcoded 120-term keyword list across AOI, Commodity, and Supply Chain Node groups
- PDF text extraction via PyMuPDF with PyPDF2 fallback
- Batch processing from local directory, single file, or ZIP archive
- Long-format Excel output: Batch, Document Name, Title, Year, Term, Count
- Title and year metadata extraction from PDF metadata and first-page text
- PRISMA-S Keyword Protocol v1.1 specification document
- Keyword dictionary CSV `keyword_dictionary_v1.1.csv`
