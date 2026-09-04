# PRISMA-S Lit Review — Windows desktop build

A standalone Windows executable of the `prisma_s` package: no Python install
required. The GUI (`prisma_s.gui`) is the front end; a run does exactly what
`prisma-s run` does.

## Build it

From the repository root, on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File desktop\build_exe.ps1 -WithCli -Zip
```

- `-WithCli` also puts a console `prisma-s.exe` inside the onedir folder
  (used for the acceptance diff; handy for scripting).
- `-Zip` also writes `dist\PRISMA-S-Lit-Review-<version>-win64.zip`.

Output: `dist\PRISMA-S-Lit-Review\` — run `PRISMA-S-Lit-Review.exe`.

The script builds in an isolated venv (`desktop\.build-venv`), installs
`.[dev]` + PyInstaller, and runs `desktop\prisma-s.spec`. It **aborts** if
PyMuPDF is present in the build venv.

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
