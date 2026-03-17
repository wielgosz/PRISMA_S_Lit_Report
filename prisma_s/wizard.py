"""
Interactive setup wizard for prisma-s.

Running ``prisma-s wizard`` (or calling ``run_wizard()`` from Python) walks
the user through four configuration steps on the command line:

    Step 1 — Search terms
        Choose the bundled keyword dictionary, enter terms manually, or
        point to a custom CSV file.

    Step 2 — Source location
        Paste a Google Drive folder URL / ID  OR  enter a local folder path.

    Step 3 — Batch identifier
        A short label written into every output row (e.g. "batch_01").

    Step 4 — Output location
        Enter a local folder path where the .xlsx will be written.
        (Google Drive output is not yet supported; upload manually after the run.)

After confirmation the wizard calls ``run_analysis()`` directly.

Design notes
------------
- All prompts accept blank input to accept the suggested default.
- Drive folder URLs (https://drive.google.com/drive/folders/...) are accepted
  and the folder ID is extracted automatically.
- Terms entered manually are assigned to a user-supplied group name (default
  "Custom") so the output Group column remains consistent.
- A temporary in-memory CSV is built when the user enters terms manually,
  meaning keyword loading still flows through the standard ``keywords.py``
  path — no special-case code in the runner.
"""

from __future__ import annotations

import csv
import io
import os
import re
import tempfile
from pathlib import Path

from .drive import parse_folder_id
from .keywords import BUNDLED_DICT_NAME, BUNDLED_VERSION, _KEYWORDS_DIR


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _prompt(message: str, default: str = "") -> str:
    """Print *message* and read a line of input.

    If the user presses Enter without typing anything and *default* is
    provided, the default value is returned and echoed.
    """
    suffix = f" [{default}]" if default else ""
    raw = input(f"{message}{suffix}: ").strip()
    if not raw and default:
        print(f"  (using default: {default})")
        return default
    return raw


def _hr(char: str = "─", width: int = 60) -> None:
    """Print a horizontal rule."""
    print(char * width)


def _header(title: str) -> None:
    _hr()
    print(f"  {title}")
    _hr()


# ---------------------------------------------------------------------------
# Step implementations
# ---------------------------------------------------------------------------

def _step_terms() -> tuple[Path, str]:
    """Prompt the user for a keyword source.

    Returns
    -------
    csv_path : Path
        Path to the keyword CSV to use (may be a temp file).
    kw_version : str
        Version string to display (may be 'custom').
    """
    _header("Step 1 of 4 — Search Terms")
    print(
        "  How would you like to specify the search terms?\n"
        "\n"
        "  [1]  Use the bundled keyword dictionary"
        f" (v{BUNDLED_VERSION}, {_count_bundled_terms()} terms)\n"
        "  [2]  Enter terms manually (you will be prompted one by one)\n"
        "  [3]  Load from a custom CSV file  (columns: group, term)\n"
    )
    choice = _prompt("Choice", default="1")

    if choice == "1":
        csv_path = _KEYWORDS_DIR / BUNDLED_DICT_NAME
        print(f"\n  Using bundled dictionary: {csv_path.name}")
        return csv_path, BUNDLED_VERSION

    elif choice == "2":
        return _enter_terms_manually()

    elif choice == "3":
        while True:
            path_str = _prompt("Path to CSV file")
            csv_path = Path(path_str)
            if csv_path.is_file():
                m = re.search(r"v(\d+\.\d+)", csv_path.stem)
                version = m.group(1) if m else "custom"
                print(f"\n  Loaded: {csv_path.name}")
                return csv_path, version
            print(f"  File not found: {csv_path}  — please try again.")

    else:
        print("  Unrecognised choice — using bundled dictionary.")
        return _KEYWORDS_DIR / BUNDLED_DICT_NAME, BUNDLED_VERSION


def _count_bundled_terms() -> int:
    """Return the number of terms in the bundled dictionary."""
    try:
        with open(_KEYWORDS_DIR / BUNDLED_DICT_NAME, newline="", encoding="utf-8") as f:
            return sum(1 for row in csv.DictReader(f) if row.get("term", "").strip())
    except Exception:
        return 0


def _enter_terms_manually() -> tuple[Path, str]:
    """Interactively collect terms from the user and write to a temp CSV."""
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
                print("  No terms entered — using bundled dictionary.")
                return _KEYWORDS_DIR / BUNDLED_DICT_NAME, BUNDLED_VERSION
            break
        terms.append(term)

    # Write to a named temp file so keywords.py can read it normally
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix="_keyword_dictionary_vcustom.csv",
        delete=False,
        encoding="utf-8",
        newline="",
    )
    writer = csv.writer(tmp)
    writer.writerow(["group", "term"])
    for t in terms:
        writer.writerow([group, t])
    tmp.close()

    print(f"\n  {len(terms)} term(s) saved to temporary dictionary.")
    return Path(tmp.name), "custom"


def _step_source() -> tuple[str | None, str | None, str | None]:
    """Prompt the user for the document source.

    Returns
    -------
    input_path : str or None
        Local folder/file path (None if Drive is used).
    drive_folder_id : str or None
        Parsed Drive folder ID (None if local is used).
    drive_credentials : str or None
        Path to credentials.json (None if local is used).
    """
    _header("Step 2 of 4 — Source Location")
    print(
        "  Where are the documents to be searched?\n"
        "\n"
        "  [1]  Local folder or file\n"
        "  [2]  Google Drive folder (URL or folder ID)\n"
    )
    choice = _prompt("Choice", default="1")

    if choice == "2":
        raw = _prompt("Drive folder URL or folder ID")
        folder_id = parse_folder_id(raw)
        print(f"  Folder ID: {folder_id}")

        creds_default = "credentials.json"
        creds = _prompt("Path to credentials.json", default=creds_default)
        if not Path(creds).is_file():
            print(
                f"\n  WARNING: credentials file not found at '{creds}'.\n"
                "  The run will fail unless this file exists at runtime.\n"
                "  See README.md → 'Google Drive setup' for instructions.\n"
            )
        return None, folder_id, creds

    else:
        while True:
            path_str = _prompt("Local folder or file path")
            p = Path(path_str)
            if p.exists():
                return str(p), None, None
            print(f"  Path not found: {p}  — please try again.")


def _step_batch() -> str:
    """Prompt the user for a batch identifier."""
    _header("Step 3 of 4 — Batch Identifier")
    print(
        "  The batch ID is written into every output row so multiple runs\n"
        "  can be combined and distinguished in analysis.\n"
        "  Example: 'batch_01', 'pilot_2026', 'update_jun_2026'\n"
    )
    return _prompt("Batch ID", default="batch_01")


def _step_output() -> str:
    """Prompt the user for the output folder path."""
    _header("Step 4 of 4 — Output Location")
    print(
        "  Enter a local folder path where the Excel results file will be written.\n"
        "  The folder will be created if it does not exist.\n"
    )
    folder = _prompt("Output folder", default="results")
    return folder


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_wizard() -> None:
    """Run the interactive setup wizard and execute the analysis.

    This is the function called by ``prisma-s wizard`` on the command line.
    It can also be imported and called directly from a Python script for a
    guided interactive session.
    """
    print("\n" + "═" * 60)
    print("  PRISMA-S Keyword Corpus Analysis — Interactive Wizard")
    print("  https://www.prisma-statement.org/prisma-search")
    print("═" * 60)
    print(
        "\n  This wizard will guide you through configuring a keyword\n"
        "  search of your document corpus according to PRISMA-S\n"
        "  methodology.  You will be asked to specify:\n"
        "\n"
        "    1. Search terms (keyword dictionary)\n"
        "    2. Source location (local folder or Google Drive)\n"
        "    3. Batch identifier\n"
        "    4. Output folder\n"
    )

    # Collect configuration
    keyword_csv, _kw_ver = _step_terms()
    print()
    input_path, drive_folder_id, drive_credentials = _step_source()
    print()
    batch_id = _step_batch()
    print()
    output_folder = _step_output()

    # Build output path
    output_xlsx = str(Path(output_folder) / f"{batch_id}_results.xlsx")

    # Confirm
    _header("Confirm settings")
    print(f"  Keyword dictionary : {keyword_csv}")
    print(f"  Source             : {input_path or ('gdrive:' + drive_folder_id)}")
    print(f"  Batch ID           : {batch_id}")
    print(f"  Output file        : {output_xlsx}")
    print()
    confirm = _prompt("Run analysis? (yes/no)", default="yes").lower()
    if confirm not in ("yes", "y"):
        print("  Cancelled.")
        return

    # Run
    print()
    from .runner import run_analysis
    run_analysis(
        batch_id=batch_id,
        output_xlsx=output_xlsx,
        input_path=input_path,
        drive_folder_id=drive_folder_id,
        drive_credentials=drive_credentials,
        keyword_csv=str(keyword_csv),
    )
