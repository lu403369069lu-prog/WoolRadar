"""A report must retain one event/evidence/status identity during real review."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from core.db import Database
from core.models import Candidate,Evidence,Status
from core.report import ReportGenerator

class ReportSnapshotTests(unittest.TestCase):
    def check_snapshot(self,claimable):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);db=Database(root/'radar.db');writer=Database(db.path)
            a,b='https://publisher.example/a','https://publisher.example/b'
            titles={a:'Launch Vendor credit grant',b:'Last chance Vendor credit grant'}
            first,old=[db.upsert_candidate(Candidate('n','s',titles[u],u)).event_id for u in (a,b)]
            if claimable:db.set_status(old,Status.CLAIMABLE,'test stale state','PUBLIC_APPLICATION')
            review={'method':'normal_browser_read','campaign_url':'https://gleam.io/Ab123','member_urls':[a,b],'member_titles':titles}
            attempted,finished=threading.Event(),threading.Event();results={};original=db.list_events
            def migrate():
                attempted.set()
                try:
                    writer.review_campaign(review)
                    value=writer.upsert_candidate(Candidate('n','s','Unrelated grant','https://unrelated.example/new'))
                    results['id']=value.event_id
                    writer.add_evidence(value.event_id,Evidence('official','https://unrelated.example/new','unrelated-proof',claims={'open':True,'public':True}))
                except BaseException as exc:results['error']=repr(exc)
                finally:finished.set()
            worker=threading.Thread(target=migrate)
            def snapshot():
                rows=original();worker.start();self.assertTrue(attempted.wait(5))
                results['blocked']=not finished.wait(.2)
                return rows
            try:
                with patch.object(db,'list_events',side_effect=snapshot):paths=ReportGenerator(db,root/'reports').generate('2026-10-16')
            finally:
                if worker.ident is not None:worker.join(10)
            self.assertFalse(worker.is_alive());self.assertNotIn('error',results)
            self.assertTrue(results['blocked'],'migration changed event identity during report snapshot')
            self.assertEqual(results['id'],old,'exercise actual rowid reuse')
            data=json.loads(paths.json.read_text(encoding='utf-8'))
            old_rows=[x for x in data['events'] if x['primary_url']==b];self.assertEqual(len(old_rows),1)
            self.assertFalse(any(e['url']=='https://unrelated.example/new' for x in old_rows for e in x['evidence']))
            replacement=writer.get_event(old);self.assertEqual(replacement['status'],'DISCOVERED')
            with writer.connect() as conn:self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(),[])
    def test_evidence_cannot_be_attached_to_recycled_report_id(self):self.check_snapshot(False)
    def test_claimable_revalidation_cannot_write_to_recycled_report_id(self):self.check_snapshot(True)

if __name__=='__main__':unittest.main()
