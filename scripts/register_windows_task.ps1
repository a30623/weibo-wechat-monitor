param(
    [string]$TaskName = 'WeiboWechatMonitor'
)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $PSScriptRoot 'server_run.ps1'
if (-not (Test-Path -LiteralPath $Runner)) { throw "Runner is missing: $Runner" }

$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`""
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments -WorkingDirectory $ProjectDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description 'Monitor public Weibo updates and notify through WeChat Official Account.' `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName
Write-Output "Scheduled task registered and started: $TaskName"
