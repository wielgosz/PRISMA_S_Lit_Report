# Supply Chain Data Review Protocol v2.0: Numbered dependency sequence

This document is the human-readable map of the package. It mirrors the Python module numbering so the workflow can be relearned from an IDE.

## Governing principle

All outputs are downstream of a single reconciled corpus manifest and a frozen extracted-text corpus. The protocol does not allow keyword counting or dataset crosswalk generation directly from ad hoc PDF extraction.

## Sequence

### 1. Corpus Generation and Reconciliation

Module: `scripts/01_reconcile_corpus_v20.py`

Creates the authoritative corpus manifest from uploaded ZIP/PDF batches and historical corpus metadata. Applies duplicate, converted-source, new-addition and confidential/review rules.

### 2. Frozen extracted-text corpus

Module: `scripts/02_freeze_extract_text_corpus_v20.py`

Freezes PDF text into persistent artifacts with hashes, page counts and status flags.

### 3. Frozen corpus validation

Module: `scripts/03_validate_frozen_corpus_v20.py`

Compares frozen text to v1.3 Text_Extraction_QA baseline where available.

### 4. Preflight gate

Module: `scripts/04_preflight_protocol_gate_v20.py`

Blocks downstream execution when extraction, corpus, dictionary or parameterization prerequisites are not met.

### 5. v1.3 keyword protocol from frozen text

Module: `scripts/05_run_v13_keyword_counts_frozen_v20.py`

Runs the executable v1.3 dictionary using exact, case-insensitive regex matching with alphanumeric boundaries.

### 6. Matrix comparison to v1.3 baseline

Module: `scripts/06_compare_keyword_matrix_to_baseline_v20.py`

Compares the current Document_Term_Matrix to the prior valid v1.3 matrix.

### 7. C1 normalization and E1 subset generation

Module: `scripts/07_normalize_c1_registry_v20.py`

Turns curated C1 into a canonical dataset registry and derives E1 from Appendix E cross references.

### 8. v1.4 Stage A dataset mention extraction

Module: `scripts/08_run_v14_stageA_extract_dataset_mentions_v20.py`

Extracts raw dataset mention candidates from the frozen text corpus.

### 9. v1.4 Stage B canonicalization

Module: `scripts/09_run_v14_stageB_canonicalize_v20.py`

Maps raw mentions to the canonical C1 dataset registry and alias crosswalk.

### 10. v1.4 Stage C dataset-document crosswalk

Module: `scripts/10_run_v14_stageC_crosswalk_v20.py`

Builds the dataset-document evidence crosswalk.

### 11. v1.4 Stage D dataset summaries

Module: `scripts/11_run_v14_stageD_summary_v20.py`

Generates dataset summary/ranking outputs.

### 12. Final output package builder

Module: `scripts/12_build_v20_output_package.py`

Builds the Excel workbook, SVG figures, CSV outputs and run manifest.

## Wrapper call

Use `scripts/run_v20_full_protocol.py` to execute modules 1-12 in order.
