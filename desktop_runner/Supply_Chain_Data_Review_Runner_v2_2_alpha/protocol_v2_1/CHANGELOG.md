# Changelog

## Supply Chain Data Review Protocol v2.0

- Renamed the integrated project package from PRISMA-S protocol v1.5 state/frozen-text layer to **Supply Chain Data Review Protocol v2.0**.
- Added numbered module sequence `01` through `12` to make dependencies explicit from a Python IDE.
- Added `run_v20_full_protocol.py` wrapper.
- Retained v1.3 as the authoritative keyword protocol.
- Retained v1.4 as the authoritative dataset mention/canonicalization/crosswalk protocol.
- Retained v1.5 frozen extracted-text QA layer.
- Added corpus reconciliation as Stage 1 before frozen text and analytical outputs.
- Added C1 normalization and E1 subset generation as Stage 7 before v1.4 dataset stages.
- Added final output package builder as Stage 12.
- Persisted rule that keyword counts must use exact, case-insensitive regex matching with alphanumeric boundaries.


## 2026-05-28 - Export repair update
- Repaired Stage 12 workbook export by sanitizing Excel cell values and validating saved workbooks.
- Restored legacy SVG figure filenames (DCF_PRISMA_S_Figure_1/2/3_...) and added alias copies for v2.0 filenames.
- Added default copying of keyword/dataset/QA CSV outputs into the final package.
- Added May 27 compatibility aliases for core keyword CSV outputs.


## 2026-05-28 - Figure contract update
- Removed duplicate SVG alias outputs; only canonical legacy SVG filenames are now emitted.
- Updated Figures 1-3 to plot `reports_referencing` (document frequency) rather than `total_occurrences`.
- Restricted Figure 1 to jurisdictional / landscape terms only; AOI terms are excluded.


## 2026-05-28 - Version 2.1 release
- Promoted the repaired/export-adjusted v2.x package to v2.1.
- Simplified the spreadsheet output style toward the v1.3 tabular workbook.
- Finalized the figure contract: only canonical SVG names, axes only, unnumbered titles, and `reports_referencing` metric.
- Updated Figure 1 scope to jurisdictional / landscape terms only, excluding AOI terms.
- Added APA citation metadata for the two newly uploaded corpus additions from RTRS and ECF.
