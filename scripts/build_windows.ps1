param(
  [string]$Version = "0.1.3-beta"
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
  --clean `
  --windowed `
  --name $AppName `
  --add-data "daily_tasks.example.json;." `
  --add-data "app_settings.example.json;." `
  --hidden-import PySide6.QtCore `
  --hidden-import PySide6.QtGui `
  --hidden-import PySide6.QtWidgets `
  "src\daily_task\app.py"

$AppDistDir = Join-Path $DistDir $AppName

Copy-Item -LiteralPath (Join-Path $ProjectRoot "README.md") -Destination (Join-Path $AppDistDir "README.md") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "README.zh-CN.md") -Destination (Join-Path $AppDistDir "README.zh-CN.md") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "LICENSE") -Destination (Join-Path $AppDistDir "LICENSE") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "daily_tasks.example.json") -Destination (Join-Path $AppDistDir "daily_tasks.example.json") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "app_settings.example.json") -Destination (Join-Path $AppDistDir "app_settings.example.json") -Force

$SmokeLog = Join-Path $AppDistDir "desktask_smoke_test_error.log"
Remove-Item -LiteralPath $SmokeLog -Force -ErrorAction SilentlyContinue
$Smoke = Start-Process -FilePath (Join-Path $AppDistDir "$AppName.exe") -ArgumentList "--gui-smoke-test" -WorkingDirectory $AppDistDir -PassThru -WindowStyle Hidden
if (-not $Smoke.WaitForExit(30000)) {
  Stop-Process -Id $Smoke.Id -Force
  throw "GUI smoke test timed out."
}
if ($Smoke.ExitCode -ne 0) {
  if (Test-Path $SmokeLog) {
    Get-Content $SmokeLog
  }
  throw "GUI smoke test failed with exit code $($Smoke.ExitCode)."
}
Remove-Item -LiteralPath $SmokeLog -Force -ErrorAction SilentlyContinue

$ZipPath = Join-Path $ReleaseDir "$AppName-$Version-win64.zip"
$PackageDir = Join-Path $ReleaseDir "$AppName-$Version-win64"
Remove-Item -LiteralPath $ZipPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $PackageDir -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $AppDistDir -Destination $PackageDir -Recurse
Compress-Archive -Path $PackageDir -DestinationPath $ZipPath
Remove-Item -LiteralPath $PackageDir -Recurse -Force

Write-Host "Built $ZipPath"
