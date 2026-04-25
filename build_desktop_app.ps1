$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$specPath = Join-Path $projectRoot "CampusFix.spec"
$distRoot = Join-Path $projectRoot "dist"
$releaseDir = Join-Path $projectRoot "portable-release\CampusFix Portable"
$packagedExe = Join-Path $distRoot "CampusFix.exe"
$portableDataDir = Join-Path $releaseDir ".campusfix-data"
$sourceDbCandidates = @(
    (Join-Path $projectRoot ".campusfix-data\campusfix.db"),
    (Join-Path $projectRoot "campusfix.db")
)
$sourceDbPath = $sourceDbCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not (Test-Path $pythonExe)) {
    throw "Virtual environment Python not found at $pythonExe"
}

if (-not (Test-Path $specPath)) {
    throw "PyInstaller spec file not found at $specPath"
}

& $pythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    $specPath

if (Test-Path $releaseDir) {
    Remove-Item -Recurse -Force $releaseDir
}

New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
Copy-Item -Force $packagedExe $releaseDir
New-Item -ItemType Directory -Force -Path $portableDataDir | Out-Null

if ($sourceDbPath) {
    Copy-Item -Force $sourceDbPath (Join-Path $portableDataDir "campusfix.db")
}

$portableReadme = @"
CampusFix Portable
==================

Files:
- CampusFix.exe : portable desktop application
- .campusfix-data\campusfix.db : bundled application data

How to use:
1. Copy this folder to another Windows laptop.
2. Double-click CampusFix.exe.
3. The app stores and updates all data in .campusfix-data next to the exe, so the folder stays self-contained.
"@

Set-Content -Path (Join-Path $releaseDir "README.txt") -Value $portableReadme
