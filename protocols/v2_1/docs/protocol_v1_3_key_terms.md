# Protocol v1.3: PRISMA-S Key Term Analysis

## Purpose

Protocol v1.3 quantifies how often predefined sectoral literature terms appear across a vetted corpus of guidance documents and how widely those terms are referenced across documents.

## Inputs

- Vetted corpus metadata CSV with `doc_id`, title, year, organization, file name, source URL, and protocol inclusion status.
- Extracted plain text per document.
- Dictionary CSV with `category`, `canonical_term`, and exact `search_variant` values.

## Matching rule

The default matching rule is exact, case-insensitive matching of each explicit `search_variant` listed in the dictionary. Automatic stemming, lemmatization, and fuzzy matching are excluded from the main count to maintain auditability.

## Variant handling

Multiple explicit variants may roll up to one `canonical_term`. Outputs may preserve variant-level counts while D1 uses canonical rolled-up term counts.

## Core outputs

- `D1_Key_Terms`: report-ready ranked table by category.
- `Zero_Reference_Terms`: dictionary terms not found in the counted corpus.
- `Term_Summary`: term-level count summary.
- `Document_Term_Counts`: document-by-term count table.
- `Document_Term_Matrix`: wide matrix for downstream analysis.
- `Text_Extraction_QA`: source coverage and extraction-status checks.
- Four SVG visual outputs using color `#F0B310` and shared x-scale.

## Ranking metric

Terms are ranked by number of corpus documents referencing the term. Total occurrence counts are secondary.

