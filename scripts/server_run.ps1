$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectDir 'runtime\python\python.exe'
$Config = Join-Path $ProjectDir 'config.local.yml'
$StdoutLog = Join-Path $ProjectDir 'logs\monitor.stdout.log'
$StderrLog = Join-Path $ProjectDir 'logs\monitor.stderr.log'

if (-not (Test-Path -LiteralPath $Python)) { throw "Project Python is missing: $Python" }
if (-not (Test-Path -LiteralPath $Config)) { throw "Private configuration is missing: $Config" }

New-Item -ItemType Directory -Path (Join-Path $ProjectDir 'data') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $ProjectDir 'logs') -Force | Out-Null
Set-Location -LiteralPath $ProjectDir
$env:AIO_CONFIG_FILE = $Config
& $Python -u (Join-Path $ProjectDir 'main.py') 1>> $StdoutLog 2>> $StderrLog
exit $LASTEXITCODE
