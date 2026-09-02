"""
Desktop GUI for prisma-s (``prisma-s-gui``).

A single-window Tkinter front-end over :func:`prisma_s.runner.run_analysis`.
It offers the same run as ``prisma-s run``: pick a corpus (local folder, local
file/zip, or a Google Drive folder), an output folder, a keyword dictionary, and
the figure / OCR / citation toggles, then watch the log.

The kwarg-assembly step is the module-level :func:`build_run_kwargs` so it can be
unit-tested without a display.  The Tk classes are only imported when the GUI is
actually constructed, so ``import prisma_s.gui`` works on a headless machine.
"""

from __future__ import annotations

import contextlib
import io
import os
import queue
import sys
import threading
import traceback
from pathlib import Path
from typing import Any

from .drive import parse_folder_id
from .wizard import _sanitize_batch_id

DICT_CHOICES = {
    "v13": ("Bundled v1.3 - 98 canonical terms (default)", None),
    "v11": ("Bundled v1.1 - flat term list", "bundled:1.1"),
    "custom": ("Custom CSV...", "custom"),
}


def build_run_kwargs(state: dict[str, Any]) -> dict[str, Any]:
    """Translate GUI field values into :func:`prisma_s.runner.run_analysis` kwargs.

    *state* keys: ``source_mode`` (``folder``/``file``/``drive``),
    ``source_path``, ``drive_url``, ``drive_credentials``, ``output_dir``,
    ``batch_id``, ``dict_mode`` (``v13``/``v11``/``custom``),
    ``custom_dict_path``, ``figures``, ``citation``, ``ocr``, ``ocr_lang``.

    Raises :class:`ValueError` with a user-facing message on missing/invalid
    input.
    """
    output_dir = (state.get("output_dir") or "").strip()
    if not output_dir:
        raise ValueError("Choose an output folder.")
    out = Path(output_dir)
    if not out.is_dir():
        raise ValueError(f"Output folder does not exist:\n{out}")

    batch = _sanitize_batch_id((state.get("batch_id") or "").strip() or "batch_01")

    kwargs: dict[str, Any] = {
        "batch_id": batch,
        "output_xlsx": str(out / f"{batch}_results.xlsx"),
        "emit_citation": bool(state.get("citation", True)),
        "figures": bool(state.get("figures", True)),
        "enable_ocr": bool(state.get("ocr", True)),
        "ocr_lang": (state.get("ocr_lang") or "eng").strip() or "eng",
    }

    mode = state.get("source_mode", "folder")
    if mode == "drive":
        url = (state.get("drive_url") or "").strip()
        creds = (state.get("drive_credentials") or "").strip()
        if not url:
            raise ValueError("Enter a Google Drive folder URL or ID.")
        if not creds or not Path(creds).is_file():
            raise ValueError("Choose a valid credentials.json for Google Drive.")
        kwargs["drive_folder_id"] = parse_folder_id(url)
        kwargs["drive_credentials"] = creds
    else:
        src = (state.get("source_path") or "").strip()
        if not src or not Path(src).exists():
            raise ValueError("Choose a corpus folder or file that exists.")
        kwargs["input_path"] = src

    dict_mode = state.get("dict_mode", "v13")
    if dict_mode == "custom":
        cp = (state.get("custom_dict_path") or "").strip()
        if not cp or not Path(cp).is_file():
            raise ValueError("Choose a custom keyword dictionary CSV.")
        kwargs["keyword_csv"] = cp
    else:
        kwargs["keyword_csv"] = DICT_CHOICES[dict_mode][1]

    return kwargs


# ---------------------------------------------------------------------------
# Tk application
# ---------------------------------------------------------------------------

def _run_app() -> int:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    from ._version import __version__
    from .citation import all_citations
    from .runner import run_analysis

    root = tk.Tk()
    root.title(f"PRISMA-S Lit Review {__version__}")
    root.geometry("860x640")
    root.minsize(720, 540)

    pad = {"padx": 8, "pady": 4}
    frm = ttk.Frame(root)
    frm.pack(fill="both", expand=True, padx=12, pady=12)
    frm.columnconfigure(1, weight=1)

    source_mode = tk.StringVar(value="folder")
    source_path = tk.StringVar()
    drive_url = tk.StringVar()
    drive_creds = tk.StringVar()
    output_dir = tk.StringVar()
    batch_id = tk.StringVar(value="batch_01")
    dict_mode = tk.StringVar(value="v13")
    custom_dict = tk.StringVar()
    want_figures = tk.BooleanVar(value=True)
    want_citation = tk.BooleanVar(value=True)
    want_ocr = tk.BooleanVar(value=True)
    ocr_lang = tk.StringVar(value="eng")

    row = 0
    ttk.Label(frm, text="Corpus source", font=("Segoe UI", 10, "bold")).grid(
        row=row, column=0, columnspan=3, sticky="w", **pad
    )
    row += 1
    for value, label in (
        ("folder", "Local folder"),
        ("file", "Local file or .zip"),
        ("drive", "Google Drive folder"),
    ):
        ttk.Radiobutton(frm, text=label, value=value, variable=source_mode).grid(
            row=row, column=0, columnspan=3, sticky="w", padx=20
        )
        row += 1

    def browse_source() -> None:
        if source_mode.get() == "file":
            p = filedialog.askopenfilename(
                filetypes=[("PDF / DOCX / ZIP", "*.pdf *.docx *.zip"), ("All files", "*.*")]
            )
        else:
            p = filedialog.askdirectory()
        if p:
            source_path.set(p)

    ttk.Label(frm, text="Path").grid(row=row, column=0, sticky="w", **pad)
    ttk.Entry(frm, textvariable=source_path).grid(row=row, column=1, sticky="ew", **pad)
    ttk.Button(frm, text="Browse", command=browse_source).grid(row=row, column=2, **pad)
    row += 1

    ttk.Label(frm, text="Drive URL / ID").grid(row=row, column=0, sticky="w", **pad)
    ttk.Entry(frm, textvariable=drive_url).grid(row=row, column=1, sticky="ew", **pad)
    row += 1
    ttk.Label(frm, text="credentials.json").grid(row=row, column=0, sticky="w", **pad)
    ttk.Entry(frm, textvariable=drive_creds).grid(row=row, column=1, sticky="ew", **pad)
    ttk.Button(
        frm,
        text="Browse",
        command=lambda: drive_creds.set(
            filedialog.askopenfilename(filetypes=[("JSON", "*.json")]) or drive_creds.get()
        ),
    ).grid(row=row, column=2, **pad)
    row += 1

    ttk.Separator(frm, orient="horizontal").grid(
        row=row, column=0, columnspan=3, sticky="ew", pady=8
    )
    row += 1

    ttk.Label(frm, text="Output folder").grid(row=row, column=0, sticky="w", **pad)
    ttk.Entry(frm, textvariable=output_dir).grid(row=row, column=1, sticky="ew", **pad)
    ttk.Button(
        frm,
        text="Browse",
        command=lambda: output_dir.set(filedialog.askdirectory() or output_dir.get()),
    ).grid(row=row, column=2, **pad)
    row += 1

    ttk.Label(frm, text="Batch ID").grid(row=row, column=0, sticky="w", **pad)
    ttk.Entry(frm, textvariable=batch_id).grid(row=row, column=1, sticky="ew", **pad)
    row += 1

    ttk.Label(frm, text="Keyword dictionary", font=("Segoe UI", 10, "bold")).grid(
        row=row, column=0, columnspan=3, sticky="w", **pad
    )
    row += 1
    for value in ("v13", "v11", "custom"):
        ttk.Radiobutton(
            frm, text=DICT_CHOICES[value][0], value=value, variable=dict_mode
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=20)
        row += 1
    ttk.Entry(frm, textvariable=custom_dict).grid(row=row, column=1, sticky="ew", **pad)
    ttk.Button(
        frm,
        text="Browse",
        command=lambda: custom_dict.set(
            filedialog.askopenfilename(filetypes=[("CSV", "*.csv")]) or custom_dict.get()
        ),
    ).grid(row=row, column=2, **pad)
    row += 1

    opts = ttk.Frame(frm)
    opts.grid(row=row, column=0, columnspan=3, sticky="w", **pad)
    ttk.Checkbutton(opts, text="Generate figures", variable=want_figures).pack(side="left", padx=6)
    ttk.Checkbutton(opts, text="Print citation", variable=want_citation).pack(side="left", padx=6)
    ttk.Checkbutton(opts, text="Enable OCR", variable=want_ocr).pack(side="left", padx=6)
    ttk.Label(opts, text="OCR lang").pack(side="left", padx=(12, 2))
    ttk.Entry(opts, textvariable=ocr_lang, width=10).pack(side="left")
    row += 1

    progress = ttk.Progressbar(frm, mode="indeterminate")
    progress.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)
    row += 1

    log = tk.Text(frm, height=14, wrap="word")
    log.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
    frm.rowconfigure(row, weight=1)
    row += 1

    msg_q: "queue.Queue[str]" = queue.Queue()
    state = {"running": False, "last_output": None}
    _SENTINEL = "\x00"

    def log_write(text: str) -> None:
        log.insert("end", text)
        log.see("end")

    def finish() -> None:
        state["running"] = False
        progress.stop()
        run_btn.config(state="normal")
        if state["last_output"]:
            open_btn.config(state="normal")

    def drain_queue() -> None:
        try:
            while True:
                item = msg_q.get_nowait()
                if item == _SENTINEL:
                    finish()
                else:
                    log_write(item)
        except queue.Empty:
            pass
        root.after(100, drain_queue)

    def collect_state() -> dict[str, Any]:
        return {
            "source_mode": source_mode.get(),
            "source_path": source_path.get(),
            "drive_url": drive_url.get(),
            "drive_credentials": drive_creds.get(),
            "output_dir": output_dir.get(),
            "batch_id": batch_id.get(),
            "dict_mode": dict_mode.get(),
            "custom_dict_path": custom_dict.get(),
            "figures": want_figures.get(),
            "citation": want_citation.get(),
            "ocr": want_ocr.get(),
            "ocr_lang": ocr_lang.get(),
        }

    def worker(kwargs: dict[str, Any]) -> None:
        class _Tee(io.TextIOBase):
            def write(self, s: str) -> int:  # noqa: D401
                msg_q.put(s)
                return len(s)

        tee = _Tee()
        try:
            with contextlib.redirect_stdout(tee), contextlib.redirect_stderr(tee):
                run_analysis(**kwargs)
            state["last_output"] = Path(kwargs["output_xlsx"]).parent
            msg_q.put(f"\nDone. Output written to:\n  {state['last_output']}\n")
        except Exception:
            msg_q.put("\n" + traceback.format_exc() + "\n")
        finally:
            msg_q.put(_SENTINEL)  # re-enable UI

    def on_run() -> None:
        if state["running"]:
            return
        try:
            kwargs = build_run_kwargs(collect_state())
        except ValueError as exc:
            messagebox.showerror("Check your inputs", str(exc))
            return
        state["running"] = True
        run_btn.config(state="disabled")
        open_btn.config(state="disabled")
        progress.start(12)
        log.delete("1.0", "end")
        log_write(f"Running batch {kwargs['batch_id']} ...\n\n")
        threading.Thread(target=worker, args=(kwargs,), daemon=True).start()

    def open_output() -> None:
        out = state["last_output"]
        if out and Path(out).is_dir():
            try:
                os.startfile(str(out))  # noqa: S606  (Windows only; guarded)
            except AttributeError:
                messagebox.showinfo("Output folder", str(out))

    btns = ttk.Frame(frm)
    btns.grid(row=row, column=0, columnspan=3, sticky="w", **pad)
    run_btn = ttk.Button(btns, text="Run", command=on_run)
    run_btn.pack(side="left", padx=4)
    open_btn = ttk.Button(btns, text="Open output folder", command=open_output, state="disabled")
    open_btn.pack(side="left", padx=4)
    ttk.Button(
        btns,
        text="How to cite",
        command=lambda: messagebox.showinfo("How to cite", all_citations()),
    ).pack(side="left", padx=4)
    ttk.Button(btns, text="Quit", command=root.destroy).pack(side="left", padx=4)

    root.after(100, drain_queue)
    root.mainloop()
    return 0


def main() -> None:
    """Entry point for the ``prisma-s-gui`` console script."""
    try:
        import tkinter  # noqa: F401
    except Exception:  # pragma: no cover - headless
        print(
            "prisma-s-gui needs Tkinter, which is not available in this Python.\n"
            "Use the command line instead:  prisma-s run --help",
            file=sys.stderr,
        )
        raise SystemExit(1)
    raise SystemExit(_run_app())


if __name__ == "__main__":
    main()
