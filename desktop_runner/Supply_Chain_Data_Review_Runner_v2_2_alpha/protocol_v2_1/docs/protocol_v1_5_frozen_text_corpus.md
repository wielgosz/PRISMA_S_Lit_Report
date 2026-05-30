# Protocol v1.5 frozen extracted-text corpus layer

This v1.5 update adds a blocking extraction and reproducibility layer before the v1.3 keyword-count protocol is run.

## Rationale

The v1.3 keyword protocol remains authoritative for term counting. However, keyword reproducibility depends on having identical document text. Therefore v1.5 separates the workflow into two stages:

1. **Corpus freeze:** extract all included PDFs to durable text artifacts and record hashes, page counts, character counts, and extraction status.
2. **Keyword execution:** run the v1.3 dictionary only against the frozen text artifacts.

The keyword script must not silently re-extract PDFs during counting.

## Blocking extraction statuses

A corpus cannot be committed if any included document has one of the following unresolved statuses:

- `EXTRACTION_TIMEOUT`
- `EXTRACTION_ERROR`
- `MISSING_PDF`
- `MISSING_TEXT_ARTIFACT`
- `EMPTY_TEXT`
- `TEXT_HASH_CHANGED_UNAPPROVED`
- `PAGE_COUNT_CHANGED_UNAPPROVED`

## Required v1.3 keyword matcher

All v1.5 keyword executions inherit the v1.3 rule:

> Exact, case-insensitive regex matching with alphanumeric boundaries, with aliases/variants rolled up to canonical terms.

The executable dictionary remains `config/keyword_dictionary_v1_3.csv`. Table D1 is report-facing and must not replace the full executable dictionary unless explicitly expanded and approved.

## Added scripts

- `scripts/freeze_extract_text_corpus.py`
- `scripts/validate_frozen_corpus.py`
- `scripts/preflight_protocol_gate.py`
- `scripts/run_v13_keyword_counts_frozen.py`
- `scripts/compare_keyword_matrix_to_baseline.py`

## Required parameters

Parameters are stored in:

- `config/frozen_text_protocol_params_v1_5.yml`

This file defines extraction timeouts, retry behavior, blocking QA statuses, char-count tolerance, expected active dictionary term count, and the required v1.3 matching rule.

## Recommended command sequence

```bash
python scripts/freeze_extract_text_corpus.py \
  --corpus examples/current_milestone/vetted_corpus_metadata_2026-05-13.csv \
  --pdf-root data/raw_pdfs \
  --out-root data/frozen_text/v1_5 \
  --params config/frozen_text_protocol_params_v1_5.yml

python scripts/validate_frozen_corpus.py \
  --manifest data/frozen_text/v1_5/frozen_text_manifest.csv \
  --baseline outputs/reference_milestone/prisma_s_v13_complete_results_QA_metadata_visuals_2026-05-13.xlsx \
  --baseline-sheet Text_Extraction_QA \
  --out outputs/v15_validation/frozen_text_qa_report.csv \
  --params config/frozen_text_protocol_params_v1_5.yml

python scripts/preflight_protocol_gate.py \
  --corpus examples/current_milestone/vetted_corpus_metadata_2026-05-13.csv \
  --manifest data/frozen_text/v1_5/frozen_text_manifest.csv \
  --dictionary config/keyword_dictionary_v1_3.csv \
  --qa-report outputs/v15_validation/frozen_text_qa_report.csv \
  --out outputs/v15_validation/preflight_gate_report.csv \
  --params config/frozen_text_protocol_params_v1_5.yml

python scripts/run_v13_keyword_counts_frozen.py \
  --manifest data/frozen_text/v1_5/frozen_text_manifest.csv \
  --dictionary config/keyword_dictionary_v1_3.csv \
  --out outputs/v15_keyword_test_from_frozen_text \
  --params config/frozen_text_protocol_params_v1_5.yml

python scripts/compare_keyword_matrix_to_baseline.py \
  --current outputs/v15_keyword_test_from_frozen_text/Document_Term_Matrix.csv \
  --baseline outputs/reference_milestone/prisma_s_v13_complete_results_QA_metadata_visuals_2026-05-13.xlsx \
  --baseline-sheet Document_Term_Matrix \
  --out-dir outputs/v15_validation/matrix_comparison
```
