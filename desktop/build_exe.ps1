<#
.SYNOPSIS
    Build the standalone PRISMA-S Lit Review Windows executable (PyInstaller onedir).

.DESCRIPTION
    1. Finds a usable Python (or takes -Python <path>), preferring a python.org /
       pyenv layout over Conda over anything embedded. "Usable" is proven by
       actually building a throwaway venv.
    2. Creates an isolated build venv (desktop\.build-venv) and installs
       `.[dev]` + PyInstaller.
    3. Asks that interpreter where its native DLLs live (desktop\_pyenv_probe.py)
       and prepends those directories to PATH + passes them to PyInstaller. This
       makes Conda / non-standard layouts work: ffi.dll (_ctypes), libbz2.dll
       (_bz2), tcl86t/tk86t.dll (_tkinter) resolve wherever they are.
    4. Builds, then runs `prisma-s.exe selftest` inside the bundle - imports
       ctypes, importlib.resources, pandas, openpyxl, pypdf, python-docx and
       renders a matplotlib figure. A broken bundle fails HERE with the missing
       DLL named, not when a user double-clicks the GUI.

    No copyleft components are bundled: PDF text extraction is pypdf only, there
    is no PyMuPDF / OCR.

.PARAMETER Python
    Explicit interpreter to build with (e.g. C:\Python312\python.exe). Skips
    auto-discovery.

.PARAMETER WithCli
    Keep the console prisma-s.exe in the onedir. (It is always built for the
    selftest; without this switch it is deleted afterwards.)

.PARAMETER Zip
    Also produce dist\PRISMA-S-Lit-Review-<version>-win64.zip.

.NOTES
    Run from the repository root:
        powershell -ExecutionPolicy Bypass -File desktop\build_exe.ps1 -WithCli -Zip
    No administrator rights required.
#>
[CmdletBinding()]
param(
    [string] $Python,
    [switch] $WithCli,
    [switch] $Zip
)

$ErrorActionPreference = 'Stop'
$repoRoot  = Split-Path -Parent $PSScriptRoot
$venvPath  = Join-Path $PSScriptRoot '.build-venv'
$probe     = Join-Path $PSScriptRoot '_pyenv_probe.py'

function Test-CanBuildVenv {
    param([string] $Exe)
    if (-not $Exe -or -not (Test-Path $Exe)) { return $false }
    try { $null = (& $Exe -c 'import sys' 2>$null) } catch { return $false }
    if ($LASTEXITCODE -ne 0) { return $false }
    & $Exe -c 'import sys; sys.exit(0 if sys.version_info[0:2] >= (3, 9) else 1)' 2>$null
    if ($LASTEXITCODE -ne 0) { return $false }
    & $Exe -c 'import encodings, venv, ensurepip' 2>$null
    if ($LASTEXITCODE -ne 0) { return $false }
    $t = Join-Path ([System.IO.Path]::GetTempPath()) ("pyprobe-" + [guid]::NewGuid().ToString('N'))
    try {
        & $Exe -m venv --without-pip $t 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0 -and (Test-Path (Join-Path $t 'pyvenv.cfg')))
    } finally { if (Test-Path $t) { Remove-Item -Recurse -Force $t -ErrorAction SilentlyContinue } }
}

function Get-PyRank {
    # Lower is better. python.org / pyenv layout (DLLs\ present, no conda-meta) wins.
    param([string] $Exe)
    try { $prefix = (& $Exe -c "import sys; print(sys.base_prefix)" 2>$null).Trim() } catch { return 9 }
    if (-not $prefix) { return 9 }
    $isConda = Test-Path (Join-Path $prefix 'conda-meta')
    $hasDLLs = Test-Path (Join-Path $prefix 'DLLs')
    if (-not $isConda -and $hasDLLs) { return 0 }   # python.org / pyenv
    if ($isConda)                    { return 2 }   # conda - works, DLL dirs injected
    return 1                                         # other non-conda
}

function Find-Python {
    $cands = New-Object System.Collections.Generic.List[string]
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in '-3.13','-3.12','-3.11','-3.10','-3.9','-3') {
            try { $p = (& py $v -c "import sys; print(sys.executable)" 2>$null) } catch { $p = $null }
            if ($LASTEXITCODE -eq 0 -and $p) { $cands.Add($p.Trim()) }
        }
    }
    foreach ($n in 'python','python3') {
        $c = Get-Command $n -ErrorAction SilentlyContinue
        if ($c) { $cands.Add($c.Source) }
    }
    Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue |
        ForEach-Object { $cands.Add($_.FullName) }
    Get-ChildItem "C:\Python3*\python.exe" -ErrorAction SilentlyContinue |
        ForEach-Object { $cands.Add($_.FullName) }
    $cands.Add((Join-Path $env:ProgramData 'miniconda3\python.exe'))
    $cands.Add((Join-Path $env:ProgramData 'anaconda3\python.exe'))
    $cands.Add((Join-Path $env:LOCALAPPDATA 'miniconda3\python.exe'))
    $cands.Add((Join-Path $env:LOCALAPPDATA 'anaconda3\python.exe'))

    $usable = $cands | Select-Object -Unique | Where-Object { Test-CanBuildVenv $_ }
    if (-not $usable) { return $null }
    return ($usable | Sort-Object { Get-PyRank $_ } | Select-Object -First 1)
}

# --- pick the interpreter --------------------------------------------------
if ($Python) {
    if (-not (Test-CanBuildVenv $Python)) { Write-Error "-Python '$Python' cannot build a venv (needs 3.9+ with venv/ensurepip)."; exit 1 }
    $python = $Python
} else {
    Write-Host 'Looking for a usable Python 3.9+ interpreter...'
    $python = Find-Python
    if (-not $python) {
        Write-Error @'
No usable Python 3.9+ found. Install the official build from
https://www.python.org/downloads/windows/ (tick "Add python.exe to PATH"),
open a new terminal, and re-run - or pass -Python <path> explicitly.
'@
        exit 1
    }
}
$rank = Get-PyRank $python
$flavour = @{ 0 = 'python.org / pyenv layout'; 1 = 'non-standard layout'; 2 = 'Conda (DLL dirs will be injected)' }[$rank]
Write-Host "Using: $python  [$flavour]"

# --- build venv + deps ---------------------------------------------------
if (-not (Test-Path $venvPath)) {
    & $python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { Write-Error "venv creation failed (exit $LASTEXITCODE)."; exit 1 }
}
$venvPy = Join-Path $venvPath 'Scripts\python.exe'

Write-Host 'Installing package + PyInstaller into the build venv...'
& $venvPy -m pip install --upgrade pip --quiet
& $venvPy -m pip install --upgrade --force-reinstall "$repoRoot[dev]" "pyinstaller>=6.0"
if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed (exit $LASTEXITCODE)."; exit 1 }

# Guard: never bundle an AGPL PDF engine.
& $venvPy -c "import importlib.util,sys; sys.exit(1 if importlib.util.find_spec('fitz') or importlib.util.find_spec('pymupdf') else 0)"
if ($LASTEXITCODE -ne 0) {
    Write-Error 'PyMuPDF is present in the build venv. Run: & "$venvPy" -m pip uninstall -y PyMuPDF pymupdf'
    exit 1
}

# --- probe the interpreter for its DLL directories ---------------------
Write-Host 'Probing interpreter for native DLL directories...'
$probeOut = & $venvPy -X utf8 $probe
$dllDirs = @()
foreach ($line in $probeOut) {
    if ($line -like 'dll_dirs=*') {
        $dllDirs = ($line.Substring(9) -split ';') | Where-Object { $_ }
    }
    Write-Host "  $line"
}
# The .spec reads PRISMA_S_DLL_DIRS: it adds them to Analysis(pathex=...) and
# force-bundles a critical-DLL allowlist from them. (`--paths` on the command
# line is a makespec-only option and is rejected when a .spec is given.)
if ($dllDirs) {
    $env:PATH = ($dllDirs -join ';') + ';' + $env:PATH
    $env:PRISMA_S_DLL_DIRS = ($dllDirs -join ';')
    Write-Host "Prepended $($dllDirs.Count) DLL dir(s) to PATH and PRISMA_S_DLL_DIRS for the build."
}

# --- clear stale build output before PyInstaller does (loudly, with retry) --
# A previous run's exe (or antivirus, or an open Explorer window) can hold a
# file in dist\ / build\ locked for a moment. `Remove-Item -ErrorAction
# SilentlyContinue` would hide that and let PyInstaller's own cleanup fail
# deep inside COLLECT with a confusing WinError 32. Do it here, loudly.
function Remove-DirRetry {
    param([string] $Path, [int] $Retries = 6, [int] $DelayMs = 1000)
    if (-not (Test-Path $Path)) { return }
    for ($i = 1; $i -le $Retries; $i++) {
        try { Remove-Item -Recurse -Force $Path -ErrorAction Stop; return }
        catch {
            if ($i -eq $Retries) {
                Write-Error @"
Could not remove '$Path' - a file inside it is locked by another process.
Common causes: the built app (PRISMA-S-Lit-Review.exe / prisma-s.exe) is still
running - check Task Manager - an Explorer window has that folder open, or
antivirus is scanning it. Close those and re-run.
Underlying error: $($_.Exception.Message)
"@
                exit 1
            }
            Write-Host "  '$Path' is locked, retrying in ${DelayMs}ms... ($i/$Retries)"
            Start-Sleep -Milliseconds $DelayMs
        }
    }
}

Get-Process -Name 'PRISMA-S-Lit-Review', 'prisma-s' -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue
Remove-DirRetry (Join-Path $repoRoot 'dist')
Remove-DirRetry (Join-Path $repoRoot 'build')

# --- build (always with the CLI, for the selftest) --------------------
$env:PRISMA_S_BUILD_CLI = '1'
Push-Location $repoRoot
try {
    & $venvPy -m PyInstaller --clean --noconfirm (Join-Path $PSScriptRoot 'prisma-s.spec')
    if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller failed (exit $LASTEXITCODE)."; exit 1 }
} finally { Pop-Location }

$distDir = Join-Path $repoRoot 'dist\PRISMA-S-Lit-Review'
$cliExe  = Join-Path $distDir 'prisma-s.exe'

# --- verify the artifact ---------------------------------------------
Write-Host ''
Write-Host 'Verifying the built bundle (prisma-s.exe selftest)...'
$out = & $cliExe selftest 2>&1
$ok = ($LASTEXITCODE -eq 0)
$out | ForEach-Object { Write-Host "  $_" }
if (-not $ok) {
    Write-Error @"
The built executable is broken - the bundle is missing a native DLL or data
file (see the error above; a 'DLL load failed while importing _ctypes' means
ffi.dll was not found). This usually means the build Python's DLL directories
were not discovered. Try: -Python <a python.org install>, or open an
'Anaconda Prompt' (so Conda's Library\bin is on PATH) and re-run.
"@
    exit 1
}
& $cliExe --version | ForEach-Object { Write-Host "  $_" }

if (-not $WithCli) {
    Remove-Item $cliExe -Force
    Write-Host 'Removed prisma-s.exe (pass -WithCli to keep it).'
}

$sizeMB = [math]::Round((Get-ChildItem $distDir -Recurse | Measure-Object Length -Sum).Sum / 1MB, 0)
Write-Host ''
Write-Host "Built OK: $distDir  (~$sizeMB MB)"
Write-Host "  GUI: $distDir\PRISMA-S-Lit-Review.exe"
if ($WithCli) { Write-Host "  CLI: $cliExe" }

if ($Zip) {
    $version = (& $venvPy -c "import prisma_s; print(prisma_s.__version__)").Trim()
    $zipPath = Join-Path $repoRoot "dist\PRISMA-S-Lit-Review-$version-win64.zip"
    if (Test-Path $zipPath) { Remove-Item $zipPath }
    Compress-Archive -Path $distDir -DestinationPath $zipPath
    Write-Host "  Zip: $zipPath"
}
