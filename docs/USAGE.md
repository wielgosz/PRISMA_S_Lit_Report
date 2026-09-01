# Using prisma-s

## Install

See [`INSTALL.md`](../INSTALL.md). In short, from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1   # Windows
```
```bash
./install.sh                                            # macOS / Linux
```

For higher-fidelity PDF extraction (optional, adds the AGPL-licensed PyMuPDF):

```bash
pip install "prisma-s-lit-review[fast-pdf]"
```

## Guided run

```
prisma-s wizard
```

Four prompts — search terms, source location, batch ID, output folder — then a
confirmation. Every prompt has a default; press Enter to accept it. On a machine
with no console (a double-clicked shortcut) or piped input the wizard exits
cleanly with a message rather than a traceback.

## Scripted run

```
prisma-s run --batch BATCH --output OUT.xlsx [--input PATH | --drive-folder ID_OR_URL ...]
```

| Flag | Meaning |
|---|---|
| `--batch` | Label written into every output row. |
| `--output` | Destination `.xlsx`. `run_metadata.json` and `HOW_TO_CITE.txt` are written beside it. |
| `--input` | A local `.pdf` / `.docx` file, a folder (searched recursively), or a `.zip`. |
| `--drive-folder` | A Google Drive folder ID **or** a full folder URL. Needs `--drive-credentials`. |
| `--drive-credentials` | Path to `credentials.json` from Google Cloud Console. |
| `--drive-token` | Where to cache the OAuth token (default `token.json`, written `0600`). |
| `--keywords` | A keyword dictionary CSV. Columns: `group` (or `category`) and `term`, any case or order. Excel "CSV UTF-8" files (with BOM) are accepted. Omit to use the bundled dictionary. |
| `--no-citation` | Do not print the "How to cite" block when the run finishes. |
| `--no-ocr` | Skip the OCR rung. By default a PDF still textless after pypdf/PyMuPDF is OCR'd — but only if `tesseract` is on `PATH`. |
| `--ocr-lang` | Tesseract language code(s) for OCR, e.g. `eng` or `eng+por` (default `eng`). |

**PDF extraction is a per-document chain** (see [METHOD.md](METHOD.md)): a light
library first, the other library only for documents that come back thin, and OCR
only for documents with no text layer at all. For the OCR rung, install PyMuPDF
and a system Tesseract:

```bash
pip install "prisma-s-lit-review[ocr]"     # PyMuPDF
# then install Tesseract:  https://tesseract-ocr.github.io/tessdoc/Installation.html
```

A CSV that has no `term` column, or that yields zero terms, is a hard error —
the run does not proceed to write an empty workbook.

## Output

Written to the folder containing `--output`:

| File / sheet | Contents |
|---|---|
| `*_results.xlsx` → `Long_AllTerms` | One row per document × (group, term): `Count`, plus `Batch`, `Title`, `Year`, protocol / dictionary version, run timestamp, source. |
| `*_results.xlsx` → `PRISMA-S_Compliance` | The 16-item PRISMA-S checklist with per-item status and runtime notes. |
| `*_results.xlsx` → `Run_Metadata` | One row per document: extraction backend, pages, words, characters, status. |
| `run_metadata.json` | The same run + per-document facts, machine-readable. |
| `HOW_TO_CITE.txt` | The trilingual citation block. |

## Citation

```
prisma-s cite               # English + Português (Brasil) + Español
prisma-s cite --lang pt-br
```

The citation is also printed at the end of every run unless `--no-citation` is
given. See the "How to cite" section of the [README](../README.md).

## Reproducibility check

Run the same corpus twice and compare:

```
prisma-s run --batch chk --input CORPUS --output out/a/r.xlsx
prisma-s run --batch chk --input CORPUS --output out/b/r.xlsx
```

`Long_AllTerms` and `Run_Metadata` should be identical bar the timestamp; every
document in `Run_Metadata` should show `pages > 0` and `words > 0`, or an
explicit `skipped:` status.
