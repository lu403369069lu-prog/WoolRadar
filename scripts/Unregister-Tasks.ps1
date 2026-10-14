[CmdletBinding(SupportsShouldProcess, ConfirmImpact='High')]
param()
$taskPath = '\WoolRadar\'
$tasks = Get-ScheduledTask -TaskPath $taskPath -ErrorAction SilentlyContinue
foreach ($task in $tasks) {
    if ($PSCmdlet.ShouldProcess("$taskPath$($task.TaskName)", 'Unregister scheduled task')) {
        Unregister-ScheduledTask -TaskName $task.TaskName -TaskPath $taskPath -Confirm:$false
    }
}
