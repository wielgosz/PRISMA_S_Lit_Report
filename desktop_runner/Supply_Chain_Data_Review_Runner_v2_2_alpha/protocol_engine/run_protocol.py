"""Runtime orchestration for the v2.2 Desktop Runner.

This module is intentionally usable both from the GUI and from the command
line. It prepares a runtime copy of the v2.1 protocol backend, injects the
user's input workbook values, runs the full protocol, and writes a dated
output folder.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .input_workbook_loader import (
    create_runtime_baseline_workbook,
    export_runtime_inputs,
    read_input_workbook,
    validate_input_data,
    write_issues_csv,
)

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "protocol_v2_1"
TEMPLATE = ROOT / "templates" / "Supply_Chain_Data_Review_Input_Template_v2_2.xlsx"


def _log(msg: str, callback: Optional[Callable[[str], None]] = None) -> None:
    print(msg, flush=True)
    if callback:
        callback(msg)


def create_dated_output_root(base_output: Path) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out = base_output / f"Supply_Chain_Data_Review_Output_{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    return out


def run_desktop_protocol(
    input_workbook: Path,
    pdf_folder: Path,
    output_folder: Path,
    log_callback: Optional[Callable[[str], None]] = None,
    validate_only: bool = False,
) -> Path:
    input_workbook = Path(input_workbook)
    pdf_folder = Path(pdf_folder)
    output_folder = Path(output_folder)

    run_root = create_dated_output_root(output_folder)
    logs_dir = run_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir = run_root / "_runtime"
    protocol_dir = runtime_dir / "protocol_v2_1"
    protocol_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BACKEND, protocol_dir)

    _log(f"Output folder: {run_root}", log_callback)
    _log("Reading input workbook...", log_callback)
    input_data = read_input_workbook(input_workbook)
    issues = validate_input_data(input_data, pdf_folder)
    validation_csv = run_root / "Validation_Log.csv"
    write_issues_csv(issues, validation_csv)
    export_runtime_inputs(input_data, runtime_dir / "input_workbook_exports")
    shutil.copy2(input_workbook, run_root / f"Input_Template_Validated_Copy_{datetime.now().strftime('%Y-%m-%d_%H%M')}.xlsx")

    errors = [i for i in issues if i.severity.upper() == "ERROR"]
    warnings = [i for i in issues if i.severity.upper() == "WARNING"]
    _log(f"Validation complete: {len(errors)} error(s), {len(warnings)} warning(s).", log_callback)
    if errors:
        _log(f"Blocked. See {validation_csv}", log_callback)
        return run_root
    if validate_only:
        _log("Validate-only mode complete.", log_callback)
        return run_root

    runtime_dict = runtime_dir / "input_workbook_exports" / "keyword_dictionary_v1_3.csv"
    shutil.copy2(runtime_dict, protocol_dir / "config" / "keyword_dictionary_v1_3.csv")

    baseline_v13 = protocol_dir / "outputs" / "reference_milestone" / "prisma_s_v13_complete_results_QA_metadata_visuals_2026-05-13.xlsx"
    runtime_baseline = runtime_dir / "runtime_v13_baseline_with_input_metadata.xlsx"
    create_runtime_baseline_workbook(input_data, baseline_v13, runtime_baseline)

    cmd = [
        sys.executable,
        "scripts/run_v20_full_protocol.py",
        "--input-root", str(pdf_folder),
        "--out-root", str(run_root / "protocol_outputs"),
        "--historical-v13", str(runtime_baseline),
        "--template", "examples/current_milestone/figure_template_guided_data_review_2026-05-26_v2_0_source.xlsx",
        "--dictionary", "config/keyword_dictionary_v1_3.csv",
    ]
    _log("Running protocol backend...", log_callback)
    _log(" ".join(cmd), log_callback)
    log_path = logs_dir / "protocol_run.log"
    with log_path.open("w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(cmd, cwd=protocol_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip()
            log_file.write(line + "\n")
            _log(line, log_callback)
        rc = proc.wait()

    manifest = {
        "desktop_runner_version": "2.2-alpha",
        "backend_protocol": "2.1",
        "input_workbook": str(input_workbook),
        "pdf_folder": str(pdf_folder),
        "run_root": str(run_root),
        "return_code": rc,
        "validation_errors": len(errors),
        "validation_warnings": len(warnings),
        "log_path": str(log_path),
    }
    (run_root / "desktop_run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if rc == 0:
        _log("Protocol completed successfully.", log_callback)
    else:
        _log(f"Protocol completed with return code {rc}. See logs.", log_callback)
    return run_root


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Supply Chain Data Review Protocol v2.2 desktop backend from the command line.")
    ap.add_argument("--input-workbook", required=True)
    ap.add_argument("--pdf-folder", required=True)
    ap.add_argument("--output-folder", required=True)
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()
    run_desktop_protocol(Path(args.input_workbook), Path(args.pdf_folder), Path(args.output_folder), validate_only=args.validate_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
