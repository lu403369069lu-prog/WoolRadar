#!/usr/bin/env python3
"""Derive review-only Python -I candidate from the baseline filtered gate."""
from pathlib import Path

root = Path(__file__).resolve().parent
source = root / 'integration_gate_candidate.py'
dest = root / 'integration_gate_candidate_isolated.py'
content = source.read_text(encoding='utf-8')
needle = 'cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]'
replacement = 'cmd = [sys.executable, "-I", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]'
if content.count(needle) != 1:
    raise SystemExit('candidate source drift: expected one WoolRadar unittest command')
dest.write_text(content.replace(needle, replacement), encoding='utf-8', newline='\n')
print(dest, dest.stat().st_size)
