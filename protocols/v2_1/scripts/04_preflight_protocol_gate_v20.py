#!/usr/bin/env python3
"""
04_preflight_protocol_gate_v20.py
=================================

Stage 4 of the Supply Chain Data Review Protocol v2.0.

Purpose
-------
Stop the pipeline if core prerequisites are not satisfied. This gate sits after
corpus reconciliation and frozen-text validation and before any analytical
outputs are generated.

Checks expected in v2.0
-----------------------
- Reconciled corpus manifest exists.
- No historically excluded/confidential file is included.
- Required converted source PDFs are present.
- Frozen text artifacts exist for all included/countable rows.
- No blocking extraction statuses remain.
- Full executable v1.3 dictionary is used.
- v1.3 matching rule is declared in params.

This wrapper calls the v1.5 preflight gate and can be extended with corpus-level
checks as the reconciliation manifest stabilizes.
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(description="04 - Run protocol preflight gate.")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dictionary", required=True)
    ap.add_argument("--qa-report", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--params", default="config/protocol_v2_0_params.yml")
    args = ap.parse_args()
    script = Path(__file__).with_name("preflight_protocol_gate.py")
    cmd = [sys.executable, str(script), "--corpus", args.corpus, "--manifest", args.manifest, "--dictionary", args.dictionary, "--qa-report", args.qa_report, "--out", args.out, "--params", args.params]
    print("04 executing:", " ".join(cmd))
    return subprocess.call(cmd)
if __name__ == "__main__": raise SystemExit(main())
