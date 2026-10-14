[CmdletBinding(SupportsShouldProcess, ConfirmImpact='High')]
param(
    [switch]$ArchiveFiles,
    [ValidateSet('C:\WoolRadar')]
    [string]$ConfirmRoot = 'C:\WoolRadar'
)
$root = [System.IO.Path]::GetFullPath($ConfirmRoot)
if ($root -ne 'C:\WoolRadar') { throw "Refusing unexpected root: $root" }
if (-not $PSCmdlet.ShouldProcess($root, 'Stop and unregister WoolRadar tasks; optionally archive installation')) { return }
& (Join-Path $root 'scripts\Stop-WoolRadar.ps1') -DisableSchedules
& (Join-Path $root 'scripts\Unregister-Tasks.ps1') -Confirm:$false
if ($ArchiveFiles) {
    $archive = "C:\WoolRadar-uninstalled-$(Get-Date -Format yyyyMMdd-HHmmss)"
    if ($PSCmdlet.ShouldProcess($root, "Move installation to recoverable archive $archive")) {
        Move-Item -LiteralPath $root -Destination $archive
        Write-Output "Archived to $archive"
    }
} else {
    Write-Output 'Tasks removed; files retained. Re-run with -ArchiveFiles to move them to a recoverable archive.'
}
