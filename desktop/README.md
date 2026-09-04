# PRISMA-S Lit Review — Windows desktop build

A standalone Windows executable of the `prisma_s` package: no Python install
required. The GUI (`prisma_s.gui`) is the front end; a run does exactly what
`prisma-s run` does.

## Build it

From the repository root, on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File desktop\build_exe.ps1 -WithCli -Zip
```

- `-WithCli` keeps the console `prisma-s.exe` in the onedir (it is always built
  for the self-test; without this switch it is deleted afterwards).
- `-Zip` also writes `dist\PRISMA-S-Lit-Review-<version>-win64.zip`.
- `-Python <path>` builds with a specific interpreter, skipping auto-discovery.

Output: `dist\PRISMA-S-Lit-Review\` — run `PRISMA-S-Lit-Review.exe`.

### How it adapts to your Python

The script works with **any** Windows Python 3.9+ distribution — python.org,
pyenv-win, Miniconda / Anaconda:

1. It ranks the interpreters it can find (preferring a python.org / pyenv
   layout), and proves each one usable by *actually building a throwaway venv*.
2. After installing the deps it runs `desktop\_pyenv_probe.py` to ask that
   interpreter **where its native DLLs live** (`ffi.dll` for `_ctypes`,
   `libbz2.dll`, `tcl86t.dll`, …). Conda keeps these in `…\Library\bin`;
   python.org keeps them in `…\DLLs`. Those directories are put on `PATH` for
   the build and passed to PyInstaller as `--paths`; the spec also force-bundles
   a small critical-DLL allowlist from them.
3. It then runs `prisma-s.exe selftest` inside the finished bundle — importing
   `ctypes`, `importlib.resources`, pandas, openpyxl, pypdf, python-docx, and
   rendering a matplotlib figure. **A bundle missing a DLL fails here, at build
   time, with the DLL named** — not when you double-click the GUI.

It **aborts** if PyMuPDF is present in the build venv (it must not be bundled).

If discovery still lands on a broken interpreter, pass `-Python` explicitly or,
for Conda, run the build from an **Anaconda Prompt** (so `Library\bin` is
already on `PATH`).

### CI (one-time setup)

A ready-made GitHub Actions workflow is checked in as
[`desktop/build-exe.workflow.yml`](build-exe.workflow.yml) — it builds this
onedir on every `v*` tag and attaches the zip to the Release. It is **not** under
`.github/workflows/` because updating workflow files needs a token with the
`workflow` scope. To enable it, once:

```bash
mkdir -p .github/workflows
cp desktop/build-exe.workflow.yml .github/workflows/build-exe.yml
git add .github/workflows/build-exe.yml && git commit -m "ci: build the Windows exe on tags" && git push
```

## Licensing

No copyleft or network-copyleft components are bundled. PDF text comes from
pypdf (BSD); there is **no PyMuPDF and no OCR**. Scanned / image-only PDFs must
be OCR'd with an external tool (e.g. `ocrmypdf`) before analysis — the run flags
any file with no or thin text.

Bundled reference texts (at the onedir root): `LICENSE` (MIT, code),
`LICENSE-CC-BY-4.0.txt` + `CITATION.cff` + `THIRD_PARTY_NOTICES.md`. Note that
`keyword_dictionary_v1.3.csv` and the protocol specs are adapted from the WRI
guidebook and their licence is **pending** — see
`_internal\prisma_s\data\DATA_LICENSE.md` in the build.

PyInstaller itself (GPL-2.0-with-exception) is a build tool and is not
redistributed; its bootloader exception permits shipping the frozen app under
this project's own licence.

## Notes for users running the .exe

- **Unsigned.** Windows SmartScreen shows "Windows protected your PC" → *More
  info* → *Run anyway*. Some antivirus engines flag PyInstaller onedir folders
  heuristically; the source and build script are in this repo.
- **Size.** ~0.4–0.7 GB unzipped (matplotlib + pandas/numpy + the Google API
  client). ~0.2–0.3 GB zipped.
- **First figure is slow** — matplotlib builds its font cache once per machine.
- Keep the whole `PRISMA-S-Lit-Review\` folder together; the `.exe` needs
  `_internal\`.
