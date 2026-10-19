"""Portable trace review: real restricted-runtime processes, disposable files."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--worker-root', type=Path)
    parser.add_argument('--mode', choices=['publish', 'hold'])
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    sys.path.insert(0, str(repo))
    from core.official_trace import OfficialTracer, _trace_publication_lock
    record = {'event_id': 1, 'checked_at': '2026-10-16T00:00:00Z',
              'status': 'DISCOVERED', 'references': []}

    def tracer_at(root):
        tracer = OfficialTracer.__new__(OfficialTracer)
        tracer.root = root
        return tracer

    if args.worker_root:
        if args.mode == 'hold':
            destination = args.worker_root / 'evidence/official-trace'
            destination.mkdir(parents=True, exist_ok=True)
            with _trace_publication_lock(destination / '.publish.lock'):
                print('HELD', flush=True)
                assert sys.stdin.readline().strip() == 'EXIT'
                os._exit(17)  # Kernel must release the lock without finally.
        print('READY', flush=True)
        assert sys.stdin.readline().strip() == 'GO'
        print('ATTEMPTED', flush=True)
        tracer_at(args.worker_root)._write_record(1, record)
        print('DONE', flush=True)
        return

    out = Path(__file__).resolve().parent
    temp_root = out / 'review-temp'
    temp_root.mkdir(exist_ok=True)
    tempfile.tempdir = str(temp_root)
    files = ['core/db.py', 'core/official_trace.py', 'core/report.py',
             'tests/test_reindex_notification_collision.py', 'tests/test_trace_audit_atomic.py',
             'tests/test_report_snapshot.py']
    hashes = {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in files}
    suite = unittest.TestSuite()
    counts = {}
    for name in ['test_reindex_notification_collision.py', 'test_trace_audit_atomic.py',
                 'test_report_snapshot.py', 'test_notify_reindex_transaction.py']:
        tests = unittest.defaultTestLoader.discover(str(repo / 'tests'), pattern=name)
        counts[name] = tests.countTestCases()
        suite.addTests(tests)
    stream = io.StringIO()
    results = unittest.TextTestRunner(stream=stream).run(suite)
    assert results.wasSuccessful(), stream.getvalue()
    checks = []
    with tempfile.TemporaryDirectory() as name:
        tracer = tracer_at(Path(name))
        tracer._write_record(1, record)
        destination = tracer.root / 'evidence/official-trace'
        archive = next((destination / 'history').glob('*.json'))
        latest = (destination / '1.json').read_bytes()
        archive.write_bytes(b'actual preexisting different bytes')
        try:
            tracer._write_record(1, record)
        except ValueError as exc:
            assert str(exc) == 'OFFICIAL_TRACE_AUDIT_HASH_COLLISION'
        else:
            raise AssertionError('Stored corruption was silently overwritten')
        assert archive.read_bytes() == b'actual preexisting different bytes'
        assert (destination / '1.json').read_bytes() == latest
        assert not list(destination.rglob('*.tmp'))
        checks.append({'name': 'real-preexisting-different-bytes-collision-preserved', 'passed': True})

    for stage in ['history-replace', 'latest-replace', 'fsync']:
        with tempfile.TemporaryDirectory() as name:
            tracer = tracer_at(Path(name))
            tracer._write_record(1, record)
            destination = tracer.root / 'evidence/official-trace'
            latest = (destination / '1.json').read_bytes()
            real_replace = os.replace

            def fail_replace(source, target):
                is_history = Path(target).parent.name == 'history'
                if is_history == (stage == 'history-replace'):
                    raise PermissionError('injected publication denial')
                return real_replace(source, target)

            target = 'core.official_trace.os.fsync' if stage == 'fsync' else 'core.official_trace.os.replace'
            effect = PermissionError('injected fsync denial') if stage == 'fsync' else fail_replace
            with patch(target, side_effect=effect):
                try:
                    tracer._write_record(1, dict(record, status='STALE_EVENT_ID'))
                except PermissionError:
                    pass
                else:
                    raise AssertionError('Write failure was swallowed')
            assert (destination / '1.json').read_bytes() == latest
            for path in (destination / 'history').glob('*.json'):
                json.loads(path.read_text(encoding='utf-8'))
            assert not list(destination.rglob('*.tmp'))
            checks.append({'name': stage + '-failure-cleans-temp-and-preserves-complete-views', 'passed': True})

    def worker(root, mode):
        return subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()),
                                 '--repo-root', str(repo), '--worker-root', str(root), '--mode', mode],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

    def finish(process):
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, (stdout, stderr, process.returncode)
        assert 'DONE' in stdout

    def cleanup(process):
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe:
                pipe.close()

    with tempfile.TemporaryDirectory() as name:
        root = Path(name)
        processes = [worker(root, 'publish') for _ in range(2)]
        try:
            for process in processes:
                assert process.stdout.readline().strip() == 'READY'
            for process in processes:
                process.stdin.write('GO\n')
                process.stdin.flush()
            for process in processes:
                finish(process)
        finally:
            for process in processes:
                cleanup(process)
        destination = root / 'evidence/official-trace'
        history = list((destination / 'history').glob('*.json'))
        assert len(history) == 1 and json.loads(history[0].read_text(encoding='utf-8')) == record
        assert json.loads((destination / '1.json').read_text(encoding='utf-8')) == record
        assert not list(destination.rglob('*.tmp'))
        checks.append({'name': 'two-real-processes-publish-identical-record-one-complete-history',
                       'child_exit_codes': [p.returncode for p in processes], 'passed': True})

    with tempfile.TemporaryDirectory() as name:
        root = Path(name)
        holder = worker(root, 'hold')
        publisher = None
        try:
            assert holder.stdout.readline().strip() == 'HELD'
            publisher = worker(root, 'publish')
            assert publisher.stdout.readline().strip() == 'READY'
            publisher.stdin.write('GO\n')
            publisher.stdin.flush()
            assert publisher.stdout.readline().strip() == 'ATTEMPTED'
            time.sleep(.2)
            assert publisher.poll() is None
            holder.stdin.write('EXIT\n')
            holder.stdin.flush()
            holder.communicate(timeout=5)
            assert holder.returncode == 17
            finish(publisher)
        finally:
            cleanup(holder)
            if publisher is not None:
                cleanup(publisher)
        destination = root / 'evidence/official-trace'
        assert (destination / '.publish.lock').is_file()
        assert json.loads((destination / '1.json').read_text(encoding='utf-8')) == record
        assert not list(destination.rglob('*.tmp'))
        checks.append({'name': 'kernel-lock-released-after-holder-os-exit-without-finally',
                       'holder_exit': 17, 'publisher_exit': 0, 'passed': True})

    assert hashes == {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in files}
    report = {'reviewer': 'independent budget_review agent', 'python': sys.executable,
              'command': 'python -B portable_trace_checks.py --repo-root <integration-worktree>',
              'exit_code': 0, 'source_sha256': hashes, 'focused_methods': counts,
              'focused_methods_run': results.testsRun, 'test_output': stream.getvalue(),
              'additional_checks': checks, 'blocking_findings': [],
              'conclusion': 'Portable trace publisher passes on the same restricted interpreter '
                            'that denied hard links, with real-process publication and crash-lock recovery.',
              'limits': ['No full regression, production, worktree edits, network or external delivery.',
                         'Old hard-link failure review retained separately.',
                         'Publication errors still propagate; no success claimed on failed file writes.']}
    path = out / 'portable-trace-review.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert json.loads(path.read_text(encoding='utf-8')) == report
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
