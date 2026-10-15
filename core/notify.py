from __future__ import annotations

import json
import os
import time
from pathlib import Path
import urllib.parse
import urllib.request
from .models import utc_now, Candidate
from .verifier import VerificationEngine


class NotificationQueue:
    """Durable outbox. Delivery is at-least-once after ambiguous network failures."""
    def __init__(self, db):
        self.db = db

    def enqueue(self, event_id: int, batch_id: str, channel: str, payload: str) -> bool:
        with self.db.connect() as conn:
            cursor = conn.execute('''INSERT OR IGNORE INTO notifications
                (event_id,batch_id,channel,created_at,result,payload) VALUES(?,?,?,?,?,?)''',
                (event_id, batch_id, channel, utc_now(), 'PENDING', payload))
            if cursor.rowcount == 1:
                return True
            # SENT is never requeued. A stale unsent/uncertain notification may
            # retry after fresh verification (documented at-least-once delivery).
            return conn.execute("UPDATE notifications SET result='PENDING',payload=?,next_attempt=0 "
                "WHERE event_id=? AND batch_id=? AND channel=? AND result='STALE'",
                (payload, event_id, batch_id, channel)).rowcount == 1

    def pending(self) -> list[dict]:
        with self.db.connect() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM notifications WHERE result IN ('PENDING','RETRY','CLAIMED') ORDER BY id")]

    def record_health(self, node: str, status: str, error_code: str) -> bool:
        if status == 'SKIPPED':
            return False  # No request means no evidence of recovery.
        fingerprint = 'OK' if status == 'OK' else ('ISSUE:' + error_code if error_code else status + ':')
        with self.db.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            previous = conn.execute('SELECT fingerprint FROM node_health WHERE node=?', (node,)).fetchone()
            previous_fingerprint = previous['fingerprint'] if previous else ''
            if previous_fingerprint.partition(':')[0] in ('PARTIAL', 'PAUSED', 'FAILED'):
                old_error = previous_fingerprint.partition(':')[2]
                if old_error:
                    previous_fingerprint = 'ISSUE:' + old_error
            if previous and previous_fingerprint == fingerprint:
                return False
            conn.execute('INSERT INTO node_health VALUES(?,?,?) ON CONFLICT(node) DO UPDATE SET '
                'fingerprint=excluded.fingerprint,checked_at=excluded.checked_at', (node, fingerprint, utc_now()))
            if not previous and status == 'OK':
                return False
            message = f'【节点恢复】{node}' if status == 'OK' else f'【节点故障或受限】{node}\n状态：{status}\n原因：{error_code}'
            conn.execute('INSERT INTO notifications(event_id,batch_id,channel,created_at,result,payload) '
                'VALUES(NULL,?,?,?,?,?)', (node, 'local-health', utc_now(), 'PENDING', message))
            return True

    def flush(self, policy: dict, sender=None, retry_seconds: int = 300, local_dir: Path | None = None) -> dict:
        summary = {'sent': 0, 'retry': 0, 'local': 0}
        for item in self.pending():
            local = item['channel'].startswith('local')
            if local and local_dir is None:
                continue
            if not local and not policy.get('telegram_send_enabled', False):
                continue
            now = time.time()
            # pending() is a snapshot. A campaign reindex may merge away its
            # event before this worker claims the notice. Hold the same SQLite
            # writer reservation used by ingestion/reindex across *both* the
            # event/evidence validation and the outbox claim. Network delivery
            # and local file writes happen strictly after the lock is released.
            with self.db.candidate_transaction():
                # pending() is an unlocked snapshot. SQLite INTEGER PRIMARY KEY
                # may recycle a deleted notice ID after campaign reindex.
                with self.db.connect() as conn:
                    live = conn.execute('SELECT * FROM notifications WHERE id=?',
                                        (item['id'],)).fetchone()
                identity = ('event_id', 'batch_id', 'channel', 'created_at',
                            'payload', 'attempts', 'next_attempt', 'result')
                if live is None or any(live[field] != item[field] for field in identity):
                    continue
                if item['channel'].endswith('-verified'):
                    try:
                        event = self.db.get_event(item['event_id'])
                    except KeyError:
                        validation = None  # The snapshot refers to a merged event.
                    else:
                        validation = VerificationEngine().evaluate(Candidate(event['node'], event['source'],
                            event['title'], event['primary_url']), self.db.get_evidence(event['id']))
                    if validation is None or validation.status.value != 'CLAIMABLE':
                        with self.db.connect() as conn:
                            conn.execute("UPDATE notifications SET result='STALE' WHERE id=? "
                                "AND result IN ('PENDING','RETRY','CLAIMED') AND next_attempt<=?", (item['id'], now))
                        continue
                claim_deadline = now + 300
                with self.db.connect() as conn:
                    claimed = conn.execute("""UPDATE notifications SET result='CLAIMED',
                        next_attempt=?,attempts=attempts+1 WHERE id=? AND next_attempt<=?
                        AND result IN ('PENDING','RETRY','CLAIMED')
                        AND event_id IS ? AND batch_id=? AND channel=? AND created_at=?
                        AND payload=? AND attempts=? AND next_attempt=?""",
                        (claim_deadline, item['id'], now, item['event_id'], item['batch_id'],
                         item['channel'], item['created_at'], item['payload'],
                         item['attempts'], item['next_attempt'])).rowcount
            if not claimed:
                continue
            try:
                if local:
                    output = Path(local_dir)
                    output.mkdir(parents=True, exist_ok=True)
                    destination = output / f"notification-{item['id']}.json"
                    temporary = destination.with_suffix('.tmp')
                    temporary.write_text(json.dumps({'event_id': item['event_id'], 'batch_id': item['batch_id'],
                        'created_at': item['created_at'], 'message': item['payload']}, ensure_ascii=False, indent=2), encoding='utf-8')
                    temporary.replace(destination)
                    result = 'SENT'
                else:
                    result = (sender or TelegramNotifier(policy).send)(item['payload'])
            except Exception:
                # Exceptions can contain a bot token in a request URL. Never persist them.
                result = 'FAILED'
            success = result == 'SENT'
            with self.db.connect() as conn:
                # Do not mark a recycled ID as SENT after network/file I/O.
                conn.execute('''UPDATE notifications SET result=?,next_attempt=? WHERE id=?
                    AND result='CLAIMED' AND attempts=? AND next_attempt=?
                    AND event_id IS ? AND batch_id=? AND channel=? AND created_at=? AND payload=?''',
                    ('SENT' if success else 'RETRY', 0 if success else now + max(0, retry_seconds),
                     item['id'], item['attempts'] + 1, claim_deadline, item['event_id'],
                     item['batch_id'], item['channel'], item['created_at'], item['payload']))
            summary['local' if local and success else 'sent' if success else 'retry'] += 1
        return summary


class TelegramNotifier:
    def __init__(self, policy: dict):
        self.policy = policy

    def send(self, text: str) -> str:
        if not self.policy.get('telegram_send_enabled', False):
            return 'DISABLED'
        token = os.getenv('WOOLRADAR_TELEGRAM_BOT_TOKEN', '')
        chat_id = os.getenv('WOOLRADAR_TELEGRAM_CHAT_ID', '')
        if not token or not chat_id:
            return 'MISSING_CREDENTIALS'
        payload = urllib.parse.urlencode({'chat_id': chat_id, 'text': text, 'disable_web_page_preview': 'true'}).encode()
        request = urllib.request.Request(f'https://api.telegram.org/bot{token}/sendMessage', data=payload, method='POST')
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read())
        return 'SENT' if result.get('ok') else 'FAILED'
