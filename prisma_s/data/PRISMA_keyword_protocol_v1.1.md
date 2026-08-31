# PRISMA-Aligned Keyword Corpus Review Protocol v1.1

## Overview
This protocol describes a PRISMA-aligned, reproducible full-text keyword review of OCR-enabled PDF documents.

## Corpus Assumptions
- Input files are OCR-text PDFs
- One PDF = one analytical document unit
- English-language documents unless otherwise specified

## Search / Matching Rules
- Case-insensitive matching
- Exact word matching for single-word terms
- Exact phrase matching for multi-word terms
- No stemming
- No lemmatization
- No partial substring matching
- All document × term combinations retained, including zero counts

## Metadata Extraction
Title priority:
1. PDF metadata title if meaningful
2. First-page heading / cover-page fallback
3. Unknown

Year priority:
1. First-page publication year if available
2. PDF metadata creation/modification year
3. Unknown

## Large-Document Rule
For very large PDFs, full-text extraction may be performed in fixed page chunks and counts aggregated across chunks.

## Canonical Output Format
- Batch
- Document Name
- Title
- Year
- Term
- Count
