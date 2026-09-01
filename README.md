# PRISMA-S Lit Review

A transparent, reproducible Python package (`prisma_s`, distributed as
`prisma-s-lit-review`) for **PRISMA-S-aligned keyword corpus analysis** of
PDF/DOCX literature. Point it at a local folder or a Google Drive folder and get
an auditable, long-format Excel matrix of term counts plus a PRISMA-S compliance
sheet. Every output row is stamped with the protocol version, keyword-dictionary
version, run timestamp, and source reference so a run can be replicated exactly.

Aligned to PRISMA 2020 / PRISMA-S (Rethlefsen et al. 2021,
<https://doi.org/10.1186/s13643-020-01542-z>).

## Install

Python 3.9+ required. From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1   # Windows
```

```bash
./install.sh                                            # macOS / Linux
```

This creates a private virtual environment and installs the `prisma-s` command.
Manual install and troubleshooting (including the Windows *"Filename too long"*
clone error and broken-Python venv failures) are covered in [INSTALL.md](INSTALL.md).

## Use

Guided, interactive:

```
prisma-s wizard
```

Non-interactive:

```
# Default: the bundled v1.3 canonicalization registry (98 canonical terms)
prisma-s run --batch batch_01 --input /path/to/docs --output results/batch_01.xlsx

# The flat v1.1 dictionary instead (v1.4 behaviour)
prisma-s run --batch batch_01 --input /path/to/docs --output results/batch_01.xlsx \
    --keywords bundled:1.1

# A custom dictionary (flat CSV, or a registry CSV with canonical_term/search_variant)
prisma-s run --batch batch_01 --input /path/to/docs --output results/batch_01.xlsx \
    --keywords /path/to/my_dictionary.csv

# Google Drive folder (URL or bare ID); needs credentials.json
prisma-s run --batch batch_01 --output results/batch_01.xlsx \
    --drive-folder "https://drive.google.com/drive/folders/1Abc123XYZ" \
    --drive-credentials credentials.json
```

The default dictionary is the **v1.3 canonicalization registry** bundled at
`prisma_s/data/keyword_dictionary_v1.3.csv`: many explicit `search_variant`s roll
up to one `canonical_term`, counts are summed per canonical term, and results are
ranked by document frequency — the method behind the published guidebook's
Table D-1 and Figures 1–3. `--keywords bundled:1.1` restores the flat v1.1 list.
Excel "CSV UTF-8" files and headers in any case/order are accepted; a CSV with no
usable key column, or zero rows, is a hard error, not a silently empty run.

Written beside `--output`:

- `*_results.xlsx` — **registry mode**: `Long_AllTerms` (document × canonical
  term, with per-variant breakdown), `Term_Summary`, `D1_Key_Terms` (report-ready,
  ranked), `Zero_Reference_Terms`, `PRISMA-S_Compliance`, `Run_Metadata`.
  **Flat mode**: `Long_AllTerms`, `PRISMA-S_Compliance`, `Run_Metadata`.
- `figures/` — term-frequency bar charts (SVG + PNG); the three
  `DCF_PRISMA_S_Figure_{1,2,3}_*` when the canonical categories are present.
  `--no-figures` to skip.
- `run_metadata.json`, `HOW_TO_CITE.txt`.

**PDF extraction is a per-document escalation chain** — a light library first,
the other PDF library only for documents that come back thin, and OCR
(Tesseract, opt-in via `[ocr]`) only for documents with no text layer at all.
Install PyMuPDF for better/faster extraction: `pip install
"prisma-s-lit-review[fast-pdf]"` (AGPL-3.0; the default pypdf-only install stays
MIT-clean). See [docs/METHOD.md](docs/METHOD.md).

## Package layout

```text
prisma_s/
  keywords.py     keyword-dictionary loader (bundled dict in data/)
  extract.py      PDF (pypdf; optional PyMuPDF) and DOCX text extraction
  search.py       case-insensitive, alphanumeric-boundary regex matching engine
  drive.py        Google Drive folder ingestion
  compliance.py   PRISMA-S 16-item compliance report builder
  citation.py     "How to cite" text (English / Português / Español)
  runner.py       run_analysis() orchestrator
  wizard.py       interactive CLI setup wizard
  cli.py          argparse entry point (the prisma-s command)
  data/           bundled keyword dictionary, locked protocol spec, citation text
```

- Usage reference: [docs/USAGE.md](docs/USAGE.md)
- Method — each protocol rule paired with the code that implements it:
  [docs/METHOD.md](docs/METHOD.md)
- Version history: [CHANGELOG.md](CHANGELOG.md)

## License

The **source code** is released under the [MIT License](LICENSE). The **keyword
dictionary, protocol specification, generated figures, and documentation** are
released under [Creative Commons Attribution 4.0](LICENSE-CC-BY-4.0.txt)
(see [prisma_s/data/DATA_LICENSE.md](prisma_s/data/DATA_LICENSE.md)) — reuse and
adaptation are welcome **provided you cite the original tool and publication**.

## How to cite / Como citar / Cómo citar

Run `prisma-s cite` for this text in all three languages; it is also printed
when a run finishes and written to `HOW_TO_CITE.txt`.

**The tool** — Wielgosz, B. (2026). *PRISMA-S Lit Review* (Version 1.4)
[Computer software]. https://github.com/wielgosz/PRISMA_S_Lit_Report

**The associated publication** — Wielgosz, B., dos Santos, A. B., Carter, S.,
Berger, A., Schneider, M., Despontin, M., Immelman, J., Richter, J., Couto, A.,
Fitts, L. A., Gao, Y., & Dionizio, E. (in press). *Data for deforestation- and
conversion-free (DCF) supply chain analyses: Applied learnings from soy in
Brazil (Guidebook).* World Resources Institute.
*(Final citation and DOI to be added on publication.)*

Author: https://www.linkedin.com/in/benjamin-wielgosz/

> Portuguese and Spanish translations are provided (`prisma-s cite --lang pt-br`
> / `es`); native-speaker review is welcome. The bibliographic references are
> kept in canonical English in every language.

---

## Supply Chain Data Review Protocol v2.1 / Desktop Runner v2.2-alpha

The `protocols/v2_1/` and `desktop_runner/runner/` trees hold a separate
deliverable: the **Supply Chain Data Review Protocol v2.1** and a Tkinter +
PyInstaller Windows desktop runner that uses it as a backend engine. These are
not part of the `prisma_s` package and are not installed by `pip`.

Protocol v2.1 consolidates the May 2026 revisions to the Supply Chain Data
Review workflow: the v1.3 exact keyword-counting rule, the frozen extracted-text
workflow, the v1.4 dataset-reference crosswalk workflow, a v1.3-style tabular
reference workbook, canonical SVG figures keyed on `reports_referencing`, and APA
references for the RTRS and ECF corpus additions.

The desktop runner lives under `desktop_runner/runner/`; its editable input
workbook is `desktop_runner/runner/templates/Supply_Chain_Data_Review_Input_Template_v2_2.xlsx`
(sheets: `README`, `A1_Organizations`, `B1_Corpus_Documents`, `Dictionary`,
`Run_Settings`, `Exclusions_Duplicates`, `New_Documents`, `Validation_Log`). It
lets the user pick an input workbook, a folder of PDFs / batch ZIPs, and an
output folder, then validates the workbook and runs the protocol to produce a
date-stamped folder of Excel, SVG, CSV, QA, frozen-text, log, and manifest
outputs.

Build the Windows desktop runner on a machine with Python installed:

```bat
cd desktop_runner\runner
python -m pip install -r requirements.txt
build_windows.bat
```

The PyInstaller `onedir` folder is written to `dist\SupplyChainDataReviewRunner\`.
