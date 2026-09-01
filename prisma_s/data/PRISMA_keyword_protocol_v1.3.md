# PRISMA-S Key Term Analysis — Protocol v1.3

Adapted from `protocols/v2_1/docs/protocol_v1_3_key_terms.md` (do not edit the
source). This is the version implemented by `prisma_s` in registry mode.

## Purpose

Quantify how often predefined sectoral literature terms appear across a corpus
of guidance documents, and how widely each term is referenced across documents.

## Inputs

- A corpus of PDF/DOCX documents.
- A dictionary CSV with `category`, `canonical_term`, and one or more exact
  `search_variant` values per canonical term (plus optional `term_id`,
  `active`, `include_in_visuals`).

## Text normalisation

Each document's extracted text is normalised before counting: NFC Unicode,
CRLF/CR → LF, trailing whitespace stripped per line. No de-hyphenation and no
internal-whitespace collapse.

## Matching rule

Exact, case-insensitive matching of each explicit `search_variant`, with
**alphanumeric boundaries** — `(?<![A-Za-z0-9]) … (?![A-Za-z0-9])` — so a term
is not matched inside a longer alphanumeric token and `_` is a boundary.
Multi-word variants match a **single literal space** between words. No stemming,
lemmatisation, or fuzzy matching.

## Variant roll-up

A document's count for a `canonical_term` is the **sum** of its
`search_variant` counts. Per-variant counts are preserved in the
`Variant Counts` column of `Long_AllTerms`.

## Ranking metric

Terms are ranked by **number of documents referencing the term**
(`reports_referencing`). Total occurrence count is the secondary sort key.

## Outputs

- `Long_AllTerms` — one row per (document × canonical term).
- `Term_Summary` — per canonical term: reports referencing, total occurrences,
  percent of corpus documents.
- `D1_Key_Terms` — report-ready ranked table: canonical terms with
  `include_in_visuals = yes` and at least one referencing document, ranked
  within category.
- `Zero_Reference_Terms` — dictionary terms not found in the corpus.
- `Run_Metadata`, `PRISMA-S_Compliance`.
- Three SVG+PNG figures (`#F0B310`, shared x-scale): jurisdictional/landscape,
  supply chain node, and farm level terms.
