"""
Interactive setup wizard for prisma-s.

``prisma-s wizard`` (or ``run_wizard()`` from Python) walks the user through
four steps on the command line:

    Step 1 - Search terms   : bundled dictionary, manual entry, or a custom CSV.
    Step 2 - Source location: a local folder / file, or a Google Drive folder.
    Step 3 - Batch identifier.
    Step 4 - Output folder.

After a confirmation prompt it calls ``run_analysis()``.

Notes
-----
- All prompts accept blank input to take the shown default.
- Drive folder URLs are accepted and the folder ID is extracted automatically.
- Manually entered terms are written to a CSV inside a temporary directory that
  is removed when the wizard returns; keyword loading always flows through the
  normal ``keywords.py`` path.
"""

from __future__ import annotations

import contextlib
import csv
import re
import tempfile
from pathlib import Path

from ._console import enable_utf8_console
from .drive import parse_folder_id
from .keywords import BUNDLED_VERSION, bundled_dict_path, load_keywords

_ILLEGAL_BATCH_CHARS = re.compile(r'[\\/:*?"<>|]+')


def _sanitize_batch_id(raw: str) -> str:
    """Make *raw* safe to embed in a filename on every OS."""
    cleaned = _ILLEGAL_BATCH_CHARS.sub("", raw).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned or "batch"


def _prompt(message: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{message}{suffix}: ").strip()
    if not raw and default:
        print(f"  (using default: {default})")
        return default
    return raw


def _hr(char: str = "-", width: int = 60) -> None:
    print(char * width)


def _header(title: str) -> None:
    _hr()
    print(f"  {title}")
    _hr()


def _count_bundled_terms() -> int:
    return load_keywords(None).n_terms


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def _step_terms(tmpdir: Path) -> tuple[Path, str]:
    """Return ``(csv_path, version)`` for the chosen keyword source."""
    _header("Step 1 of 4 - Search Terms")
    print(
        "  How would you like to specify the search terms?\n\n"
        "  [1]  Use the bundled keyword dictionary"
        f" (v{BUNDLED_VERSION} canonical registry, {_count_bundled_terms()} terms;"
        " `prisma-s run --keywords bundled:1.1` for the flat v1.1 list)\n"
        "  [2]  Enter terms manually (you will be prompted one by one)\n"
        "  [3]  Load from a custom CSV file  (columns: group/category and term)\n"
    )
    choice = _prompt("Choice", default="1")

    if choice == "2":
        return _enter_terms_manually(tmpdir)

    if choice == "3":
        while True:
            csv_path = Path(_prompt("Path to CSV file"))
            if csv_path.is_file():
                m = re.search(r"v(\d+\.\d+)", csv_path.stem)
                print(f"\n  Loaded: {csv_path.name}")
                return csv_path, (m.group(1) if m else "custom")
            print(f"  File not found: {csv_path}  - please try again.")

    if choice != "1":
        print("  Unrecognised choice - using bundled dictionary.")
    print(f"\n  Using bundled dictionary: {bundled_dict_path().name}")
    return bundled_dict_path(), BUNDLED_VERSION


def _enter_terms_manually(tmpdir: Path) -> tuple[Path, str]:
    print(
        "\n  Enter one search term per line.  Press Enter on a blank line when done.\n"
        "  Terms are case-insensitive; multi-word phrases are supported.\n"
    )
    group = _prompt("Group name for all terms", default="Custom")
    print()

    terms: list[str] = []
    while True:
        term = input(f"  Term {len(terms) + 1} (blank to finish): ").strip()
        if not term:
            if not terms:
                print("  No terms entered - using bundled dictionary.")
                return bundled_dict_path(), BUNDLED_VERSION
            break
        terms.append(term)

    csv_path = tmpdir / "manual_keyword_dictionary_vcustom.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["group", "term"])
        for t in terms:
            writer.writerow([group, t])

    print(f"\n  {len(terms)} term(s) recorded.")
    return csv_path, "custom"


def _step_source() -> tuple[str | None, str | None, str | None]:
    """Return ``(input_path, drive_folder_id, drive_credentials)``."""
    _header("Step 2 of 4 - Source Location")
    print(
        "  Where are the documents to be searched?\n\n"
        "  [1]  Local folder or file\n"
        "  [2]  Google Drive folder (URL or folder ID)\n"
    )
    choice = _prompt("Choice", default="1")

    if choice == "2":
        folder_id = parse_folder_id(_prompt("Drive folder URL or folder ID"))
        print(f"  Folder ID: {folder_id}")
        creds = _prompt("Path to credentials.json", default="credentials.json")
        if not Path(creds).is_file():
            print(
                f"\n  WARNING: credentials file not found at '{creds}'.\n"
                "  The run will fail unless this file exists at runtime.\n"
                "  See the Google Drive section of the README for setup.\n"
            )
        return None, folder_id, creds

    while True:
        p = Path(_prompt("Local folder or file path"))
        if p.exists():
            return str(p), None, None
        print(f"  Path not found: {p}  - please try again.")


def _step_batch() -> str:
    _header("Step 3 of 4 - Batch Identifier")
    print(
        "  The batch ID is written into every output row so multiple runs\n"
        "  can be combined and distinguished in analysis.\n"
        "  Example: 'batch_01', 'pilot_2026', 'update_jun_2026'\n"
    )
    return _sanitize_batch_id(_prompt("Batch ID", default="batch_01"))


def _step_output() -> str:
    _header("Step 4 of 4 - Output Location")
    print(
        "  Enter a local folder path where the results will be written.\n"
        "  The folder will be created if it does not exist.\n"
    )
    return _prompt("Output folder", default="results")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_wizard() -> None:
    """Run the interactive setup wizard and execute the analysis."""
    enable_utf8_console()
    print("\n" + "=" * 60)
    print("  PRISMA-S Keyword Corpus Analysis - Interactive Wizard")
    print("  https://www.prisma-statement.org/prisma-search")
    print("=" * 60)
    print(
        "\n  You will be asked to specify:\n\n"
        "    1. Search terms (keyword dictionary)\n"
        "    2. Source location (local folder or Google Drive)\n"
        "    3. Batch identifier\n"
        "    4. Output folder\n"
    )

    with contextlib.ExitStack() as stack:
        tmpdir = Path(
            stack.enter_context(tempfile.TemporaryDirectory(prefix="prisma_s_wiz_"))
        )

        keyword_csv, _kw_ver = _step_terms(tmpdir)
        print()
        input_path, drive_folder_id, drive_credentials = _step_source()
        print()
        batch_id = _step_batch()
        print()
        output_folder = _step_output()

        output_xlsx = Path(output_folder) / f"{batch_id}_results.xlsx"

        _header("Confirm settings")
        print(f"  Keyword dictionary : {keyword_csv}")
        print(f"  Source             : {input_path or ('gdrive:' + str(drive_folder_id))}")
        print(f"  Batch ID           : {batch_id}")
        print(f"  Output file        : {output_xlsx}")
        print()

        if output_xlsx.exists():
            overwrite = _prompt(
                f"{output_xlsx.name} already exists. Overwrite? (yes/no)", default="no"
            ).lower()
            if overwrite not in ("yes", "y"):
                print("  Cancelled.")
                return

        if _prompt("Run analysis? (yes/no)", default="yes").lower() not in ("yes", "y"):
            print("  Cancelled.")
            return

        print()
        from .runner import run_analysis

        run_analysis(
            batch_id=batch_id,
            output_xlsx=str(output_xlsx),
            input_path=input_path,
            drive_folder_id=drive_folder_id,
            drive_credentials=drive_credentials,
            keyword_csv=str(keyword_csv),
        )
