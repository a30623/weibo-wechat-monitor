param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Cookie', 'SendKey')]
    [string]$Field
)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $ProjectDir 'config.local.yml'
$Secret = Get-Clipboard -Raw
if ([string]::IsNullOrWhiteSpace($Secret)) { throw 'Clipboard is empty.' }
$Secret = $Secret.Trim()
if ($Secret.Contains("`r") -or $Secret.Contains("`n")) { throw 'Clipboard must contain a single value.' }

$Placeholder = if ($Field -eq 'Cookie') { '<WEIBO_COOKIE>' } else { '<SERVERCHAN_SENDKEY>' }
if ($Field -eq 'Cookie' -and -not $Secret.Contains('=')) { throw 'Clipboard does not look like a Cookie value.' }
if ($Field -eq 'SendKey' -and $Secret.Length -lt 10) { throw 'Clipboard does not look like a SendKey.' }

$Config = [IO.File]::ReadAllText($ConfigPath, [Text.Encoding]::UTF8)
if (-not $Config.Contains($Placeholder)) { throw "$Field placeholder is absent; refusing to overwrite an existing secret." }
# YAML double-quoted scalar escaping. Cookie and SendKey normally need neither,
# but escaping makes the helper fail-safe for unexpected characters.
$Escaped = $Secret.Replace('\', '\\').Replace('"', '\"')
$Config = $Config.Replace($Placeholder, $Escaped)
[IO.File]::WriteAllText($ConfigPath, $Config, (New-Object Text.UTF8Encoding($false)))
Write-Output "$Field saved to the ignored local configuration (value not displayed)."
