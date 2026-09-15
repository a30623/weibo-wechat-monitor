$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$LogDirectory = Join-Path $ProjectDir 'logs'
$LauncherLog = Join-Path $LogDirectory 'launcher.error.log'

try {
    $Python = Join-Path $ProjectDir 'runtime\python\python.exe'
    $Config = Join-Path $ProjectDir 'config.local.yml'
    $StdoutLog = Join-Path $LogDirectory 'monitor.stdout.log'
    $StderrLog = Join-Path $LogDirectory 'monitor.stderr.log'

    if (-not (Test-Path -LiteralPath $Python)) { throw "Project Python is missing: $Python" }
    if (-not (Test-Path -LiteralPath $Config)) { throw "Private configuration is missing: $Config" }

    New-Item -ItemType Directory -Path (Join-Path $ProjectDir 'data') -Force | Out-Null
    New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
    Set-Location -LiteralPath $ProjectDir
    $env:AIO_CONFIG_FILE = $Config
    # Windows PowerShell 5 wraps native stderr as ErrorRecord objects. Keep the
    # child attached to the scheduled-task process tree, but do not treat normal
    # application logging on stderr as a terminating PowerShell error.
    $ErrorActionPreference = 'Continue'
    & $Python -u (Join-Path $ProjectDir 'main.py') 1>> $StdoutLog 2>> $StderrLog
    exit $LASTEXITCODE
} catch {
    New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
    $safeMessage = "{0:s} launcher failure: {1}: {2}" -f (Get-Date), $_.Exception.GetType().Name, $_.Exception.Message
    Add-Content -LiteralPath $LauncherLog -Value $safeMessage -Encoding UTF8
    exit 1
}
