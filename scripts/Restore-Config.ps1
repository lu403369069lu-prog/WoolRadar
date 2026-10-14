[CmdletBinding(SupportsShouldProcess, ConfirmImpact='Medium')]
param([Parameter(Mandatory)][string]$Backup, [string]$Root = 'C:\WoolRadar')
. "$PSScriptRoot\Common.ps1"
$Root = Get-WoolRadarRoot -Root $Root
$python = Get-WoolRadarPython
Push-Location $Root
try {
    $arguments = @('-X','utf8','-m','core.config_backup','--root',$Root,'restore','--backup',$Backup)
    if (-not $PSCmdlet.ShouldProcess($Root, 'Restore fingerprint-checked read-only public config')) { $arguments += '--dry-run' }
    & $python @arguments
    exit $LASTEXITCODE
}
finally { Pop-Location }
