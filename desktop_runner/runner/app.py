"""Supply Chain Data Review Protocol v2.2 Desktop Runner.

Tkinter desktop wrapper around the v2.1 protocol backend. The Excel input
workbook is the editable source of truth. The app validates the workbook,
runs the protocol, and writes a dated output folder.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from protocol_engine.run_protocol import run_desktop_protocol


class RunnerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Supply Chain Data Review Protocol v2.2")
        self.geometry("900x620")
        self.resizable(True, True)

        self.input_workbook = tk.StringVar()
        self.pdf_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.last_output: Path | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 5}
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Label(
            frm,
            text="Supply Chain Data Review Protocol v2.2 Desktop Runner",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", **pad)
        ttk.Label(
            frm,
            text="Use an Excel input workbook as the editable source of truth, select a PDF corpus folder, and run the protocol.",
        ).grid(row=1, column=0, columnspan=3, sticky="w", **pad)

        self._path_row(frm, 2, "Input workbook", self.input_workbook, self.browse_workbook)
        self._path_row(frm, 3, "PDF corpus folder", self.pdf_folder, self.browse_pdf_folder)
        self._path_row(frm, 4, "Output folder", self.output_folder, self.browse_output_folder)

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=3, sticky="w", **pad)
        ttk.Button(btns, text="Validate only", command=lambda: self.run(validate_only=True)).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Run protocol", command=lambda: self.run(validate_only=False)).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Open input template", command=self.open_template).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Open last output", command=self.open_last_output).pack(side="left", padx=(0, 8))

        self.progress = ttk.Progressbar(frm, mode="indeterminate")
        self.progress.grid(row=6, column=0, columnspan=3, sticky="ew", **pad)

        ttk.Label(frm, text="Run log").grid(row=7, column=0, sticky="w", **pad)
        self.log = tk.Text(frm, height=22, wrap="word")
        self.log.grid(row=8, column=0, columnspan=3, sticky="nsew", **pad)
        scroll = ttk.Scrollbar(frm, command=self.log.yview)
        scroll.grid(row=8, column=3, sticky="ns")
        self.log.configure(yscrollcommand=scroll.set)

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(8, weight=1)

    def _path_row(self, parent, row: int, label: str, var: tk.StringVar, command) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=5)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(parent, text="Browse", command=command).grid(row=row, column=2, sticky="ew", padx=8, pady=5)

    def browse_workbook(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Excel workbooks", "*.xlsx"), ("All files", "*.*")])
        if path:
            self.input_workbook.set(path)

    def browse_pdf_folder(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.pdf_folder.set(path)

    def browse_output_folder(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_folder.set(path)

    def append_log(self, text: str) -> None:
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.update_idletasks()

    def _validate_paths(self) -> bool:
        if not self.input_workbook.get() or not Path(self.input_workbook.get()).exists():
            messagebox.showerror("Missing input", "Please select an input workbook.")
            return False
        if not self.pdf_folder.get() or not Path(self.pdf_folder.get()).exists():
            messagebox.showerror("Missing input", "Please select a PDF corpus folder.")
            return False
        if not self.output_folder.get() or not Path(self.output_folder.get()).exists():
            messagebox.showerror("Missing input", "Please select an output folder.")
            return False
        return True

    def run(self, validate_only: bool = False) -> None:
        if not self._validate_paths():
            return
        self.progress.start(10)
        self.append_log("Starting validation..." if validate_only else "Starting protocol run...")

        def worker() -> None:
            try:
                out = run_desktop_protocol(
                    Path(self.input_workbook.get()),
                    Path(self.pdf_folder.get()),
                    Path(self.output_folder.get()),
                    log_callback=lambda msg: self.after(0, self.append_log, msg),
                    validate_only=validate_only,
                )
                self.last_output = out
                self.after(0, self.append_log, f"Done. Output: {out}")
            except Exception as exc:
                self.after(0, self.append_log, f"ERROR: {exc}")
                self.after(0, messagebox.showerror, "Run failed", str(exc))
            finally:
                self.after(0, self.progress.stop)

        threading.Thread(target=worker, daemon=True).start()

    def open_template(self) -> None:
        template = Path(__file__).resolve().parent / "templates" / "Supply_Chain_Data_Review_Input_Template_v2_2.xlsx"
        if template.exists():
            self._open_path(template)
        else:
            messagebox.showerror("Template missing", str(template))

    def open_last_output(self) -> None:
        if self.last_output and self.last_output.exists():
            self._open_path(self.last_output)
        else:
            messagebox.showinfo("No output yet", "No output folder is available yet.")

    @staticmethod
    def _open_path(path: Path) -> None:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])


def main() -> None:
    app = RunnerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
