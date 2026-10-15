"""Atomic per-candidate persistence against a real concurrent campaign review."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from core.db import Database
from core.models import Candidate
from core.pipeline import Pipeline


class IngestTransactionTests(unittest.TestCase):
    def inbox(self, root, candidates):
        folder=root/'data/inbox';folder.mkdir(parents=True,exist_ok=True)
        (folder/'n.jsonl').write_text('\n'.join(json.dumps(x.to_dict()) for x in candidates),encoding='utf-8')

    def test_review_waits_until_evidence_and_status_are_committed(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);pipeline=Pipeline(root);other=Database(pipeline.db.path)
            urls=['https://publisher.example/a','https://publisher.example/b']
            titles=['Launch Vendor credit grant','Last chance Vendor credit grant']
            ids=[other.upsert_candidate(Candidate('n','s',title,url)).event_id for title,url in zip(titles,urls)]
            review={'method':'normal_browser_read','campaign_url':'https://gleam.io/Ab123',
                    'member_urls':urls,'member_titles':dict(zip(urls,titles))}
            self.inbox(root,[Candidate('n','s',titles[1],urls[1],source_kind='official',
                                      metadata={'evidence_claims':{'open':True,'public':True,'remaining':0}})])
            reached=threading.Event();release=threading.Event();attempted=threading.Event();done=threading.Event()
            results={};original=pipeline.db.upsert_candidate
            def pause(candidate):
                value=original(candidate);reached.set()
                if not release.wait(5):raise TimeoutError('test did not release ingest')
                return value
            def ingest():
                try:results['ingest']=pipeline.ingest_node('n')
                except BaseException as exc:results['ingest_error']=repr(exc)
            def merge():
                attempted.set()
                try:results['merge']=other.review_campaign(review)
                except BaseException as exc:results['merge_error']=repr(exc)
                finally:done.set()
            blocked=False
            with mock.patch.object(pipeline.db,'upsert_candidate',side_effect=pause):
                worker=threading.Thread(target=ingest);worker.start();migrator=threading.Thread(target=merge)
                try:
                    self.assertTrue(reached.wait(5));migrator.start();self.assertTrue(attempted.wait(5))
                    blocked=not done.wait(.2)
                finally:
                    release.set();worker.join(10)
                    if migrator.ident is not None:migrator.join(10)
            self.assertFalse(worker.is_alive());self.assertFalse(migrator.is_alive())
            self.assertTrue(blocked,'review committed after upsert but before evidence persistence')
            self.assertNotIn('ingest_error',results);self.assertNotIn('merge_error',results)
            events=other.list_events();self.assertEqual(len(events),1)
            self.assertEqual(events[0]['id'],ids[0]);self.assertEqual(events[0]['status'],'OFFICIAL_VERIFIED')
            self.assertEqual(events[0]['claim_scope'],'NONE')
            self.assertTrue(any(e.kind=='official' and e.claims.get('remaining')==0 for e in other.get_evidence(ids[0])))
            with other.connect() as conn:
                self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_failure_rolls_back_event_sighting_evidence_history_and_notice(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);pipeline=Pipeline(root)
            self.inbox(root,[Candidate('n','s','VendorA free VPS','https://a.example/free')])
            with mock.patch.object(pipeline.db,'set_status',side_effect=RuntimeError('injected-status-failure')):
                with self.assertRaisesRegex(RuntimeError,'injected-status-failure'):pipeline.ingest_node('n')
            with pipeline.db.connect() as conn:
                for table in ['events','sightings','evidence','status_history','notifications','node_runs']:
                    self.assertEqual(conn.execute('SELECT count(*) FROM '+table).fetchone()[0],0,table)
            self.assertEqual(pipeline.ingest_node('n')['notify'],1)
            self.assertEqual(pipeline.ingest_node('n')['notify'],0)
            self.assertEqual(len(pipeline.db.list_events()),1)

    def test_completed_candidate_survives_later_candidate_failure(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);pipeline=Pipeline(root)
            self.inbox(root,[Candidate('n','s','VendorA free VPS','https://a.example/free'),
                             Candidate('n','s','VendorB free VPS','https://b.example/free')])
            original=pipeline.verifier.evaluate;calls=[]
            def evaluate(*args):
                calls.append(True)
                if len(calls)==2:raise RuntimeError('second-candidate-failed')
                return original(*args)
            with mock.patch.object(pipeline.verifier,'evaluate',side_effect=evaluate):
                with self.assertRaisesRegex(RuntimeError,'second-candidate-failed'):pipeline.ingest_node('n')
            events=pipeline.db.list_events();self.assertEqual(len(events),1)
            self.assertEqual(events[0]['primary_url'],'https://a.example/free')
            self.assertEqual(len(pipeline.db.get_evidence(events[0]['id'])),1)
            with pipeline.db.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM notifications').fetchone()[0],1)

if __name__=='__main__':unittest.main()
