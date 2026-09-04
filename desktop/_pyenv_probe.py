"""
Print facts about the running interpreter for desktop/build_exe.ps1.

Emits KEY=VALUE lines. The important one is `dll_dirs` -- a `;`-separated list
of directories that (a) exist and (b) contain at least one .dll. build_exe.ps1
prepends these to PATH and passes them to PyInstaller as --paths so the native
DLLs behind Python's C extensions (_ctypes -> ffi.dll, _bz2 -> libbz2.dll,
_tkinter -> tcl86t/tk86t.dll, ...) resolve regardless of the Python distro
(python.org, Miniconda/Anaconda, pyenv-win, ...).
"""

from __future__ import annotations

import os
import sys
import sysconfig


def _has_dll(path: str) -> bool:
    try:
        with os.scandir(path) as it:
            return any(e.is_file() and e.name.lower().endswith(".dll") for e in it)
    except OSError:
        return False


def _dll_dirs() -> list[str]:
    prefixes = {sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix}
    candidates: list[str] = []
    for p in prefixes:
        candidates += [
            p,
            os.path.join(p, "DLLs"),
            os.path.join(p, "bin"),
            os.path.join(p, "Library", "bin"),            # conda
            os.path.join(p, "Library", "mingw-w64", "bin"),  # conda
            os.path.join(p, "Library", "usr", "bin"),     # conda
        ]
    # pywin32, if present (pulled in by some Google auth stacks)
    for sp in (sysconfig.get_path("platlib"), sysconfig.get_path("purelib")):
        if sp:
            candidates.append(os.path.join(sp, "pywin32_system32"))
    # Any PATH entry that lives under one of our prefixes (covers activated
    # conda envs and unusual layouts) and holds DLLs.
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if entry and any(os.path.normcase(entry).startswith(os.path.normcase(p)) for p in prefixes):
            candidates.append(entry)

    seen: set[str] = set()
    out: list[str] = []
    for c in candidates:
        n = os.path.normcase(os.path.abspath(c))
        if n in seen:
            continue
        seen.add(n)
        if os.path.isdir(c) and _has_dll(c):
            out.append(os.path.abspath(c))
    return out


def main() -> None:
    is_conda = os.path.isdir(os.path.join(sys.base_prefix, "conda-meta"))
    print(f"executable={sys.executable}")
    print(f"version={'.'.join(map(str, sys.version_info[:3]))}")
    print(f"prefix={sys.prefix}")
    print(f"base_prefix={sys.base_prefix}")
    print(f"is_conda={'1' if is_conda else '0'}")
    print(f"is_venv={'1' if sys.prefix != sys.base_prefix else '0'}")
    print("dll_dirs=" + ";".join(_dll_dirs()))
    try:
        import tkinter  # noqa: F401

        print(f"tcl_library={os.environ.get('TCL_LIBRARY', '')}")
        print(f"tk_library={os.environ.get('TK_LIBRARY', '')}")
    except Exception as exc:  # pragma: no cover
        print(f"tkinter_error={exc}")


if __name__ == "__main__":
    main()
