"""
Main analysis orchestrator.

Connects ingestion (local or Google Drive), text extraction, keyword matching,
and Excel output into a single ``run_analysis()`` call.

Two dictionary shapes drive two output shapes:

* **Registry (v1.3, default)** -- variant counts roll up to canonical terms;
  text is NFC/line-ending normalised first; output sheets are ``Long_AllTerms``
  (document x canonical term), ``Term_Summary``, ``D1_Key_Terms``,
  ``Zero_Reference_Terms``, plus ``Run_Metadata`` and ``PRISMA-S_Compliance``,
  and the three DCF figures.
* **Flat (v1.1)** -- one row per (group, term); output identical to v1.4.

A ``Run_Metadata`` sheet + ``run_metadata.json`` record, per document, which
extractor was used and how many pages / words / characters it recovered.
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

# Flat (v1.1) long-format columns -- unchanged from v1.4.
OUTPUT_COLUMNS = [
    "Batch", "Document Name", "Title", "Year", "Group", "Term", "Count",
    "Protocol Version", "Keyword Dict Version", "Run UTC", "Source Ref",
]

REGISTRY_LONG_COLUMNS = [
    "Batch", "Document Name", "Title", "Year", "Category", "Term ID",
    "Canonical Term", "Variants Included", "Variant Counts", "Count", "Referenced",
    "Protocol Version", "Keyword Dict Version", "Run UTC", "Source Ref",
]

_TERM_SUMMARY_COLUMNS = [
    "category", "term id", "term", "variants included",
    "number of reports referencing term",
    "total occurrences of term across corpus", "percent of corpus documents",
]
_D1_COLUMNS = [
    "category", "term", "variants included",
    "number of reports referencing term",
    "total occurrences of term across corpus", "usage rank in category",
]
# Report-ready category order (mirrors the guidebook's Table D-1).
_D1_CATEGORY_ORDER = [
    "Jurisdictional terms", "Supply chain terms", "Farm level terms",
    "AOI terms", "Commodity terms", "search topic",
]

_XLSX_MAX_ROWS = 1_048_576


def _is_junk(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).parts
    return any(part == "__MACOSX" or part.startswith("._") for part in rel)


def _collect_local_files(input_path: Path, stack: contextlib.ExitStack) -> list[Path]:
    if input_path.is_file() and input_path.suffix.lower() in SUPPORTED_EXTENSIONS:
        return [input_path]
    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        tmp = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="prisma_s_zip_")))
        with zipfile.ZipFile(input_path) as z:
            z.extractall(tmp)
        return sorted(
            p for p in tmp.rglob("*")
            if p.suffix.lower() in SUPPORTED_EXTENSIONS and not _is_junk(p, tmp)
        )
    if input_path.is_dir():
        return sorted(
            p for p in input_path.rglob("*")
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
    figures: bool = True,
) -> pd.DataFrame:
    """Run a PRISMA-S keyword corpus analysis and write results to Excel.

    *keyword_csv* accepts ``None`` / ``"bundled:1.3"`` (default registry),
    ``"bundled:1.1"`` (flat), or a path.  Returns the long-format dataframe.
    """
    if input_path is None and drive_folder_id is None:
        raise ValueError("Provide either input_path or drive_folder_id.")

    from .keywords import load_keywords
    from .search import build_registry_index, build_term_index, count_registry, count_terms

    kw = load_keywords(keyword_csv)
    kw_version = kw.version
    is_registry = kw.is_registry
    protocol_version = "1.3" if is_registry else PROTOCOL_VERSION

    if is_registry:
        registry_index = build_registry_index(kw)
        n_terms = kw.n_canonical
        if kw_version == "1.3" and n_terms != 98:
            warnings.warn(
                f"bundled v1.3 dictionary resolved to {n_terms} canonical terms "
                "(expected 98).",
                stacklevel=2,
            )
        from .normalize import normalize_text
    else:
        term_index = build_term_index(kw.flat_rows)
        n_terms = len(term_index)
    if not n_terms:
        raise ValueError("The keyword dictionary produced 0 terms; nothing to search.")

    run_dt = datetime.now(tz=timezone.utc).isoformat()

    with contextlib.ExitStack() as stack:
        if drive_folder_id:
            if drive_credentials is None:
                raise ValueError("drive_credentials is required when using drive_folder_id.")
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
            raise ValueError(f"No .pdf or .docx documents found under {source_ref!r}.")

        rows: list[dict] = []
        doc_meta: list[dict] = []
        # registry accumulator: (Category, Term ID, Canonical Term, Variants) -> [reports, occ]
        summary_acc: dict[tuple, list[int]] = {}

        for fp in file_paths:
            try:
                res = extract_text(fp)
            except Exception as exc:
                print(f"WARNING: skipping {fp.name} - {exc}")
                doc_meta.append({
                    "Document Name": fp.name, "Backend": "", "Pages": pd.NA,
                    "Words": 0, "Chars": 0, "Needs OCR": False,
                    "Status": f"skipped: {exc}",
                })
                continue

            title = guess_title(res.metadata, res.first_text)
            year = guess_year(res.metadata, res.first_text)
            if not res.full_text.strip():
                status = "no text layer - OCR externally and re-run"
            elif res.thin:
                status = "thin text - verify extraction (may need OCR)"
            else:
                status = "ok"
            doc_meta.append({
                "Document Name": fp.name, "Backend": res.backend,
                "Pages": res.pages if res.pages is not None else pd.NA,
                "Words": len(res.full_text.split()), "Chars": len(res.full_text),
                "Needs OCR": bool(res.thin), "Status": status,
            })

            common = {
                "Batch": batch_id, "Document Name": fp.name, "Title": title,
                "Year": year, "Protocol Version": protocol_version,
                "Keyword Dict Version": kw_version, "Run UTC": run_dt,
                "Source Ref": source_ref,
            }

            if is_registry:
                text = normalize_text(res.full_text)
                for c in count_registry(text, registry_index):
                    rows.append({
                        **common,
                        "Category": c["Category"], "Term ID": c["Term ID"],
                        "Canonical Term": c["Canonical Term"],
                        "Variants Included": c["Variants Included"],
                        "Variant Counts": json.dumps(c["Variant Counts"], sort_keys=True),
                        "Count": c["Count"], "Referenced": c["Referenced"],
                    })
                    key = (c["Category"], c["Term ID"], c["Canonical Term"],
                           c["Variants Included"])
                    acc = summary_acc.setdefault(key, [0, 0])
                    acc[0] += c["Referenced"]
                    acc[1] += c["Count"]
            else:
                for c in count_terms(res.full_text, term_index):
                    rows.append({
                        **common, "Group": c["Group"], "Term": c["Term"],
                        "Count": c["Count"],
                    })

    n_attempted = len(file_paths)
    # "processed" = extraction did not raise. A document with an empty or thin
    # text layer was still processed - it just contributes few or no matches and
    # is flagged in "Needs OCR".
    n_processed = sum(1 for m in doc_meta if not m["Status"].startswith("skipped:"))
    n_skipped = n_attempted - n_processed

    output_xlsx = Path(output_xlsx)
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    # ---- assemble the long dataframe --------------------------------------
    if is_registry:
        df = pd.DataFrame(rows, columns=REGISTRY_LONG_COLUMNS)
        long_sheet = "Long_AllTerms"
        term_summary_df = _build_term_summary(summary_acc, n_processed)
        d1_df = _build_d1(term_summary_df, registry_index)
        zero_df = term_summary_df[
            term_summary_df["number of reports referencing term"] == 0
        ].reset_index(drop=True)
    else:
        df = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
        long_sheet = "Long_AllTerms"
        term_summary_df = d1_df = zero_df = None

    df["Year"] = df["Year"].astype("Int64")
    for col in [c for c in ("Group", "Term", "Category", "Canonical Term", "Document Name") if c in df.columns]:
        df[col] = df[col].astype("category")

    if len(df) > _XLSX_MAX_ROWS:
        raise ValueError(
            f"{len(df):,} result rows exceed the .xlsx limit of {_XLSX_MAX_ROWS:,}. "
            "Use a smaller batch or a narrower keyword dictionary."
        )

    meta_df = pd.DataFrame(
        doc_meta,
        columns=["Document Name", "Backend", "Pages", "Words", "Chars", "Needs OCR", "Status"],
    )
    if not meta_df.empty:
        meta_df["Pages"] = meta_df["Pages"].astype("Int64")

    backend_counts: dict[str, int] = {}
    for m in doc_meta:
        b = m["Backend"] or "(skipped)"
        backend_counts[b] = backend_counts.get(b, 0) + 1
    needs_ocr_docs = [m["Document Name"] for m in doc_meta if m.get("Needs OCR")]

    # ---- figures --------------------------------------------------------
    figure_files: list[str] = []
    if figures:
        from .figures import generate_figures

        fig_dir = output_xlsx.parent / "figures"
        fig_input = d1_df if is_registry else _flat_term_summary(df)
        figure_files = [p.name for p in generate_figures(fig_input, fig_dir)]

    run_summary = {
        "batch": batch_id, "run_utc": run_dt, "source_ref": source_ref,
        "protocol_version": protocol_version, "keyword_dict_version": kw_version,
        "dictionary_mode": "registry" if is_registry else "flat",
        "n_terms": n_terms,
        "n_canonical_terms": kw.n_canonical if is_registry else None,
        "n_variants": kw.n_variants if is_registry else None,
        "documents_discovered": n_attempted, "documents_processed": n_processed,
        "documents_skipped": n_skipped, "result_rows": len(df),
        "backend_counts": backend_counts,
        "documents_needing_ocr": needs_ocr_docs, "figures": figure_files,
        "documents": doc_meta_jsonable(doc_meta),
    }

    from .compliance import build_compliance_report

    compliance_df = build_compliance_report(
        source_ref=source_ref, batch_id=batch_id, keyword_dict_version=kw_version,
        protocol_version=protocol_version, run_utc=run_dt,
        n_documents=n_processed, n_terms=n_terms,
    )

    with pd.ExcelWriter(str(output_xlsx), engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=long_sheet)
        if is_registry:
            term_summary_df.to_excel(writer, index=False, sheet_name="Term_Summary")
            d1_df.to_excel(writer, index=False, sheet_name="D1_Key_Terms")
            zero_df.to_excel(writer, index=False, sheet_name="Zero_Reference_Terms")
        compliance_df.to_excel(writer, index=False, sheet_name="PRISMA-S_Compliance")
        meta_df.to_excel(writer, index=False, sheet_name="Run_Metadata")

    (output_xlsx.parent / "run_metadata.json").write_text(
        json.dumps(run_summary, indent=2, default=str), encoding="utf-8"
    )
    from .citation import all_citations

    citation_block = all_citations()
    (output_xlsx.parent / "HOW_TO_CITE.txt").write_text(citation_block + "\n", encoding="utf-8")

    print(f"Wrote {len(df):,} rows -> {output_xlsx}   [{run_summary['dictionary_mode']} mode]")
    print(f"  Long_AllTerms       ({len(df):,} rows)")
    if is_registry:
        print(f"  Term_Summary        ({len(term_summary_df)} canonical terms)")
        print(f"  D1_Key_Terms        ({len(d1_df)} report-ready rows)")
        print(f"  Zero_Reference_Terms({len(zero_df)})")
    print(f"  Run_Metadata        ({len(meta_df)} documents)")
    print(f"  Documents: {n_processed} processed, {n_skipped} skipped of {n_attempted} discovered")
    print(f"  Extraction backend: {backend_counts}")
    if figure_files:
        print(f"  Figures: {', '.join(figure_files)}")
    if needs_ocr_docs:
        print(
            f"  {len(needs_ocr_docs)} document(s) have an empty or thin text layer. "
            "prisma-s does not OCR; run these through an external OCR tool "
            "(e.g. `ocrmypdf in.pdf out.pdf`) and re-run:"
        )
        for name in needs_ocr_docs:
            print(f"    - {name}")
    if n_skipped:
        warnings.warn(
            f"{n_skipped} document(s) could not be processed; see Run_Metadata.",
            stacklevel=2,
        )
    if emit_citation:
        print("\n" + citation_block + "\n")

    return df


# ---------------------------------------------------------------------------
# Registry summary helpers
# ---------------------------------------------------------------------------

def _build_term_summary(acc: dict[tuple, list[int]], n_docs: int) -> pd.DataFrame:
    denom = max(n_docs, 1)
    recs = [
        {
            "category": cat, "term id": tid, "term": canon,
            "variants included": variants,
            "number of reports referencing term": reports,
            "total occurrences of term across corpus": occ,
            "percent of corpus documents": round(reports / denom, 4),
        }
        for (cat, tid, canon, variants), (reports, occ) in acc.items()
    ]
    return pd.DataFrame(recs, columns=_TERM_SUMMARY_COLUMNS)


def _build_d1(term_summary: pd.DataFrame, registry_index: list[dict]) -> pd.DataFrame:
    visible = {e["term_id"] for e in registry_index if e["include_in_visuals"]}
    d1 = term_summary[
        term_summary["term id"].isin(visible)
        & (term_summary["number of reports referencing term"] > 0)
    ].copy()
    order = {c: i for i, c in enumerate(_D1_CATEGORY_ORDER)}
    d1["_cat_order"] = d1["category"].map(lambda c: order.get(c, len(order)))
    d1 = d1.sort_values(
        ["_cat_order", "number of reports referencing term",
         "total occurrences of term across corpus"],
        ascending=[True, False, False],
    )
    d1["usage rank in category"] = d1.groupby("category", sort=False).cumcount() + 1
    return d1[_D1_COLUMNS].reset_index(drop=True)


def _flat_term_summary(long_df: pd.DataFrame) -> pd.DataFrame:
    """A minimal Term_Summary-shaped frame for figures in flat (v1.1) mode."""
    g = (long_df.assign(_ref=(long_df["Count"] > 0).astype(int))
         .groupby(["Group", "Term"], observed=True)
         .agg(**{
             "number of reports referencing term": ("_ref", "sum"),
             "total occurrences of term across corpus": ("Count", "sum"),
         })
         .reset_index()
         .rename(columns={"Group": "category", "Term": "term"}))
    g["variants included"] = g["term"]
    return g


def doc_meta_jsonable(doc_meta: list[dict]) -> list[dict]:
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
