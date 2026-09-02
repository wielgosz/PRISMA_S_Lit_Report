# PyInstaller spec for PRISMA-S Lit Review.
#
# Build with desktop/build_exe.ps1 (which sets the env vars this spec reads):
#   PRISMA_S_BUILD_CLI = "1"   -> also emit a console prisma-s.exe in the onedir
#
# Whatever is installed in the build environment is what gets bundled.  In
# particular PyMuPDF is bundled only if `fitz` imports -- see build_exe.ps1's
# -FastPdf switch and the licensing note in desktop/README.md.

import os

from PyInstaller.utils.hooks import collect_all, collect_data_files, copy_metadata

# SPECPATH is injected by PyInstaller = the directory containing this spec.
DESKTOP_DIR = os.path.abspath(SPECPATH)  # noqa: F821
REPO = os.path.dirname(DESKTOP_DIR)

BUILD_CLI = os.environ.get("PRISMA_S_BUILD_CLI") == "1"

try:
    import fitz  # noqa: F401  (PyMuPDF)

    HAVE_FITZ = True
except Exception:
    HAVE_FITZ = False

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

for pkg in ("matplotlib", "googleapiclient", "google_auth_oauthlib"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

if HAVE_FITZ:
    d, b, h = collect_all("fitz")
    datas += d
    binaries += b
    hiddenimports += h
    _notice = os.path.join(DESKTOP_DIR, "NOTICE-AGPL.txt")
    if os.path.exists(_notice):
        datas.append((_notice, "."))

for name in ("LICENSE", "LICENSE-CC-BY-4.0.txt", "CITATION.cff"):
    p = os.path.join(REPO, name)
    if os.path.exists(p):
        datas.append((p, "."))

EXCLUDES = ["PyQt5", "PyQt6", "PySide2", "PySide6", "IPython", "pytest", "notebook"]

# ---------------------------------------------------------------------------
# GUI executable (always)
# ---------------------------------------------------------------------------
a_gui = Analysis(
    [os.path.join(DESKTOP_DIR, "launcher_gui.py")],
    pathex=[REPO],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=EXCLUDES,
    noarchive=False,
)
pyz_gui = PYZ(a_gui.pure)
exe_gui = EXE(
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
# Console CLI executable (only with -WithCli)
# ---------------------------------------------------------------------------
if BUILD_CLI:
    a_cli = Analysis(
        [os.path.join(DESKTOP_DIR, "launcher_cli.py")],
        pathex=[REPO],
        binaries=binaries,
        datas=datas,
        hiddenimports=hiddenimports,
        excludes=EXCLUDES,
        noarchive=False,
    )
    pyz_cli = PYZ(a_cli.pure)
    exe_cli = EXE(
        pyz_cli,
        a_cli.scripts,
        [],
        exclude_binaries=True,
        name="prisma-s",
        console=True,
    )
    collect += [exe_cli, a_cli.binaries, a_cli.datas]

COLLECT(*collect, strip=False, upx=False, name="PRISMA-S-Lit-Review")
