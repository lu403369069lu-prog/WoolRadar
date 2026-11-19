"""Codex Stop JSON gate; only explicit session-bound handoffs control continuation."""
import json
import re
import sys
import hashlib
from pathlib import Path

HANDOFF = Path('_outbox/stop-continuity-handoff.json')


def recent_user_messages(path, limit=20):
    """Read the latest human messages across the whole rollout, even after long tool output."""
    if not path:
        return []
    from collections import deque
    found = deque(maxlen=limit)
    try:
        with Path(path).open('rb') as stream:
            for raw in stream:
                # Large tool results must not hide earlier human continuation;
                # avoid JSON-parsing their large, irrelevant payloads.
                if len(raw) > 4_000_000 or (b'"user"' not in raw and b'"user_message"' not in raw):
                    continue
                try:
                    obj = json.loads(raw)
                except ValueError:
                    continue
                payload = obj.get('payload', {})
                value = None
                if obj.get('type') == 'response_item' and payload.get('type') == 'message' and payload.get('role') == 'user':
                    value = '\n'.join(v.get('text', '') for v in payload.get('content', []) if isinstance(v, dict))
                elif obj.get('type') == 'event_msg' and payload.get('type') == 'user_message':
                    value = payload.get('message')
                if not isinstance(value, str) or len(value) > 10000:
                    continue
                if value.lstrip().startswith(('<hook_prompt', '<environment_context>', '<codex_delegation>',
                    '<external_codex_apps_open_page>', '<send_user_message_question_reply>',
                    '# AGENTS.md', 'The following is the Codex agent history')):
                    continue
                found.append(value.strip())
    except (OSError, ValueError, TypeError):
        return []
    return list(found)


def latest_user_pause(path):
    """Recognize a pause imperative with a short explanation, but not a question."""
    human = recent_user_messages(path, limit=1)
    if not human:
        return False
    command = human[-1].strip()
    if len(command) > 100:
        return False
    # Negative continuation imperatives are explicit pause requests as well.
    # The punctuation boundary avoids interpreting "do not continue the wrong
    # command" or a question as a pause of the whole task.
    if re.match(
        r'^(?:(?:现在|这轮|本轮|今天)\s*)?(?:(?:请先|请|先)\s*)?'
        r'(?:(?:别干了|别继续了|到此为止|到这里)|(?:不要|不用|别)\s*继续(?:干|执行|工作|推进|开发)?)'
        r'(?:了|吧)?(?=$|[，,。.!！\s])', command
    ):
        return True
    # Require a command boundary after the pause phrase. In particular,
    # "停了？继续干" is a question/report, not permission to stop.
    return bool(re.match(
        r'^(?:请(?:先)?|你可以|可以(?:先)?|先)?'
        r'(?:暂停一下|暂停|停止|停下|停了|停一下|停|别干了|别继续了)'
        r'(?:当前(?:任务|工作)|任务|工作|执行|项目开发)?'
        r'(?:吧|了)?(?=$|[，,。.!！\s])', command))


def latest_user_resume(path):
    """Detect an explicit new continuation after a previous pause."""
    messages = recent_user_messages(path, limit=1)
    if not messages:
        return False
    command = messages[-1].strip()
    if len(command) > 100:
        return False
    return bool(re.match(
        r'^(?:请|现在|那就|好|好的)?\s*'
        r'(?:继续|恢复)(?:干|工作|执行|推进|做|审核|开发|任务)?'
        r'(?:吧|了)?(?=$|[，,。.!！\s])', command))


def explicit_unbound_continuation(event, handoff):
    """Safeguard unbound continuation in the current project without claiming a binding."""
    recent = recent_user_messages(event.get('transcript_path'))
    if latest_user_pause(event.get('transcript_path')):
        return False
    entries = handoff.get('sessions', {})
    active = [entry for entry in entries.values() if isinstance(entry, dict) and
              entry.get('disposition') == 'active']
    cwd = Path(event['cwd']).resolve()
    def belongs_to_current_project(entry):
        project = entry.get('project')
        if isinstance(project, str):
            try:
                if Path(project).resolve() == cwd:
                    return True
            except (OSError, RuntimeError):
                pass
        # Some active entries lost their project field during resume. A
        # session-bound next-action file under this exact cwd is still an
        # explicit project anchor, so a missing transcript must fail closed.
        next_file = entry.get('next_action_file')
        if isinstance(next_file, str):
            try:
                action_path = Path(next_file).resolve()
                if action_path == cwd or cwd in action_path.parents:
                    return True
            except (OSError, RuntimeError):
                pass
        return False
    same_project = [entry for entry in active if belongs_to_current_project(entry)]
    # If the runtime omits the rollout path, a current-project active contract
    # must be reconciled rather than silently allowed to stop.
    if not recent:
        return bool(same_project)
    continuing = any(re.search(r'继续|没干完|开始工作|承接|resume|keep going', value, re.I)
                     for value in recent[-3:])
    latest = recent[-1].strip()
    if re.search(r'别的项目|其他项目|其它项目|无关程序|新任务|another project|unrelated', latest, re.I):
        return False
    # A named unfinished task can request status/review without saying
    # "continue". Only inspect the latest message for this implicit case;
    # older named task context must not capture an unrelated new request.
    context = '\n'.join(recent if continuing else recent[-1:]).casefold()
    eligible = [entry for entry in active if not entry.get('project') or entry in same_project]
    named_task = any(any(isinstance(term, str) and len(term) >= 4 and
                             term.casefold() in context
                             for term in entry.get('continuity_terms', []))
                     for entry in eligible)
    return named_task or (continuing and bool(same_project))


def decide(event):
    if not isinstance(event, dict):
        return {'systemMessage': 'Stop verification input malformed; continuation state not verified.'}
    if event.get('hook_event_name') not in (None, 'Stop'):
        return {}
    sid = event.get('session_id')
    cwd = event.get('cwd')
    if not sid or not cwd:
        return {'systemMessage': 'Stop input lacks session_id/cwd; no task completion inference made.'}
    handoff_path = Path(cwd) / HANDOFF
    if not handoff_path.exists():
        return {}
    try:
        handoff = json.loads(handoff_path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return {'systemMessage': 'Continuation handoff unreadable; verify task status before stopping.'}
    entry = handoff.get('sessions', {}).get(sid)
    if entry is None:
        matches=[t for t in handoff.get('transfers', {}).values() if t.get('target_thread')==sid]
        if len(matches)>1:return {'decision':'block','reason':'Ambiguous transfer binding; preserve source and reconcile.'}
        if not matches:
            if explicit_unbound_continuation(event, handoff):
                return {'decision': 'block', 'reason': (
                    'Explicit continuing task has no exact session binding. Register this session_id '
                    'in the project continuation registry with verified current requirements; '
                    'do not borrow another session entry or claim overall completion.')}
            return {}
        transfer=matches[0]
        tasks=transfer.get('pending',[])
        entry={'schema_version':1,'disposition':'active',
               'pending_requirements':transfer.get('pending_requirements') or [t['id'] for t in tasks],
               'actionable_tasks':transfer.get('actionable_tasks') or [t['action'] for t in tasks]}
    if latest_user_pause(event.get('transcript_path')):
        return {}
    if not isinstance(entry, dict) or entry.get('schema_version') != 1:
        return {'decision': 'block', 'reason': 'Repair this session continuation handoff schema before claiming completion.'}
    disposition = entry.get('disposition', 'active')
    pending = entry.get('pending_requirements', [])
    actionable = entry.get('actionable_tasks', [])
    if disposition == 'transferred':
        try:
            manifest=Path(entry['transfer_manifest'])
            transfer=json.loads(manifest.read_text(encoding='utf-8-sig'))
            valid=(transfer['source_thread']==sid and transfer['target_thread']==entry['target_thread']
                   and Path(transfer['project']).resolve()==Path(cwd).resolve()
                   and transfer['state']=='archive-ready' and bool(transfer['progress'])
                   and hashlib.sha256(Path(transfer['checkpoint']).read_bytes()).hexdigest()==transfer['checkpoint_sha256'])
            valid=valid and all(hashlib.sha256(Path(v['evidence']).read_bytes()).hexdigest()==v['sha256'] for v in transfer['progress'])
            if valid:return {}
        except (OSError,ValueError,KeyError,TypeError):pass
        return {'decision':'block','reason':'Transfer not verified; preserve source and repair receiver continuation.'}
    if disposition == 'complete' and not pending and entry.get('verification_record'):
        return {}
    if disposition == 'paused' and entry.get('user_pause_evidence') and not latest_user_resume(event.get('transcript_path')):
        return {}
    if disposition == 'waiting_for_user' and not actionable and entry.get('required_question'):
        return {}
    if disposition == 'externally_blocked' and not actionable and entry.get('blocker_evidence'):
        return {}
    if actionable or pending or disposition == 'active':
        next_file = entry.get('next_action_file')
        detailed = []
        goal = ''
        stop_condition = ''
        if next_file:
            try:
                payload = json.loads(Path(next_file).read_text(encoding='utf-8-sig'))
                if not isinstance(payload, dict) or payload.get('session_id') != sid:
                    raise ValueError('Next actions are not bound to this session')
                detailed = [str(item) for item in payload.get('next_actions', [])][:10]
                goal = str(payload.get('goal', ''))
                stop_condition = str(payload.get('stop_condition', ''))
            except (OSError, ValueError, TypeError):
                detailed = []
        if detailed:
            actions = ' | '.join(detailed)
            return {'decision': 'block', 'reason': (
                'Continue the authorized original task; a coordination receipt, dispatch receipt, or partial completion is not its endpoint. '
                f'Read {handoff_path} and {next_file}. Goal: {goal} '
                f'Next actions: {actions} '
                f'Stop condition: {stop_condition} '
                'Inspect returned artifacts, run independent checks, dispatch concrete rework, and update the task ledger. '
                'stop_hook_active does not prove completion. User pause/cancellation overrides continuation; do not expand authorization or invent verification.'
            )}
        ids = ', '.join(str(x)[:80] for x in actionable[:12]) or 'original pending requirements'
        return {'decision': 'block', 'reason': (
            'Continue the authorized original task; a coordination receipt or partial completion is not its endpoint. '
            f'Read {handoff_path}; next actions: {ids}. '
            'Inspect returned artifacts, run appropriate independent checks, dispatch concrete rework, '
            'and update the task ledger. stop_hook_active does not prove completion. '
            'User pause/cancellation overrides continuation; do not expand authorization or invent verification.'
        )}
    return {'decision': 'block', 'reason': 'Unknown continuation disposition; reconcile requirements and handoff before stopping.'}


def main():
    try:
        event = json.loads(sys.stdin.read())
    except ValueError:
        event = None
    print(json.dumps(decide(event), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
