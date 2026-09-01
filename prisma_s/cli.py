"""
Command-line interface for prisma-s.

Subcommands
-----------
  prisma-s wizard
      Interactive guided setup: prompts for search terms, source location,
      batch ID, and output folder, then runs the analysis.

  prisma-s run [options]
      Non-interactive batch run; all parameters as flags.

  prisma-s cite [--lang en|pt-br|es|all]
      Print the "How to cite" / attribution text.

Examples
--------
prisma-s wizard

prisma-s run --batch batch_01 --output results/batch_01.xlsx --input /path/to/docs

prisma-s run --batch batch_01 --output results/batch_01.xlsx \\
    --drive-folder "https://drive.google.com/drive/folders/1Abc123XYZ" \\
    --drive-credentials credentials.json

prisma-s run --batch batch_01 --output results/batch_01.xlsx \\
    --input /path/to/docs --keywords /path/to/keyword_dictionary_v1.2.csv
"""

from __future__ import annotations

import argparse
import sys

from ._console import enable_utf8_console
from ._version import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prisma-s",
        description=(
            "PRISMA-S keyword corpus analysis - "
            "reproducible keyword searching on PDFs and Word documents."
        ),
    )
    parser.add_argument("--version", action="version", version=f"prisma-s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "wizard",
        help=(
            "Interactive setup wizard - prompts for search terms, source "
            "location, batch ID, and output folder, then runs the analysis."
        ),
    )

    run_p = sub.add_parser("run", help="Non-interactive batch run (all parameters as flags).")
    run_p.add_argument(
        "--batch", required=True,
        help="Batch identifier written into every output row (e.g. batch_01).",
    )
    run_p.add_argument("--output", required=True, help="Destination Excel (.xlsx) file.")
    run_p.add_argument(
        "--input", default=None,
        help="Local PDF/DOCX file, directory, or .zip archive.",
    )
    run_p.add_argument(
        "--drive-folder", default=None, dest="drive_folder",
        help="Google Drive folder ID or full folder URL to download documents from.",
    )
    run_p.add_argument(
        "--drive-credentials", default=None, dest="drive_credentials",
        help="Path to credentials.json for Google Drive OAuth.",
    )
    run_p.add_argument(
        "--drive-token", default="token.json", dest="drive_token",
        help="Path to cache the Drive OAuth token (default: token.json).",
    )
    run_p.add_argument(
        "--keywords", default=None,
        help="Path to a keyword dictionary CSV (columns: group/category and term). "
             "Defaults to the bundled dictionary.",
    )
    run_p.add_argument(
        "--no-citation", action="store_true", dest="no_citation",
        help="Do not print the 'How to cite' block after the run.",
    )

    cite_p = sub.add_parser("cite", help="Print the 'How to cite' / attribution text.")
    cite_p.add_argument(
        "--lang", default="all", choices=["en", "pt-br", "es", "all"],
        help="Language to print (default: all).",
    )

    return parser


def _cmd_run(args: argparse.Namespace) -> None:
    from .drive import parse_folder_id
    from .runner import run_analysis

    folder_id = parse_folder_id(args.drive_folder) if args.drive_folder else None
    df = run_analysis(
        batch_id=args.batch,
        output_xlsx=args.output,
        input_path=args.input,
        drive_folder_id=folder_id,
        drive_credentials=args.drive_credentials,
        drive_token=args.drive_token,
        keyword_csv=args.keywords,
        emit_citation=not args.no_citation,
    )
    print(f"Done - {len(df):,} rows written to {args.output}")


def _cmd_cite(args: argparse.Namespace) -> None:
    from .citation import all_citations, citation_text

    print(all_citations() if args.lang == "all" else citation_text(args.lang))


def _cmd_wizard() -> None:
    from .wizard import run_wizard

    run_wizard()


def main() -> None:
    enable_utf8_console()
    args = _build_parser().parse_args()

    try:
        if args.command == "wizard":
            _cmd_wizard()
        elif args.command == "run":
            _cmd_run(args)
        elif args.command == "cite":
            _cmd_cite(args)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
