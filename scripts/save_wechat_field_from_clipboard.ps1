param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('AppID', 'AppSecret', 'TemplateID', 'OpenID')]
    [string]$Field
)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $ProjectDir 'config.wechat.local.yml'
$Value = Get-Clipboard -Raw
if ([string]::IsNullOrWhiteSpace($Value)) { throw 'Clipboard is empty.' }
$Value = $Value.Trim()
if ($Value.Contains("`r") -or $Value.Contains("`n")) { throw 'Clipboard must contain one value only.' }

$Metadata = @{
    AppID      = @{ Placeholder = '<WECHAT_APP_ID>'; MinimumLength = 10; Prefix = 'wx' }
    AppSecret  = @{ Placeholder = '<WECHAT_APP_SECRET>'; MinimumLength = 16; Prefix = '' }
    TemplateID = @{ Placeholder = '<WECHAT_TEMPLATE_ID>'; MinimumLength = 10; Prefix = '' }
    OpenID     = @{ Placeholder = '<WECHAT_OPEN_ID>'; MinimumLength = 10; Prefix = '' }
}
$Rule = $Metadata[$Field]
if ($Value.Length -lt $Rule.MinimumLength) { throw "Clipboard does not look like a valid $Field." }
if ($Rule.Prefix -and -not $Value.StartsWith($Rule.Prefix)) { throw "Clipboard does not look like a valid $Field." }

$Config = [IO.File]::ReadAllText($ConfigPath, [Text.Encoding]::UTF8)
if (-not $Config.Contains($Rule.Placeholder)) {
    throw "$Field placeholder is absent; refusing to overwrite an existing value."
}
$Escaped = $Value.Replace('\', '\\').Replace('"', '\"')
$Config = $Config.Replace($Rule.Placeholder, $Escaped)
[IO.File]::WriteAllText($ConfigPath, $Config, (New-Object Text.UTF8Encoding($false)))
Write-Output "$Field saved to the ignored local configuration (value not displayed)."
