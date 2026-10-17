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
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

_CONTRACT_SPEC = importlib.util.spec_from_file_location(
    'historical_batch_contract', Path(__file__).resolve().with_name('HISTORICAL_CODEX_BATCH_RUNNER_20261017.py'))
contract = importlib.util.module_from_spec(_CONTRACT_SPEC)
_CONTRACT_SPEC.loader.exec_module(contract)

MANIFEST = Path(__file__).resolve().with_name('HISTORICAL_80_PERCENT_CODEX_JOBS_20261017.json')
PROJECTS = {'wool': ('WoolRadar', 'W'), 'sam': ('YinQieJi-SAM', 'S'),
            'coord': ('WoolRadar-Coord', 'C')}


def pin_command(repo: Path, job: dict, blob_lookup=None) -> tuple[Path, list[str]]:
    """Validate the exact committed test file and allowlisted no-shell argv."""
    root = repo.resolve()
    rel = job['verified_test_path']
    if not isinstance(rel, str) or not rel or '\\' in rel or ':' in rel:
        raise RuntimeError('Invalid historical test source path.')
    target = (root / rel).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise RuntimeError('Historical test target missing, symlinked outside root or invalid.')
    if target.is_symlink():
        raise RuntimeError('Historical test symlink not admitted.')
    if blob_lookup is None:
        blob_lookup = lambda path: contract.git(['rev-parse', 'HEAD:' + path], root)
    if blob_lookup(rel) != job['verified_test_blob']:
        raise RuntimeError('Historical test Git blob differs from reviewed manifest.')
    cwd = (root / job['local_cwd']).resolve()
    if not cwd.is_relative_to(root) or not cwd.is_dir():
        raise RuntimeError('Job working directory is outside this checkout.')
    argv = shlex.split(job['run_command'])
    if (len(argv) == 10 and argv[:6] == ['python','-B','-m','unittest','discover','-s']
            and argv[7] == '-p' and argv[9] == '-v'):
        candidate = (cwd / argv[6] / argv[8]).resolve()
        argv[0] = sys.executable
    elif (len(argv) == 5 and argv[:4] == ['node','--import','tsx','--test']):
        candidate = (cwd / argv[4]).resolve()
    elif (len(argv) == 3 and argv[:2] == ['node','--test']):
        candidate = (cwd / argv[2]).resolve()
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
        if key not in commands:
            commands[key] = {'command':key, 'cwd':cwd, 'argv':argv,
                             'key_sha256':hashlib.sha256(key.encode('utf-8')).hexdigest()}
        mapping.append({'family_id':job['family_id'], 'source_blob':job['verified_test_blob'],
                        'command_key':commands[key]['key_sha256']})
    return list(commands.values()), mapping


def run_commands(commands: list[dict], mapping: list[dict], repo_head: str,
                 project: str) -> tuple[int, dict, Path]:
    output = Path(tempfile.mkdtemp(prefix='history-code-batch-'+project+'-'))
    by_key = {}
    for item in commands:
        key = item['key_sha256']
        try:
            done = subprocess.run(item['argv'], cwd=item['cwd'], shell=False,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, errors='replace', timeout=1800, check=False)
            code, log = done.returncode, done.stdout
        except (OSError, subprocess.TimeoutExpired) as exc:
            code, log = 125, repr(exc)
        logbytes = log.encode('utf-8')
        (output / (key[:16]+'.log')).write_bytes(logbytes)
        verdict, counts = contract.evaluate_run('HISTORY-TEST',code,log)
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
    (output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
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
    contract.validate_handoff_manifest(MANIFEST,args.project,args.expected_head)
    root = args.repo.expanduser().resolve()
    head = contract.preflight(root,args.project,args.expected_head)
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    commands,mapping = plan_jobs(root,args.project,manifest)
    print(json.dumps({'project':args.project,'repo_head':head,'families':len(mapping),
                      'distinct_commands':len(commands),
                      'mode':'RUN' if args.run else 'DRY_RUN'},ensure_ascii=False))
    if not args.run:
        for entry in commands:
            print(json.dumps({'sha256':entry['key_sha256'],'command':entry['command'],
                              'cwd':str(entry['cwd'])},ensure_ascii=False))
        return 0
    rc,receipt,output=run_commands(commands,mapping,head,args.project)
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
