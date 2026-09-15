param(
    [string]$TaskName = 'WeiboWechatMonitor'
)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $PSScriptRoot 'server_run.cmd'
if (-not (Test-Path -LiteralPath $Runner)) { throw "Runner is missing: $Runner" }

$arguments = "/d /c `"$Runner`""
$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument $arguments -WorkingDirectory $ProjectDir
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
