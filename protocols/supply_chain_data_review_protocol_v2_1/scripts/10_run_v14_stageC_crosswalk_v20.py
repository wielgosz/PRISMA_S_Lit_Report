#!/usr/bin/env python3
"""
10_run_v14_stageC_crosswalk_v20.py
==================================

Stage 10 of the Supply Chain Data Review Protocol v2.0.

Purpose
-------
Produce dataset-document crosswalk outputs from canonicalized Stage B mentions.
This crosswalk is the central evidence table linking corpus documents to known
C1 datasets and possible new dataset discoveries.
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(description="10 - v1.4 Stage C dataset-document crosswalk.")
    ap.add_argument("--stageB", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    script = Path(__file__).with_name("run_v14_stageC_crosswalk.py")
    cmd = [sys.executable, str(script), "--stageB", args.stageB, "--out", args.out]
    print("10 executing:", " ".join(cmd))
    return subprocess.call(cmd)
if __name__ == "__main__": raise SystemExit(main())
