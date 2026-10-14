[CmdletBinding()]
param([string]$Root = 'C:\WoolRadar')
. "$PSScriptRoot\Common.ps1"
$Root = Get-WoolRadarRoot -Root $Root
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$profile = Join-Path $Root 'nodes\twitter-monitor\chrome-profile'
if (-not (Test-Path -LiteralPath $chrome)) { throw 'Chrome not found' }
$existing = Get-NetTCPConnection -LocalPort 9222 -State Listen -ErrorAction SilentlyContinue
if ($existing) { throw 'Port 9222 already in use; inspect ownership before launching.' }
New-Item -ItemType Directory -Path $profile -Force | Out-Null
Start-Process -FilePath $chrome -ArgumentList @('--remote-debugging-port=9222','--remote-debugging-address=127.0.0.1',"--user-data-dir=`"$profile`"",'--no-first-run','https://x.com/home')
Write-Output '独立 X Chrome 已打开。请手动登录；完成后运行 TwitterMonitor 定时任务。'
