#!/usr/bin/env python3
"""
07_normalize_c1_registry_v20.py
===============================

Stage 7 of the Supply Chain Data Review Protocol v2.0.

Purpose
-------
Normalize Table C1 into a canonical dataset registry before running v1.4 dataset
mention extraction/crosswalk. This is where curated Table C1 names, URLs, APA
references, DCF relevance and Appendix E cross references become the registry
against which corpus mentions are reconciled.

Key v2.0 logic
--------------
- C1 is canonical for known datasets.
- E1 is not independently maintained; it is a subset/output view generated from
  C1 via Appendix E cross reference and DCF Relevance.
- E-8 is a grouped output only: GLAD Alerts, Integrated alerts, and RADD Alerts
  remain distinct C1 evidence rows.
- New dataset mentions discovered in Stage A-D must be flagged for review rather
  than silently inserted into C1.

Inputs
------
- A workbook/template containing Table C1, or a CSV registry.
- Optional v1.5/v2.0 correction CSVs.

Outputs
-------
- dataset_canonical_registry_v2_0.csv
- c1_normalization_log_v2_0.csv
- e1_subset_from_c1_v2_0.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List
import pandas as pd


def read_c1(source: Path, sheet_name: str) -> pd.DataFrame:
    if source.suffix.lower() in [".xlsx", ".xlsm", ".xls"]:
        return pd.read_excel(source, sheet_name=sheet_name).fillna("")
    return pd.read_csv(source).fillna("")


def canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map common Table C1 column headings to registry field names."""
    lookup = {c.lower().strip(): c for c in df.columns}
    mapping = {
        "dataset_id": ["dataset_id", "data_id", "id"],
        "preferred_dataset_name": ["preferred_dataset_name", "dataset name", "dataset_name", "data source", "name"],
        "preferred_access_url": ["preferred_access_url", "access url", "url", "preferred url"],
        "apa_reference": ["apa_reference", "apa reference", "reference"],
        "provider": ["provider", "organization", "publisher", "source organization"],
        "dcf_relevance": ["dcf relevance", "dcf_relevance"],
        "appendix_e_cross_reference": ["appendix e cross reference", "appendix_e_cross_reference", "appendix e", "e1 cross reference"],
    }
    out = pd.DataFrame()
    for new_col, candidates in mapping.items():
        found = None
        for cand in candidates:
            if cand in lookup:
                found = lookup[cand]; break
        out[new_col] = df[found] if found else ""
    # Preserve original columns for traceability.
    for c in df.columns:
        out[f"source__{c}"] = df[c]
    return out


def apply_v2_rules(reg: pd.DataFrame) -> pd.DataFrame:
    # Normalize the known E-8 alert-service subgroup while preserving distinct rows.
    if "appendix_e_cross_reference" in reg.columns and "preferred_dataset_name" in reg.columns:
        e8 = reg["appendix_e_cross_reference"].astype(str).str.strip().eq("E-8")
        reg.loc[e8, "e1_group_name"] = "RADD, GLAD and Integrated Deforestation Alerts"
        reg.loc[e8, "e1_grouping_note"] = "Grouped in E1 for presentation only; C1 evidence rows remain distinct."
    if "e1_group_name" not in reg.columns:
        reg["e1_group_name"] = ""
    if "e1_grouping_note" not in reg.columns:
        reg["e1_grouping_note"] = ""
    return reg


def main() -> int:
    ap = argparse.ArgumentParser(description="07 - Normalize C1 into canonical dataset registry and E1 subset.")
    ap.add_argument("--c1-source", required=True, help="Workbook or CSV containing Table C1.")
    ap.add_argument("--sheet", default="Table C1")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    raw = read_c1(Path(args.c1_source), args.sheet)
    reg = apply_v2_rules(canonicalize_columns(raw))
    if "dataset_id" in reg.columns:
        reg["dataset_id"] = reg["dataset_id"].replace("", pd.NA)
        generated = [f"C1-{i+1:03d}" for i in range(len(reg))]
        reg["dataset_id"] = [v if pd.notna(v) and str(v).strip() else generated[i] for i, v in enumerate(reg["dataset_id"].tolist())]
    e1 = reg[reg["appendix_e_cross_reference"].astype(str).str.strip().ne("")].copy()
    log = pd.DataFrame([
        {"step": "normalize_c1", "rows_in": len(raw), "rows_out": len(reg), "e1_rows": len(e1), "note": "C1 normalized; E1 subset generated from Appendix E cross reference."}
    ])
    reg.to_csv(out / "dataset_canonical_registry_v2_0.csv", index=False)
    e1.to_csv(out / "e1_subset_from_c1_v2_0.csv", index=False)
    log.to_csv(out / "c1_normalization_log_v2_0.csv", index=False)
    print(f"07 complete: registry rows={len(reg)}, E1 rows={len(e1)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
