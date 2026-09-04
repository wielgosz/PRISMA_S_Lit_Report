# Installing `prisma-s`

`prisma-s` is a normal Python package. You need **Python 3.9 or newer**.

## Quick install (recommended)

From the repository root:

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

**macOS / Linux**

```bash
./install.sh
```

The script finds a usable Python, creates a private virtual environment
(`%LOCALAPPDATA%\prisma-s\venv` on Windows, `~/.local/share/prisma-s/venv`
elsewhere), and installs the package into it. When it finishes it prints the
full path to the `prisma-s` command.

Verify:

```
prisma-s --version
```

Start the guided run:

```
prisma-s wizard
```

## Manual install

```bash
python -m venv .venv
.venv/Scripts/python -m pip install .      # Windows
# .venv/bin/python -m pip install .        # macOS / Linux
```

## Cloning on Windows

A few files in the `desktop_runner/` and `protocols/` trees have long names.
If `git clone` reports **"Filename too long"**, enable long paths once:

```bash
git config --global core.longpaths true
```

then clone again. (This is not needed for the `prisma_s` package itself.)

## Troubleshooting

**`ModuleNotFoundError: No module named 'encodings'` when creating the venv.**
Your `python` on `PATH` is a broken or embedded interpreter - some bundled
Pythons (those shipped inside GIS/desktop suites, or the Microsoft Store
`python.exe` stub) cannot create a venv. `install.ps1` verifies each candidate
by actually building a throwaway venv and skips any that fail. To fix it
manually, install the official build from
<https://www.python.org/downloads/windows/> (tick *Add python.exe to PATH*),
open a new terminal, and use `py -3 -m venv .venv`.

**`'charmap' codec can't encode character` while printing.**
Fixed in this version - the CLI switches its output to UTF-8 on start-up. If you
still hit it in an embedded context, set the environment variable
`PYTHONUTF8=1`.

**Non-English keyword dictionaries.**
Save the CSV as UTF-8. Accented terms (e.g. `ação`, `região`, `análisis`) match
case-insensitively and print correctly.
