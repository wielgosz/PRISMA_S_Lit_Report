#!/usr/bin/env python3
"""
11_run_v14_stageD_summary_v20.py
================================

Stage 11 of the Supply Chain Data Review Protocol v2.0.

Purpose
-------
Summarize Stage C dataset-document crosswalk outputs into report-ready dataset
summary tables. These outputs feed Table C1 validation, Table E1 subset context,
and the final output package.
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(description="11 - v1.4 Stage D dataset summaries.")
    ap.add_argument("--stageC", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    script = Path(__file__).with_name("run_v14_stageD_summary.py")
    cmd = [sys.executable, str(script), "--stageC", args.stageC, "--out", args.out]
    print("11 executing:", " ".join(cmd))
    return subprocess.call(cmd)
if __name__ == "__main__": raise SystemExit(main())
