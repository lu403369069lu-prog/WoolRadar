"""Verify the reviewed original coordination source/test delta, without network."""
import hashlib
import json
from pathlib import Path


def verify(root):
    root = Path(root).resolve()
    rows = json.loads((root / 'coordination/original-tests/SOURCE_MANIFEST.json').read_bytes())
    expected = {'coordination/' + name for name in (
        'relay.py', 'relay_git.py', 'dispatcher.py', 'github_event_adapter.py', 'github_webhook.py')}
    expected |= {'coordination/original-tests/' + name for name in (
        'test_github_webhook.py', 'test_dispatcher.py', 'test_relay.py',
        'test_relay_faults.py', 'test_relay_git.py', 'test_return_sync.py')}
    if len(rows) != len(expected) or {r['target'] for r in rows} != expected:
        raise ValueError('ORIGINAL_SUITE_SCOPE_MISMATCH')
    for row in rows:
        if row['source_commit'] != '27796df5f9847c1bb5d48d2a445e418dfb3d8e96':
            raise ValueError('ORIGINAL_SUITE_SOURCE_MISMATCH')
        path = root / row['target']
        if path.is_symlink() or path.resolve() != path.absolute():
            raise ValueError('ORIGINAL_SUITE_PATH_ALIAS')
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('ORIGINAL_SUITE_BYTES_MISMATCH')
    return len(rows)


if __name__ == '__main__':
    print(json.dumps({'verified_original_files': verify(Path(__file__).resolve().parent.parent)}))
