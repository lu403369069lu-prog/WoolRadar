#!/usr/bin/env python3
"""Run the reviewed 42 historical Codex tests, deduped, in a disposable local clone.

The 50-family manifest is mandatory. DRY RUN by default. No checkout,
install, deploy, push, private-data export or shell command is performed here.
"""
from __future__ import annotations

import argparse
import importlib.util
import hashlib
import json
import os
import platform
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

_CONTRACT_SPEC = importlib.util.spec_from_file_location(
    'historical_batch_contract', Path(__file__).resolve().with_name('HISTORICAL_CODEX_BATCH_RUNNER_20261017.py'))
contract = importlib.util.module_from_spec(_CONTRACT_SPEC)
_CONTRACT_SPEC.loader.exec_module(contract)

_GUARD_SPEC = importlib.util.spec_from_file_location(
    'historical_formal_receipt_guard', Path(__file__).resolve().with_name(
        'HISTORICAL_CODEX_42_RECEIPT_GUARD_20261017.py'))
formal_guard = importlib.util.module_from_spec(_GUARD_SPEC)
_GUARD_SPEC.loader.exec_module(formal_guard)

MANIFEST = Path(__file__).resolve().with_name('HISTORICAL_80_PERCENT_CODEX_JOBS_20261017.json')
PROJECTS = {'wool': ('WoolRadar', 'W'), 'sam': ('YinQieJi-SAM', 'S'),
            'coord': ('WoolRadar-Coord', 'C')}


def _reject_symlink_chain(root: Path, relative: str) -> Path:
    """Walk original lexical components: resolving first erases symlink evidence."""
    path = root
    value = Path(relative)
    if value.is_absolute() or ':' in relative or '\\' in relative:
        raise RuntimeError('Absolute/non-portable historical test path not admitted.')
    for component in value.parts:
        if component == '..':
            path = path.parent
        elif component != '.':
            path = path / component
            if path.is_symlink():
                raise RuntimeError('Historical test/command symlink component not admitted.')
        if not path.resolve().is_relative_to(root):
            raise RuntimeError('Historical test/command path escapes checkout.')
    return path.resolve()


def pin_command(repo: Path, job: dict, blob_lookup=None) -> tuple[Path, list[str]]:
    """Validate the exact committed test file and allowlisted no-shell argv."""
    root = repo.resolve()
    rel = job['verified_test_path']
    if not isinstance(rel, str) or not rel or '\\' in rel or ':' in rel:
        raise RuntimeError('Invalid historical test source path.')
    target = _reject_symlink_chain(root, rel)
    if not target.is_relative_to(root) or not target.is_file():
        raise RuntimeError('Historical test target missing, symlinked outside root or invalid.')
    check_actual_worktree = blob_lookup is None
    if blob_lookup is None:
        blob_lookup = lambda path: contract.git(['rev-parse', 'HEAD:' + path], root)
    if blob_lookup(rel) != job['verified_test_blob']:
        raise RuntimeError('Historical test Git blob differs from reviewed manifest.')
    if check_actual_worktree:
        # HEAD:path verifies committed provenance only. A changed on-disk test
        # could otherwise run after preflight (or if pin_command is reused).
        raw = target.read_bytes()
        disk_blob = hashlib.sha1(
            b'blob ' + str(len(raw)).encode('ascii') + b'\x00' + raw).hexdigest()
        if disk_blob != job['verified_test_blob']:
            raise RuntimeError('Pinned historical working-tree test contents differ from HEAD blob.')
    cwd = _reject_symlink_chain(root, job['local_cwd'])
    if not cwd.is_relative_to(root) or not cwd.is_dir():
        raise RuntimeError('Job working directory is outside this checkout.')
    argv = shlex.split(job['run_command'])
    if (len(argv) == 10 and argv[:6] == ['python','-B','-m','unittest','discover','-s']
            and argv[7] == '-p' and argv[9] == '-v'):
        candidate = _reject_symlink_chain(root, str(Path(job['local_cwd']) / argv[6] / argv[8]))
        argv[0] = sys.executable
    elif (len(argv) == 5 and argv[:4] == ['node','--import','tsx','--test']):
        candidate = _reject_symlink_chain(root, str(Path(job['local_cwd']) / argv[4]))
    elif (len(argv) == 3 and argv[:2] == ['node','--test']):
        candidate = _reject_symlink_chain(root, str(Path(job['local_cwd']) / argv[2]))
    else:
        raise RuntimeError('Not an allowlisted offline unit-test command.')
    if candidate != target:
        raise RuntimeError('Command test path is not the pinned reviewed test target.')
    return cwd, argv


def plan_jobs(repo: Path, project: str, document: dict,
              blob_lookup=None) -> tuple[list[dict], list[dict]]:
    """Map every runnable family to exactly one deduplicated source command."""
    project_label, _ = PROJECTS[project]
    jobs = [job for job in document['jobs']
            if job['project'] == project_label
            and job['disposition'] == 'READY_FOR_LOCAL_CODEX']
    commands: dict[str, dict] = {}
    mapping = []
    for job in jobs:
        cwd, argv = pin_command(repo, job, blob_lookup)
        key = job['run_command']
        pinned = {'root':repo.resolve(), 'relative':job['verified_test_path'],
                  'blob':job['verified_test_blob']}
        if key not in commands:
            commands[key] = {'command':key, 'cwd':cwd, 'argv':argv,
                             'cwd_contract':job['local_cwd'], 'pinned_test':pinned,
                             'require_git_clean':blob_lookup is None,
                             'key_sha256':hashlib.sha256(key.encode('utf-8')).hexdigest()}
        elif commands[key]['pinned_test'] != pinned:
            raise RuntimeError('Identical command mapped to conflicting reviewed test source.')
        mapping.append({'family_id':job['family_id'], 'source_blob':job['verified_test_blob'],
                        'command_key':commands[key]['key_sha256']})
    return list(commands.values()), mapping


# A disposable checkout is not a security sandbox. Still prevent accidental
# credential/environment leakage into formal test subprocesses: opt in only
# OS process-launch essentials, never inherit authentication or preload hooks.
_CHILD_ENV_ALLOW = frozenset({
    'PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'OS',
    'PROCESSOR_ARCHITECTURE', 'NUMBER_OF_PROCESSORS',
    'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ',
})


def _isolated_test_env(home: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k.upper() in _CHILD_ENV_ALLOW}
    for name in ('HOME', 'USERPROFILE', 'TMP', 'TEMP', 'TMPDIR',
                 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME'):
        env[name] = str(home)
    env.update({'PYTHONDONTWRITEBYTECODE':'1', 'PYTHONIOENCODING':'utf-8', 'CI':'1'})
    return env


def _verify_frozen_worktree(root: Path, expected_head: str) -> None:
    """Reject changes masked by Git index assume-unchanged/skip-worktree bits.

    Git status alone can report clean after an earlier subprocess modifies an
    imported module and hides it via update-index. Check every tracked file
    against its actual immutable HEAD blob before and after every command.
    """
    if contract.git(['rev-parse', 'HEAD'], root) != expected_head:
        raise RuntimeError('Historical repo HEAD changed between commands.')
    if contract.git(['status', '--porcelain'], root):
        raise RuntimeError('Historical repo reports a dirty worktree.')
    try:
        raw = subprocess.run(['git', 'ls-tree', '-r', '-z', 'HEAD'], cwd=root,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=30, check=True).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError('Failed to enumerate immutable tracked files.') from exc
    for entry in raw.split(b'\x00'):
        if not entry:
            continue
        try:
            header, name = entry.split(b'\t', 1)
            mode, kind, digest = header.split(b' ', 2)
            rel = os.fsdecode(name)
        except (ValueError, UnicodeError) as exc:
            raise RuntimeError('Invalid frozen tracked Git tree record.') from exc
        if kind != b'blob' or mode not in (b'100644', b'100755'):
            raise RuntimeError('Unsupported frozen Git tree object or tracked symlink.')
        path = _reject_symlink_chain(root, rel)
        if not path.is_file():
            raise RuntimeError('Immutable tracked file missing from on-disk source tree.')
        payload = path.read_bytes()
        got = hashlib.sha1(b'blob ' + str(len(payload)).encode('ascii')
                           + b'\x00' + payload).hexdigest().encode('ascii')
        if got != digest:
            raise RuntimeError('Immutable tracked dependency differs from frozen Git HEAD.')


def run_commands(commands: list[dict], mapping: list[dict], repo_head: str,
                 project: str) -> tuple[int, dict, Path]:
    if not commands or not mapping:
        raise RuntimeError('Empty historical batch cannot count as accepted evidence.')
    command_keys = [x['key_sha256'] for x in commands]
    if (len(set(command_keys)) != len(command_keys)
            or any(len(k) != 64 or any(c not in '0123456789abcdef' for c in k)
                   for k in command_keys)):
        raise RuntimeError('Duplicate/malformed historical command digest.')
    family_ids = [x['family_id'] for x in mapping]
    mapping_keys = [x['command_key'] for x in mapping]
    if (len(set(family_ids)) != len(family_ids)
            or set(mapping_keys) != set(command_keys)):
        raise RuntimeError('Duplicate or unmapped historical family/command.')
    output = Path(tempfile.mkdtemp(prefix='history-code-batch-'+project+'-'))
    by_key = {}
    for item in commands:
        key = item['key_sha256']
        try:
            if 'pinned_test' in item:
                pinned = item['pinned_test']
                root = Path(pinned['root']).resolve()
                target = _reject_symlink_chain(root, pinned['relative'])
                if not target.is_file():
                    raise RuntimeError('Pinned historical test no longer exists before execution.')
                payload = target.read_bytes()
                actual = hashlib.sha1(
                    b'blob ' + str(len(payload)).encode('ascii') + b'\x00' + payload).hexdigest()
                if actual != pinned['blob']:
                    raise RuntimeError('Historical test changed after planning; refusing execution.')
            # Direct HEAD-object hashing catches index-masked dependency
            # changes too; git status --porcelain alone is insufficient.
            if item.get('require_git_clean'):
                _verify_frozen_worktree(root, repo_head)
            # Per-command disposable home/tmp prevents accidental reads from
            # user dotfiles or runtime tokens inherited through env variables.
            with tempfile.TemporaryDirectory(prefix='child-', dir=output) as private_home:
                done = subprocess.run(item['argv'], cwd=item['cwd'], shell=False,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      env=_isolated_test_env(Path(private_home)),
                                      timeout=1800, check=False)
                code, logbytes = done.returncode, done.stdout or b''
                if item.get('require_git_clean'):
                    try:
                        _verify_frozen_worktree(root, repo_head)
                    except RuntimeError:
                        # Preserve exact stdout for hashing; reject the batch.
                        if code == 0:
                            code = 126
        except RuntimeError as exc:
            code, logbytes = 126, repr(exc).encode('utf-8')
        except (OSError, subprocess.TimeoutExpired) as exc:
            code, logbytes = 125, repr(exc).encode('utf-8')
        # Persist/hash ORIGINAL child bytes. Lossy decoding may be used only
        # for human-readable verdict parsing, never for evidence identity.
        (output / (key+'.log')).write_bytes(logbytes)
        verdict, counts = contract.evaluate_run('HISTORY-TEST',code,logbytes.decode('utf-8', errors='replace'))
        # The official receipt guard requires strict UTF-8 raw log parsing.
        try:
            logbytes.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            if verdict == 0:
                verdict = 126
        # Independently enforce official raw-log grammar before building
        # either legacy or formal receipts: appended/mixed summaries cannot
        # turn a failed, skipped or partial command into PASS.
        genuine = formal_guard.parse_actual_log_counts(logbytes)
        if (genuine is None or genuine != {
                'tests': counts['tests_reported'], 'passed': counts['passed'],
                'failed': counts['failed'], 'skipped': counts['skipped']}):
            verdict = 126 if verdict == 0 else verdict
        by_key[key] = {'command':item['command'], 'exit_code':verdict,
                       'observed_exit_code':code, 'counts':counts,
                       'log_sha256':hashlib.sha256(logbytes).hexdigest(),
                       'status':'PASS_EXACT_HEAD' if verdict == 0 else
                                'NOT_RUN_BLOCKED' if verdict in (125,126) else 'FAIL_REPRODUCED'}
    rows = [{**m, **by_key[m['command_key']]} for m in mapping]
    receipt = {'schema':1, 'source':'local-disposable-codex',
               'project':project,'repo_head':repo_head,
               'executed_commands':len(commands),'covered_families':len(rows),
               'results':rows, 'private_inputs_exported':False,
               'review_logs_before_sharing':True}
    # The official family guard uses a grouped-command wire protocol,
    # different from the legacy per-family receipt. Emit both explicitly.
    formal_results = []
    for index, item in enumerate(commands):
        key = item['key_sha256']
        stored = (output / (key + '.log')).read_bytes()
        if hashlib.sha256(stored).hexdigest() != by_key[key]['log_sha256']:
            raise RuntimeError('Raw process log changed before formal receipt.')
        name = f'test-{index:03d}.log'
        (output / name).write_bytes(stored)
        n = by_key[key]['counts']
        formal_results.append({
            'cwd': item.get('cwd_contract', '.'),
            'argv': item['argv'],
            'family_ids': [m['family_id'] for m in mapping if m['command_key'] == key],
            'local_log': name, 'sha256': by_key[key]['log_sha256'],
            'exit_code': by_key[key]['exit_code'],
            'status': 'PASS' if by_key[key]['exit_code'] == 0 else 'FAIL',
            'counts': {'tests': n['tests_reported'], 'passed': n['passed'],
                       'failed': n['failed'], 'skipped': n['skipped']}
        })
    runtime = {'python': sys.version.split()[0], 'platform': platform.platform()}
    if project == 'sam':
        try:
            node_info = subprocess.run(['node', '--version'], stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL, timeout=10, check=False,
                                       env=_isolated_test_env(output))
            runtime['node'] = (node_info.stdout.decode('ascii', 'replace').strip()
                               if node_info.returncode == 0 else 'unavailable')
        except (OSError, subprocess.TimeoutExpired):
            runtime['node'] = 'unavailable'
    formal_receipt = {
        'schema_version': 1, 'source': 'disposable-local-codex',
        'project': project, 'repo_sha': repo_head,
        'unique_commands': len(formal_results),
        'tested_families': len(mapping), 'no_real_gold_claim': True,
        'production_modified': False, 'runtime': runtime,
        'results': formal_results
    }
    (output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'receipt-guard-v1.json').write_text(
        json.dumps(formal_receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    return (0 if all(r['exit_code'] == 0 for r in rows) else 1), receipt, output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True,choices=sorted(PROJECTS))
    parser.add_argument('--repo',required=True,type=Path)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--run',action='store_true',help='Execute reviewed offline tests; default dry-run')
    args = parser.parse_args()
    if args.expected_head != contract.EXPECTED[args.project]:
        raise RuntimeError('Source SHA not in the reviewed contract.')
    # Verify the exact frozen Git blob BEFORE planning, preflight or executing
    # any command, rather than only when checking the receipt afterwards.
    # Reuse this parsed immutable document: never reread unchecked manifest bytes.
    frozen_jobs = formal_guard.load_verified_manifest(MANIFEST)
    contract.validate_handoff_manifest(MANIFEST,args.project,args.expected_head)
    root = args.repo.expanduser().resolve()
    head = contract.preflight(root,args.project,args.expected_head)
    commands,mapping = plan_jobs(root,args.project,frozen_jobs)
    print(json.dumps({'project':args.project,'repo_head':head,'families':len(mapping),
                      'distinct_commands':len(commands),
                      'mode':'RUN' if args.run else 'DRY_RUN'},ensure_ascii=False))
    if not args.run:
        for entry in commands:
            print(json.dumps({'sha256':entry['key_sha256'],'command':entry['command'],
                              'cwd':str(entry['cwd'])},ensure_ascii=False))
        return 0
    rc,receipt,output=run_commands(commands,mapping,head,args.project)
    # A successful subprocess batch is NOT an accepted historical-family
    # receipt until the separate frozen guard validates every raw log and job.
    raw_formal = json.loads((output / 'receipt-guard-v1.json').read_text(encoding='utf-8'))
    guard_verdict = formal_guard.review(raw_formal, frozen_jobs, output)
    (output / 'guard-verdict.json').write_text(
        json.dumps(guard_verdict, ensure_ascii=False, indent=2), encoding='utf-8')
    if not guard_verdict['local_full_family_receipt_accepted']:
        rc = 1
        print('OFFICIAL_HISTORY_GUARD_REJECTED:', guard_verdict['errors'], file=sys.stderr)
    print(json.dumps({'exit_code':rc,'covered_families':receipt['covered_families'],
                      'results':{k:sum(x['status']==k for x in receipt['results'])
                                 for k in ('PASS_EXACT_HEAD','FAIL_REPRODUCED','NOT_RUN_BLOCKED')},
                      'local_receipt_dir':str(output)},ensure_ascii=False))
    print('Review/redact all local logs before sending any GitHub evidence. No private exports.')
    return rc


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError,OSError,ValueError,KeyError) as exc:
        print('PRECHECK_BLOCKED:',exc,file=sys.stderr)
        raise SystemExit(2)
