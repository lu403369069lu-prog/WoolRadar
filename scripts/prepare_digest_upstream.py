"""Install the real, pinned digest RSS upstream in this isolated checkout.

Run once before strict source-integration tests on Windows or Ubuntu:
    python -B -X utf8 scripts/prepare_digest_upstream.py

No source files, credentials, or virtualenv contents belong in a Git commit.
The upstream commit comes from the reviewed UPSTREAMS.json manifest.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run(*args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True,
                            encoding='utf-8', env=env)
    return result.stdout.strip()


def prepare(root: Path, verify_only: bool = False) -> Path:
    root = root.resolve()
    entries = json.loads((root / 'UPSTREAMS.json').read_text(encoding='utf-8'))
    digest = next(item for item in entries if item['node'] == 'digest-ai-agent')
    remote, pinned = digest['repository'], digest['commit']
    if not remote.startswith('https://github.com/') or len(pinned) != 40 or any(
        c not in '0123456789abcdef' for c in pinned):
        raise RuntimeError('INVALID_UPSTREAM_PIN')

    checkout = root / 'nodes' / 'digest-ai-agent' / 'upstream'
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['PIP_NO_INPUT'] = '1'
    if not checkout.exists():
        if verify_only:
            raise RuntimeError('UPSTREAM_NOT_INSTALLED')
        checkout.parent.mkdir(parents=True, exist_ok=True)
        run('git', 'clone', '--no-checkout', remote, str(checkout), env=env)
        run('git', '-C', str(checkout), 'checkout', '--detach', pinned, env=env)
    actual = run('git', '-C', str(checkout), 'rev-parse', 'HEAD', env=env)
    if actual != pinned:
        if verify_only:
            raise RuntimeError('UPSTREAM_PIN_MISMATCH')
        # A previous clone may have stopped before the detached pin checkout.
        # Git refuses to overwrite dirty files without --force; leave such
        # checkouts for manual review rather than deleting or resetting them.
        run('git', '-C', str(checkout), 'checkout', '--detach', pinned, env=env)
        actual = run('git', '-C', str(checkout), 'rev-parse', 'HEAD', env=env)
        if actual != pinned:
            raise RuntimeError('UPSTREAM_PIN_MISMATCH')

    # A matching commit alone does not attest to the executed source bytes:
    # tracked edits and imported untracked modules can override that commit.
    # Ignore only this checkout's disposable virtual environment.
    # Git's porcelain status trusts index flags. A tracked source modified
    # under --assume-unchanged or --skip-worktree can evade status entirely.
    # `ls-files -v` marks assume-unchanged entries with lowercase tags and
    # skip-worktree entries with S; reject both before any pip/import.
    tracked = run('git', '-C', str(checkout), 'ls-files', '-v', '-z', '--',
                  '.', ':(exclude).venv', env=env)
    if any(entry and (entry[0].islower() or entry[0] == 'S')
           for entry in tracked.split('\0')):
        raise RuntimeError('UPSTREAM_WORKTREE_DIRTY')
    if run('git', '-C', str(checkout), 'status', '--porcelain=v1',
           '--untracked-files=all', '--', '.', ':(exclude).venv', env=env):
        raise RuntimeError('UPSTREAM_WORKTREE_DIRTY')
    # git status hides paths intentionally ignored by upstream .gitignore.
    # Importable .py/native modules in those paths still affect runtime bytes.
    ignored = run('git', '-C', str(checkout), 'ls-files', '-z', '--others',
                  '--ignored', '--exclude-standard', '--', '.',
                  ':(exclude).venv', env=env)
    # A sourceless .pyc and a ZIP/EGG/WHEEL/PYZ on sys.path can execute
    # unreviewed Python without introducing a .py or altering git status.
    # Refuse ignored importable code and archives before pip or runtime import.
    importable = ('.py', '.pyi', '.pyc', '.pyo', '.so', '.pyd', '.pth', '.dll',
                  '.zip', '.egg', '.whl', '.pyz', '.pyzw')
    if any(path.casefold().endswith(importable)
           for path in ignored.split('\0') if path):
        raise RuntimeError('UPSTREAM_IGNORED_EXECUTABLE_SOURCE')

    venv = checkout / '.venv'
    interpreter = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not interpreter.is_file():
        if verify_only:
            raise RuntimeError('UPSTREAM_VENV_NOT_INSTALLED')
        run(sys.executable, '-m', 'venv', str(venv), env=env)
    if not verify_only:
        # Editable installation uses real pinned sources and their declared
        # dependencies, not an artificial stand-in for RSSProvider.
        run(str(interpreter), '-m', 'pip', 'install', '-e', str(checkout), env=env)

    run(str(interpreter), '-c',
        'import httpx, newsbrief; from newsbrief.sources.rss import RSSProvider; '
        'assert RSSProvider is not None', env=env)
    print(f'UPSTREAM_VERIFIED commit={actual} python={interpreter.name}')
    return interpreter


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--verify-only', action='store_true')
    options = parser.parse_args()
    try:
        prepare(options.root, verify_only=options.verify_only)
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError,
            RuntimeError) as exc:
        print(f'UPSTREAM_SETUP_FAILED {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1) from None
