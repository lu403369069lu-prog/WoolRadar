"""Git branch checkpoint transport. No force push, AI calls or credential reads.

Uses existing Git authentication if a human has configured it. A local bare Git
remote is also supported for reproducible isolated acceptance. Never initializes
or changes a business checkout: workspace must be a dedicated empty directory.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path
from coordination.relay import (RemoteError, apply_event, canonical, digest,
                                validate_state, Outbox, atomic_checkpoint, read_checkpoint)


class GitStateStore:
    def __init__(self, workspace, remote, branch='codex/relay-state-v3'):
        self.workspace = Path(workspace)
        if os.path.normcase(str(self.workspace.resolve())) != os.path.normcase(str(self.workspace.absolute())):
            raise ValueError('WORKSPACE_PATH_ALIAS_DENIED')
        if branch != 'codex/relay-state-v3':
            raise ValueError('FIXED_COORDINATION_BRANCH_REQUIRED')
        if remote.startswith('https://'):
            if remote != 'https://github.com/lu403369069lu-prog/WoolRadar.git':
                raise ValueError('REMOTE_NOT_ALLOWED')
        elif not Path(remote).is_absolute() or not Path(remote).is_dir():
            raise ValueError('REMOTE_NOT_ALLOWED')
        self.remote, self.ref = remote, 'refs/heads/' + branch
        if not self.workspace.exists():
            self.workspace.mkdir(parents=True)
        if not (self.workspace / 'HEAD').exists():
            if any(self.workspace.iterdir()):
                raise ValueError('ISOLATED_EMPTY_WORKSPACE_REQUIRED')
            subprocess.run(['git', 'init', '--bare', str(self.workspace)],
                           check=True, capture_output=True, timeout=30)
        elif not (self.workspace / 'objects').is_dir():
            raise ValueError('DEDICATED_BARE_STORE_REQUIRED')
        check = self.git('rev-parse', '--is-bare-repository')
        if check.returncode or check.stdout.strip() != b'true':
            raise ValueError('DEDICATED_BARE_STORE_REQUIRED')

    def git(self, *args, data=None):
        env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never', GIT_AUTHOR_NAME='Relay Checkpoint',
                   GIT_AUTHOR_EMAIL='relay@localhost', GIT_COMMITTER_NAME='Relay Checkpoint',
                   GIT_COMMITTER_EMAIL='relay@localhost')
        try:
            run = subprocess.run(['git', '--git-dir', str(self.workspace), *args],
                                 input=data, capture_output=True, timeout=45, env=env)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RemoteError(0) from error
        return run

    def read(self):
        fetched = self.git('fetch', '--no-tags', self.remote, self.ref)
        if fetched.returncode:
            self._transport_failure(fetched)
        sha = self.git('rev-parse', 'FETCH_HEAD').stdout.decode().strip()
        raw = self.git('show', sha + ':state.json')
        if raw.returncode:
            raise ValueError('STATE_FILE_MISSING')
        try:
            envelope = json.loads(raw.stdout)
            if set(envelope) != {'format', 'sha256', 'payload'} or envelope['format'] != 1:
                raise ValueError('CHECKPOINT_FORMAT')
            state = envelope['payload']
            if digest(state) != envelope['sha256']:
                raise ValueError('CHECKPOINT_DIGEST')
            validate_state(state)
        except (json.JSONDecodeError, TypeError, KeyError) as error:
            raise ValueError('CORRUPT_REMOTE_STATE') from error
        return sha, state

    def observe(self, refs, cache):
        """One bounded read; persist identities, never execute or claim discovered work."""
        if not refs or len(refs) > 20 or len(set(refs)) != len(refs):
            raise ValueError('INVALID_OBSERVED_REFS')
        for ref in refs:
            if (not re.fullmatch(r'refs/heads/(?:codex|chatgpt)/[A-Za-z0-9_./-]+', ref) or
                    '..' in ref or ref.endswith(('/', '.')) or '//' in ref):
                raise ValueError('INVALID_OBSERVED_REF')
        run = self.git('ls-remote', '--refs', self.remote, *refs)
        if run.returncode:
            self._transport_failure(run)
        observed = dict.fromkeys(refs)
        for line in run.stdout.decode('ascii').splitlines():
            sha, ref = line.split('\t')
            if ref not in observed or not re.fullmatch('[0-9a-f]{40}', sha):
                raise ValueError('INVALID_REMOTE_REF_RESPONSE')
            observed[ref] = sha
        cache = Path(cache)
        previous = read_checkpoint(cache) if cache.exists() else {}
        if not isinstance(previous, dict) or any(not isinstance(k, str) or
                (v is not None and (not isinstance(v, str) or not re.fullmatch('[0-9a-f]{40}', v)))
                for k, v in previous.items()):
            raise ValueError('INVALID_OBSERVATION_CACHE')
        changes = [dict(ref=ref, before=previous.get(ref), after=sha)
                   for ref, sha in observed.items() if ref not in previous or previous[ref] != sha]
        atomic_checkpoint(cache, observed)
        return dict(changes=changes, refs=observed, model_calls=0)

    def _commit(self, state, parent=None):
        validate_state(state)
        envelope = {'format': 1, 'sha256': digest(state), 'payload': state}
        blob = self.git('hash-object', '-w', '--stdin', data=canonical(envelope))
        if blob.returncode:
            raise ValueError('GIT_BLOB_FAILED')
        entry = b'100644 blob ' + blob.stdout.strip() + b'\tstate.json\n'
        tree = self.git('mktree', data=entry)
        if tree.returncode:
            raise ValueError('GIT_TREE_FAILED')
        args = ['commit-tree', tree.stdout.decode().strip()]
        if parent:
            args += ['-p', parent]
        commit = self.git(*args, data=b'chore(coordination): persist validated checkpoint\n')
        if commit.returncode:
            raise ValueError('GIT_COMMIT_FAILED')
        return commit.stdout.decode().strip()

    def initialize(self, state):
        # Explicit operator operation; never called automatically by read/replay.
        # A root commit cannot overwrite any existing branch (non-fast-forward).
        if state['revision'] != 0:
            raise ValueError('INITIAL_REVISION_REQUIRED')
        return self._push(self._commit(state))

    def _push(self, sha):
        result = self.git('push', self.remote, sha + ':' + self.ref)
        if result.returncode:
            details = (result.stdout + result.stderr).lower()
            if (any(x in details for x in (b'non-fast-forward', b'fetch first', b'stale info')) or
                    (b'cannot lock ref' in details and b'expected' in details)):
                raise ValueError('REMOTE_CONFLICT')
            self._transport_failure(result)
        return sha

    def _transport_failure(self, result):
        details = (result.stdout + result.stderr).lower()
        status = re.search(rb'(?:returned error|http(?:/[0-9.]+)?(?: error)?|status(?: code)?)\s*[:=]?\s*(401|403|429|500|502|503)\b', details)
        code = int(status[1]) if status else None
        if (code == 401 or b'authentication failed' in details or b'could not read username' in details or
                b'terminal prompts disabled' in details or b'could not read password' in details):
            raise RemoteError(401)
        if code in (429, 503, 502, 500):
            raise RemoteError(code)
        if code == 403 or b'permission denied' in details:
            raise RemoteError(403, rate_limited=b'rate limit' in details)
        raise RemoteError(0)  # unknown transport failures must not be mislabelled as success

    def publish(self, expected_sha, state, *, event=None):
        if not isinstance(expected_sha, str) or not re.fullmatch('[0-9a-f]{40}', expected_sha):
            raise ValueError('EXPECTED_FULL_SHA_REQUIRED')
        validate_state(state)
        parent = self.git('cat-file', '-e', expected_sha + '^{commit}')
        if parent.returncode:
            raise ValueError('EXPECTED_PARENT_NOT_READ')
        old = self.git('show', expected_sha + ':state.json')
        try:
            envelope = json.loads(old.stdout)
            previous = envelope['payload']
            if envelope['format'] != 1 or envelope['sha256'] != digest(previous):
                raise ValueError('CHECKPOINT_DIGEST')
            validate_state(previous)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError('EXPECTED_PARENT_INVALID') from error
        if state['revision'] != previous['revision'] + 1:
            raise ValueError('REVISION_MUST_ADVANCE_ONCE')
        if any(state['events'].get(key) != value for key, value in previous['events'].items()):
            raise ValueError('EVENT_HISTORY_REWRITE_DENIED')
        if event is None:
            raise ValueError('EVENT_REQUIRED')
        key = event['project'] + '/' + event['task_id']
        receiver_time = state['tasks'].get(key, {}).get('checkpoint_at')
        actual_now = int(time.time())
        if type(receiver_time) is not int or receiver_time > actual_now:
            raise ValueError('INVALID_RECEIVER_TIME')
        # Recheck authorization against the live receiver clock. The stored timestamp
        # is used only for deterministic reconstruction, never for lease validity.
        apply_event(previous, event, observed_now=actual_now)
        output_task = state['tasks'].get(key, {})
        if output_task.get('owner') and output_task.get('lease_until', 0) <= actual_now:
            raise ValueError('EXPIRED_OUTPUT_LEASE')
        expected, _ = apply_event(previous, event, observed_now=receiver_time)
        if expected != state:
            raise ValueError('INVALID_TRANSITION_RESULT')
        return self._push(self._commit(state, expected_sha))

    def deliver(self, event):
        sha, state = self.read()
        updated, receipt = apply_event(state, event, observed_now=int(time.time()))
        if receipt['result'] == 'duplicate_noop':
            return dict(receipt, sha=sha)
        try:
            return dict(receipt, sha=self.publish(sha, updated, event=event))
        except ValueError as error:
            if str(error) == 'REMOTE_CONFLICT':
                raise RemoteError(409) from error
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--remote', required=True)
    commands = parser.add_subparsers(dest='operation', required=True)
    commands.add_parser('read')
    observe = commands.add_parser('observe')
    observe.add_argument('--ref',action='append',required=True)
    observe.add_argument('--cache',type=Path,required=True)
    deliver = commands.add_parser('deliver')
    deliver.add_argument('--event', type=Path, required=True)
    enqueue = commands.add_parser('enqueue')
    enqueue.add_argument('--event', type=Path, required=True)
    enqueue.add_argument('--outbox',type=Path,required=True)
    sync = commands.add_parser('sync')
    sync.add_argument('--outbox',type=Path,required=True)
    args = parser.parse_args()
    if args.operation == 'enqueue':
        Outbox(args.outbox).enqueue(json.loads(args.event.read_bytes()))
        print(json.dumps({'queued':True,'remote_write':False}))
        return
    store = GitStateStore(args.workspace, args.remote)
    if args.operation == 'observe':
        print(json.dumps(store.observe(args.ref,args.cache),indent=2))
    elif args.operation == 'read':
        sha, state = store.read()
        print(json.dumps({'sha': sha, 'state': state}, indent=2))
    elif args.operation == 'deliver':
        print(json.dumps(store.deliver(json.loads(args.event.read_bytes())), indent=2))
    else:
        # Each sender invocation cold-reads the remote and performs the state transition there.
        report=Outbox(args.outbox).replay(store.deliver,now=int(time.time()))
        try:
            sha,state=store.read()
            atomic_checkpoint(args.outbox/'last-good-state.json.cache',state)
            atomic_checkpoint(args.outbox/'last-sync.json.cache',
                              {'sha':sha,'confirmed_at':int(time.time())})
            report['last_confirmed_sha']=sha
        except RemoteError:
            report['remote_read']='unavailable; preserve previous sync receipt'
        print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
