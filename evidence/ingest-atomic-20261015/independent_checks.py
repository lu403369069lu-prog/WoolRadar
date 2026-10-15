"""Focused disposable SQLite checks; no production DB or network access.

Run: python -B independent_checks.py --repo-root PATH
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--worker-db', type=Path)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    sys.path.insert(0, str(repo))
    from core.db import Database
    from core.models import Candidate
    from core.pipeline import Pipeline

    a, b = 'https://publisher.example/a', 'https://publisher.example/b'
    titles = {a: 'Launch Vendor credit grant', b: 'Last chance Vendor credit grant'}
    review = {'method': 'normal_browser_read', 'campaign_url': 'https://gleam.io/Ab123',
              'member_urls': [a, b], 'member_titles': titles}
    if args.worker_db:
        db = Database(args.worker_db)
        print('READY', flush=True)
        assert sys.stdin.readline().strip() == 'GO'
        print('ATTEMPTED', flush=True)
        result = db.review_campaign(review)
        print(json.dumps(result), flush=True)
        return 0

    out = Path(__file__).resolve().parent
    temp_root = out / 'temp'
    temp_root.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(temp_root)
    checks = []
    suite = unittest.TestSuite()
    for pattern in ['test_ingest_transaction.py', 'test_concurrent_upsert.py',
                    'test_reindex_upsert_serialization.py', 'test_pipeline.py']:
        suite.addTests(unittest.defaultTestLoader.discover(str(repo / 'tests'), pattern=pattern))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(suite)
    assert result.wasSuccessful(), stream.getvalue()

    def inbox(root, candidate):
        folder = root / 'data/inbox'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'n.jsonl').write_text(json.dumps(candidate.to_dict()), encoding='utf-8')

    with tempfile.TemporaryDirectory() as name:
        root = Path(name)
        pipeline = Pipeline(root)
        inbox(root, Candidate('n', 's', 'Vendor free API grant', a, source_kind='official',
                              metadata={'evidence_claims': {'open': True, 'public': True}}))
        real_enqueue = pipeline.notifications.enqueue
        calls = []

        def fail_second(*values):
            inserted = real_enqueue(*values)
            calls.append(True)
            if len(calls) == 2:
                raise RuntimeError('verified-notice-injected-failure')
            return inserted

        with patch.object(pipeline.notifications, 'enqueue', side_effect=fail_second):
            try:
                pipeline.ingest_node('n')
            except RuntimeError as exc:
                assert str(exc) == 'verified-notice-injected-failure'
            else:
                raise AssertionError('Notification failure was swallowed')
        assert len(calls) == 2
        with pipeline.db.connect() as conn:
            for table in ['events', 'sightings', 'evidence', 'status_history', 'notifications']:
                assert conn.execute('SELECT count(*) FROM ' + table).fetchone()[0] == 0, table
        assert pipeline.ingest_node('n')['notify'] == 1
        checks.append({'name': 'second-notification-insert-then-failure-rolls-back-all-candidate-writes',
                       'passed': True})

    with tempfile.TemporaryDirectory() as name:
        db = Database(Path(name) / 'thread.db')
        observed = {}
        with db.candidate_transaction():
            stored = db.upsert_candidate(Candidate('n', 's', 'Vendor thread grant', a))
            with db.connect() as outer:
                with db.connect() as nested:
                    assert outer is nested

                def other_thread():
                    try:
                        with db.connect() as conn:
                            observed['different_connection'] = conn is not outer
                            observed['visible_rows'] = conn.execute('SELECT count(*) FROM events').fetchone()[0]
                    except BaseException as exc:
                        observed['error'] = repr(exc)

                worker = threading.Thread(target=other_thread)
                worker.start()
                worker.join(5)
                assert not worker.is_alive()
                assert observed == {'different_connection': True, 'visible_rows': 0}, observed
        assert db.get_event(stored.event_id)
        try:
            with db.candidate_transaction():
                db.upsert_candidate(Candidate('n', 's', 'Vendor rollback grant', b))
                with db.connect():
                    raise RuntimeError('nested-connect-failure')
        except RuntimeError as exc:
            assert str(exc) == 'nested-connect-failure'
        else:
            raise AssertionError('Nested connect swallowed exception')
        assert len(db.list_events()) == 1
        with db.candidate_transaction():
            db.upsert_candidate(Candidate('n', 's', 'Vendor retry grant', b))
        assert len(db.list_events()) == 2
        checks.append({'name': 'same-thread-reuse-cross-thread-isolation-and-exception-propagation',
                       'passed': True, 'observed': observed})

    with tempfile.TemporaryDirectory() as name:
        root = Path(name)
        pipeline = Pipeline(root)
        for url in (a, b):
            pipeline.db.upsert_candidate(Candidate('n', 's', titles[url], url))
        inbox(root, Candidate('n', 's', titles[b], b, source_kind='official',
                              metadata={'evidence_claims': {'open': True, 'public': True,
                                                           'remaining': 0}}))
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        process = subprocess.Popen(
            [sys.executable, '-B', str(Path(__file__).resolve()), '--repo-root', str(repo),
             '--worker-db', str(pipeline.db.path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=env,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        original = pipeline.db.upsert_candidate
        try:
            assert process.stdout.readline().strip() == 'READY'
            blocked = []

            def pause_after_upsert(candidate):
                stored = original(candidate)
                process.stdin.write('GO\n')
                process.stdin.flush()
                assert process.stdout.readline().strip() == 'ATTEMPTED'
                time.sleep(0.3)
                blocked.append(process.poll() is None)
                return stored

            with patch.object(pipeline.db, 'upsert_candidate', side_effect=pause_after_upsert):
                pipeline.ingest_node('n')
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0, (stdout, stderr)
            assert blocked == [True], blocked
            assert json.loads(stdout.strip())['merged'] == 1
            events = pipeline.db.list_events()
            assert len(events) == 1
            assert events[0]['status'] == 'OFFICIAL_VERIFIED'
            assert events[0]['claim_scope'] == 'NONE'
            assert any(e.kind == 'official' and e.claims.get('remaining') == 0
                       for e in pipeline.db.get_evidence(events[0]['id']))
            with pipeline.db.connect() as conn:
                assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
                assert not conn.execute('PRAGMA foreign_key_check').fetchall()
            checks.append({'name': 'real-separate-process-review-waits-for-complete-candidate-commit',
                           'passed': True, 'child_exit': process.returncode,
                           'zero_evidence_saved': True})
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
            for pipe in (process.stdin, process.stdout, process.stderr):
                if pipe:
                    pipe.close()

    files = ['core/db.py', 'core/pipeline.py', 'tests/test_ingest_transaction.py']
    record = {
        'reviewer': 'independent budget_review agent',
        'command': f'python -B {Path(__file__).name} --repo-root <candidate-repo>',
        'exit_code': 0, 'source_sha256': {
            name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in files},
        'focused_test_methods': result.testsRun, 'test_output': stream.getvalue(),
        'checks': checks, 'blocking_findings': [],
        'conclusion': 'No blocker found in the per-candidate transaction fix. Exception propagation, '
                      'full notification-write rollback, thread isolation and real cross-process '
                      'reindex exclusion verified on disposable databases.',
        'limits': ['No full suite rerun, production writes or network.',
                   'Trace, flush, report and other operations after candidate commit remain outside '
                   'this reservation; no claim of universal concurrency safety.',
                   'An exception deliberately caught inside candidate_transaction is not automatically '
                   'a rollback-only marker; reviewed Pipeline lets persistence exceptions escape.']}
    path = out / 'independent-review.json'
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert json.loads(path.read_text(encoding='utf-8')) == record
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
