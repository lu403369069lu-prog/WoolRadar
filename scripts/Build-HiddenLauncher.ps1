[CmdletBinding()]
param([string]$Root = 'C:\WoolRadar')
. "$PSScriptRoot\Common.ps1"
$Root = Get-WoolRadarRoot -Root $Root
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw 'Built-in .NET compiler unavailable' }
$source = Join-Path $Root 'scripts\Run-Hidden.cs'
$output = Join-Path $Root 'scripts\Run-Hidden.exe'
$manifest = Join-Path $Root 'scripts\Run-Hidden.build.json'
$sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
if ((Test-Path -LiteralPath $output) -and (Test-Path -LiteralPath $manifest)) {
    $existing = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
    if ($existing.source_sha256 -eq $sourceHash -and $existing.binary_sha256 -eq (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash) {
        Get-FileHash -LiteralPath $output -Algorithm SHA256
        return
    }
}
$info = [Diagnostics.ProcessStartInfo]::new()
$info.FileName = $compiler
$info.Arguments = '/nologo /target:winexe /platform:anycpu /reference:System.Web.Extensions.dll /out:"' + $output + '" "' + $source + '"'
$info.UseShellExecute = $false
$info.CreateNoWindow = $true
$info.RedirectStandardOutput = $true
$info.RedirectStandardError = $true
$process = [Diagnostics.Process]::new()
$process.StartInfo = $info
try {
    if (-not $process.Start()) { throw 'Compiler start failed' }
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $output)) { throw ('Hidden launcher build failed: ' + $stdout.Result + $stderr.Result) }
}
finally { $process.Dispose() }
@{source_sha256=$sourceHash;binary_sha256=(Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash} | ConvertTo-Json -Compress | Set-Content -LiteralPath $manifest -Encoding UTF8
Get-FileHash -LiteralPath $output -Algorithm SHA256
