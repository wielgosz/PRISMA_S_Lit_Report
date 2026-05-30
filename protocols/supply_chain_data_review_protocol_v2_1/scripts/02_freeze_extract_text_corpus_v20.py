#!/usr/bin/env python3
"""
02_freeze_extract_text_corpus_v20.py
====================================

Stage 2 of the Supply Chain Data Review Protocol v2.0.

Purpose
-------
Convert the reconciled corpus manifest from Stage 1 into a frozen extracted-text
corpus. The keyword-count and dataset-crosswalk stages must consume this frozen
text, not re-extract from PDFs ad hoc.

Why this exists
---------------
PDF extraction is a major reproducibility risk. Back-end model/tool timeouts or
parser differences can silently change term counts. This stage freezes text,
hashes it, records page/character counts, and flags extraction warnings so later
stages can be repeated consistently.

Output contract
---------------
- `frozen_text_manifest.csv` with one row per included document.
- `text/<doc_id>.txt` raw extracted text with page markers.
- `normalized_text/<doc_id>.txt` normalized text used for deterministic counting.

This wrapper calls the v1.5 extraction implementation, but it documents the v2.0
dependency sequence and maps v2.0 argument names to the frozen-text layer.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="02 - Freeze PDFs into extracted text artifacts.")
    ap.add_argument("--corpus", required=True, help="Stage 1 v20_corpus_manifest.csv")
    ap.add_argument("--pdf-root", required=True, help="Root containing unpacked/copy-staged PDFs from Stage 1")
    ap.add_argument("--out-root", required=True, help="Frozen text output root")
    ap.add_argument("--params", default="config/protocol_v2_0_params.yml")
    args = ap.parse_args()
    script = Path(__file__).with_name("freeze_extract_text_corpus.py")
    cmd = [sys.executable, str(script), "--corpus", args.corpus, "--pdf-root", args.pdf_root, "--out-root", args.out_root, "--params", args.params]
    print("02 executing:", " ".join(cmd))
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
