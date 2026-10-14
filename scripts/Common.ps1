Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-WoolRadarRoot {
    [CmdletBinding()]
    param([string]$Root = 'C:\WoolRadar')
    $full = [System.IO.Path]::GetFullPath($Root)
    if ($full -ne 'C:\WoolRadar') {
        throw "Refusing unexpected WoolRadar root: $full"
    }
    return $full
}

function Get-WoolRadarPython {
    param([switch]$Background)
    if ($Background) {
        $bundled = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        if (Test-Path -LiteralPath $bundled) { return $bundled }
    }
    $command = Get-Command python -ErrorAction Stop | Select-Object -First 1
    if ($Background -and $command.Source -match '\\scoop\\shims\\') {
        $actual = Join-Path $env:USERPROFILE 'scoop\apps\python\current\python.exe'
        if (-not (Test-Path -LiteralPath $actual)) { throw 'Background Python requires a direct interpreter' }
        return $actual
    }
    return $command.Source
}

function Invoke-WoolRadarBackgroundPython {
    [CmdletBinding()]
    param([string]$Python, [string[]]$Arguments, [string]$Root, [string]$Log)
    $Root = Get-WoolRadarRoot -Root $Root
    $quoted = foreach ($value in $Arguments) {
        if ($value.Contains('"') -or $value.Contains("`r") -or $value.Contains("`n")) { throw 'Unexpected background argument' }
        '"' + $value + '"'
    }
    $info = [System.Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $Python
    $info.Arguments = $quoted -join ' '
    $info.WorkingDirectory = $Root
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $info.StandardErrorEncoding = [System.Text.Encoding]::UTF8
    $info.EnvironmentVariables['PYTHONUTF8'] = '1'
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $info
    $receipt = Join-Path (Split-Path -Parent $Log) ('python-launch-' + [IO.Path]::GetFileNameWithoutExtension($Log) + '.json')
    try {
        if (-not $process.Start()) { throw 'Background Python start failed' }
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        $started = [DateTime]::UtcNow.ToString('o')
        $launcherAssembly = Join-Path $Root 'scripts\Run-Hidden.exe'
        $hasConsole = $null
        try { if (Test-Path -LiteralPath $launcherAssembly) {
            [Reflection.Assembly]::LoadFile($launcherAssembly) | Out-Null
            $hasConsole = [WoolRadarConsoleProbe]::HasConsole()
        } } catch { }
        try { @{started_at=$started;parent_pid=$PID;python_pid=$process.Id;interpreter=$Python;powershell_has_console=$hasConsole;create_no_window=$true;running=$true} | ConvertTo-Json -Compress | Set-Content -LiteralPath $receipt -Encoding UTF8 } catch { }
        $process.WaitForExit()
        $logEncoding = [Text.Encoding]::Unicode
        if (Test-Path -LiteralPath $Log) {
            $stream = [IO.File]::Open($Log, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
            try {
                if ($stream.Length -gt 0) {
                    $first = $stream.ReadByte(); $second = $stream.ReadByte()
                    if ($first -ne 255 -or $second -ne 254) { $logEncoding = [Text.UTF8Encoding]::new($false) }
                }
            }
            finally { $stream.Dispose() }
        }
        [IO.File]::AppendAllText($Log, $stdout.Result + $stderr.Result, $logEncoding)
        $code = $process.ExitCode
        try { @{started_at=$started;finished_at=[DateTime]::UtcNow.ToString('o');parent_pid=$PID;python_pid=$process.Id;interpreter=$Python;powershell_has_console=$hasConsole;create_no_window=$true;running=$false;exit_code=$code} | ConvertTo-Json -Compress | Set-Content -LiteralPath $receipt -Encoding UTF8 } catch { }
        return $code
    }
    finally {
        try { if ($process.Id -and -not $process.HasExited) { $process.Kill(); $process.WaitForExit() } } catch { }
        $process.Dispose()
    }
}

function Rotate-WoolRadarLogs {
    [CmdletBinding()]
    param([string]$LogDirectory, [int64]$MaxBytes = 10MB, [int]$Keep = 5)
    if (-not (Test-Path -LiteralPath $LogDirectory)) { return }
    Get-ChildItem -LiteralPath $LogDirectory -Filter '*.log' -File | ForEach-Object {
        if ($_.Length -lt $MaxBytes) { return }
        for ($index = $Keep - 1; $index -ge 1; $index--) {
            $older = "$($_.FullName).$index"
            $newer = "$($_.FullName).$($index + 1)"
            if (Test-Path -LiteralPath $older) { Move-Item -LiteralPath $older -Destination $newer -Force }
        }
        Move-Item -LiteralPath $_.FullName -Destination "$($_.FullName).1" -Force
    }
}
