# Desktop runner design

The v2.2 desktop runner is intentionally thin. The GUI collects file paths,
validates the Excel input workbook, prepares a runtime copy of the v2.1
protocol backend, injects user-edited dictionary/A1/B1 metadata, and invokes
the backend workflow.

## Source of truth

The Excel input workbook is the editable source of truth. The runner never
overwrites it. A validated copy is written into the run output folder.

## Runtime metadata injection

The runner creates a runtime copy of the v1.3 baseline workbook where:

- `A1_Org_Links_Snapshot` is replaced by `A1_Organizations`
- `B1_Corpus_Metadata_Snapshot` is replaced by `B1_Corpus_Documents`
- `Vetted_Corpus_Metadata` is replaced by `B1_Corpus_Documents`

Baseline `Text_Extraction_QA` and `Document_Term_Matrix` remain intact for
reproducibility comparison.

## Runtime dictionary injection

The `Dictionary` tab is exported to `config/keyword_dictionary_v1_3.csv` in
the runtime protocol copy. This ensures user dictionary edits drive the run
while preserving the v1.3 exact-boundary matching rule.
