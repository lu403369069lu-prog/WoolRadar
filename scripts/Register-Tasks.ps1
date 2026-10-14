[CmdletBinding()]
param([string]$Root = 'C:\WoolRadar')
. "$PSScriptRoot\Common.ps1"
$Root = Get-WoolRadarRoot -Root $Root
& "$PSScriptRoot\Build-HiddenLauncher.ps1" -Root $Root | Out-Null
$python = Get-WoolRadarPython
$taskPath = '\WoolRadar\'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5) -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20)

function Register-WoolRadarNodeTask {
    param([string]$Name, [string]$Node, [System.Collections.Generic.List[Microsoft.Management.Infrastructure.CimInstance]]$Triggers)
    $launcher = Join-Path $Root 'scripts\Run-Hidden.exe'
    $action = New-ScheduledTaskAction -Execute $launcher -Argument "node $Node `"$Root`"" -WorkingDirectory $Root
    Register-ScheduledTask -TaskName $Name -TaskPath $taskPath -Action $action -Trigger $Triggers.ToArray() -Settings $settings -Description "WoolRadar 7.1 read-only collector: $Node" -RunLevel Limited -Force | Out-Null
}

$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$logon = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
$start = (Get-Date).AddMinutes(5)
$every30 = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
$every60 = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Minutes 60) -RepetitionDuration (New-TimeSpan -Days 3650)
$twice = [System.Collections.Generic.List[Microsoft.Management.Infrastructure.CimInstance]]::new()
$twice.Add((New-ScheduledTaskTrigger -Daily -At '08:00'))
$twice.Add((New-ScheduledTaskTrigger -Daily -At '20:00'))
$twice.Add($logon)

foreach ($spec in @(
    @{Name='TwitterMonitor';Node='twitter-monitor';Trigger=$every30},
    @{Name='OpenMagpie';Node='openmagpie';Trigger=$every60},
    @{Name='ClawRadar';Node='clawradar';Trigger=$every30},
    @{Name='LinuxDoMonitor';Node='linuxdo-monitor';Trigger=$every30}
)) {
    $triggers = [System.Collections.Generic.List[Microsoft.Management.Infrastructure.CimInstance]]::new()
    $triggers.Add($logon)
    $triggers.Add($spec.Trigger)
    Register-WoolRadarNodeTask -Name $spec.Name -Node $spec.Node -Triggers $triggers
}
Register-WoolRadarNodeTask -Name 'DigestAIAgent' -Node 'digest-ai-agent' -Triggers $twice

$reportLauncher = Join-Path $Root 'scripts\Run-Hidden.exe'
$reportAction = New-ScheduledTaskAction -Execute $reportLauncher -Argument "report `"$Root`"" -WorkingDirectory $Root
$reportTriggers = @((New-ScheduledTaskTrigger -Daily -At '08:30'), (New-ScheduledTaskTrigger -Daily -At '20:30'))
Register-ScheduledTask -TaskName 'ChineseReport' -TaskPath $taskPath -Action $reportAction -Trigger $reportTriggers -Settings $settings -Description 'WoolRadar Markdown and JSON report' -RunLevel Limited -Force | Out-Null
Get-ScheduledTask -TaskPath $taskPath | Select-Object TaskName,State
