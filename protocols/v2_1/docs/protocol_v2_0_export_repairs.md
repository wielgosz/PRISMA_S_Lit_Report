# Protocol v2.0 export repairs

This note documents the post-run repair to the v2.0 package export path.

## Problems observed

1. Some XLSX exports were not reliably openable in Excel.
2. SVG figure names drifted from the established DCF / PRISMA-S naming contract.
3. Users needed May 27-style keyword CSV compatibility aliases.

## Repairs applied

- Stage 12 now sanitizes workbook cell values before writing.
- The saved workbook is validated by reopening it with openpyxl.
- Legacy SVG names are emitted by default:
  - `DCF_PRISMA_S_Figure_1_jurisdictional_terms.svg`
  - `DCF_PRISMA_S_Figure_2_supply_chain_terms.svg`
  - `DCF_PRISMA_S_Figure_3_farm_level_terms.svg`
- Alias copies are also emitted for the original v2.0 internal names.
- Core keyword CSV outputs are copied into the final package and may receive
  May 27 compatibility alias filenames.


## Figure filename and scope refinement
Only one canonical SVG set is emitted. Figure 1 is limited to jurisdictional / landscape terms and excludes AOI terms. All three figures plot the number of reports referencing each term (`reports_referencing`).
