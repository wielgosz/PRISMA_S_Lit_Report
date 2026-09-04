<#
.SYNOPSIS
    Install the prisma-s command-line tool into a private virtual environment.

.DESCRIPTION
    Finds a usable Python 3.9+ interpreter, creates a virtual environment at a
    short, stable path (%LOCALAPPDATA%\prisma-s\venv), and installs this package
    into it.

    This avoids two common Windows problems:
      * a broken / embedded Python early on PATH - some bundled interpreters (a
        GIS suite's Python, the Microsoft Store `python.exe` stub) cannot create
        a working venv ("ModuleNotFoundError: No module named 'encodings'"). Each
        candidate is verified by actually building a throwaway venv before use;
        interpreter path names are not special-cased.
      * long checkout paths - the venv lives at a short location, not under a
        deep project directory.

    Run from the repository root:
        powershell -ExecutionPolicy Bypass -File install.ps1

.NOTES
    No administrator rights required. Re-running is safe; it reuses the venv and
    force-reinstalls the package so local edits take effect.
#>
[CmdletBinding()]
param(
    [string] $VenvPath = (Join-Path $env:LOCALAPPDATA 'prisma-s\venv')
)

$ErrorActionPreference = 'Stop'
$repoRoot = $PSScriptRoot

function Test-UsablePython {
    param([string] $Exe)
    if (-not $Exe) { return $false }
    try {
        $resolved = (& $Exe -c "import sys; print(sys.executable)")
    } catch { return $false }
    if ($LASTEXITCODE -ne 0 -or -not $resolved) { return $false }
    # Python >= 3.9 with the modules a venv needs.
    & $Exe -c "import sys; sys.exit(0 if sys.version_info[:2] >= (3, 9) else 1)"
    if ($LASTEXITCODE -ne 0) { return $false }
    & $Exe -c "import encodings, venv, ensurepip"
    if ($LASTEXITCODE -ne 0) { return $false }
    # Behavioural gate: it must actually be able to create a venv. This rejects
    # embedded / stub interpreters (GIS suites, the Store stub) by what they do,
    # not by their path.
    $probe = Join-Path ([System.IO.Path]::GetTempPath()) ("prisma-s-pyprobe-" + [guid]::NewGuid().ToString('N'))
    try {
        & $Exe -m venv --without-pip $probe 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0 -and (Test-Path (Join-Path $probe 'pyvenv.cfg')))
    } finally {
        if (Test-Path $probe) { Remove-Item -Recurse -Force $probe -ErrorAction SilentlyContinue }
    }
}

function Find-Python {
    $candidates = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in @('-3.13', '-3.12', '-3.11', '-3.10', '-3.9', '-3')) {
            try { $p = (& py $v -c "import sys; print(sys.executable)") } catch { $p = $null }
            if ($LASTEXITCODE -eq 0 -and $p) { $candidates += $p }
        }
    }
    foreach ($name in @('python3', 'python')) {
        $c = Get-Command $name -ErrorAction SilentlyContinue
        if ($c) { $candidates += $c.Source }
    }
    $candidates += (Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    $candidates += @(
        (Join-Path $env:ProgramData 'miniconda3\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'miniconda3\python.exe')
    )
    foreach ($c in ($candidates | Select-Object -Unique)) {
        if ((Test-Path $c) -and (Test-UsablePython $c)) { return $c }
    }
    return $null
}

Write-Host 'Looking for a usable Python 3.9+ interpreter...'
$python = Find-Python
if (-not $python) {
    Write-Error @'
No usable Python 3.9+ interpreter was found.

Install the official build from https://www.python.org/downloads/windows/
(tick "Add python.exe to PATH"), open a new terminal, and run this script again.
'@
    exit 1
}
Write-Host "Using: $python"

if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment at $VenvPath"
    & $python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) { Write-Error "venv creation failed (exit $LASTEXITCODE)."; exit 1 }
} else {
    Write-Host "Reusing existing virtual environment at $VenvPath"
}

$venvPy = Join-Path $VenvPath 'Scripts\python.exe'
Write-Host 'Upgrading pip...'
& $venvPy -m pip install --upgrade pip --quiet
Write-Host 'Installing prisma-s (downloads pandas, pypdf, and the Google API client; can take a few minutes)...'
& $venvPy -m pip install --upgrade --force-reinstall "$repoRoot"
if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed (exit $LASTEXITCODE)."; exit 1 }

$prismaExe = Join-Path $VenvPath 'Scripts\prisma-s.exe'
Write-Host ''
Write-Host 'Installed. Verify with:'
Write-Host "    & '$prismaExe' --version"
Write-Host ''
Write-Host 'Then start the guided wizard with:'
Write-Host "    & '$prismaExe' wizard"
Write-Host ''
Write-Host "Tip: add '$(Join-Path $VenvPath 'Scripts')' to your PATH to call 'prisma-s' directly."
Write-Host "Desktop GUI: & '$(Join-Path $VenvPath 'Scripts\prisma-s-gui.exe')'"
Write-Host "Note: prisma-s reads a PDF's text layer only. OCR scanned PDFs externally first (e.g. ocrmypdf)."
