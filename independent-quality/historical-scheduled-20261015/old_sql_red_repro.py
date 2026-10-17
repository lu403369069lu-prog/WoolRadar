import sqlite3
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
class ExistingSqlRedTest(unittest.TestCase):
 def test_sent_loser_must_not_become_pending(self):
  with TemporaryDirectory() as td:
   with sqlite3.connect(Path(td)/'copy.db') as conn:
    conn.executescript('''CREATE TABLE notifications (id INTEGER PRIMARY KEY,event_id INTEGER,batch_id TEXT NOT NULL,channel TEXT NOT NULL,created_at TEXT NOT NULL,result TEXT NOT NULL,payload TEXT NOT NULL DEFAULT '',attempts INTEGER NOT NULL DEFAULT 0,next_attempt REAL NOT NULL DEFAULT 0,UNIQUE(event_id,batch_id,channel));''')
    conn.execute("INSERT INTO notifications(event_id,batch_id,channel,created_at,result) VALUES(1,'','digest','2026-10-15','PENDING')")
    conn.execute("INSERT INTO notifications(event_id,batch_id,channel,created_at,result) VALUES(2,'','digest','2026-10-15','SENT')")
    # Exact INSERT OR IGNORE migration SQL shape from WoolRadar PR19 core/db.py
    columns='batch_id,channel,created_at,result,payload,attempts,next_attempt'
    conn.execute(f'INSERT OR IGNORE INTO notifications(event_id,{columns}) SELECT ?,{columns} FROM notifications WHERE event_id=?',(1,2))
    conn.execute('DELETE FROM notifications WHERE event_id=?',(2,))
    state=conn.execute('SELECT result FROM notifications WHERE event_id=1').fetchone()[0]
    self.assertEqual(state,'SENT','reindex must not lose a previously sent notice')
if __name__=='__main__':unittest.main()