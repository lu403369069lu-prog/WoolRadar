import sqlite3,tempfile,unittest
from contextlib import closing,contextmanager
from pathlib import Path
from unittest.mock import patch
from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue

class SchemaAndCooldownInterleavingTests(unittest.TestCase):
    def test_future_schema_committed_after_inspection_is_never_downgraded(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db.sqlite';Database(path)
            class RacingDatabase(Database):
                @contextmanager
                def connect(self):
                    if not getattr(self,'injected',False):
                        self.injected=True
                        with closing(sqlite3.connect(self.path)) as writer:
                            writer.execute('PRAGMA user_version=2');writer.execute('CREATE TABLE future_sentinel(x)');writer.commit()
                    with super().connect() as conn:yield conn
            with self.assertRaisesRegex(RuntimeError,'UNSUPPORTED_DATABASE_SCHEMA_VERSION'):RacingDatabase(path)
            with closing(sqlite3.connect(path)) as conn:
                self.assertEqual(conn.execute('PRAGMA user_version').fetchone()[0],2)
                self.assertIsNotNone(conn.execute("SELECT name FROM sqlite_master WHERE name='future_sentinel'").fetchone())

    def merged_notice(self,root,old_state,current_state='RETRY'):
        db=Database(root/'db.sqlite')
        a=db.upsert_candidate(Candidate('n','one','Acme Launch 2026','https://one.example/offer')).event_id
        with db.connect() as c:c.execute("UPDATE events SET canonical_key='historical-key' WHERE id=?",(a,))
        b=db.upsert_candidate(Candidate('n','two','Acme Launch 2026','https://two.example/offer')).event_id
        q=NotificationQueue(db);q.enqueue(a,'','telegram','survivor');q.enqueue(b,'','telegram','loser')
        with db.connect() as c:
            c.execute('UPDATE notifications SET result=?,attempts=1,next_attempt=30300 WHERE event_id=?',(current_state,a))
            c.execute('UPDATE notifications SET result=?,attempts=2,next_attempt=37200 WHERE event_id=?',(old_state,b))
        answer=db.reindex();self.assertEqual(answer['merged'],1)
        with db.connect() as c:row=dict(c.execute('SELECT * FROM notifications').fetchone())
        self.assertEqual(row['next_attempt'],37200);self.assertEqual(row['attempts'],2)
        with patch('core.notify.time.time',return_value=30301):
            self.assertEqual(NotificationQueue(Database(db.path)).flush({'telegram_send_enabled':True},sender=lambda _:self.fail('cooldown lost during merge'))['sent'],0)
        return row

    def test_merge_preserves_retry_and_uncertain_cooldown_in_both_directions(self):
        for old,current in [('RETRY','RETRY'),('UNCERTAIN','RETRY'),('RETRY','UNCERTAIN')]:
            with self.subTest(old=old,current=current),tempfile.TemporaryDirectory() as td:
                row=self.merged_notice(Path(td),old,current)
                self.assertEqual(row['result'],'UNCERTAIN' if 'UNCERTAIN' in (old,current) else 'RETRY')

    def test_active_claim_retains_longer_cooldown_after_merge(self):
        with tempfile.TemporaryDirectory() as td:
            row=self.merged_notice(Path(td),'RETRY','CLAIMED')
            self.assertEqual(row['result'],'CLAIMED')
