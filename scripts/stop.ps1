$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $ProjectDir 'run\monitor.pid'
if (-not (Test-Path -LiteralPath $PidFile)) { Write-Output 'Not running (no PID file).'; exit 0 }
$MonitorPid = [int](Get-Content -LiteralPath $PidFile -Raw)
$Process = Get-Process -Id $MonitorPid -ErrorAction SilentlyContinue
if ($Process) { Stop-Process -Id $MonitorPid; $Process.WaitForExit(10000) }
Remove-Item -LiteralPath $PidFile -Force
Write-Output 'Stopped.'
