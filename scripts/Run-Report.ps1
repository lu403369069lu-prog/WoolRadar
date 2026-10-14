[CmdletBinding()]
param([string]$Root = 'C:\WoolRadar', [int64]$MaxLogBytes = 10MB)
. "$PSScriptRoot\Common.ps1"
$Root = Get-WoolRadarRoot -Root $Root
$python = Get-WoolRadarPython -Background
$logDir = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Rotate-WoolRadarLogs -LogDirectory $logDir -MaxBytes $MaxLogBytes
$log = Join-Path $logDir 'report.log'
Push-Location $Root
try {
    $arguments = @('-X','utf8',(Join-Path $Root 'scripts\background_python.py'),'--root',$Root,'report')
    $code = Invoke-WoolRadarBackgroundPython -Python $python -Arguments $arguments -Root $Root -Log $log
    exit $code
}
finally { Pop-Location }
