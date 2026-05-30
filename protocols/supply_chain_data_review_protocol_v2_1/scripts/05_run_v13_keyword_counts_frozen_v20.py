#!/usr/bin/env python3
"""
05_run_v13_keyword_counts_frozen_v20.py
=======================================

Stage 5 of the Supply Chain Data Review Protocol v2.0.

Purpose
-------
Execute the authoritative v1.3 keyword-count protocol from frozen text.

Mandatory rule
--------------
Exact, case-insensitive regex matching with alphanumeric boundaries, with
aliases/variants rolled up to canonical terms. This is non-negotiable because
substring counting produces invalid inflated terms such as `gin` in `origin` or
`port` in `report`.

Outputs
-------
- Document_Term_Counts.csv
- Document_Term_Matrix.csv
- Term_Summary.csv
- Zero_Reference_Terms.csv
- D1_Key_Terms.csv
- keyword_run_manifest.json
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(description="05 - Run v1.3 keyword protocol from frozen text.")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dictionary", default="config/keyword_dictionary_v1_3.csv")
    ap.add_argument("--out", required=True)
    ap.add_argument("--params", default="config/protocol_v2_0_params.yml")
    ap.add_argument("--allow-warnings", action="store_true")
    args = ap.parse_args()
    script = Path(__file__).with_name("run_v13_keyword_counts_frozen.py")
    cmd = [sys.executable, str(script), "--manifest", args.manifest, "--dictionary", args.dictionary, "--out", args.out, "--params", args.params]
    if args.allow_warnings: cmd.append("--allow-warnings")
    print("05 executing:", " ".join(cmd))
    return subprocess.call(cmd)
if __name__ == "__main__": raise SystemExit(main())
