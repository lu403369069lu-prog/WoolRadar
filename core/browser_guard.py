"""Fail closed before attaching CDP to any browser profile."""
import json
import re
import subprocess
from pathlib import PureWindowsPath


def is_dedicated_chrome(name: str, command: str, profile: str) -> bool:
    if name.lower() != 'chrome.exe':
        return False
    match = re.search(r'--user-data-dir(?:=|\s+)(?:"([^"]+)"|([^\s]+))', command)
    if not match:
        return False
    actual = PureWindowsPath(match.group(1) or match.group(2))
    expected = PureWindowsPath(profile)
    if '..' in actual.parts or not actual.is_absolute():
        return False
    return str(actual).rstrip('\\').casefold() == str(expected).rstrip('\\').casefold()


def assert_dedicated_listener(profile: str, port: int = 9222):
    # Query only the listener process. Never enumerate browser secrets or files.
    script = f"""$ErrorActionPreference='Stop'
$ownerIds = @(Get-NetTCPConnection -LocalPort {int(port)} -State Listen | Select-Object -ExpandProperty OwningProcess -Unique)
if ($ownerIds.Count -ne 1) {{ throw 'CDP_OWNER_AMBIGUOUS' }}
$ownerProcess = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $ownerIds[0])
@{{name=$ownerProcess.Name; command=$ownerProcess.CommandLine}} | ConvertTo-Json -Compress
"""
    try:
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
            capture_output=True, text=True, timeout=15, check=True,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        owner = json.loads(result.stdout)
        valid = is_dedicated_chrome(owner.get('name', ''), owner.get('command', ''), profile)
    except Exception:
        raise RuntimeError('CDP_PROFILE_NOT_VERIFIED') from None
    if not valid:
        raise RuntimeError('CDP_PROFILE_NOT_VERIFIED')
