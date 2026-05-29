param(
  [string]$Version = "0.1.3-beta",
  [string]$VersionInfo = "0.1.3.0",
  [switch]$SkipAppBuild
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$InnoScript = Join-Path $ProjectRoot "installer\DeskTask.iss"
$ReleaseDir = Join-Path $ProjectRoot "release"

function Find-Iscc {
  $command = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }

  $candidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
  )
  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  throw "Inno Setup compiler not found. Install it with: winget install --id JRSoftware.InnoSetup -e"
}

if (-not $SkipAppBuild) {
  & (Join-Path $PSScriptRoot "build_windows.ps1") -Version $Version
}

$Iscc = Find-Iscc
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null

& $Iscc `
  "/DMyAppVersion=$Version" `
  "/DMyAppVersionInfo=$VersionInfo" `
  $InnoScript

$InstallerPath = Join-Path $ReleaseDir "DeskTaskSetup-$Version.exe"
if (-not (Test-Path $InstallerPath)) {
  throw "Installer was not created: $InstallerPath"
}

Write-Host "Built $InstallerPath"
