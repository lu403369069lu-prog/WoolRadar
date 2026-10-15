"""V3 deterministic handoff state machine. No AI, shell, credentials or deployment."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

PROJECTS = {'SAM': 'lu403369069lu-prog/YinQieJi', 'WoolRadar': 'lu403369069lu-prog/WoolRadar'}
STATUSES = ['proposed', 'ready', 'claimed', 'in_progress', 'evidence_ready',
            'review_pending', 'reviewed', 'done', 'blocked_local', 'quota_paused',
            'network_blocked', 'conflict', 'failed', 'needs_approval']
KINDS = {'register', 'claim', 'heartbeat', 'start', 'evidence', 'request_review', 'review',
         'done', 'quota_pause', 'release', 'recover', 'block', 'checkpoint'}
SHA = r'^[0-9a-f]{40}$'
ID = r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode('ascii')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _string(pattern=None):
    result = {'type': 'string', 'minLength': 1, 'maxLength': 2048}
    if pattern:
        result['pattern'] = pattern
    return result


def _object(properties):
    return {'type': 'object', 'required': list(properties), 'properties': properties,
            'additionalProperties': False}


def _array(items):
    return {'type': 'array', 'items': items}


INTEGER = {'type': 'integer', 'minimum': 0}
NULLABLE_ID = {'anyOf': [_string(ID), {'type': 'null'}]}
EVIDENCE_SCHEMA = _object({'command': _string(), 'exit_code': {'type': 'integer'},
    'passed': INTEGER, 'failed': INTEGER, 'head_sha': _string(SHA), 'artifact': _string()})
REVIEW_SCHEMA = _object({'reviewer': _string(ID), 'head_sha': _string(SHA), 'artifact': _string()})
TASK_SCHEMA = _object({
    'project': {'enum': list(PROJECTS)}, 'task_id': _string(ID), 'version': INTEGER,
    'status': {'enum': STATUSES}, 'owner': NULLABLE_ID, 'previous_owner': NULLABLE_ID,
    'executor': NULLABLE_ID, 'claimed_at': INTEGER, 'lease_until': INTEGER,
    'fencing_token': INTEGER, 'priority': {'enum': ['P0', 'P1', 'P2']},
    'dependencies': _array(_string()), 'base_branch': _string(), 'base_sha': _string(SHA),
    'work_branch': _string(), 'head_sha': _string(SHA), 'worktree_clean': {'type': 'boolean'},
    'allowed_files': _array(_string()), 'change_summary': {'type': 'string'},
    'evidence': _array(EVIDENCE_SCHEMA), 'reviews': _array(REVIEW_SCHEMA),
    'blockers': _array(_string()), 'error_type': {'type': ['string', 'null']},
    'checkpoint_at': INTEGER, 'last_sync_at': {'type': ['integer', 'null']},
    'next_action': _string(), 'definition_of_done': _string(),
    'requires_windows': {'type': 'boolean'}, 'remote_takeover_allowed': {'type': 'boolean'},
    'restrictions': _array(_string())})
STATE_SCHEMA = _object({'schema_version': {'const': 3}, 'revision': INTEGER,
    'tasks': {'type': 'object', 'additionalProperties': TASK_SCHEMA},
    'events': {'type': 'object', 'additionalProperties': _object({
        'payload_hash': _string(r'^[0-9a-f]{64}$'), 'receipt': _object({
            'result': {'enum': ['applied']}, 'version': INTEGER, 'fencing_token': INTEGER})})}})
STATE_SCHEMA.update({'$schema': 'https://json-schema.org/draft/2020-12/schema',
                     '$id': 'urn:sam-woolradar:relay-state:v3'})


def validate_schema(value, schema, path='$'):
    """Validate the deliberately small JSON Schema subset used by this contract."""
    if 'anyOf' in schema:
        for alternative in schema['anyOf']:
            try:
                validate_schema(value, alternative, path)
                return
            except ValueError:
                pass
        raise ValueError('SCHEMA ' + path)
    types = {'string': lambda x: isinstance(x, str), 'integer': lambda x: type(x) is int,
             'boolean': lambda x: type(x) is bool, 'null': lambda x: x is None,
             'object': lambda x: type(x) is dict, 'array': lambda x: type(x) is list}
    expected = schema.get('type')
    if expected is not None:
        options = expected if isinstance(expected, list) else [expected]
        if not any(types[t](value) for t in options):
            raise ValueError('SCHEMA_TYPE ' + path)
    if ('const' in schema and value != schema['const']) or ('enum' in schema and value not in schema['enum']):
        raise ValueError('SCHEMA_VALUE ' + path)
    if isinstance(value, str):
        if not schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', 1000000):
            raise ValueError('SCHEMA_LENGTH ' + path)
        if 'pattern' in schema and not re.fullmatch(schema['pattern'], value):
            raise ValueError('SCHEMA_PATTERN ' + path)
    if type(value) is int and value < schema.get('minimum', value):
        raise ValueError('SCHEMA_MINIMUM ' + path)
    if isinstance(value, list):
        for item in value:
            validate_schema(item, schema.get('items', {}), path + '[]')
    if isinstance(value, dict):
        if set(schema.get('required', [])) - value.keys():
            raise ValueError('SCHEMA_REQUIRED ' + path)
        props = schema.get('properties', {})
        for key, item in value.items():
            rule = props.get(key, schema.get('additionalProperties', {}))
            if rule is False:
                raise ValueError('SCHEMA_UNKNOWN ' + path + '.' + key)
            if isinstance(rule, dict):
                validate_schema(item, rule, path + '.' + key)


def safe_path(value):
    if (not isinstance(value, str) or not value or value.startswith('/') or
        '\\' in value or ':' in value or any(x in ('', '.', '..') for x in value.rstrip('/').split('/')) or
        any(ord(c) < 32 for c in value)):
        raise ValueError('UNSAFE_PATH')
    reserved = {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}
    for part in value.rstrip('/').split('/'):
        if part.endswith(('.', ' ')) or part.split('.')[0].upper() in reserved or any(c in part for c in '*?<>|"'):
            raise ValueError('WINDOWS_PATH_ALIAS_DENIED')
    return value


def in_scope(path, scopes):
    safe_path(path)
    return any(path == s or (s.endswith('/') and path.startswith(s)) for s in scopes)


def scopes_overlap(left, right):
    # Windows paths are case-insensitive, so ownership is conservative everywhere.
    return any(in_scope(a.lower(), [b.lower()]) or in_scope(b.lower(), [a.lower()])
               for a in left for b in right)


def validate_state(state):
    validate_schema(state, STATE_SCHEMA)
    for key, task in state['tasks'].items():
        if key != task['project'] + '/' + task['task_id'] or not task['allowed_files']:
            raise ValueError('TASK_IDENTITY_OR_EMPTY_SCOPE')
        for scope in task['allowed_files']:
            safe_path(scope)
        for evidence in task['evidence']:
            safe_path(evidence['artifact'])
            if evidence['head_sha'] != task['head_sha']:
                raise ValueError('STALE_EVIDENCE_SHA')
        executor = task['owner'] or task['previous_owner']
        for review in task['reviews']:
            safe_path(review['artifact'])
            if review['head_sha'] != task['head_sha'] or review['reviewer'] == executor:
                raise ValueError('STALE_OR_NOT_INDEPENDENT_REVIEW')
        if task['status'] in {'claimed','in_progress','evidence_ready','review_pending','reviewed'} and not task['owner']:
            raise ValueError('ACTIVE_OWNER_REQUIRED')
        if task['status'] in {'evidence_ready','review_pending','reviewed','done'} and not task['evidence']:
            raise ValueError('EVIDENCE_REQUIRED')
        if task['status'] in {'reviewed','done'} and not task['reviews']:
            raise ValueError('INDEPENDENT_REVIEW_REQUIRED')
        if task['status'] == 'done' and (task['owner'] is not None or
                any(e['exit_code'] or e['failed'] for e in task['evidence']) or
                sum(e['passed'] for e in task['evidence']) < 1):
            raise ValueError('PASSING_EVIDENCE_REQUIRED')
        if task['owner'] is None and task['lease_until'] != 0:
            raise ValueError('OWNER_LEASE_MISMATCH')
    return state


def empty_state():
    return {'schema_version': 3, 'revision': 0, 'tasks': {}, 'events': {}}


def new_task(project, task_id, head_sha, files, next_action):
    task = dict(project=project, task_id=task_id, version=0, status='ready', owner=None,
                previous_owner=None, executor=None, claimed_at=0, lease_until=0, fencing_token=0,
                priority='P1', dependencies=[], base_branch='unassigned', base_sha=head_sha,
                work_branch='unassigned', head_sha=head_sha, worktree_clean=False,
                allowed_files=files, change_summary='', evidence=[], reviews=[], blockers=[],
                error_type=None, checkpoint_at=0, last_sync_at=None, next_action=next_action,
                definition_of_done='Evidence at current SHA and independent review; no deployment',
                requires_windows=False, remote_takeover_allowed=True,
                restrictions=['no_production', 'no_merge', 'no_credentials', 'no_paid_api'])
    state = empty_state()
    state['tasks'][project + '/' + task_id] = task
    validate_state(state)
    return task


def event_key(event):
    # A version suffix permits distinct heartbeats at the same code identity.
    return '{project}/{task_id}/{head_sha}/{event_type}:{expected_version}'.format(**event)


def apply_event(state, event, *, observed_now=None):
    validate_state(state)
    required = {'project', 'task_id', 'head_sha', 'event_type', 'actor', 'expected_version',
                'lease_seconds', 'now', 'fencing_token', 'data'}
    if not isinstance(event, dict) or set(event) != required:
        raise ValueError('INVALID_EVENT_FIELDS')
    for field in ['task_id', 'actor']:
        validate_schema(event[field], _string(ID))
    validate_schema(event['head_sha'], _string(SHA))
    for field in ['expected_version', 'now', 'lease_seconds']:
        validate_schema(event[field], INTEGER)
    if event['fencing_token'] is not None:
        validate_schema(event['fencing_token'], INTEGER)
    if event['event_type'] not in KINDS or not 1 <= event['lease_seconds'] <= 900:
        raise ValueError('INVALID_EVENT_TYPE_OR_LEASE')
    if not isinstance(event['data'], dict):
        raise ValueError('INVALID_EVENT_DATA')
    kind = event['event_type']
    extras = {'register': {'task'}, 'evidence': {'evidence'}, 'review': {'review'}, 'block': {'status'},
              'recover': {'observed_head_sha'},
              'checkpoint': {'new_head_sha','change_summary','worktree_clean','work_branch'}}
    allowed = {'observed_head_sha','changed_files'} | extras.get(kind, set())
    if event['data'].keys() - allowed:
        raise ValueError('UNKNOWN_EVENT_DATA')
    if 'changed_files' in event['data']:
        validate_schema(event['data']['changed_files'], _array(_string()))
    key, fingerprint = event_key(event), digest(event)
    prior = state['events'].get(key)
    if prior:
        if prior['payload_hash'] != fingerprint:
            raise ValueError('EVENT_KEY_PAYLOAD_CHANGED')
        return copy.deepcopy(state), dict(prior['receipt'], result='duplicate_noop')
    result = copy.deepcopy(state)
    if kind == 'register':
        task = copy.deepcopy(event['data'].get('task'))
        validate_schema(task, TASK_SCHEMA)
        identity = event['project'] + '/' + event['task_id']
        if (identity in result['tasks'] or event['expected_version'] != 0 or
                event['fencing_token'] is not None or
                task['project'] != event['project'] or task['task_id'] != event['task_id'] or
                task['head_sha'] != event['head_sha'] or task['version'] != 0 or
                task['status'] != 'ready' or task['owner'] is not None or
                task['previous_owner'] is not None or task['executor'] is not None or
                task['fencing_token'] != 0 or task['evidence'] or task['reviews']):
            raise ValueError('INVALID_REGISTRATION')
        now = event['now'] if observed_now is None else observed_now
        validate_schema(now, INTEGER)
        task.update(version=1, checkpoint_at=now)
        result['tasks'][identity] = task
        receipt = {'result': 'applied', 'version': 1, 'fencing_token': 0}
        result['events'][key] = {'payload_hash': fingerprint, 'receipt': receipt}
        result['revision'] += 1
        validate_state(result)
        return result, receipt
    task = result['tasks'].get(event['project'] + '/' + event['task_id'])
    if task is None or task['version'] != event['expected_version']:
        raise ValueError('TASK_VERSION_CONFLICT')
    if task['head_sha'] != event['head_sha']:
        raise ValueError('STALE_CODE_SHA')
    now, kind, data, actor = (event['now'] if observed_now is None else observed_now), event['event_type'], event['data'], event['actor']
    validate_schema(now, INTEGER)
    if now < task['checkpoint_at']:
        raise ValueError('CLOCK_MOVED_BACKWARDS')
    if data.get('observed_head_sha', task['head_sha']) != task['head_sha']:
        raise ValueError('STALE_OBSERVED_SHA')
    for path in data.get('changed_files', []):
        if not in_scope(path, task['allowed_files']):
            raise ValueError('FILE_SCOPE_DENIED')
    if kind == 'claim':
        if task['status'] == 'quota_paused' and actor.startswith('codex'):
            raise ValueError('QUOTA_RESTORATION_REQUIRED')
        if task['owner']:
            raise ValueError('TASK_OWNED' if task['lease_until'] > now else 'EXPIRED_REQUIRES_RECOVERY')
        if task['status'] not in {'ready', 'quota_paused', 'blocked_local', 'network_blocked'}:
            raise ValueError('INVALID_CLAIM_STATE')
        for other in result['tasks'].values():
            if other is not task and other['project'] == task['project'] and other['owner']:
                if scopes_overlap(task['allowed_files'], other['allowed_files']):
                    raise ValueError('FILE_CONFLICT')
        if any(result['tasks'].get(dep, {}).get('status') != 'done' for dep in task['dependencies']):
            raise ValueError('DEPENDENCY_NOT_DONE')
        if actor.startswith('chatgpt') and (task['requires_windows'] or not task['remote_takeover_allowed']):
            raise ValueError('REMOTE_TAKEOVER_DENIED')
        task.update(owner=actor, executor=actor, claimed_at=now,
                    lease_until=now + event['lease_seconds'], status='claimed',
                    fencing_token=task['fencing_token'] + 1)
    elif kind == 'recover':
        if not task['owner'] or task['lease_until'] > now or data.get('observed_head_sha') != task['head_sha']:
            raise ValueError('RECOVERY_NOT_PROVEN')
        task.update(previous_owner=task['owner'], owner=None, lease_until=0,
                    status='ready', fencing_token=task['fencing_token'] + 1)
    else:
        if task['owner'] is None or event['fencing_token'] != task['fencing_token']:
            raise ValueError('OWNER_FENCE_DENIED')
        if task['lease_until'] <= now:
            raise ValueError('EXPIRED_OWNER')
        if actor != task['owner'] and kind != 'review':
            raise ValueError('OWNER_DENIED')
        if kind == 'heartbeat':
            task['lease_until'] = now + event['lease_seconds']
        elif kind == 'checkpoint':
            if task['status'] not in {'claimed','in_progress','evidence_ready','review_pending','reviewed'}:
                raise ValueError('INVALID_CHECKPOINT_STATE')
            validate_schema(data.get('new_head_sha'), _string(SHA))
            if not data.get('changed_files'):
                raise ValueError('CHANGED_FILES_REQUIRED')
            validate_schema(data.get('change_summary'), _string())
            if 'worktree_clean' in data:
                validate_schema(data['worktree_clean'], {'type':'boolean'})
            task.update(head_sha=data['new_head_sha'], change_summary=data['change_summary'],
                        worktree_clean=data.get('worktree_clean', False), evidence=[], reviews=[],
                        status='in_progress')
            if 'work_branch' in data:
                validate_schema(data['work_branch'], _string())
                task['work_branch'] = data['work_branch']
        elif kind == 'review':
            if actor == task['owner'] or task['status'] != 'review_pending':
                raise ValueError('INDEPENDENT_REVIEW_REQUIRED')
            review = dict(data.get('review', {}), reviewer=actor)
            validate_schema(review, REVIEW_SCHEMA)
            safe_path(review['artifact'])
            if review['head_sha'] != task['head_sha']:
                raise ValueError('STALE_REVIEW_SHA')
            task['reviews'].append(review)
            task['status'] = 'reviewed'
        elif kind in {'quota_pause', 'release', 'block'}:
            target = {'quota_pause': 'quota_paused', 'release': 'ready', 'block': data.get('status')}[kind]
            if kind == 'block' and target not in {'blocked_local','network_blocked','conflict','failed','needs_approval'}:
                raise ValueError('INVALID_BLOCK_STATE')
            task.update(status=target, previous_owner=task['owner'], owner=None, lease_until=0)
        else:
            transitions = {'start': ('claimed', 'in_progress'), 'evidence': ('in_progress', 'evidence_ready'),
                           'request_review': ('evidence_ready', 'review_pending'), 'done': ('reviewed', 'done')}
            before, after = transitions[kind]
            if task['status'] != before:
                raise ValueError('INVALID_TRANSITION')
            if kind == 'evidence':
                evidence = data.get('evidence')
                if evidence is None:
                    raise ValueError('EVIDENCE_REQUIRED')
                validate_schema(evidence, EVIDENCE_SCHEMA)
                safe_path(evidence['artifact'])
                if evidence['head_sha'] != task['head_sha']:
                    raise ValueError('STALE_EVIDENCE_SHA')
                task['evidence'].append(evidence)
            if kind == 'done':
                if not task['evidence'] or any(e['exit_code'] or e['failed'] for e in task['evidence']):
                    raise ValueError('PASSING_EVIDENCE_REQUIRED')
                if not task['reviews']:
                    raise ValueError('INDEPENDENT_REVIEW_REQUIRED')
                task.update(previous_owner=task['owner'], owner=None, lease_until=0)
            task['status'] = after
    task['version'] += 1
    task['checkpoint_at'] = now
    receipt = {'result': 'applied', 'version': task['version'], 'fencing_token': task['fencing_token']}
    result['events'][key] = {'payload_hash': fingerprint, 'receipt': receipt}
    result['revision'] += 1
    validate_state(result)
    return result, receipt


def atomic_checkpoint(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        previous = read_checkpoint(path)  # refuse to silently replace a corrupt checkpoint
        if previous == payload:
            return
        history = path.parent / '.versions' / path.name / (digest(previous) + '.json')
        if not history.exists():
            atomic_checkpoint(history, previous)
    envelope = {'format': 1, 'sha256': digest(payload), 'payload': payload}
    fd, name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(canonical(envelope))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def read_checkpoint(path):
    try:
        envelope = json.loads(Path(path).read_bytes())
        if set(envelope) != {'format', 'sha256', 'payload'} or envelope['format'] != 1:
            raise ValueError('CHECKPOINT_FORMAT')
        if digest(envelope['payload']) != envelope['sha256']:
            raise ValueError('CHECKPOINT_DIGEST')
        return envelope['payload']
    except (OSError, TypeError, KeyError, json.JSONDecodeError) as error:
        raise ValueError('CHECKPOINT_UNREADABLE') from error


class RemoteError(Exception):
    def __init__(self, status, retry_after=0, rate_limited=False):
        self.status, self.retry_after, self.rate_limited = status, retry_after, rate_limited
        super().__init__('REMOTE_' + str(status))


class Outbox:
    """Single local writer, durable per-event receipts. Remote sender MUST be idempotent."""
    def __init__(self, root, max_attempts=5):
        self.root, self.max_attempts = Path(root), max_attempts

    def enqueue(self, event):
        key = event_key(event)
        path = self.root / (hashlib.sha256(key.encode()).hexdigest() + '.json')
        if path.exists():
            if read_checkpoint(path)['event'] != event:
                raise ValueError('EVENT_KEY_PAYLOAD_CHANGED')
            return
        sequences = [read_checkpoint(p)['sequence'] for p in self.root.glob('*.json')]
        atomic_checkpoint(path, {'event': event, 'sequence': max(sequences, default=-1) + 1,
                                  'attempts': 0, 'next_at': 0,
                                  'status': 'pending', 'last_sync_at': None, 'receipt': None})

    def replay(self, sender, now):
        attempted, pending, blocked = 0, 0, None
        ordered = sorted(((read_checkpoint(p), p) for p in self.root.glob('*.json')),
                         key=lambda pair: pair[0]['sequence'])
        for item, path in ordered:
            if item['status'] == 'acknowledged':
                continue
            if item['status'] != 'pending':
                blocked = item['status']
                break
            if item['next_at'] > now:
                pending += 1
                break
            attempted += 1
            item['attempts'] += 1
            try:
                item['receipt'] = sender(item['event'])
                item.update(status='acknowledged', last_sync_at=now)
            except RemoteError as error:
                item['last_error'] = 'REMOTE_' + str(error.status)
                if error.status == 401:
                    item['status'] = 'BLOCKED_AUTH'
                elif error.status == 403 and not error.rate_limited:
                    item['status'] = 'permission_denied'
                elif error.status == 409:
                    item['status'] = 'conflict'
                elif error.status not in (0, 403, 429, 500, 502, 503, 504):
                    item['status'] = 'failed'
                elif item['attempts'] >= self.max_attempts:
                    item['status'] = 'retry_exhausted'
                else:
                    item['next_at'] = now + max(error.retry_after, min(300, 2**item['attempts']))
                if item['status'] == 'pending':
                    pending += 1
                else:
                    blocked = item['status']
            except ValueError as error:
                # Expected state/identity rejection is terminal until explicit reconciliation.
                # Persist only the validator code, never arbitrary payload or credential text.
                code = str(error).split()[0] if str(error) else 'INVALID_EVENT'
                item['last_error'] = code if re.fullmatch('[A-Z_]+', code) else 'INVALID_EVENT'
                item['status'] = ('conflict' if any(word in code for word in
                    ('CONFLICT','VERSION','STALE','OWNER','FENCE','EXPIRED','CLOCK')) else 'invalid_event')
                blocked = item['status']
            atomic_checkpoint(path, item)
            if blocked:
                break
            if item['status'] == 'pending':
                break  # preserve causal order across transient network failures
        return {'attempted': attempted, 'pending': pending, 'blocked': blocked}
