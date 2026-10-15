"""Read-only migration preflight must observe one consistent WAL transaction."""
import hashlib
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock
from core.db import Database
from core.dedup import normalize_title, normalize_url
from core.models import Candidate


class ReindexSnapshotTests(TestCase):
    def test_concurrent_writer_not_visible_halfway_through_preview(self):
        with TemporaryDirectory() as folder:
            db = Database(Path(folder) / 'radar.db')
            url='https://vendor.example/promo'
            a = db.upsert_candidate(Candidate('n','s','Free VPS 1GB',url))
            normal_key=db.get_event(a.event_id)['canonical_key']
            old_title='Free VPS 1 GB'
            old_key=hashlib.sha256((normalize_title(old_title)+'|'+normalize_url(url)).encode()).hexdigest()[:24]
            with db.connect() as conn:
                conn.execute('UPDATE events SET canonical_key=? WHERE id=?',(old_key,a.event_id))
                conn.execute('''INSERT INTO events(canonical_key,batch_id,title,primary_url,source,node,first_seen,last_seen)
                                VALUES(?,?,?,?,?,?,?,?)''',(normal_key,'','Free VPS 1GB',url,'s','n2','2026-01-01','2026-01-01'))
                second=conn.execute('SELECT id FROM events WHERE canonical_key=?',(normal_key,)).fetchone()[0]
                conn.execute('''INSERT INTO notifications(event_id,batch_id,channel,created_at,result)
                                VALUES(?,?,?,?,?)''',(a.event_id,'','digest','2026-01-01','sent'))
            real_connect=sqlite3.connect
            hook_calls=[]
            class HookedConnection(sqlite3.Connection):
                def execute(self, sql, parameters=()):
                    if 'SELECT url,review_json FROM campaign_links' in sql:
                        with real_connect(db.path,timeout=5) as writer:
                            writer.execute('''INSERT INTO notifications(event_id,batch_id,channel,created_at,result)
                                              VALUES(?,?,?,?,?)''',(second,'','digest','2026-01-01','sent'))
                        hook_calls.append('writer-committed')
                    return super().execute(sql,parameters)
            def intercept(path,*args,**kwargs):
                if isinstance(path,str) and '?mode=ro' in path:
                    kwargs['factory']=HookedConnection
                return real_connect(path,*args,**kwargs)
            with mock.patch('core.db.sqlite3.connect',side_effect=intercept):
                result=db.preview_reindex()
            self.assertEqual(hook_calls,['writer-committed'])
            self.assertEqual(result['total_events'],2)
            self.assertEqual(result['would_merge_events'],1)
            self.assertEqual(result['notification_conflict_count'],0)
            with db.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM notifications').fetchone()[0],2)
