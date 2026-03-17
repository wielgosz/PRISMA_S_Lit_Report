"""
Command-line interface for prisma-s.

Two subcommands are available:

  prisma-s wizard
      Interactive guided setup.  Prompts for search terms, source location,
      batch ID, and output folder — then runs the analysis.  Best for first
      use or when running from a terminal.

  prisma-s run  [options]
      Non-interactive mode for scripting and automation.  All parameters are
      supplied as flags.

Examples
--------
# Guided interactive mode (recommended for new users)
prisma-s wizard

# Non-interactive — local folder
prisma-s run --batch batch_01 --output results/batch_01.xlsx --input /path/to/docs

# Non-interactive — Google Drive (URL or folder ID both accepted)
prisma-s run --batch batch_01 --output results/batch_01.xlsx \\
    --drive-folder "https://drive.google.com/drive/folders/1Abc123XYZ" \\
    --drive-credentials credentials.json

# Non-interactive — custom keyword dictionary
prisma-s run --batch batch_01 --output results/batch_01.xlsx \\
    --input /path/to/docs --keywords keywords/keyword_dictionary_v1.2.csv
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .runner import run_analysis


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="prisma-s",
        description=(
            "PRISMA-S keyword corpus analysis — "
            "reproducible keyword searching on PDFs and Word documents."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"prisma-s {__version__}"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ---- wizard subcommand --------------------------------------------------
    sub.add_parser(
        "wizard",
        help=(
            "Interactive setup wizard — prompts for search terms, source "
            "location, batch ID, and output folder, then runs the analysis."
        ),
    )

    # ---- run subcommand -----------------------------------------------------
    run_p = sub.add_parser(
        "run",
        help="Non-interactive batch run (all parameters as flags).",
    )
    run_p.add_argument(
        "--batch", required=True,
        help="Batch identifier written into every output row (e.g. batch_01)."
    )
    run_p.add_argument(
        "--output", required=True,
        help="Destination Excel (.xlsx) file."
    )
    run_p.add_argument(
        "--input", default=None,
        help="Local PDF/DOCX file, directory, or .zip archive."
    )
    run_p.add_argument(
        "--drive-folder", default=None, dest="drive_folder",
        help="Google Drive folder ID to download documents from."
    )
    run_p.add_argument(
        "--drive-credentials", default=None, dest="drive_credentials",
        help="Path to credentials.json for Google Drive OAuth."
    )
    run_p.add_argument(
        "--drive-token", default="token.json", dest="drive_token",
        help="Path to cache the Drive OAuth token (default: token.json)."
    )
    run_p.add_argument(
        "--keywords", default=None,
        help="Path to a custom keyword dictionary CSV (group,term columns). "
             "Defaults to the bundled keyword_dictionary_v1.1.csv."
    )

    # Also accept --drive-folder as a URL — parse out the folder ID
    from .drive import parse_folder_id

    args = parser.parse_args()

    if args.command == "wizard":
        from .wizard import run_wizard
        run_wizard()
        return

    if args.command == "run":
        try:
            # Accept full Drive URLs as well as bare folder IDs
            folder_id = parse_folder_id(args.drive_folder) if args.drive_folder else None
            df = run_analysis(
                batch_id=args.batch,
                output_xlsx=args.output,
                input_path=args.input,
                drive_folder_id=folder_id,
                drive_credentials=args.drive_credentials,
                drive_token=args.drive_token,
                keyword_csv=args.keywords,
            )
            print(f"Done — {len(df):,} rows written to {args.output}")
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
