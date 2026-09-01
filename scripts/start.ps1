$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectDir '.venv\Scripts\python.exe'
$ConfigFile = Join-Path $ProjectDir 'config.local.yml'
$RunDir = Join-Path $ProjectDir 'run'
$LogDir = Join-Path $ProjectDir 'logs'
$PidFile = Join-Path $RunDir 'monitor.pid'

if (-not (Test-Path -LiteralPath $PythonExe)) { throw 'Project virtual environment is missing.' }
$env:PYTHONUTF8 = '1'
& $PythonExe (Join-Path $PSScriptRoot 'preflight.py') $ConfigFile
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

New-Item -ItemType Directory -Force -Path $RunDir, $LogDir, (Join-Path $ProjectDir 'data') | Out-Null
if (Test-Path -LiteralPath $PidFile) {
    $ExistingPid = [int](Get-Content -LiteralPath $PidFile -Raw)
    if (Get-Process -Id $ExistingPid -ErrorAction SilentlyContinue) {
        Write-Output "Already running. PID=$ExistingPid"
        exit 0
    }
}

$env:AIO_CONFIG_FILE = $ConfigFile
$Process = Start-Process -FilePath $PythonExe -ArgumentList '-u', (Join-Path $ProjectDir 'main.py') `
    -WorkingDirectory $ProjectDir -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $LogDir 'monitor.stdout.log') `
    -RedirectStandardError (Join-Path $LogDir 'monitor.stderr.log')
Set-Content -LiteralPath $PidFile -Value $Process.Id -Encoding ascii
Start-Sleep -Seconds 2
if (-not (Get-Process -Id $Process.Id -ErrorAction SilentlyContinue)) { throw 'Process exited immediately; inspect logs.' }
Write-Output "Started. PID=$($Process.Id)"
