$ProjectDir = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ProjectDir 'logs'
Get-Content -LiteralPath (Join-Path $LogDir 'monitor.stderr.log') -Encoding UTF8 -Tail 100 -Wait
