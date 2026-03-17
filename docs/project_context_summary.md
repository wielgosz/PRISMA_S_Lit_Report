# Project Context Summary

## Project Goal
Build a reproducible corpus-analysis workflow for traceability-related OCR PDFs, then scale the workflow across multiple production batches and aggregate outputs into a single master dataset.

## Major Method Decisions
- Protocol aligned to PRISMA 2020 / PRISMA-S principles
- OCR-text PDFs only
- Exact case-insensitive keyword/phrase matching
- No stemming or lemmatization
- Include zero-count rows for all document × term combinations
- Canonical output uses long format
- Batch processing used for scalability
- Large PDFs may be processed in page chunks

## Production Protocol Lock
Production Protocol v1.1 was locked before running production batches.

## Completed Outputs
- Seven production batch matrices
- Master workbook for production batches 1–7
- Document summary workbook
- Publication-quality subgroup term-frequency SVG charts
