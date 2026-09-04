# PyInstaller spec for PRISMA-S Lit Review (onedir, GUI).
#
# Build with desktop/build_exe.ps1. Environment variables it may set:
#   PRISMA_S_BUILD_CLI = "1"   -> also emit a console prisma-s.exe in the onedir
#
# No copyleft components. PDF text extraction is pypdf (BSD); there is no
# PyMuPDF / OCR. Whatever is installed in the build venv is bundled -- keep that
# venv to `pip install -e ".[dev]"` + pyinstaller only.

import os

from PyInstaller.utils.hooks import collect_all, collect_data_files, copy_metadata

# SPECPATH is injected by PyInstaller = the directory containing this spec.
DESKTOP_DIR = os.path.abspath(SPECPATH)  # noqa: F821
REPO = os.path.dirname(DESKTOP_DIR)

BUILD_CLI = os.environ.get("PRISMA_S_BUILD_CLI") == "1"

# ---------------------------------------------------------------------------
# Shared data / hidden imports
# ---------------------------------------------------------------------------
datas = []
binaries = []
hiddenimports = ["matplotlib.backends.backend_agg", "pypdf"]

# The package's own data tree (dictionaries, protocol specs, citation/*.md) and
# its installed metadata, so importlib.resources works frozen.
datas += collect_data_files("prisma_s")
datas += copy_metadata("prisma-s-lit-review")

# matplotlib (mpl-data + fonts) and the lazily-imported Google Drive stack.
for pkg in ("matplotlib", "googleapiclient", "google_auth_oauthlib", "google_auth_httplib2"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Reference texts placed at the onedir root for the user.
for name in (
    "LICENSE",
    "LICENSE-CC-BY-4.0.txt",
    "CITATION.cff",
    "THIRD_PARTY_NOTICES.md",
):
    p = os.path.join(REPO, name)
    if os.path.exists(p):
        datas.append((p, "."))

EXCLUDES = [
    "PyQt5", "PyQt6", "PySide2", "PySide6", "IPython", "pytest", "notebook",
    "tkinter.test", "test",
]


def _analysis(script):
    return Analysis(  # noqa: F821
        [os.path.join(DESKTOP_DIR, script)],
        pathex=[REPO],
        binaries=binaries,
        datas=datas,
        hiddenimports=hiddenimports,
        excludes=EXCLUDES,
        noarchive=False,
    )


# ---------------------------------------------------------------------------
# GUI executable (always) -- windowed, no console
# ---------------------------------------------------------------------------
a_gui = _analysis("launcher_gui.py")
pyz_gui = PYZ(a_gui.pure)  # noqa: F821
exe_gui = EXE(  # noqa: F821
    pyz_gui,
    a_gui.scripts,
    [],
    exclude_binaries=True,
    name="PRISMA-S-Lit-Review",
    console=False,
    disable_windowed_traceback=False,
)
collect = [exe_gui, a_gui.binaries, a_gui.datas]

# ---------------------------------------------------------------------------
# Console CLI executable (only with -WithCli / PRISMA_S_BUILD_CLI=1)
# ---------------------------------------------------------------------------
if BUILD_CLI:
    a_cli = _analysis("launcher_cli.py")
    pyz_cli = PYZ(a_cli.pure)  # noqa: F821
    exe_cli = EXE(  # noqa: F821
        pyz_cli,
        a_cli.scripts,
        [],
        exclude_binaries=True,
        name="prisma-s",
        console=True,
    )
    collect += [exe_cli, a_cli.binaries, a_cli.datas]

COLLECT(*collect, strip=False, upx=False, name="PRISMA-S-Lit-Review")  # noqa: F821
