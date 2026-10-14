[CmdletBinding()]
param([string]$Root = 'C:\WoolRadar')
. "$PSScriptRoot\Common.ps1"
$Root = Get-WoolRadarRoot -Root $Root
$python = Get-WoolRadarPython
Write-Output '## Required paths'
@('core','nodes','config\sources.yaml','data','reports','logs','scripts') | ForEach-Object {
    $path = Join-Path $Root $_
    [pscustomobject]@{Path=$path;Exists=Test-Path -LiteralPath $path}
} | Format-Table -AutoSize | Out-String | Write-Output
Write-Output '## SQLite quick check'
& $python -X utf8 -c "import sqlite3; c=sqlite3.connect(r'$Root\data\woolradar.db'); result=c.execute('pragma quick_check').fetchone()[0]; print(result); c.close(); raise SystemExit(0 if result=='ok' else 1)"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output '## Node status'
Push-Location $Root
try {
    & $python -X utf8 -m core.cli --root $Root status --summary
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally { Pop-Location }
Write-Output '## Scheduled tasks'
Get-ScheduledTask -TaskPath '\WoolRadar\' -ErrorAction SilentlyContinue | Select-Object TaskName,State | Format-Table -AutoSize | Out-String | Write-Output
Write-Output '## Relevant listening ports'
netstat -ano | Select-String -Pattern ':3000 |:3001 |:3002 |:3010 |:5432 |:8000 |:8080 |:8191 |:9222 '
