param(
  [string]$Version = "0.1.0-beta"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$PyInstaller = Join-Path $ProjectRoot ".venv\Scripts\pyinstaller.exe"
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"
$ReleaseDir = Join-Path $ProjectRoot "release"
$AppName = "DeskTask"

if (-not (Test-Path $Python)) {
  throw "Virtual environment not found. Create .venv and install dependencies first."
}

if (-not (Test-Path $PyInstaller)) {
  & $Python -m pip install pyinstaller
}

Remove-Item -LiteralPath $DistDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $BuildDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null

& $PyInstaller `
  --noconfirm `
  --windowed `
  --name $AppName `
  --add-data "daily_tasks.example.json;." `
  --add-data "app_settings.example.json;." `
  "src\daily_task\app.py"

Copy-Item -LiteralPath (Join-Path $ProjectRoot "README.md") -Destination (Join-Path $DistDir "$AppName\README.md") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "LICENSE") -Destination (Join-Path $DistDir "$AppName\LICENSE") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "daily_tasks.example.json") -Destination (Join-Path $DistDir "$AppName\daily_tasks.example.json") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "app_settings.example.json") -Destination (Join-Path $DistDir "$AppName\app_settings.example.json") -Force

$ZipPath = Join-Path $ReleaseDir "$AppName-$Version-win64.zip"
Remove-Item -LiteralPath $ZipPath -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $DistDir "$AppName\*") -DestinationPath $ZipPath

Write-Host "Built $ZipPath"
