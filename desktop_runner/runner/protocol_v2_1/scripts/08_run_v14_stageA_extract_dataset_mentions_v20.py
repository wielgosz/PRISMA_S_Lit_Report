#!/usr/bin/env python3
"""
08_run_v14_stageA_extract_dataset_mentions_v20.py
=================================================

Stage 8 of the Supply Chain Data Review Protocol v2.0.

Purpose
-------
Run v1.4 Stage A on the frozen extracted-text corpus to identify raw dataset
mentions. Stage A should not decide canonical identity; it only extracts mention
candidates with context snippets and document links.

Dependency
----------
Uses the reconciled corpus manifest and frozen text created in Stages 1-3.
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(description="08 - v1.4 Stage A raw dataset mention extraction.")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--text-root", required=True)
    ap.add_argument("--patterns", default="config/dataset_extraction_patterns_v1_5.csv")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    script = Path(__file__).with_name("run_v14_stageA_extract_dataset_mentions.py")
    cmd = [sys.executable, str(script), "--corpus", args.corpus, "--text-root", args.text_root, "--patterns", args.patterns, "--out", args.out]
    print("08 executing:", " ".join(cmd))
    return subprocess.call(cmd)
if __name__ == "__main__": raise SystemExit(main())
