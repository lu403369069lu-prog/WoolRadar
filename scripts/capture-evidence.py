"""Capture safe local deployment evidence, never credential/profile contents."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r'C:\WoolRadar')
sys.path.insert(0, str(ROOT))
from core.db import Database
from core.models import utc_now

def main():
    db = Database(ROOT / 'data' / 'woolradar.db')
    with db.connect() as conn:
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        counts = {table: conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                  for table in ('events','sightings','evidence','status_history','node_runs','notifications')}
        states = {row[0]: row[1] for row in conn.execute('SELECT status,count(*) FROM events GROUP BY status')}
    result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests'],
        cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=60)
    manifests = {}
    # Explicit source-only allowlist. Do not recurse into any upstream/profile/state directory.
    for directory, patterns in [('core', ('*.py',)), ('scripts', ('*.ps1','*.py')), ('config', ('sources.yaml','keywords.json','security-policy.json','official-trace.json'))]:
        for pattern in patterns:
            for path in (ROOT / directory).glob(pattern):
                manifests[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    payload = {'checked_at': utc_now(), 'sqlite_integrity': integrity, 'counts': counts,
        'event_states': states, 'core_tests': {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr},
        'nodes': db.latest_node_runs(), 'sha256': manifests,
        'not_verified': ['X login/collection','Reddit OAuth collection','OpenMagpie backend',
            'Telegram delivery','physical restart/offline recovery','95% real-sample recall/dedup',
            'new-batch detection without explicit official numeric marker','long-duration stability']}
    output = ROOT / 'evidence' / 'deployment-verification.json'
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'path': str(output), 'integrity': integrity, 'counts': counts,
        'event_states': states, 'core_test_exit_code': result.returncode}, ensure_ascii=False))
    return result.returncode

if __name__ == '__main__':
    raise SystemExit(main())
