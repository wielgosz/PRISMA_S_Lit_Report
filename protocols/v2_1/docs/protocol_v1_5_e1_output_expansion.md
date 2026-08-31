# Table E1 output expansion v1.5

Table E1 is a standard appendix-style protocol output built from a highlighted subset of Table C1.

## Required links

- Table C1 must retain the columns `DCF Relevance` and `Appendix E cross reference`.
- Table E1 rows map back to C1 by Appendix E cross-reference, preferred access URL, APA citation, and dataset name.
- Table E1 may group rows for presentation, but the sidecar crosswalk must preserve all underlying C1 evidence rows.

## E-8 rule

E-8 is an alert-services sub-group in Table E1. The three underlying C1 records remain distinct:

- GLAD Alerts
- Integrated alerts
- RADD Alerts

Do not rename the C1 evidence rows to a single aggregate dataset name.

## New context columns

- `Corpus context / use summary`: paragraph text derived from corpus PDFs linked to the C1/E1 crosswalk.
- `External / non-corpus context summary`: paragraph text derived from the preferred access URL and official/provider web-source checks.

The context pass must be rerun only after the corpus is validated.
