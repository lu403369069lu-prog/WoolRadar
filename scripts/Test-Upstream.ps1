[CmdletBinding()]
param([string]$Root = 'C:\WoolRadar')
. "$PSScriptRoot\Common.ps1"
$Root = Get-WoolRadarRoot -Root $Root
$env:PYTHONUTF8 = '1'
Push-Location "$Root\nodes\digest-ai-agent\upstream"
try { & .\.venv\Scripts\python.exe -m pytest -q; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
finally { Pop-Location }
Push-Location "$Root\nodes\linuxdo-reference\upstream"
try { npm test; exit $LASTEXITCODE }
finally { Pop-Location }
