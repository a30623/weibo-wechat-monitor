$ProjectDir = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $ProjectDir 'run\monitor.pid'
if (-not (Test-Path -LiteralPath $PidFile)) { Write-Output 'STOPPED'; exit 1 }
$MonitorPid = [int](Get-Content -LiteralPath $PidFile -Raw)
if (Get-Process -Id $MonitorPid -ErrorAction SilentlyContinue) { Write-Output "RUNNING PID=$MonitorPid"; exit 0 }
Write-Output 'STOPPED (stale PID file)'
exit 1
