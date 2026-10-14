[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('twitter-monitor','openmagpie','digest-ai-agent','clawradar','linuxdo-monitor')]
    [string]$Node,
    [switch]$ForceScan,
    [string]$Root = 'C:\WoolRadar'
)
. "$PSScriptRoot\Common.ps1"
$Root = Get-WoolRadarRoot -Root $Root
$python = Get-WoolRadarPython -Background
$logDir = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Rotate-WoolRadarLogs -LogDirectory $logDir
$log = Join-Path $logDir "$Node.log"
$arguments = @('-X','utf8',(Join-Path $Root 'scripts\background_python.py'),'--root',$Root,'run-node',$Node)
if ($ForceScan) { $arguments += '--force' }
Push-Location $Root
try {
    $code = Invoke-WoolRadarBackgroundPython -Python $python -Arguments $arguments -Root $Root -Log $log
    exit $code
}
finally { Pop-Location }
