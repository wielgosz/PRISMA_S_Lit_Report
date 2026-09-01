"""
Main analysis orchestrator.

Connects ingestion (local or Google Drive), text extraction, keyword matching,
and long-format Excel output into a single ``run_analysis()`` call.
Reproducibility columns are stamped onto every output row, and a
``Run_Metadata`` sheet plus ``run_metadata.json`` record — per document — which
extractor was used and how many pages / words / characters it recovered, so a
reviewer can confirm extraction was complete and consistent.
"""

from __future__ import annotations

import contextlib
import json
import tempfile
import warnings
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ._version import PROTOCOL_VERSION
from .extract import SUPPORTED_EXTENSIONS, extract_text, guess_title, guess_year

OUTPUT_COLUMNS = [
    "Batch",
    "Document Name",
    "Title",
    "Year",
    "Group",
    "Term",
    "Count",
    "Protocol Version",
    "Keyword Dict Version",
    "Run UTC",
    "Source Ref",
]

# openpyxl / the .xlsx format cap.
_XLSX_MAX_ROWS = 1_048_576


def _is_junk(path: Path, root: Path) -> bool:
    """AppleDouble / resource-fork noise that macOS zips carry."""
    rel = path.relative_to(root).parts
    return any(part == "__MACOSX" or part.startswith("._") for part in rel)


def _collect_local_files(input_path: Path, stack: contextlib.ExitStack) -> list[Path]:
    """Return every supported document under *input_path* (file, dir, or .zip).

    A ``.zip`` is extracted into a temp directory whose cleanup is registered on
    *stack*, so it never leaks regardless of how the run ends.
    """
    if input_path.is_file() and input_path.suffix.lower() in SUPPORTED_EXTENSIONS:
        return [input_path]

    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        tmp = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="prisma_s_zip_")))
        with zipfile.ZipFile(input_path) as z:
            z.extractall(tmp)
        return sorted(
            p
            for p in tmp.rglob("*")
            if p.suffix.lower() in SUPPORTED_EXTENSIONS and not _is_junk(p, tmp)
        )

    if input_path.is_dir():
        return sorted(
            p
            for p in input_path.rglob("*")
            if p.suffix.lower() in SUPPORTED_EXTENSIONS and not _is_junk(p, input_path)
        )

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
    emit_citation: bool = True,
) -> pd.DataFrame:
    """Run a PRISMA-S keyword corpus analysis and write results to Excel.

    Parameters
    ----------
    batch_id:
        Short label for this batch, written into every output row.
    output_xlsx:
        Destination ``.xlsx`` file.  ``run_metadata.json`` and ``HOW_TO_CITE.txt``
        are written alongside it.  Parent directories are created if needed.
    input_path:
        Local directory, single PDF/DOCX, or ``.zip`` of documents.  Mutually
        exclusive with *drive_folder_id*.
    drive_folder_id, drive_credentials, drive_token:
        Google Drive ingestion (see :mod:`prisma_s.drive`).
    keyword_csv:
        Path to a keyword dictionary CSV.  Defaults to the bundled one.
    emit_citation:
        When true, print the trilingual "How to cite" block after the run.

    Returns
    -------
    pd.DataFrame
        The long-format results dataframe (columns: :data:`OUTPUT_COLUMNS`).

    Raises
    ------
    ValueError
        If no source is given, no documents are found, the dictionary yields no
        terms, or the result would exceed the ``.xlsx`` row limit.
    """
    if input_path is None and drive_folder_id is None:
        raise ValueError("Provide either input_path or drive_folder_id.")

    from .keywords import load_keywords
    from .search import build_term_index, count_terms

    keyword_rows, kw_version = load_keywords(keyword_csv)
    term_index = build_term_index(keyword_rows)
    if not term_index:
        raise ValueError("The keyword dictionary produced 0 terms; nothing to search.")

    run_dt = datetime.now(tz=timezone.utc).isoformat()

    with contextlib.ExitStack() as stack:
        if drive_folder_id:
            if drive_credentials is None:
                raise ValueError(
                    "drive_credentials is required when using drive_folder_id."
                )
            from .drive import download_folder

            print(f"Downloading files from Drive folder: {drive_folder_id}")
            file_paths, tmp_drive_dir = download_folder(
                drive_folder_id, drive_credentials, drive_token
            )
            stack.callback(_rmtree, tmp_drive_dir)
            source_ref = f"gdrive:{drive_folder_id}"
        else:
            file_paths = _collect_local_files(Path(input_path), stack)
            source_ref = str(input_path)

        if not file_paths:
            raise ValueError(
                f"No .pdf or .docx documents found under {source_ref!r}."
            )

        rows: list[dict] = []
        doc_meta: list[dict] = []

        for fp in file_paths:
            try:
                res = extract_text(fp)
            except Exception as exc:
                print(f"WARNING: skipping {fp.name} - {exc}")
                doc_meta.append(
                    {
                        "Document Name": fp.name,
                        "Backend": "",
                        "Pages": pd.NA,
                        "Words": 0,
                        "Chars": 0,
                        "Status": f"skipped: {exc}",
                    }
                )
                continue

            title = guess_title(res.metadata, res.first_text)
            year = guess_year(res.metadata, res.first_text)
            words = len(res.full_text.split())
            doc_meta.append(
                {
                    "Document Name": fp.name,
                    "Backend": res.backend,
                    "Pages": res.pages if res.pages is not None else pd.NA,
                    "Words": words,
                    "Chars": len(res.full_text),
                    "Status": "ok" if res.full_text.strip() else "ok: no text extracted",
                }
            )

            for c in count_terms(res.full_text, term_index):
                rows.append(
                    {
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
                    }
                )

    n_attempted = len(file_paths)
    n_processed = sum(1 for m in doc_meta if m["Status"].startswith("ok"))
    n_skipped = n_attempted - n_processed

    df = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    df["Year"] = df["Year"].astype("Int64")
    for col in ("Group", "Term", "Document Name"):
        df[col] = df[col].astype("category")

    if len(df) > _XLSX_MAX_ROWS:
        raise ValueError(
            f"{len(df):,} result rows exceed the .xlsx limit of {_XLSX_MAX_ROWS:,}. "
            "Use a smaller batch or a narrower keyword dictionary."
        )

    meta_df = pd.DataFrame(
        doc_meta, columns=["Document Name", "Backend", "Pages", "Words", "Chars", "Status"]
    )
    if not meta_df.empty:
        meta_df["Pages"] = meta_df["Pages"].astype("Int64")

    run_summary = {
        "batch": batch_id,
        "run_utc": run_dt,
        "source_ref": source_ref,
        "protocol_version": PROTOCOL_VERSION,
        "keyword_dict_version": kw_version,
        "n_terms": len(term_index),
        "documents_discovered": n_attempted,
        "documents_processed": n_processed,
        "documents_skipped": n_skipped,
        "result_rows": len(df),
        "documents": doc_meta_jsonable(doc_meta),
    }

    from .compliance import build_compliance_report

    compliance_df = build_compliance_report(
        source_ref=source_ref,
        batch_id=batch_id,
        keyword_dict_version=kw_version,
        protocol_version=PROTOCOL_VERSION,
        run_utc=run_dt,
        n_documents=n_processed,
        n_terms=len(term_index),
    )

    output_xlsx = Path(output_xlsx)
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(str(output_xlsx), engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Long_AllTerms")
        compliance_df.to_excel(writer, index=False, sheet_name="PRISMA-S_Compliance")
        meta_df.to_excel(writer, index=False, sheet_name="Run_Metadata")

    (output_xlsx.parent / "run_metadata.json").write_text(
        json.dumps(run_summary, indent=2, default=str), encoding="utf-8"
    )

    from .citation import all_citations

    citation_block = all_citations()
    (output_xlsx.parent / "HOW_TO_CITE.txt").write_text(
        citation_block + "\n", encoding="utf-8"
    )

    print(f"Wrote {len(df):,} rows -> {output_xlsx}")
    print(f"  Sheet 1: Long_AllTerms       ({len(df):,} rows)")
    print(f"  Sheet 2: PRISMA-S_Compliance ({len(compliance_df)} items)")
    print(f"  Sheet 3: Run_Metadata        ({len(meta_df)} documents)")
    print(
        f"  Documents: {n_processed} processed, {n_skipped} skipped "
        f"of {n_attempted} discovered"
    )
    if n_skipped:
        warnings.warn(
            f"{n_skipped} document(s) could not be processed; see the Run_Metadata "
            "sheet for the reason on each.",
            stacklevel=2,
        )

    if emit_citation:
        print("\n" + citation_block + "\n")

    return df


def doc_meta_jsonable(doc_meta: list[dict]) -> list[dict]:
    """Convert pandas sentinels in *doc_meta* to plain JSON-safe values."""
    out = []
    for m in doc_meta:
        row = dict(m)
        if row.get("Pages") is pd.NA:
            row["Pages"] = None
        out.append(row)
    return out


def _rmtree(path) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)
