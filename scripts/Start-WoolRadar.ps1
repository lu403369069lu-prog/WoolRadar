[CmdletBinding()]
param([switch]$ForceScan, [string]$Root = 'C:\WoolRadar')
. "$PSScriptRoot\Common.ps1"
$Root = Get-WoolRadarRoot -Root $Root
Get-ScheduledTask -TaskPath '\WoolRadar\' -ErrorAction SilentlyContinue | Enable-ScheduledTask | Out-Null
$python = Get-WoolRadarPython
$logDir = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Rotate-WoolRadarLogs -LogDirectory $logDir
$log = Join-Path $logDir 'orchestrator.log'
$arguments = @('-m','core.cli','--root',$Root,'run-all')
if ($ForceScan) { $arguments += '--force' }
Push-Location $Root
try {
    & $python @arguments *>&1 | Tee-Object -FilePath $log -Append
    $scanExit = $LASTEXITCODE
    & $python -m core.cli --root $Root report *>&1 | Tee-Object -FilePath $log -Append
    if ($scanExit -ne 0) { exit $scanExit }
    exit $LASTEXITCODE
}
finally { Pop-Location }
