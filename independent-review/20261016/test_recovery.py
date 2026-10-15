"""Real-process isolated crash/restore probes. No network or production paths."""
import json,os,subprocess,sys,tempfile,unittest,shutil
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,os.environ['REVIEW_WOOL_ROOT'])
from core.db import Database
from core.models import Candidate,Evidence
from core.notify import NotificationQueue
W=Path(os.environ['REVIEW_WOOL_ROOT'])
CHILD='''import os,sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from core.db import Database
from core.models import Candidate,Evidence
from core.notify import NotificationQueue
root=Path(sys.argv[2]);db=Database(root/'db.sqlite')
if sys.argv[3]=='transaction':
 with db.candidate_transaction():
  event=db.upsert_candidate(Candidate('n','s','Transient API offer','https://vendor.example/transient')).event_id
  db.add_evidence(event,Evidence('official','https://vendor.example/transient','p',claims={'open':True,'public':True}))
  NotificationQueue(db).enqueue(event,'','local','transient')
  os._exit(17)
else:
 def sender(payload):
  (root/'external-delivered.txt').write_text(payload)
  os._exit(17)
 NotificationQueue(db).flush({'telegram_send_enabled':True},sender=sender)
'''
def dump(db):
 with db.connect() as c:
  names=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
  return {n:[tuple(r) for r in c.execute('SELECT * FROM "'+n+'" ORDER BY rowid')] for n in names}
class CrashRecovery(unittest.TestCase):
 def child(self,root,mode):
  p=subprocess.run([sys.executable,'-X','utf8','-c',CHILD,str(W),str(root),mode],cwd=W,capture_output=True,text=True,timeout=30)
  self.assertEqual(p.returncode,17,p.stderr)
 def test_process_death_rolls_back_every_candidate_table(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);db=Database(root/'db.sqlite');before=dump(db)
   self.child(root,'transaction');reopened=Database(db.path)
   self.assertEqual(dump(reopened),before)
   with reopened.connect() as c:self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
 def test_external_send_then_process_death_retains_at_least_once_uncertainty(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);db=Database(root/'db.sqlite');event=db.upsert_candidate(Candidate('n','s','Public offer','https://vendor.example/one')).event_id
   q=NotificationQueue(db);q.enqueue(event,'','telegram','public message')
   self.child(root,'send');self.assertTrue((root/'external-delivered.txt').exists())
   live=NotificationQueue(Database(db.path));pending=live.pending();self.assertEqual(len(pending),1);self.assertEqual(pending[0]['result'],'CLAIMED')
   calls=[]
   with patch('core.notify.time.time',return_value=pending[0]['next_attempt']+1):
    result=live.flush({'telegram_send_enabled':True},sender=lambda payload:calls.append(payload) or 'SENT')
   self.assertEqual(result['sent'],1);self.assertEqual(calls,['public message']);self.assertEqual(live.pending(),[])
   # Two observed deliveries after ambiguous death: explicitly not exactly-once.
 def test_review_backup_restores_all_tables_and_replay_is_idempotent(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);db=Database(root/'db.sqlite')
   urls=['https://publisher.example/a','https://publisher.example/b'];titles={urls[0]:'Launch Vendor credit grant',urls[1]:'Last chance Vendor credit grant'}
   for url in urls:
    event=db.upsert_candidate(Candidate('n','s',titles[url],url)).event_id
    db.add_evidence(event,Evidence('community',url,'p:'+url,claims={'open':True}))
    NotificationQueue(db).enqueue(event,'','local','notice:'+url)
   before=dump(db);review=dict(method='normal_browser_read',campaign_url='https://gleam.io/Ab123',member_urls=urls,member_titles=titles)
   result=db.review_campaign(review);self.assertEqual(result['merged'],1)
   restored=root/'restored.sqlite';shutil.copyfile(result['backup'],restored)
   self.assertEqual(dump(Database(restored)),before)
   after=dump(db);self.assertEqual(db.review_campaign(review)['merged'],0);self.assertEqual(dump(db),after)
if __name__=='__main__':unittest.main(verbosity=2)
