[CmdletBinding()]
param([switch]$DisableSchedules)
$taskPath = '\WoolRadar\'
$tasks = Get-ScheduledTask -TaskPath $taskPath -ErrorAction SilentlyContinue
foreach ($task in $tasks) {
    Stop-ScheduledTask -TaskName $task.TaskName -TaskPath $taskPath -ErrorAction SilentlyContinue
    if ($DisableSchedules) {
        Disable-ScheduledTask -TaskName $task.TaskName -TaskPath $taskPath | Out-Null
    }
}
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
    $_.CommandLine -and $_.CommandLine -match '(?i)C:\\WoolRadar(?:\\|["\s])' -and
    ($_.CommandLine -match 'core\.cli' -or $_.CommandLine -match 'C:\\WoolRadar\\nodes\\[^\\]+\\(run|rss_collect|browser_collect)\.py')
} | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
Write-Output "Stopped $(@($tasks).Count) WoolRadar scheduled task instance(s). Disabled=$DisableSchedules"
