param(
  [string]$ShortcutName = "DeskTask Dev"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Pythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$AppScript = Join-Path $ProjectRoot "src\daily_task\app.py"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "$ShortcutName.lnk"

if (-not (Test-Path $Pythonw)) {
  throw "pythonw.exe not found: $Pythonw"
}

if (-not (Test-Path $AppScript)) {
  throw "DeskTask app.py not found: $AppScript"
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Pythonw
$Shortcut.Arguments = "`"$AppScript`""
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "Open the local DeskTask development version"
$Shortcut.Save()

Write-Host "Created $ShortcutPath"
