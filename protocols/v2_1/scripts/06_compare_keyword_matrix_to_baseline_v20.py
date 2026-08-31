#!/usr/bin/env python3
"""
06_compare_keyword_matrix_to_baseline_v20.py
============================================

Stage 6 of the Supply Chain Data Review Protocol v2.0.

Purpose
-------
Compare the current v2.0/v1.5 frozen-text keyword matrix to the prior valid v1.3
baseline. Stable prior documents should reproduce exactly. New documents should
be flagged as new and not treated as differences.

Why this is separate from Stage 5
---------------------------------
Stage 5 creates outputs. Stage 6 verifies reproducibility. Keeping them separate
allows the user to inspect whether differences are due to corpus changes, text
extraction changes, dictionary changes, or new documents.
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(description="06 - Compare keyword matrix to v1.3 baseline.")
    ap.add_argument("--current", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--baseline-sheet", default="Document_Term_Matrix")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    script = Path(__file__).with_name("compare_keyword_matrix_to_baseline.py")
    cmd = [sys.executable, str(script), "--current", args.current, "--baseline", args.baseline, "--baseline-sheet", args.baseline_sheet, "--out-dir", args.out_dir]
    print("06 executing:", " ".join(cmd))
    return subprocess.call(cmd)
if __name__ == "__main__": raise SystemExit(main())
