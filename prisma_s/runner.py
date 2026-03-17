"""
Main analysis orchestrator.

Connects ingestion (local or Google Drive), text extraction, keyword
matching, and long-format Excel output into a single ``run_analysis()`` call.
Reproducibility columns are appended to every output row so that any future
user can verify exactly which protocol version and keyword dictionary
produced the results.
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import PROTOCOL_VERSION
from .extract import SUPPORTED_EXTENSIONS, extract_text, guess_title, guess_year
from .keywords import load_keywords
from .search import build_term_index, count_terms


def _iter_local_files(input_path: Path):
    """Yield every supported document under *input_path* (file, dir, or .zip)."""
    if input_path.is_file() and input_path.suffix.lower() in SUPPORTED_EXTENSIONS:
        yield input_path
    elif input_path.is_file() and input_path.suffix.lower() == ".zip":
        tmp = Path(tempfile.mkdtemp(prefix="prisma_s_zip_"))
        with zipfile.ZipFile(input_path) as z:
            z.extractall(tmp)
        for p in sorted(tmp.rglob("*")):
            if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield p
    elif input_path.is_dir():
        for p in sorted(input_path.rglob("*")):
            if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield p
    else:
        raise ValueError(f"Unsupported input: {input_path}")


def run_analysis(
    batch_id: str,
    output_xlsx: str | Path,
    *,
    input_path: str | Path | None = None,
    drive_folder_id: str | None = None,
    drive_credentials: str | Path | None = None,
    drive_token: str | Path = "token.json",
    keyword_csv: str | Path | None = None,
) -> pd.DataFrame:
    """Run a PRISMA-S keyword corpus analysis and write results to Excel.

    Parameters
    ----------
    batch_id:
        A short label for this batch, written into every output row
        (e.g. ``"batch_01"``).
    output_xlsx:
        Destination ``.xlsx`` file.  Parent directories are created if needed.
    input_path:
        Local directory, single PDF/DOCX, or ``.zip`` of documents.
        Mutually exclusive with *drive_folder_id*.
    drive_folder_id:
        Google Drive folder ID.  When set, files are downloaded to a
        temporary directory before analysis and deleted afterwards.
    drive_credentials:
        Path to ``credentials.json`` (required when *drive_folder_id* is set).
    drive_token:
        Path to cache the OAuth token (default: ``token.json``).
    keyword_csv:
        Path to a ``group,term`` CSV.  Defaults to the bundled
        ``keyword_dictionary_v1.1.csv``.

    Returns
    -------
    pd.DataFrame
        The long-format results dataframe (also written to *output_xlsx*).

    Output columns
    --------------
    Batch, Document Name, Title, Year, Group, Term, Count,
    Protocol Version, Keyword Dict Version, Run UTC, Source Ref
    """
    if input_path is None and drive_folder_id is None:
        raise ValueError("Provide either input_path or drive_folder_id.")

    # --- Load keywords -------------------------------------------------------
    keyword_rows, kw_version = load_keywords(keyword_csv)
    term_index = build_term_index(keyword_rows)

    # --- Collect document paths ----------------------------------------------
    tmp_drive_dir: Path | None = None

    if drive_folder_id:
        if drive_credentials is None:
            raise ValueError("drive_credentials is required when using drive_folder_id.")
        from .drive import download_folder
        print(f"Downloading files from Drive folder: {drive_folder_id}")
        file_paths, tmp_drive_dir = download_folder(
            drive_folder_id, drive_credentials, drive_token
        )
        source_ref = f"gdrive:{drive_folder_id}"
    else:
        file_paths = list(_iter_local_files(Path(input_path)))
        source_ref = str(input_path)

    # --- Process documents ---------------------------------------------------
    run_dt = datetime.now(tz=timezone.utc).isoformat()
    rows: list[dict] = []

    for fp in file_paths:
        try:
            full, first, md = extract_text(fp)
        except Exception as exc:
            print(f"WARNING: skipping {fp.name} — {exc}")
            continue

        title = guess_title(md, first)
        year = guess_year(md, first)

        for c in count_terms(full, term_index):
            rows.append({
                "Batch": batch_id,
                "Document Name": fp.name,
                "Title": title,
                "Year": year,
                "Group": c["Group"],
                "Term": c["Term"],
                "Count": c["Count"],
                "Protocol Version": PROTOCOL_VERSION,
                "Keyword Dict Version": kw_version,
                "Run UTC": run_dt,
                "Source Ref": source_ref,
            })

    # --- Clean up Drive temp dir ---------------------------------------------
    if tmp_drive_dir is not None:
        shutil.rmtree(tmp_drive_dir, ignore_errors=True)

    # --- Build PRISMA-S compliance report ------------------------------------
    from .compliance import build_compliance_report
    compliance_df = build_compliance_report(
        source_ref=source_ref,
        batch_id=batch_id,
        keyword_dict_version=kw_version,
        protocol_version=PROTOCOL_VERSION,
        run_utc=run_dt,
        n_documents=len(file_paths),
        n_terms=len(term_index),
    )

    # --- Write output — two sheets -------------------------------------------
    # Sheet 1: Long_AllTerms  — the full document × term matrix
    # Sheet 2: PRISMA-S_Compliance — 16-item checklist status
    df = pd.DataFrame(rows)
    output_xlsx = Path(output_xlsx)
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(str(output_xlsx), engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Long_AllTerms")
        compliance_df.to_excel(writer, index=False, sheet_name="PRISMA-S_Compliance")

    print(f"Wrote {len(df):,} rows → {output_xlsx}")
    print(f"  Sheet 1: Long_AllTerms  ({len(df):,} rows)")
    print(f"  Sheet 2: PRISMA-S_Compliance  ({len(compliance_df)} items)")

    return df
