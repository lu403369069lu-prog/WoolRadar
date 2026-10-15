import tempfile
import unittest
from pathlib import Path
from unittest import mock
from core.db import Database
from core.models import Candidate,Evidence,Status
from core.report import ReportGenerator

TEMP=Path(__file__).parents[1]/'.test-tmp'
TEMP.mkdir(exist_ok=True)
A='https://publisher.example/a'
B='https://publisher.example/b'
TITLES={A:'First launch of cloud credit grant',B:'Last chance for server credit grant'}
REVIEW={'method':'normal_browser_read','campaign_url':'https://gleam.io/Ab123','member_urls':[A,B],'member_titles':TITLES}

class MergeStatusTests(unittest.TestCase):
    def seed(self,root):
        db=Database(root/'radar.db')
        first=db.upsert_candidate(Candidate('test','publisher',TITLES[A],A))
        second=db.upsert_candidate(Candidate('test','publisher',TITLES[B],B))
        db.set_status(first.event_id,Status.UNKNOWN,'Fixture unknown')
        return db,first.event_id,second.event_id

    def official(self,db,event_id,**claims):
        db.add_evidence(event_id,Evidence('official','https://vendor.example/state','vendor',claims=claims))

    def test_merge_promotes_from_combined_evidence_and_records_history(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            root=Path(td);db,one,two=self.seed(root)
            self.official(db,two,open=True,public=True,remaining=1)
            result=db.review_campaign(REVIEW)
            self.assertEqual(result['merged'],1)
            self.assertEqual(db.get_event(one)['status'],'CLAIMABLE')
            self.assertEqual(db.get_event(one)['claim_scope'],'PUBLIC_APPLICATION')
            ReportGenerator(db,root/'reports').generate('2026-10-15')
            self.assertEqual(db.get_event(one)['status'],'CLAIMABLE')
            with db.connect() as conn:
                history=conn.execute('SELECT old_status,new_status,reason FROM status_history WHERE event_id=? ORDER BY id DESC',(one,)).fetchone()
                self.assertEqual((history['old_status'],history['new_status']),('UNKNOWN','CLAIMABLE'))
                self.assertIn('归组',history['reason'])
                self.assertEqual(conn.execute('SELECT count(*) FROM notifications').fetchone()[0],0)

    def test_merge_downgrades_existing_claimable_with_closed_proof(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db,one,two=self.seed(Path(td))
            db.set_status(one,Status.CLAIMABLE,'Fixture prior label','PUBLIC_APPLICATION')
            self.official(db,two,open=False)
            db.review_campaign(REVIEW)
            self.assertEqual(db.get_event(one)['status'],'EXPIRED')
            self.assertEqual(db.get_event(one)['claim_scope'],'NONE')

    def test_merge_uses_zero_capacity_gate(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db,one,two=self.seed(Path(td));self.official(db,two,open=True,public=True,remaining=0)
            db.review_campaign(REVIEW)
            self.assertEqual(db.get_event(one)['status'],'OFFICIAL_VERIFIED')
            self.assertEqual(db.get_event(one)['claim_scope'],'NONE')

    def test_merge_respects_combined_conflicts(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db,one,two=self.seed(Path(td))
            self.official(db,one,open=True,public=True,region='US')
            db.add_evidence(two,Evidence('official','https://vendor.example/other','vendor-other',claims={'open':True,'public':True,'region':'CA'}))
            db.review_campaign(REVIEW)
            self.assertEqual(db.get_event(one)['status'],'CONFLICTED')

    def test_unmerged_events_keep_existing_state(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db,one,two=self.seed(Path(td));self.official(db,two,open=True,public=True,remaining=1)
            third=db.upsert_candidate(Candidate('test','other','Unrelated hosted perk','https://other.example/perk')).event_id
            db.set_status(third,Status.UNKNOWN,'Fixture explicit unknown')
            self.official(db,third,open=True,public=True,remaining=1)
            db.review_campaign(REVIEW)
            self.assertEqual(db.get_event(third)['status'],'UNKNOWN')

    def test_verification_failure_rolls_back_entire_merge(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db,one,two=self.seed(Path(td));self.official(db,two,open=True,public=True,remaining=1)
            before=db.list_events()
            with mock.patch('core.verifier.VerificationEngine.evaluate',side_effect=RuntimeError('fixture verification failure')):
                with self.assertRaisesRegex(RuntimeError,'fixture verification failure'):
                    db.review_campaign(REVIEW)
            self.assertEqual(db.list_events(),before)
            self.assertEqual(len(db.get_evidence(two)),1)
            with db.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM campaign_links').fetchone()[0],0)
