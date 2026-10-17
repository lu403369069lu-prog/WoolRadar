import sqlite3
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

class MigrationNoticePrecedence(unittest.TestCase):
 def check(self, survivor, loser, channel='digest'):
  with TemporaryDirectory() as td:
   p=Path(td)/'copied.db'
   with sqlite3.connect(p) as c:
    c.executescript('''CREATE TABLE notifications(id INTEGER PRIMARY KEY,event_id INTEGER,batch_id TEXT NOT NULL,channel TEXT NOT NULL,created_at TEXT NOT NULL,result TEXT NOT NULL,payload TEXT NOT NULL DEFAULT '',attempts INTEGER NOT NULL DEFAULT 0,next_attempt REAL NOT NULL DEFAULT 0,UNIQUE(event_id,batch_id,channel));''')
    if survivor is not None:
     c.execute('INSERT INTO notifications(event_id,batch_id,channel,created_at,result,payload,attempts,next_attempt) VALUES(?,?,?,?,?,?,?,?)',(1,'',channel,'2026-10-15T01:00:00Z',survivor,'survivor',1,60))
    if loser is not None:
     c.execute('INSERT INTO notifications(event_id,batch_id,channel,created_at,result,payload,attempts,next_attempt) VALUES(?,?,?,?,?,?,?,?)',(2,'',channel,'2026-10-15T00:00:00Z',loser,'loser',2,90))
    columns='batch_id,channel,created_at,result,payload,attempts,next_attempt'
    c.execute(f'INSERT OR IGNORE INTO notifications(event_id,{columns}) SELECT ?,{columns} FROM notifications WHERE event_id=?',(1,2))
    c.execute('''UPDATE notifications SET result='SENT',
      created_at=(SELECT old.created_at FROM notifications old WHERE old.event_id=? AND old.batch_id=notifications.batch_id AND old.channel=notifications.channel AND UPPER(old.result)='SENT'),
      payload=(SELECT old.payload FROM notifications old WHERE old.event_id=? AND old.batch_id=notifications.batch_id AND old.channel=notifications.channel AND UPPER(old.result)='SENT'),
      attempts=MAX(attempts,(SELECT old.attempts FROM notifications old WHERE old.event_id=? AND old.batch_id=notifications.batch_id AND old.channel=notifications.channel AND UPPER(old.result)='SENT')),
      next_attempt=0
      WHERE event_id=? AND UPPER(result)!='SENT' AND EXISTS (
       SELECT 1 FROM notifications old WHERE old.event_id=? AND old.batch_id=notifications.batch_id AND old.channel=notifications.channel AND UPPER(old.result)='SENT')''',(2,2,2,1,2))
    c.execute('DELETE FROM notifications WHERE event_id=?',(2,))
    return c.execute('SELECT result,payload,attempts,next_attempt FROM notifications WHERE event_id=1').fetchone()
 def test_pending_plus_sent_keeps_sent(self):
  self.assertEqual(self.check('PENDING','SENT'),('SENT','loser',2,0))
 def test_retry_plus_sent_keeps_sent(self):
  self.assertEqual(self.check('RETRY','SENT'),('SENT','loser',2,0))
 def test_sent_plus_pending_keeps_original(self):
  self.assertEqual(self.check('SENT','PENDING'),('SENT','survivor',1,60))
 def test_no_conflict_copies_sent(self):
  self.assertEqual(self.check(None,'SENT'),('SENT','loser',2,90))
 def test_pending_plus_retry_preserves_pending(self):
  self.assertEqual(self.check('PENDING','RETRY'),('PENDING','survivor',1,60))
 def test_lowercase_historical_sent_promotes(self):
  self.assertEqual(self.check('CLAIMED','sent'),('SENT','loser',2,0))

if __name__=='__main__':unittest.main(verbosity=2)