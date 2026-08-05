# PRISMA-S Lit Review — Project Context

## What this project is

A transparent, reproducible Python package (`prisma_s`, published as `prisma-s-lit-review`) for
PRISMA-S-aligned keyword corpus analysis of PDF/DOCX literature — originally built for a
Deforestation and Conversion Free (DCF) supply chain traceability literature review, but designed
so any researcher can point it at their own Google Drive folder or local directory and get
identical, auditable results.

Published at: `https://github.com/wielgosz/PRISMA_S_Lit_Report`

## What it does

- Downloads PDFs/DOCX from a Google Drive folder (or reads a local path)
- Extracts full text, counts occurrences of every term in a versioned keyword dictionary
- Writes a long-format Excel matrix (one row per document × term) plus a PRISMA-S compliance sheet
- Every output row is stamped with protocol version, keyword-dict version, run timestamp, and
  source ref — so a run can be independently replicated

## Key method decisions (already made — don't re-litigate without reason)

- Protocol aligned to PRISMA 2020 / PRISMA-S (Rethlefsen et al. 2021)
- OCR-text PDFs only; case-insensitive, exact word-boundary matching; no stemming/lemmatization
- Zero-count rows included for every document × term combination
- Canonical output is long-format; Production Protocol v1.1 is **locked** — never edit a released
  protocol or keyword-dict version, only append a new version
- Batch processing for scalability; large PDFs may be chunked by page

## Repository structure

See `README.md` "Repository structure" section for the full package layout
(`prisma_s/` installable package with `keywords.py`, `extract.py`, `search.py`, `drive.py`,
`compliance.py`, `wizard.py`, `runner.py`, `cli.py`).

Additional context docs:
- `docs/CLAUDE_PROJECT_CONTEXT.md` — short task-oriented context stub
- `docs/project_context_summary.md` — project goal / method-decision summary
- `CHANGELOG.md` — full version history (currently v1.2.0)
- `protocol/PRISMA_keyword_protocol_v1.1.md` — locked protocol spec

## Working conventions

- Run tests: `pytest tests/ -v`
- Interactive entry point: `prisma-s wizard`
- Never modify a previously used keyword dictionary version — copy to a new
  `keyword_dictionary_v{MAJOR}.{MINOR}.csv` instead
- Keep `credentials.json` / `token.json` (Google Drive OAuth) out of version control

## Related projects

This is project 1 of a three-part DCF supply-chain analysis suite:
1. **PRISMA-S Lit Review** (this repo) — literature/keyword corpus analysis
2. [`Commodity-Monitoring-Catalogues`](https://github.com/wielgosz/Commodity-Monitoring-Catalogues) — STAC geospatial data catalogue of DCF-relevant datasets
3. **DCF-GHG-Emissions-Analysis** — DCF and GHG emissions analysis package, built on top of (2)
