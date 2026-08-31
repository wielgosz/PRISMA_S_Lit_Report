#!/usr/bin/env python3
"""
09_run_v14_stageB_canonicalize_v20.py
=====================================

Stage 9 of the Supply Chain Data Review Protocol v2.0.

Purpose
-------
Map raw dataset mention strings from Stage A to canonical C1 dataset names and
aliases. Mentions that do not match the canonical C1 registry are flagged as
possible new datasets requiring review.

Dependency
----------
Consumes the normalized C1 registry from Stage 7 and Stage A raw mentions.
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(description="09 - v1.4 Stage B canonicalize dataset mentions.")
    ap.add_argument("--stageA", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--crosswalk", default="config/dataset_name_crosswalk_v1_5.csv")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    script = Path(__file__).with_name("run_v14_stageB_canonicalize.py")
    cmd = [sys.executable, str(script), "--stageA", args.stageA, "--registry", args.registry, "--crosswalk", args.crosswalk, "--out", args.out]
    print("09 executing:", " ".join(cmd))
    return subprocess.call(cmd)
if __name__ == "__main__": raise SystemExit(main())
