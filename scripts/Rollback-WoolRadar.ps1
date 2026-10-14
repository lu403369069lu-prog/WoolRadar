[CmdletBinding(SupportsShouldProcess, ConfirmImpact='Medium')]
param([string]$Root = 'C:\WoolRadar')
. "$PSScriptRoot\Common.ps1"
$Root = Get-WoolRadarRoot -Root $Root
if ($PSCmdlet.ShouldProcess('\WoolRadar\*', 'Disable WoolRadar scheduled tasks and stop running task instances')) {
    & (Join-Path $Root 'scripts\Stop-WoolRadar.ps1') -DisableSchedules
}
Write-Output 'Runtime writes are limited to data, reports, and logs. Upstream repositories remain pinned under nodes\*\upstream.'
Write-Output 'No Codex, proxy, browser-profile, or system-component settings were changed.'
