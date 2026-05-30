#!/usr/bin/env python3
"""
01_reconcile_corpus_v20.py
================================

Stage 1 of the Supply Chain Data Review Protocol v2.0.

Purpose
-------
Create the authoritative corpus manifest that all later stages consume.
This stage is deliberately first because every downstream output depends on a
single reconciled view of the corpus.

Inputs
------
- Uploaded PDFs and ZIP batches in an input directory.
- Historical v1.3/v1.4 metadata, when available.
- v2.0 config files containing historical removals, converted-source rules,
  new additions, and confidential/review-pending exclusions.

Outputs
-------
- v20_corpus_manifest.csv: one row per PDF-like document, with inclusion status.
- v20_file_inventory.csv: raw inventory of discovered PDF files.
- v20_corpus_reconciliation_notes.csv: audit notes used for manual review.

Dependency rule
---------------
No frozen-text extraction, keyword count, or dataset crosswalk may run until
this manifest has been reviewed or accepted. This prevents accidental inclusion
of duplicates, historically removed records, or confidential material such as
ice-praesentation.pdf.

Design notes for future maintainers
-----------------------------------
This script is intentionally conservative. It uses exact file names and known
config rules first. Fuzzy bibliographic matching can be added, but should always
write a confidence and review flag rather than silently changing document IDs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd
import yaml

EXCLUDE_NAME_PATTERNS = [
    "ice-praesentation.pdf",
]

DUPLICATE_PREFERRED = {
    "responsible_sourcing_practical_guide_online_version (1).pdf": "responsible_sourcing_practical_guide_online_version.pdf",
    "AFi Operational Guidance - Monitoring & Verification (2020-05).pdf": "OG_Monitoring_Verification-2020-5.pdf",
    "AFi Operational Guidance - Supply Chain Management (2020-05).pdf": "OG_Supply_Chain_Management-2020-5.pdf",
    "ofi Scaling FLRI whitepaper update.pdf": "Satelligence FLRI whitepaper.pdf",
}

@dataclass
class FileRecord:
    doc_id: str
    previous_doc_id: str
    file_name: str
    source_path: str
    relative_path: str
    batch_id: str
    status: str
    status_reason: str
    pdf_sha256: str
    file_size_bytes: int
    title: str = ""
    year: str = ""
    authors_or_orgs: str = ""
    publishing_org_id: str = ""
    source_url: str = ""
    apa_reference: str = ""
    is_new_v20_addition: bool = False
    review_required: bool = False


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_params(path: Path) -> dict:
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {}


def extract_inputs(input_root: Path, work_raw: Path) -> List[Path]:
    """Copy PDFs and unpack ZIP archives into a deterministic raw PDF directory."""
    work_raw.mkdir(parents=True, exist_ok=True)
    discovered: List[Path] = []
    for p in sorted(input_root.rglob("*")):
        if p.is_dir():
            continue
        lower = p.name.lower()
        if lower.endswith(".zip"):
            batch_dir = work_raw / p.stem.replace(" ", "_")
            batch_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(p, "r") as z:
                z.extractall(batch_dir)
            discovered.extend(sorted(batch_dir.rglob("*.pdf")))
        elif lower.endswith(".pdf"):
            target = work_raw / "loose_pdfs" / p.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(p, target)
            discovered.append(target)
    # De-duplicate identical paths produced by repeated discovery.
    return sorted({p.resolve() for p in discovered})


def read_known_metadata(historical_v13: Optional[Path]) -> pd.DataFrame:
    """Read prior B1/vetted metadata if available.

    The v1.3 workbook is useful as a baseline, but this script does not assume
    that PDF metadata is authoritative. Manual corpus metadata and change logs
    remain authoritative.
    """
    if historical_v13 and historical_v13.exists():
        try:
            xls = pd.ExcelFile(historical_v13)
            for sheet in ["Vetted_Corpus_Metadata", "B1_Corpus_Metadata_Snapshot", "B1_Sectoral_Guidance_Reports"]:
                if sheet in xls.sheet_names:
                    return pd.read_excel(xls, sheet_name=sheet).fillna("")
        except Exception:
            pass
    return pd.DataFrame()


def infer_batch_id(path: Path) -> str:
    parts = [x.lower() for x in path.parts]
    for part in parts:
        if part.startswith("batch_03") or part.startswith("batch 03"):
            return "Batch 03"
        if part.startswith("batch_04") or part.startswith("batch 04"):
            return "Batch 04"
        if part.startswith("batch_05") or part.startswith("batch 05"):
            return "Batch 05"
        if part.startswith("batch_06") or part.startswith("batch 06"):
            return "Batch 06"
        if part.startswith("batch_07") or part.startswith("batch 07"):
            return "Batch 07"
        if part.startswith("batch_08") or part.startswith("batch 08"):
            return "Batch 08"
        if part.startswith("batch_09") or part.startswith("batch 09"):
            return "Batch 09"
        if part.startswith("batch_11") or part.startswith("batch 11"):
            return "Batch 11"
    return "Loose PDF"


def match_metadata_by_filename(file_name: str, meta: pd.DataFrame) -> Dict[str, str]:
    if meta.empty:
        return {}
    lower_cols = {c.lower(): c for c in meta.columns}
    file_col = lower_cols.get("file_name") or lower_cols.get("filename")
    if not file_col:
        return {}
    subset = meta[meta[file_col].astype(str).str.strip().str.lower().eq(file_name.strip().lower())]
    if subset.empty:
        return {}
    row = subset.iloc[0]
    def get(*names: str) -> str:
        for name in names:
            col = lower_cols.get(name.lower())
            if col is not None:
                return str(row.get(col, ""))
        return ""
    return {
        "doc_id": get("doc_id"),
        "previous_doc_id": get("previous_doc_id", "doc_id"),
        "title": get("title", "document_title"),
        "year": get("year"),
        "authors_or_orgs": get("authors_or_orgs", "publisher"),
        "publishing_org_id": get("publishing_org_id", "org_id"),
        "source_url": get("source_url", "preferred_access_url"),
        "apa_reference": get("apa_reference"),
    }


def build_manifest(pdf_paths: List[Path], raw_root: Path, meta: pd.DataFrame, params: dict) -> pd.DataFrame:
    new_files = set(params.get("corpus_reconciliation", {}).get("new_additions", []))
    required_converted = set(params.get("corpus_reconciliation", {}).get("converted_source_files_required", []))
    records: List[FileRecord] = []
    used_doc_ids: set[str] = set()
    seq = 1
    for pdf in pdf_paths:
        file_name = pdf.name
        md = match_metadata_by_filename(file_name, meta)
        status = "INCLUDE"
        reason = "included_pending_validation"
        review = False
        if file_name.lower() in [x.lower() for x in EXCLUDE_NAME_PATTERNS]:
            status = "EXCLUDE_CONFIDENTIAL_PENDING_HISTORY_CONFIRMATION"
            reason = "historical/user-indicated confidential exclusion review"
            review = True
        elif file_name in DUPLICATE_PREFERRED:
            status = "EXCLUDE_DUPLICATE"
            reason = f"duplicate candidate; retain {DUPLICATE_PREFERRED[file_name]}"
        elif file_name in required_converted:
            status = "INCLUDE_CONVERTED_SOURCE"
            reason = "required user-supplied converted source retained from historical change log"
        elif file_name in new_files:
            status = "INCLUDE_NEW_ADDITION"
            reason = "new v2.0 corpus addition"
        doc_id = md.get("doc_id") or f"V20-{seq:03d}"
        # Guard against duplicate doc IDs introduced by uncertain matching.
        if doc_id in used_doc_ids:
            doc_id = f"V20-{seq:03d}"
            review = True
            reason += "; generated new doc_id because matched doc_id was already used"
        used_doc_ids.add(doc_id)
        rec = FileRecord(
            doc_id=doc_id,
            previous_doc_id=md.get("previous_doc_id") or md.get("doc_id") or doc_id,
            file_name=file_name,
            source_path=str(pdf),
            relative_path=str(pdf.relative_to(raw_root)) if pdf.is_relative_to(raw_root) else file_name,
            batch_id=infer_batch_id(pdf),
            status=status,
            status_reason=reason,
            pdf_sha256=sha256_file(pdf),
            file_size_bytes=pdf.stat().st_size,
            title=md.get("title", ""),
            year=md.get("year", ""),
            authors_or_orgs=md.get("authors_or_orgs", ""),
            publishing_org_id=md.get("publishing_org_id", ""),
            source_url=md.get("source_url", ""),
            apa_reference=md.get("apa_reference", ""),
            is_new_v20_addition=file_name in new_files,
            review_required=review or not bool(md),
        )
        records.append(rec)
        seq += 1
    df = pd.DataFrame([asdict(r) for r in records])
    return df.sort_values(["status", "batch_id", "file_name"])


def main() -> int:
    ap = argparse.ArgumentParser(description="01 - Reconcile uploaded PDFs against historical corpus metadata.")
    ap.add_argument("--input-root", required=True, help="Directory containing uploaded ZIP/PDF batches.")
    ap.add_argument("--work-raw", required=True, help="Directory where PDFs will be unpacked/copied.")
    ap.add_argument("--historical-v13", default="", help="Prior v1.3 backup workbook for metadata matching.")
    ap.add_argument("--params", default="config/protocol_v2_0_params.yml")
    ap.add_argument("--out", required=True, help="Output directory for reconciliation files.")
    args = ap.parse_args()

    input_root = Path(args.input_root)
    work_raw = Path(args.work_raw)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    params = load_params(Path(args.params))
    pdf_paths = extract_inputs(input_root, work_raw)
    meta = read_known_metadata(Path(args.historical_v13) if args.historical_v13 else None)
    manifest = build_manifest(pdf_paths, work_raw, meta, params)

    inventory = manifest[["file_name", "source_path", "relative_path", "batch_id", "pdf_sha256", "file_size_bytes"]].copy()
    notes = manifest[["doc_id", "previous_doc_id", "file_name", "status", "status_reason", "review_required"]].copy()

    manifest.to_csv(out / "v20_corpus_manifest.csv", index=False)
    inventory.to_csv(out / "v20_file_inventory.csv", index=False)
    notes.to_csv(out / "v20_corpus_reconciliation_notes.csv", index=False)
    print(f"01 complete: {len(manifest)} file records written to {out / 'v20_corpus_manifest.csv'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
