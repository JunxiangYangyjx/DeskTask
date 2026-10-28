param([string]$DataPath)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $DataPath) { $DataPath = Join-Path $projectRoot 'daily_tasks.json' }
$DataPath = [IO.Path]::GetFullPath($DataPath)
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Project Python environment not found.' }
$bridgeRoot = Join-Path $projectRoot 'build\outlook-native'
New-Item -ItemType Directory -Path $bridgeRoot -Force | Out-Null
$launcherPath = Join-Path $bridgeRoot 'host.cmd'
$hostScript = Join-Path $projectRoot 'scripts\outlook_native_host.py'
$launcher = "@echo off`r`n`"$pythonPath`" `"$hostScript`" %*`r`n"
[IO.File]::WriteAllText($launcherPath, $launcher, [Text.Encoding]::Default)
$config = @{ data_path = $DataPath } | ConvertTo-Json
[IO.File]::WriteAllText((Join-Path $bridgeRoot 'config.json'), $config, [Text.UTF8Encoding]::new($false))
$manifest = @{
    name = 'com.desktask.outlook'
    description = 'DeskTask webmail import'
    path = $launcherPath
    type = 'stdio'
    allowed_origins = @('chrome-extension://nmknpdikgjjjdmpcnlnehgbnbhdojkjj/')
} | ConvertTo-Json
$manifestPath = Join-Path $bridgeRoot 'com.desktask.outlook.json'
[IO.File]::WriteAllText($manifestPath, $manifest, [Text.UTF8Encoding]::new($false))
$registryPath = 'HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.desktask.outlook'
New-Item -Path $registryPath -Force | Out-Null
Set-Item -LiteralPath $registryPath -Value $manifestPath
Write-Output "Native host registered for current user. Data: $DataPath"
Write-Output "Load Chrome extension folder: $(Join-Path $projectRoot 'extensions\outlook')"
