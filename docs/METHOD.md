# Method — how the counts are produced

This pairs each protocol rule with the code that implements it. There are two
dictionary shapes and two matching modes:

- **Registry (v1.3, default)** — `prisma_s/data/keyword_dictionary_v1.3.csv` +
  `PRISMA_keyword_protocol_v1.3.md`. Variants roll up to canonical terms; text
  is normalised; matching is strict. This is the workflow behind the published
  guidebook's Table D-1 and Figures 1–3.
- **Flat (v1.1)** — `--keywords bundled:1.1`, `PRISMA_keyword_protocol_v1.1.md`.
  Every dictionary row is an independent term; lenient whitespace matching;
  byte-identical to v1.4.

## v1.3 canonicalization registry (default)

| Rule | Implementation |
|---|---|
| Dictionary schema | `category, canonical_term, search_variant` (+ optional `term_id`, `active`, `include_in_visuals`). `prisma_s/keywords.py::load_keywords` auto-detects it (`_looks_like_registry`) and drops rows where `active != yes`. |
| Text normalisation | `prisma_s/normalize.py::normalize_text` — NFC, CRLF/CR → LF, trailing whitespace stripped per line. **No** de-hyphenation, **no** internal-whitespace collapse. Mirrors the published `freeze_extract_text_corpus.py`. Applied per document in registry mode only. |
| Variant matching | `build_regex(variant, strict=True)` — `(?<![A-Za-z0-9])` + `re.escape(variant)` + `(?![A-Za-z0-9])`, IGNORECASE. Multi-word variants need a **single literal space** between words. |
| Roll-up | `count_registry` — a document's count for a `canonical_term` is the **sum** of its `search_variant` counts (overlapping variants sum, as in the paper). Per-variant counts are kept in the `Variant Counts` column. |
| Ranking | By **document frequency** (`number of reports referencing term`), then total occurrences. `prisma_s/runner.py::_build_d1`. |
| `D1_Key_Terms` | `Term_Summary` filtered to `include_in_visuals == yes` **and** at least one referencing document, ranked within category. Category order matches the guidebook: Jurisdictional, Supply chain, Farm level, AOI. |
| Figures 1–3 | `prisma_s/figures.py` — one horizontal bar chart per canonical category (jurisdictional/landscape, supply chain node, farm level), amber `#F0B310`, shared x-scale, legacy `DCF_PRISMA_S_Figure_{1,2,3}_*` filenames, SVG + PNG. |

Byte-exact reproduction of the guidebook also depends on the same corpus and the
PyMuPDF backend (`pip install "prisma-s-lit-review[fast-pdf]"`).

## Pipeline (both modes)

| Stage | Module | Entry point |
|---|---|---|
| Discover documents (folder / file / `.zip` / Drive) | `prisma_s/runner.py` | `_collect_local_files`, `prisma_s/drive.py:download_folder` |
| Extract text | `prisma_s/extract.py` | `extract_text` → `ExtractResult` |
| Build the index | `prisma_s/search.py` | `build_term_index` (flat) / `build_registry_index` (registry) |
| Count per document | `prisma_s/search.py` | `count_terms` (flat) / `count_registry` (registry) |
| Assemble + write workbook | `prisma_s/runner.py` | `run_analysis` |
| Compliance checklist | `prisma_s/compliance.py` | `build_compliance_report` |

## Flat (v1.1) matching rules

| Protocol rule | Implementation | Notes |
|---|---|---|
| Case-insensitive | `re.IGNORECASE` in `build_regex` (`search.py`) | |
| Exact boundaries, no partial-substring matches | `(?<![A-Za-z0-9])` … `(?![A-Za-z0-9])` in `build_regex` | **Alphanumeric** boundaries, not `\b`. `\b` treats `_` as a word character and never matches a term that starts or ends with punctuation (`(CO2)`, `+ve`). The boundary is applied to an edge only when that edge character is itself alphanumeric, so punctuation-flanked terms match correctly. This mirrors the desktop protocol's rule (`protocols/v2_1/scripts/run_v13_keyword_counts_frozen.py`). |
| Multi-word phrases, whitespace-flexible | words joined with `_WORD_SEP` in `build_regex` | The separator also absorbs a **hyphenated line break** between two words of a phrase (`"supply-\nshed"` matches `"supply shed"`), a common PDF-extraction artifact. A hyphenated line break *inside a single token* (`"Poly-\ngon"` for `Polygon`) is **not** handled here — that is frozen-text normalisation territory and is out of scope for v1.4. |
| No stemming / lemmatization | none — literal `re.escape` of each term | |
| Every document × term reported, zero counts included | `count_terms` returns one dict per `(group, term)` | |
| A term listed under two groups | `build_term_index` keys by `(group, term)` | The term is counted **once per group**, not silently collapsed to one. |
| Counting | `sum(1 for _ in rgx.finditer(text))` | Non-overlapping matches, per Python `re`. |

## Year and title

`guess_year` (`extract.py`) takes the **first-page text year first**, document
metadata (`/CreationDate`, `/ModDate`) only as a fallback, and returns `None`
when nothing plausible is found (the `Year` column is nullable `Int64`).
Metadata dates are unreliable because reference managers re-stamp `/ModDate` on
save. This order follows the protocol spec.

`guess_title` prefers a non-sentinel `/Title`, else the first line of the first
page longer than 12 characters, else `"Unknown"`.

## Extraction — per-document escalation chain

Heavy processing is spent only on the documents that need it
(`prisma_s/extract.py::extract_pdf`):

1. **Primary PDF library** — PyMuPDF if the `fast-pdf` extra is installed,
   otherwise pypdf.
2. **Other PDF library** — tried when rung 1 returns no text, or fewer than
   `THIN_WORDS_PER_PAGE` (default 40) words per page on a document of ≥ 2 pages.
   The result with the most words is kept. (Real example: a 62-page standard
   that pypdf read as 783 words came back as ~11,000 with PyMuPDF.)
3. **OCR** — PyMuPDF's `get_textpage_ocr` (Tesseract), tried **only** when a
   document is still textless after the PDF libraries, and only if `tesseract`
   is on `PATH`. `enable_ocr=False` / `--no-ocr` skips it; `--ocr-lang`
   (default `eng`, e.g. `eng+por`) sets the Tesseract language.

Which rung won, whether the chain escalated, and the trace
(`"pypdf 783w -> pymupdf 11040w"`) are recorded per document in `Run_Metadata`
(`Backend`, `Escalated`, `Status`) and summarised in `run_metadata.json`
(`backend_counts`, `escalated_documents`, `textless_documents`). A document with
no text layer under any rung is reported `ok: no text extracted` — it needs an
OCR'd source file. A missing PyMuPDF is a one-time notice, never a silent
per-file downgrade.

## Large documents — no page chunking

The whole document text is extracted and scanned as one string. The v1.1
protocol spec is *locked* and still contains a permissive "may be performed in
fixed page chunks" sentence (`Large-Document Rule`); that option is
**deliberately not implemented**, so counts never depend on a chunk boundary.
The practical ceiling is memory and the `.xlsx` row limit (`1,048,576`), which
`run_analysis` checks before writing. A future protocol version should drop the
sentence.

## Failure handling

A document that cannot be parsed is recorded in `Run_Metadata` with
`Status = "skipped: <reason>"` and excluded from `documents_processed`; the
compliance sheet reports the processed count, not the discovered count. A `.zip`
corpus is extracted to a temporary directory that is always removed, and
`__MACOSX/` / `._*` AppleDouble entries are ignored.
