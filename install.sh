#!/usr/bin/env bash
# Install the prisma-s command-line tool into a private virtual environment.
#
# Creates a venv at ~/.local/share/prisma-s/venv and installs this package into
# it, so the tool is isolated from the system Python and lives at a short path.
#
# Usage, from the repository root:
#     ./install.sh
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv_path="${PRISMA_S_VENV:-$HOME/.local/share/prisma-s/venv}"

usable_python() {
    local exe="$1"
    command -v "$exe" >/dev/null 2>&1 || return 1
    "$exe" -c "import sys; assert sys.version_info[:2] >= (3, 9)" 2>/dev/null || return 1
    "$exe" -c "import encodings, venv, ensurepip" 2>/dev/null || return 1
    return 0
}

python=""
for c in python3.13 python3.12 python3.11 python3.10 python3.9 python3 python; do
    if usable_python "$c"; then python="$c"; break; fi
done

if [ -z "$python" ]; then
    echo "No usable Python 3.9+ found. Install Python 3 and re-run." >&2
    echo "  macOS:  brew install python@3.12" >&2
    echo "  Debian: sudo apt install python3 python3-venv" >&2
    exit 1
fi
echo "Using: $($python -c 'import sys; print(sys.executable)')"

if [ ! -d "$venv_path" ]; then
    echo "Creating virtual environment at $venv_path"
    "$python" -m venv "$venv_path"
else
    echo "Reusing existing virtual environment at $venv_path"
fi

"$venv_path/bin/python" -m pip install --upgrade pip --quiet
echo "Installing prisma-s (downloads pandas, pypdf, and the Google API client; can take a few minutes)..."
"$venv_path/bin/python" -m pip install --upgrade --force-reinstall "$repo_root"

echo
echo "Installed. Verify with:"
echo "    $venv_path/bin/prisma-s --version"
echo
echo "Then start the guided wizard with:"
echo "    $venv_path/bin/prisma-s wizard"
echo
echo "Tip: add $venv_path/bin to your PATH to call 'prisma-s' directly."
