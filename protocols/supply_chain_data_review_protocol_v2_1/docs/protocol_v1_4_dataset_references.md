# Protocol v1.4: PRISMA-S Dataset Reference Extraction and Crosswalk

## Purpose

Protocol v1.4 identifies geospatial datasets, registries, platforms, and data sources referenced in the vetted PRISMA-S corpus. It preserves raw nomenclature while mapping observed names to canonical dataset/source records with web-verified names, URLs, and APA-style references.

## Stage A - Raw dataset-reference extraction

Scan body text, appendices, methods, footnotes, tables, references, and guidance sections for candidate dataset mentions. Preserve original wording, context snippets, page/section hints, and trigger terms.

Output: `Dataset_Mentions_Raw`.

## Stage B - Canonical registry and name crosswalk

Deduplicate and harmonize raw candidate strings against a canonical dataset/source registry. Official web-facing sources are preferred for canonical names, access URLs, and APA references. Generic cues such as "dataset" or "satellite imagery" are preserved as raw evidence but not treated as canonical datasets unless context resolves a specific source.

Outputs: `Dataset_Canonical_Registry`, `Dataset_Name_Crosswalk`, `Dataset_Mentions_StageB_Mapped`, `Dataset_QA_Review_Queue`.

## Stage C - Dataset-document crosswalk

Build crosswalk tables listing datasets referenced in each corpus document and documents referencing each dataset.

Outputs: `Dataset_by_Document`, `Document_by_Dataset`, `Documents_by_Dataset`, `Dataset_Document_Evidence`.

## Stage D - Summary ranking and visuals

Rank canonical datasets/sources by number of corpus documents referencing them. Generate report-ready tables and SVG graphics formatted consistently with v1.3 visuals.

Outputs: `Dataset_Summary_Ranking`, provider/type summaries, and SVG visuals.

## Core rule

Never overwrite raw observed names. Use the chain:

`raw observed name` -> `normalized candidate string` -> `canonical dataset/source ID` -> `preferred dataset/source name` -> `APA reference`.

