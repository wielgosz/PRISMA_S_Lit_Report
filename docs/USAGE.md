# Using prisma-s

## Install

See [`INSTALL.md`](../INSTALL.md). In short, from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1   # Windows
```
```bash
./install.sh                                            # macOS / Linux
```

## Input requirements

prisma-s reads a PDF's **existing text layer** with pypdf. It does **not** OCR.
Scanned or image-only PDFs must be OCR'd with an external tool first, e.g.:

```bash
ocrmypdf scanned.pdf ocr'd.pdf
```

Every document with no text, or with too little text for its page count, is
flagged in `Run_Metadata` (`Needs OCR`) and `run_metadata.json`
(`documents_needing_ocr`) so you know exactly which files to re-process.

## Guided run

```
prisma-s wizard
```

Four prompts — search terms, source location, batch ID, output folder — then a
confirmation. Every prompt has a default; press Enter to accept it. On a machine
with no console (a double-clicked shortcut) or piped input the wizard exits
cleanly with a message rather than a traceback.

## Desktop GUI

```
prisma-s-gui
```

A single window with the same options as `prisma-s run`: corpus source (local
folder, local file/zip, or a Google Drive folder), output folder, batch ID,
keyword dictionary (bundled v1.3 / bundled v1.1 / a custom CSV), and the
figures / citation toggles. The run happens on a background thread; its
log streams into the window, and **Open output folder** appears when it
finishes. This GUI is also the front-end of the standalone Windows executable
(see `desktop/README.md` and the project's GitHub Releases).

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
| `--keywords` | `bundled:1.3` (default; v1.3 canonicalization registry), `bundled:1.1` (flat v1.1 list), or a path to a CSV. A registry CSV has `canonical_term` + `search_variant` columns; a flat CSV has `group`/`category` + `term`. Excel "CSV UTF-8" and any header case/order accepted. |
| `--no-figures` | Skip the term-frequency figures. |
| `--no-citation` | Do not print the "How to cite" block when the run finishes. |

PDF text comes from the existing text layer via pypdf only (see
[METHOD.md](METHOD.md) and "Input requirements" above); OCR scans externally
first.

A CSV that has no `term` column, or that yields zero terms, is a hard error —
the run does not proceed to write an empty workbook.

## Output

Written to the folder containing `--output`:

| File / sheet | Contents |
|---|---|
| `*_results.xlsx` → `Long_AllTerms` | **Registry**: one row per document × canonical term — `Category`, `Term ID`, `Canonical Term`, `Variants Included`, `Variant Counts`, `Count`, `Referenced`. **Flat**: one row per document × (group, term). Both carry `Batch`, `Title`, `Year`, protocol / dictionary version, timestamp, source. |
| `*_results.xlsx` → `Term_Summary` *(registry)* | Per canonical term: reports referencing, total occurrences, percent of corpus documents. |
| `*_results.xlsx` → `D1_Key_Terms` *(registry)* | Report-ready ranked table: `include_in_visuals` canonical terms with ≥ 1 referencing document, ranked within category. Mirrors the guidebook's Table D-1. |
| `*_results.xlsx` → `Zero_Reference_Terms` *(registry)* | Canonical terms not found in the corpus. |
| `*_results.xlsx` → `PRISMA-S_Compliance` | The 16-item PRISMA-S checklist with per-item status and runtime notes. |
| `*_results.xlsx` → `Run_Metadata` | One row per document: extraction backend, pages, words, characters, `Needs OCR`, status. |
| `figures/` | Term-frequency bar charts, SVG + PNG. `DCF_PRISMA_S_Figure_{1,2,3}_*` (jurisdictional/landscape, supply chain node, farm level) when those categories are present, else one per category. |
| `run_metadata.json` | Run + per-document facts, machine-readable (`dictionary_mode`, `n_canonical_terms`, backends, figures, …). |
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
