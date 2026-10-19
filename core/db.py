from __future__ import annotations

import json
import sqlite3
import hashlib
import threading
from datetime import datetime
from uuid import uuid4
from contextlib import contextmanager, closing
from dataclasses import dataclass
from pathlib import Path

from .dedup import canonical_key, normalize_url, reviewed_campaign_url
from .models import Candidate, Evidence, Status, utc_now


@dataclass(slots=True)
class UpsertResult:
    event_id: int
    notify: bool


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._transaction_state = threading.local()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connect(self):
        active = getattr(self._transaction_state, 'connection', None)
        if active is not None:
            # The enclosing candidate transaction owns commit/rollback/close.
            yield active
            return
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA foreign_keys=ON')
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def write_transaction(self):
        """Reserve a writer slot and reject incompatible migrations atomically.

        All application writes must enter through this boundary. Reusing an
        existing candidate transaction retains its original writer fence.
        """
        with self.connect() as conn:
            if not conn.in_transaction:
                conn.execute('BEGIN IMMEDIATE')
            if conn.execute('PRAGMA user_version').fetchone()[0] > 1:
                raise RuntimeError('UNSUPPORTED_DATABASE_SCHEMA_VERSION')
            yield conn

    @contextmanager
    def candidate_transaction(self):
        """Keep one candidate's related writes atomic against other SQLite writers.

        This reservation is database-backed, so it also covers other processes.
        Only this Database instance in this thread reuses the connection. Never
        perform network I/O or reindex/backup inside the reserved transaction.
        """
        if getattr(self._transaction_state, 'connection', None) is not None:
            raise RuntimeError('CANDIDATE_TRANSACTION_ALREADY_ACTIVE')
        with self.write_transaction() as conn:
            if not conn.in_transaction:
                conn.execute('BEGIN IMMEDIATE')
            self._transaction_state.connection = conn
            try:
                yield
            finally:
                del self._transaction_state.connection

    def _init_schema(self) -> None:
        # Reject a future version before calling connect(), which otherwise
        # switches SQLite into WAL and may execute DDL against an unknown file.
        # The inspection URI is read-only and leaves the DB untouched.
        if self.path.is_file():
            uri = self.path.resolve().as_uri() + '?mode=ro'
            with closing(sqlite3.connect(uri, uri=True)) as inspection:
                version = inspection.execute('PRAGMA user_version').fetchone()[0]
            if version > 1:
                raise RuntimeError('UNSUPPORTED_DATABASE_SCHEMA_VERSION')
        with self.write_transaction() as conn:
            # Recheck after the writer reservation: another version may have
            # committed since the read-only preflight. Never use executescript
            # here: its implicit COMMIT would release this migration fence.
            if not conn.in_transaction:
                conn.execute('BEGIN IMMEDIATE')
            if conn.execute('PRAGMA user_version').fetchone()[0] > 1:
                raise RuntimeError('UNSUPPORTED_DATABASE_SCHEMA_VERSION')
            schema = '''
                CREATE TABLE IF NOT EXISTS campaign_links (url TEXT PRIMARY KEY, review_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS migration_evidence_archive (id INTEGER PRIMARY KEY, original_event_id INTEGER, merged_into INTEGER, migrated_at TEXT, payload_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    canonical_key TEXT NOT NULL,
                    batch_id TEXT NOT NULL DEFAULT '',
                    title TEXT NOT NULL,
                    primary_url TEXT NOT NULL,
                    source TEXT NOT NULL,
                    node TEXT NOT NULL,
                    published_at TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'DISCOVERED',
                    claim_scope TEXT NOT NULL DEFAULT 'NONE',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    UNIQUE(canonical_key, batch_id)
                );
                CREATE TABLE IF NOT EXISTS sightings (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER NOT NULL REFERENCES events(id),
                    node TEXT NOT NULL,
                    source TEXT NOT NULL,
                    url TEXT NOT NULL,
                    discovered_at TEXT NOT NULL,
                    UNIQUE(event_id, node, url)
                );
                CREATE TABLE IF NOT EXISTS evidence (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER NOT NULL REFERENCES events(id),
                    kind TEXT NOT NULL,
                    url TEXT NOT NULL,
                    provenance_key TEXT NOT NULL,
                    checked_at TEXT NOT NULL,
                    excerpt TEXT,
                    claims_json TEXT NOT NULL DEFAULT '{}',
                    UNIQUE(event_id, url, provenance_key)
                );
                CREATE TABLE IF NOT EXISTS status_history (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER NOT NULL REFERENCES events(id),
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    changed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS node_runs (
                    id INTEGER PRIMARY KEY,
                    node TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    items INTEGER NOT NULL DEFAULT 0,
                    error_code TEXT,
                    detail TEXT
                );
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER REFERENCES events(id),
                    batch_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    result TEXT NOT NULL,
                    UNIQUE(event_id, batch_id, channel)
                );
                CREATE TABLE IF NOT EXISTS node_health (
                    node TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL,
                    checked_at TEXT NOT NULL
                );            '''
            # This is the fixed internal CREATE TABLE schema, with no external
            # SQL, trigger bodies or semicolons inside values.
            for statement in schema.split(';'):
                if statement.strip():
                    conn.execute(statement)

            columns = {row[1] for row in conn.execute('PRAGMA table_info(notifications)')}
            for name, declaration in (('payload', "TEXT NOT NULL DEFAULT ''"),
                                      ('attempts', 'INTEGER NOT NULL DEFAULT 0'),
                                      ('next_attempt', 'REAL NOT NULL DEFAULT 0')):
                if name not in columns:
                    conn.execute(f'ALTER TABLE notifications ADD COLUMN {name} {declaration}')
            # A confirmed external/local delivery is terminal across every SQLite
            # connection and process, not merely within NotificationQueue.flush.
            # Existing older databases receive this idempotent trigger on open.
            conn.execute('''CREATE TRIGGER IF NOT EXISTS notifications_sent_final
                BEFORE UPDATE OF result ON notifications
                FOR EACH ROW
                WHEN OLD.result='SENT' AND NEW.result!='SENT'
                BEGIN SELECT RAISE(ABORT, 'SENT_FINAL'); END''')
            # Publish version with all schema changes, within the migration transaction.
            conn.execute('PRAGMA user_version=1')

    def upsert_candidate(self, candidate: Candidate) -> UpsertResult:
        with self.write_transaction() as conn:
            # Prevent review/reindex from committing between the campaign lookup
            # and event insertion: both operations use BEGIN IMMEDIATE.
            if not conn.in_transaction:
                conn.execute('BEGIN IMMEDIATE')
            link = conn.execute('SELECT review_json FROM campaign_links WHERE url=?', (normalize_url(candidate.url),)).fetchone()
            if link:
                candidate.metadata = {**candidate.metadata, 'campaign_review': json.loads(link[0])}
            key = canonical_key(candidate)
            batch = candidate.batch_id or ''
            now = candidate.discovered_at or utc_now()
            # The lookup and insertion must not race across collection nodes.
            # SQLite resolves the unique-key conflict atomically, and rowcount
            # distinguishes the first sighting from concurrent duplicates.
            cursor = conn.execute(
                '''INSERT INTO events(canonical_key,batch_id,title,primary_url,source,node,published_at,first_seen,last_seen,metadata_json)
                   VALUES(?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(canonical_key,batch_id) DO NOTHING''',
                (key, batch, candidate.title, candidate.url, candidate.source, candidate.node,
                 candidate.published_at, now, now, json.dumps(candidate.metadata, ensure_ascii=False)))
            notify = cursor.rowcount == 1
            row = conn.execute('SELECT id FROM events WHERE canonical_key=? AND batch_id=?', (key, batch)).fetchone()
            event_id = int(row['id'])
            if not notify:
                conn.execute('UPDATE events SET last_seen=? WHERE id=?', (now, event_id))
            conn.execute(
                'INSERT OR IGNORE INTO sightings(event_id,node,source,url,discovered_at) VALUES(?,?,?,?,?)',
                (event_id, candidate.node, candidate.source, candidate.url, now))
        return UpsertResult(int(event_id), notify)

    def add_evidence(self, event_id: int, evidence: Evidence) -> None:
        with self.write_transaction() as conn:
            conn.execute(
                '''INSERT INTO evidence(event_id,kind,url,provenance_key,checked_at,excerpt,claims_json)
                   VALUES(?,?,?,?,?,?,?) ON CONFLICT(event_id,url,provenance_key) DO UPDATE SET
                   kind=excluded.kind,checked_at=excluded.checked_at,excerpt=excluded.excerpt,
                   claims_json=excluded.claims_json''',
                (event_id, evidence.kind, evidence.url, evidence.provenance_key, evidence.checked_at,
                 evidence.excerpt, json.dumps(evidence.claims, ensure_ascii=False)))

    def set_status(self, event_id: int, status: Status, reason: str, claim_scope: str = 'NONE') -> None:
        with self.write_transaction() as conn:
            # Lock before reading the previous status so history cannot record
            # another worker's state while this transaction is waiting to write.
            if not conn.in_transaction:
                conn.execute('BEGIN IMMEDIATE')
            row = conn.execute('SELECT status FROM events WHERE id=?', (event_id,)).fetchone()
            if row is None:
                raise KeyError(event_id)
            old = row['status']
            conn.execute('UPDATE events SET status=?, claim_scope=? WHERE id=?', (status.value, claim_scope, event_id))
            conn.execute(
                'INSERT INTO status_history(event_id,old_status,new_status,reason,changed_at) VALUES(?,?,?,?,?)',
                (event_id, old, status.value, reason, utc_now()))

    def record_node_run(self, node: str, status: str, items: int = 0, error_code: str = '', detail: str = '') -> None:
        now = utc_now()
        with self.write_transaction() as conn:
            conn.execute(
                'INSERT INTO node_runs(node,started_at,finished_at,status,items,error_code,detail) VALUES(?,?,?,?,?,?,?)',
                (node, now, now, status, items, error_code, detail))

    def list_events(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM events ORDER BY first_seen DESC, id DESC').fetchall()
            return [dict(row) for row in rows]

    def get_event(self, event_id: int) -> dict:
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
        if row is None:
            raise KeyError(event_id)
        return dict(row)

    def get_evidence(self, event_id: int) -> list[Evidence]:
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM evidence WHERE event_id=? ORDER BY id', (event_id,)).fetchall()
        return [Evidence(
            kind=row['kind'], url=row['url'], provenance_key=row['provenance_key'],
            checked_at=row['checked_at'], excerpt=row['excerpt'] or '',
            claims=json.loads(row['claims_json'] or '{}'),
        ) for row in rows]

    def latest_node_runs(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute('''SELECT n.* FROM node_runs n JOIN (
                SELECT node, MAX(id) id FROM node_runs GROUP BY node
            ) latest ON n.id=latest.id ORDER BY n.node''').fetchall()
            return [dict(row) for row in rows]

    def review_campaign(self, review: dict) -> dict:
        members = review.get('member_urls', [])
        if not isinstance(members, list) or not members or not reviewed_campaign_url(review, members[0]):
            raise ValueError('EXPLICIT_PUBLIC_CAMPAIGN_REVIEW_REQUIRED')
        members = {normalize_url(url) for url in members}
        if len(members) < 2:
            raise ValueError('TWO_DISTINCT_ARTICLES_REQUIRED')
        with self.connect() as conn:
            seen = {normalize_url(row[0]) for row in conn.execute('SELECT primary_url FROM events')}
            seen.update(normalize_url(row[0]) for row in conn.execute('SELECT url FROM sightings'))
            if not members <= seen:
                raise ValueError('CAMPAIGN_MEMBER_NOT_IN_DATABASE')
            prior = {row[0]: json.loads(row[1]) for row in conn.execute('SELECT url,review_json FROM campaign_links') if row[0] in members}
            if any(item.get('campaign_url') != review.get('campaign_url') for item in prior.values()):
                raise ValueError('CAMPAIGN_REVIEW_CONFLICT')
            if set(prior) == members:
                return {'unchanged': True, 'merged': 0}
        return self.reindex(campaign_review=review)

    def preview_reindex(self) -> dict:
        """Read-only inspection of current-key migration, without merging or backing up.

        Does not reconstruct campaigns already incorrectly merged under older
        algorithms or predict a not-yet-stored manual campaign review.
        """
        uri = self.path.resolve().as_uri() + '?mode=ro'
        with closing(sqlite3.connect(uri, uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            # Stable WAL read snapshot across events, campaign reviews and notices.
            conn.execute('BEGIN')
            rows = [dict(item) for item in conn.execute('SELECT * FROM events ORDER BY id')]
            links = {item['url']: json.loads(item['review_json']) for item in
                     conn.execute('SELECT url,review_json FROM campaign_links')}
            notifications = [dict(item) for item in
                             conn.execute('SELECT event_id,batch_id,channel FROM notifications')]
        groups = {}
        changed = 0
        for row in rows:
            metadata = json.loads(row['metadata_json'] or '{}')
            review = links.get(normalize_url(row['primary_url']))
            if review:
                metadata['campaign_review'] = review
            candidate = Candidate(row['node'], row['source'], row['title'], row['primary_url'],
                                  published_at=row['published_at'] or '',
                                  batch_id=row['batch_id'], metadata=metadata)
            key = canonical_key(candidate)
            changed += key != row['canonical_key']
            groups.setdefault((key, row['batch_id']), []).append(row['id'])
        collisions = [ids for ids in groups.values() if len(ids) > 1]
        notification_index = {}
        for notice in notifications:
            notice_key = (notice['batch_id'], notice['channel'])
            notification_index.setdefault(notice_key, set()).add(notice['event_id'])
        conflict_count = sum(
            sum(len(set(group) & event_ids) - 1 for event_ids in notification_index.values()
                if len(set(group) & event_ids) > 1)
            for group in collisions)
        return {
            'total_events': len(rows), 'changed_keys': changed,
            'would_merge_events': sum(len(ids) - 1 for ids in collisions),
            'collision_groups': [sorted(ids) for ids in collisions],
            'notification_conflict_count': conflict_count,
            'unrecoverable_prior_merges': 'cannot infer from current event rows',
        }

    def reindex(self, campaign_review: dict | None = None) -> dict:
        """Transactional key migration; retain a consistent, recoverable SQLite backup."""
        # utc_now() is second-granularity: two valid reviews/reindexes in the
        # same second must never collide on an otherwise safe backup filename.
        backup = self.path.with_name(self.path.stem + '-before-reindex-' +
            utc_now().replace(':', '').replace('-', '') + '-' + uuid4().hex[:12] + '.db')
        if backup.exists():
            raise FileExistsError(backup)
        with self.write_transaction() as conn:
            if not conn.in_transaction:
                conn.execute('BEGIN IMMEDIATE')
            if campaign_review is not None:
                # review_campaign() checks these preconditions before calling
                # reindex(), but another reviewer can commit a conflicting
                # campaign while this caller waits for the SQLite writer lock.
                # Recheck *inside* the same reservation before making a backup
                # or replacing campaign_links. A second different review must
                # never silently reassign an already reviewed campaign.
                members = {normalize_url(url) for url in campaign_review['member_urls']}
                seen = {normalize_url(row[0]) for row in conn.execute(
                    'SELECT primary_url FROM events')}
                seen.update(normalize_url(row[0]) for row in conn.execute(
                    'SELECT url FROM sightings'))
                if not members <= seen:
                    raise ValueError('CAMPAIGN_MEMBER_NOT_IN_DATABASE')
                for url in members:
                    previous…3797 tokens truncated…def pending(self) -> list[dict]:
        with self.db.connect() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM notifications WHERE result IN ('PENDING','RETRY','CLAIMED','UNCERTAIN') ORDER BY id")]

    def record_health(self, node: str, status: str, error_code: str) -> bool:
        if status == 'SKIPPED':
            return False  # No request means no evidence of recovery.
        fingerprint = 'OK' if status == 'OK' else ('ISSUE:' + error_code if error_code else status + ':')
        with self.db.write_transaction() as conn:
            if not conn.in_transaction:
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
                        with self.db.write_transaction() as conn:
                            conn.execute("UPDATE notifications SET result='STALE' WHERE id=? "
                                "AND result IN ('PENDING','RETRY','CLAIMED','UNCERTAIN') AND next_attempt<=?", (item['id'], now))
                        continue
                claim_deadline = now + 300
                with self.db.write_transaction() as conn:
                    claimed = conn.execute("""UPDATE notifications SET result='CLAIMED',
                        next_attempt=?,attempts=attempts+1 WHERE id=? AND next_attempt<=?
                        AND result IN ('PENDING','RETRY','CLAIMED','UNCERTAIN')
                        AND event_id IS ? AND batch_id=? AND channel=? AND created_at=?
                        AND payload=? AND attempts=? AND next_attempt=?""",
                        (claim_deadline, item['id'], now, item['event_id'], item['batch_id'],
                         item['channel'], item['created_at'], item['payload'],
                         item['attempts'], item['next_attempt'])).rowcount
            if not claimed:
                continue
            retry_delay = max(0, retry_seconds)
            try:
                if local:
                    output = Path(local_dir)
                    output.mkdir(parents=True, exist_ok=True)
                    # SQLite can recycle an integer ID after campaign reindex. Use a
                    # stable fingerprint of the full notification identity so a
                    # later unrelated notice never overwrites the first receipt.
                    identity_bytes = json.dumps([
                        item['id'], item['event_id'], item['batch_id'],
                        item['channel'], item['created_at'], item['payload']
                    ], ensure_ascii=False, separators=(',', ':')).encode('utf-8')
                    receipt_id = hashlib.sha256(identity_bytes).hexdigest()[:20]
                    destination = output / f"notification-{item['id']}-{receipt_id}.json"
                    # The claim attempt and a random nonce isolate files from
                    # another worker that reclaimed the same durable outbox row.
                    attempt = item['attempts'] + 1
                    temporary = destination.with_name(
                        f".{destination.name}.attempt-{attempt}-{os.urandom(8).hex()}.tmp")
                    try:
                        temporary.write_text(json.dumps({
                            'event_id': item['event_id'], 'batch_id': item['batch_id'],
                            'created_at': item['created_at'], 'message': item['payload']
                        }, ensure_ascii=False, indent=2), encoding='utf-8')
                        # A worker can lose ownership during the file write.
                        # Serialize the final claim check, atomic rename, and
                        # SENT transition with the same SQLite writer lock.
                        with self.db.write_transaction() as conn:
                            if not conn.in_transaction:
                                conn.execute('BEGIN IMMEDIATE')
                            owned = conn.execute("""SELECT 1 FROM notifications
                                WHERE id=? AND result='CLAIMED' AND attempts=?
                                AND next_attempt=? AND event_id IS ? AND batch_id=?
                                AND channel=? AND created_at=? AND payload=?""",
                                (item['id'], attempt, claim_deadline, item['event_id'],
                                 item['batch_id'], item['channel'], item['created_at'],
                                 item['payload'])).fetchone()
                            if owned is None:
                                summary['uncertain'] = summary.get('uncertain', 0) + 1
                                continue  # Never rename files belonging to a new owner.
                            try:
                                identical_receipt = destination.read_bytes() == temporary.read_bytes()
                            except FileNotFoundError:
                                identical_receipt = False
                            if not identical_receipt:
                                temporary.replace(destination)
                            updated = conn.execute("""UPDATE notifications
                                SET result='SENT',next_attempt=0
                                WHERE id=? AND result='CLAIMED' AND attempts=?""",
                                (item['id'], attempt)).rowcount
                            if updated != 1:
                                raise RuntimeError('LOCAL_DELIVERY_CLAIM_LOST')
                        summary['local'] += 1
                        continue  # Local SENT was already committed under fencing.
                    finally:
                        temporary.unlink(missing_ok=True)
                else:
                    result = (sender or TelegramNotifier(policy).send)(item['payload'])
            except TelegramRateLimited as exc:
                retry_delay = max(retry_delay, exc.retry_after)
                result = 'RATE_LIMITED'
            except urllib.error.HTTPError as exc:
                # A server-declared 429 cooldown is a definite throttling
                # response, not confirmation of a sent message. Do not store
                # exception text (the request URL can contain a bot token).
                if not local and exc.code == 429:
                    header = exc.headers.get('Retry-After') if exc.headers else None
                    try:
                        body = json.loads(exc.read(8192))
                    except (ValueError, TypeError, OSError):
                        body = None
                    retry_delay = max(retry_delay, _retry_after(header, body, now))
                    result = 'RATE_LIMITED'
                else:
                    result = 'UNCERTAIN' if not local else 'FAILED'
            except Exception:
                # Exceptions can contain a bot token in a request URL. Never persist them.
                # Network timeouts may occur after Telegram accepted the send.
                # Keep the ambiguity durable instead of claiming a definite fail.
                result = 'UNCERTAIN' if not local else 'FAILED'
            success = result == 'SENT'
            with self.db.write_transaction() as conn:
                # Do not mark a recycled ID as SENT after network/file I/O.
                confirmed = conn.execute('''UPDATE notifications SET result=?,next_attempt=? WHERE id=?
                    AND result='CLAIMED' AND attempts=? AND next_attempt=?
                    AND event_id IS ? AND batch_id=? AND channel=? AND created_at=? AND payload=?''',
                    ('SENT' if success else 'UNCERTAIN' if result == 'UNCERTAIN' else 'RETRY',
                     0 if success else now + retry_delay,
                     item['id'], item['attempts'] + 1, claim_deadline, item['event_id'],
                     item['batch_id'], item['channel'], item['created_at'], item['payload'])).rowcount
            if confirmed != 1:
                # An external send may have happened, but migration/recycling
                # invalidated the durable outbox claim. Never count an
                # uncommitted delivery as confirmed. At-least-once remains.
                summary['uncertain'] = summary.get('uncertain', 0) + 1
            else:
                if result == 'UNCERTAIN':
                    summary['uncertain'] = summary.get('uncertain', 0) + 1
                else:
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
        if isinstance(result, dict) and result.get('ok') is False and result.get('error_code') == 429:
            raise TelegramRateLimited(_retry_after(body=result))
        return 'SENT' if isinstance(result, dict) and result.get('ok') is True else 'FAILED'
