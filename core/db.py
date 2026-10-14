from __future__ import annotations

import json
import sqlite3
import hashlib
from datetime import datetime
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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA foreign_keys=ON')
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS campaign_links (url TEXT PRIMARY KEY, review_json TEXT NOT NULL)')
            conn.execute('CREATE TABLE IF NOT EXISTS migration_evidence_archive (id INTEGER PRIMARY KEY, original_event_id INTEGER, merged_into INTEGER, migrated_at TEXT, payload_json TEXT NOT NULL)')
            conn.executescript('''
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
                );
            ''')
            columns = {row[1] for row in conn.execute('PRAGMA table_info(notifications)')}
            for name, declaration in (('payload', "TEXT NOT NULL DEFAULT ''"),
                                      ('attempts', 'INTEGER NOT NULL DEFAULT 0'),
                                      ('next_attempt', 'REAL NOT NULL DEFAULT 0')):
                if name not in columns:
                    conn.execute(f'ALTER TABLE notifications ADD COLUMN {name} {declaration}')

    def upsert_candidate(self, candidate: Candidate) -> UpsertResult:
        with self.connect() as conn:
            link = conn.execute('SELECT review_json FROM campaign_links WHERE url=?', (normalize_url(candidate.url),)).fetchone()
        if link:
            candidate.metadata = {**candidate.metadata, 'campaign_review': json.loads(link[0])}
        key = canonical_key(candidate)
        batch = candidate.batch_id or ''
        now = candidate.discovered_at or utc_now()
        with self.connect() as conn:
            row = conn.execute('SELECT id FROM events WHERE canonical_key=? AND batch_id=?', (key, batch)).fetchone()
            notify = row is None
            if row is None:
                cursor = conn.execute(
                    '''INSERT INTO events(canonical_key,batch_id,title,primary_url,source,node,published_at,first_seen,last_seen,metadata_json)
                       VALUES(?,?,?,?,?,?,?,?,?,?)''',
                    (key, batch, candidate.title, candidate.url, candidate.source, candidate.node,
                     candidate.published_at, now, now, json.dumps(candidate.metadata, ensure_ascii=False)))
                event_id = cursor.lastrowid
            else:
                event_id = int(row['id'])
                conn.execute('UPDATE events SET last_seen=? WHERE id=?', (now, event_id))
            conn.execute(
                'INSERT OR IGNORE INTO sightings(event_id,node,source,url,discovered_at) VALUES(?,?,?,?,?)',
                (event_id, candidate.node, candidate.source, candidate.url, now))
        return UpsertResult(int(event_id), notify)

    def add_evidence(self, event_id: int, evidence: Evidence) -> None:
        with self.connect() as conn:
            conn.execute(
                '''INSERT INTO evidence(event_id,kind,url,provenance_key,checked_at,excerpt,claims_json)
                   VALUES(?,?,?,?,?,?,?) ON CONFLICT(event_id,url,provenance_key) DO UPDATE SET
                   kind=excluded.kind,checked_at=excluded.checked_at,excerpt=excluded.excerpt,
                   claims_json=excluded.claims_json''',
                (event_id, evidence.kind, evidence.url, evidence.provenance_key, evidence.checked_at,
                 evidence.excerpt, json.dumps(evidence.claims, ensure_ascii=False)))

    def set_status(self, event_id: int, status: Status, reason: str, claim_scope: str = 'NONE') -> None:
        with self.connect() as conn:
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
        with self.connect() as conn:
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

    def reindex(self, campaign_review: dict | None = None) -> dict:
        """Transactional key migration; retain a consistent, recoverable SQLite backup."""
        backup = self.path.with_name(self.path.stem + '-before-reindex-' +
            utc_now().replace(':', '').replace('-', '') + '.db')
        if backup.exists():
            raise FileExistsError(backup)
        with self.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            # Backup through a separate read connection so WAL contents are included.
            with closing(sqlite3.connect(self.path)) as reader, closing(sqlite3.connect(backup)) as target:
                reader.backup(target)
            if campaign_review is not None:
                for url in campaign_review['member_urls']:
                    conn.execute('INSERT OR REPLACE INTO campaign_links VALUES(?,?)', (normalize_url(url), json.dumps(campaign_review, ensure_ascii=False)))
                    members = conn.execute('SELECT id,primary_url FROM events UNION SELECT event_id,url FROM sightings UNION SELECT event_id,url FROM evidence').fetchall()
                    for member in members:
                        if normalize_url(member[1]) != normalize_url(url):
                            continue
                        conn.execute('''INSERT INTO evidence(event_id,kind,url,provenance_key,checked_at,excerpt,claims_json)
                            VALUES(?,?,?,?,?,?,?) ON CONFLICT(event_id,url,provenance_key) DO UPDATE SET
                            checked_at=excluded.checked_at''', (member[0], 'community_repost', member[1],
                            'reviewed-campaign:' + campaign_review['campaign_url'], utc_now(),
                            'Public article embeds the same reviewed campaign identity; no independent qualification proof.',
                            json.dumps({'campaign_identity': campaign_review['campaign_url'], 'method': 'normal_browser_read'})))
            rows = [dict(r) for r in conn.execute('SELECT * FROM events ORDER BY id')]
            for row in rows:
                conn.execute('UPDATE events SET canonical_key=? WHERE id=?',
                    ('migration:' + str(row['id']), row['id']))
            groups = {}
            merged = 0
            for row in rows:
                metadata = json.loads(row['metadata_json'])
                link = conn.execute('SELECT review_json FROM campaign_links WHERE url=?', (normalize_url(row['primary_url']),)).fetchone()
                if link:
                    metadata['campaign_review'] = json.loads(link[0])
                    conn.execute('UPDATE events SET metadata_json=? WHERE id=?', (json.dumps(metadata, ensure_ascii=False), row['id']))
                candidate = Candidate(row['node'], row['source'], row['title'], row['primary_url'],
                    published_at=row['published_at'] or '', batch_id=row['batch_id'],
                    metadata=metadata)
                key = canonical_key(candidate)
                identity = (key, row['batch_id'])
                if identity not in groups:
                    groups[identity] = row['id']
                    conn.execute('UPDATE events SET canonical_key=? WHERE id=?', (key, row['id']))
                    continue
                keep, old = groups[identity], row['id']
                self._merge_evidence(conn, keep, old)
                for table, columns in (
                    ('sightings', 'node,source,url,discovered_at'),
                    ('notifications', 'batch_id,channel,created_at,result,payload,attempts,next_attempt')):
                    conn.execute(f'INSERT OR IGNORE INTO {table}(event_id,{columns}) '
                        f'SELECT ?,{columns} FROM {table} WHERE event_id=?', (keep, old))
                    conn.execute(f'DELETE FROM {table} WHERE event_id=?', (old,))
                conn.execute('UPDATE status_history SET event_id=? WHERE event_id=?', (keep, old))
                conn.execute('UPDATE events SET first_seen=min(first_seen,?),last_seen=max(last_seen,?) WHERE id=?',
                    (row['first_seen'], row['last_seen'], keep))
                conn.execute('DELETE FROM events WHERE id=?', (old,))
                merged += 1
        return {'backup': str(backup), 'merged': merged, 'remaining': len(rows) - merged}

    def _merge_evidence(self, conn, keep, old):
        columns = ('kind', 'url', 'provenance_key', 'checked_at', 'excerpt', 'claims_json')
        for incoming in [dict(row) for row in conn.execute('SELECT * FROM evidence WHERE event_id=?', (old,))]:
            prior = conn.execute('SELECT * FROM evidence WHERE event_id=? AND url=? AND provenance_key=?', (keep, incoming['url'], incoming['provenance_key'])).fetchone()
            if prior is None:
                conn.execute('INSERT INTO evidence(event_id,kind,url,provenance_key,checked_at,excerpt,claims_json) VALUES(?,?,?,?,?,?,?)', (keep, *(incoming[key] for key in columns)))
                continue
            prior = dict(prior)
            for version in (prior, incoming):
                conn.execute('INSERT INTO migration_evidence_archive(original_event_id,merged_into,migrated_at,payload_json) VALUES(?,?,?,?)',
                             (version['event_id'], keep, utc_now(), json.dumps(version, ensure_ascii=False)))
            try:
                before = datetime.fromisoformat(prior['checked_at'].replace('Z', '+00:00'))
                after = datetime.fromisoformat(incoming['checked_at'].replace('Z', '+00:00'))
                if before.tzinfo is None or after.tzinfo is None:
                    raise ValueError('EVIDENCE_TIMEZONE_REQUIRED')
                order = (after > before) - (after < before)
            except (ValueError, TypeError, AttributeError):
                order = 0
            if incoming['kind'] == prior['kind'] and order > 0:
                conn.execute('UPDATE evidence SET kind=?,checked_at=?,excerpt=?,claims_json=? WHERE id=?',
                             (incoming['kind'], incoming['checked_at'], incoming['excerpt'], incoming['claims_json'], prior['id']))
            elif incoming['kind'] != prior['kind'] or (order == 0 and incoming['claims_json'] != prior['claims_json']):
                # Unordered/conflicting versions stay visible; the shared URL
                # keeps them in one provenance group, never two independent votes.
                version_key = incoming['provenance_key'] + ':migration:' + hashlib.sha256(json.dumps({key: incoming[key] for key in columns}, sort_keys=True).encode()).hexdigest()[:16]
                conn.execute('INSERT OR IGNORE INTO evidence(event_id,kind,url,provenance_key,checked_at,excerpt,claims_json) VALUES(?,?,?,?,?,?,?)',
                             (keep, incoming['kind'], incoming['url'], version_key, incoming['checked_at'], incoming['excerpt'], incoming['claims_json']))
        conn.execute('DELETE FROM evidence WHERE event_id=?', (old,))
