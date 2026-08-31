<#
.SYNOPSIS
    Install the prisma-s command-line tool into a private virtual environment.

.DESCRIPTION
    Finds a usable Python interpreter, creates a virtual environment at a short,
    stable path (%LOCALAPPDATA%\prisma-s\venv), and installs this package into it.

    This avoids two common Windows problems:
      * a broken / embedded Python early on PATH (e.g. one shipped inside QGIS or
        the Microsoft Store stub) that cannot create a working venv
        ("ModuleNotFoundError: No module named 'encodings'");
      * long checkout paths - the venv lives at a short location, not under a
        deep project directory.

    Run from the repository root:
        powershell -ExecutionPolicy Bypass -File install.ps1

.NOTES
    No administrator rights required. Re-running is safe; it reuses the venv.
#>
[CmdletBinding()]
param(
    [string] $VenvPath = (Join-Path $env:LOCALAPPDATA 'prisma-s\venv')
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-UsablePython {
    param([string] $Exe)
    if (-not $Exe) { return $false }
    try {
        $resolved = (& $Exe -c "import sys; print(sys.executable)" 2>$null)
    } catch { return $false }
    if (-not $resolved) { return $false }
    if ($resolved -match 'QGIS' -or $resolved -match '\\WindowsApps\\') { return $false }
    # Must be able to build a venv and bootstrap pip.
    & $Exe -c "import encodings, venv, ensurepip" 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Find-Python {
    $candidates = @()
    # The py launcher is the most reliable pointer to a real python.org install.
    $pyLauncher = (Get-Command py -ErrorAction SilentlyContinue)
    if ($pyLauncher) {
        foreach ($v in @('-3.12', '-3.11', '-3.10', '-3.9', '-3')) {
            $p = (& py $v -c "import sys; print(sys.executable)" 2>$null)
            if ($p) { $candidates += $p }
        }
    }
    foreach ($name in @('python3', 'python')) {
        $c = (Get-Command $name -ErrorAction SilentlyContinue)
        if ($c) { $candidates += $c.Source }
    }
    $candidates += (Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    $candidates += @('C:\ProgramData\miniconda3\python.exe', "$env:LOCALAPPDATA\miniconda3\python.exe")

    foreach ($c in ($candidates | Select-Object -Unique)) {
        if (Test-Path $c) {
            if (Test-UsablePython $c) { return $c }
        }
    }
    return $null
}

Write-Host 'Looking for a usable Python interpreter...'
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
} else {
    Write-Host "Reusing existing virtual environment at $VenvPath"
}

$venvPy = Join-Path $VenvPath 'Scripts\python.exe'
Write-Host 'Upgrading pip...'
& $venvPy -m pip install --upgrade pip --quiet
Write-Host 'Installing prisma-s (this downloads pandas, PyMuPDF, and the Google API client; it can take a few minutes)...'
& $venvPy -m pip install "$repoRoot"

$prismaExe = Join-Path $VenvPath 'Scripts\prisma-s.exe'
Write-Host ''
Write-Host 'Installed. Verify with:'
Write-Host "    & '$prismaExe' --version"
Write-Host ''
Write-Host 'Then start the guided wizard with:'
Write-Host "    & '$prismaExe' wizard"
Write-Host ''
Write-Host "Tip: add '$($VenvPath)\Scripts' to your PATH to call 'prisma-s' directly."
