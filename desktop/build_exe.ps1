<#
.SYNOPSIS
    Build the standalone PRISMA-S Lit Review Windows executable (PyInstaller onedir).

.DESCRIPTION
    Creates an isolated build venv under desktop\.build-venv, installs the
    package (`pip install -e ".[dev]"`) plus PyInstaller, and runs
    desktop\prisma-s.spec. The result is dist\PRISMA-S-Lit-Review\.

    No copyleft components are bundled: PDF text extraction is pypdf only, there
    is no PyMuPDF / OCR. The distributable is MIT (code) with CC BY 4.0 data/docs
    (see THIRD_PARTY_NOTICES.md and prisma_s\data\DATA_LICENSE.md).

.PARAMETER WithCli
    Also emit a console prisma-s.exe inside the onedir (used for the acceptance
    diff; optional for end users).

.PARAMETER Zip
    Also produce dist\PRISMA-S-Lit-Review-<version>-win64.zip.

.NOTES
    Run from the repository root:
        powershell -ExecutionPolicy Bypass -File desktop\build_exe.ps1 -WithCli -Zip
#>
[CmdletBinding()]
param(
    [switch] $WithCli,
    [switch] $Zip
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $PSScriptRoot '.build-venv'

function Test-UsablePython {
    param([string] $Exe)
    if (-not $Exe) { return $false }
    try { $null = (& $Exe -c "import sys; print(sys.executable)") } catch { return $false }
    if ($LASTEXITCODE -ne 0) { return $false }
    & $Exe -c "import sys; sys.exit(0 if sys.version_info[:2] >= (3, 9) else 1)"
    if ($LASTEXITCODE -ne 0) { return $false }
    & $Exe -c "import encodings, venv, ensurepip"
    if ($LASTEXITCODE -ne 0) { return $false }
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
if (-not $python) { Write-Error 'No usable Python 3.9+ found. Install python.org build and retry.'; exit 1 }
Write-Host "Using: $python"

if (-not (Test-Path $venvPath)) {
    & $python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { Write-Error "venv creation failed (exit $LASTEXITCODE)."; exit 1 }
}
$venvPy = Join-Path $venvPath 'Scripts\python.exe'

Write-Host 'Installing package + PyInstaller into the build venv...'
& $venvPy -m pip install --upgrade pip --quiet
& $venvPy -m pip install --upgrade --force-reinstall "$repoRoot[dev]" "pyinstaller>=6.0"
if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed (exit $LASTEXITCODE)."; exit 1 }

# Guard: the build must not pick up an AGPL PDF engine.
& $venvPy -c "import importlib.util,sys; sys.exit(1 if importlib.util.find_spec('fitz') or importlib.util.find_spec('pymupdf') else 0)"
if ($LASTEXITCODE -ne 0) {
    Write-Error 'PyMuPDF is present in the build venv. Remove it (pip uninstall PyMuPDF) - v1.6.0 ships pypdf-only and must not bundle AGPL code.'
    exit 1
}

if ($WithCli) { $env:PRISMA_S_BUILD_CLI = '1' } else { Remove-Item Env:\PRISMA_S_BUILD_CLI -ErrorAction SilentlyContinue }

Push-Location $repoRoot
try {
    & $venvPy -m PyInstaller --clean --noconfirm (Join-Path $PSScriptRoot 'prisma-s.spec')
    if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller failed (exit $LASTEXITCODE)."; exit 1 }
} finally {
    Pop-Location
}

$distDir = Join-Path $repoRoot 'dist\PRISMA-S-Lit-Review'
$sizeMB = [math]::Round((Get-ChildItem $distDir -Recurse | Measure-Object Length -Sum).Sum / 1MB, 0)
Write-Host ''
Write-Host "Built: $distDir  (~$sizeMB MB)"
Write-Host "  GUI: $distDir\PRISMA-S-Lit-Review.exe"
if ($WithCli) { Write-Host "  CLI: $distDir\prisma-s.exe" }

if ($Zip) {
    $version = (& $venvPy -c "import prisma_s; print(prisma_s.__version__)").Trim()
    $zipPath = Join-Path $repoRoot "dist\PRISMA-S-Lit-Review-$version-win64.zip"
    if (Test-Path $zipPath) { Remove-Item $zipPath }
    Compress-Archive -Path $distDir -DestinationPath $zipPath
    Write-Host "  Zip: $zipPath"
}
