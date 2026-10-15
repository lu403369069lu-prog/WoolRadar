"""Independent real-module report/reindex repro; synthetic SQLite only."""
import json,os,sys,tempfile,unittest,threading
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,os.environ['REVIEW_WOOL_ROOT'])
from core.db import Database
from core.models import Candidate,Evidence
from core.report import ReportGenerator
A='https://publisher.example/a';B='https://publisher.example/b'
TITLES={A:'Launch Vendor credit grant',B:'Last chance Vendor credit grant'}
REVIEW=dict(method='normal_browser_read',campaign_url='https://gleam.io/Ab123',member_urls=[A,B],member_titles=TITLES)
class ReportIdentity(unittest.TestCase):
 def test_report_never_attributes_recycled_id_proof_to_old_event(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);db=Database(root/'data/db.sqlite')
   first=db.upsert_candidate(Candidate('n','s',TITLES[A],A)).event_id
   old=db.upsert_candidate(Candidate('n','s',TITLES[B],B)).event_id
   original=db.list_events;threads=[];errors=[];finished=threading.Event()
   def concurrent_writer():
    try:
     other=Database(db.path)
     self.assertEqual(other.review_campaign(REVIEW)['merged'],1)
     new=other.upsert_candidate(Candidate('n','s','Unrelated new grant','https://unrelated.example/new')).event_id
     self.assertEqual(new,old,'actual SQLite rowid reuse is required')
     other.add_evidence(new,Evidence('official','https://unrelated.example/new','unrelated-proof',claims={'public':True,'open':True}))
    except BaseException as exc:errors.append(exc)
    finally:finished.set()
   def snapshot_then_merge_and_reuse():
    rows=original()
    worker=threading.Thread(target=concurrent_writer);threads.append(worker);worker.start()
    # Old disconnected reads allow the real writer to finish here. A fixed
    # report may reserve a snapshot/writer transaction; do not deadlock it.
    finished.wait(.5)
    return rows
   with patch.object(db,'list_events',side_effect=snapshot_then_merge_and_reuse):
    paths=ReportGenerator(db,root/'reports').generate('2026-10-16')
   for worker in threads:worker.join(5);self.assertFalse(worker.is_alive())
   self.assertEqual(errors,[])
   payload=json.loads(paths.json.read_text(encoding='utf-8'))
   old_rows=[row for row in payload['events'] if row['primary_url']==B]
   self.assertFalse(any(e['url']=='https://unrelated.example/new' for row in old_rows for e in row['evidence']),
       'P1: old report event carries proof belonging to an unrelated reused SQLite ID')
if __name__=='__main__':unittest.main(verbosity=2)
