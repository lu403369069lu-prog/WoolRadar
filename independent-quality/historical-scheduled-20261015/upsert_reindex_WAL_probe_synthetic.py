"""Synthetic SQLite interleaving of the exact two-connection upsert protocol from WoolRadar PR#19.
No production data; canonical key is a deterministic stand-in for review-dependent keying.
"""
import json, sqlite3, tempfile, threading
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def connect(path):
    c=sqlite3.connect(path,timeout=5)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA foreign_keys=ON')
    try:
        yield c
        c.commit()
    except:
        c.rollback(); raise
    finally: c.close()

def key(url, review):
    return 'review:' + review['campaign_url'] if review else 'original:' + url

def insert_like_pr19(path, url, read_done=None, proceed=None):
    # Mirrors PR19 core/db.py upsert_candidate lines 123-145:
    # review is read and canonical key computed before opening insertion connection.
    with connect(path) as conn:
        link=conn.execute('SELECT review_json FROM campaign_links WHERE url=?',(url,)).fetchone()
    review=json.loads(link[0]) if link else None
    candidate_key=key(url,review)
    if read_done:
        read_done.set()
        assert proceed.wait(5)
    with connect(path) as conn:
        cursor=conn.execute('''INSERT INTO events(canonical_key,batch_id,title,primary_url,source,node,published_at,first_seen,last_seen,metadata_json)
           VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(canonical_key,batch_id) DO NOTHING''',
           (candidate_key,'','offer',url,'source','node',None,'now','now',json.dumps({'campaign_review':review} if review else {})))
        row=conn.execute('SELECT id FROM events WHERE canonical_key=? AND batch_id=?',(candidate_key,'')).fetchone()
        return row['id'],cursor.rowcount==1,candidate_key

def run():
  with tempfile.TemporaryDirectory() as root:
    path=Path(root)/'isolated.db'
    with connect(path) as c:
        c.executescript('''CREATE TABLE campaign_links(url TEXT PRIMARY KEY,review_json TEXT NOT NULL);
        CREATE TABLE events(id INTEGER PRIMARY KEY,canonical_key TEXT NOT NULL,batch_id TEXT NOT NULL DEFAULT '',title TEXT NOT NULL,primary_url TEXT NOT NULL,source TEXT NOT NULL,node TEXT NOT NULL,published_at TEXT,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,metadata_json TEXT NOT NULL DEFAULT '{}',UNIQUE(canonical_key,batch_id));''')
    url='https://vendor.example/offer'
    first=insert_like_pr19(path,url)
    ready,proceed=threading.Event(),threading.Event()
    output={}
    def worker():
        try: output['upsert']=insert_like_pr19(path,url,ready,proceed)
        except Exception as e: output['error']=repr(e)
    t=threading.Thread(target=worker)
    t.start()
    assert ready.wait(5),'worker did not reach after-review-before-insert point'
    # Concurrent reindex(campaign_review=...) commits reviewed identity while upsert is paused.
    review={'campaign_url':'https://vendor.example/campaign','member_urls':[url,'https://vendor.example/other']}
    with connect(path) as c:
        c.execute('INSERT INTO campaign_links(url,review_json) VALUES(?,?)',(url,json.dumps(review)))
        c.execute('UPDATE events SET canonical_key=?,metadata_json=? WHERE id=?',
                  (key(url,review),json.dumps({'campaign_review':review}),first[0]))
    proceed.set();t.join(5)
    assert not t.is_alive(),'worker stalled'
    with connect(path) as c:
        rows=[dict(r) for r in c.execute('SELECT id,canonical_key,primary_url FROM events ORDER BY id')]
        link=c.execute('SELECT review_json FROM campaign_links WHERE url=?',(url,)).fetchone()
    print(json.dumps({'first_upsert':first,'paused_upsert':output,'rows_after_migration':rows,
      'current_review_present':bool(link),'duplicate_alert':output.get('upsert',(None,False))[1],
      'event_count':len(rows)},indent=2))
    assert len(rows)==2 and output['upsert'][1] is True

if __name__=='__main__':run()

def fixed_interleaving():
  with tempfile.TemporaryDirectory() as root:
    path=Path(root)/'isolated.db'
    with connect(path) as c:
      c.executescript('''CREATE TABLE campaign_links(url TEXT PRIMARY KEY,review_json TEXT NOT NULL);
      CREATE TABLE events(id INTEGER PRIMARY KEY,canonical_key TEXT NOT NULL,batch_id TEXT NOT NULL DEFAULT '',title TEXT NOT NULL,primary_url TEXT NOT NULL,source TEXT NOT NULL,node TEXT NOT NULL,published_at TEXT,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,metadata_json TEXT NOT NULL DEFAULT '{}',UNIQUE(canonical_key,batch_id));''')
    url='https://vendor.example/offer'
    first=insert_like_pr19(path,url)
    read_done,proceed=threading.Event(),threading.Event()
    migration_attempted,migration_done=threading.Event(),threading.Event()
    out={}
    def fixed_worker():
      with connect(path) as c:
        c.execute('BEGIN IMMEDIATE')
        link=c.execute('SELECT review_json FROM campaign_links WHERE url=?',(url,)).fetchone()
        review=json.loads(link[0]) if link else None
        candidate_key=key(url,review)
        read_done.set();assert proceed.wait(5)
        cursor=c.execute('''INSERT INTO events(canonical_key,batch_id,title,primary_url,source,node,published_at,first_seen,last_seen,metadata_json)
           VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(canonical_key,batch_id) DO NOTHING''',
           (candidate_key,'','offer',url,'source','node',None,'now','now','{}'))
        out['notify']=cursor.rowcount==1
    def migrate():
      review={'campaign_url':'https://vendor.example/campaign','member_urls':[url,'https://vendor.example/other']}
      migration_attempted.set()
      with connect(path) as c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('INSERT INTO campaign_links(url,review_json) VALUES(?,?)',(url,json.dumps(review)))
        c.execute('UPDATE events SET canonical_key=?,metadata_json=? WHERE id=?',
                  (key(url,review),json.dumps({'campaign_review':review}),first[0]))
      migration_done.set()
    t1=threading.Thread(target=fixed_worker);t1.start()
    assert read_done.wait(5)
    t2=threading.Thread(target=migrate);t2.start()
    assert migration_attempted.wait(5)
    # Writer transaction is held by fixed upsert, so migration cannot commit early.
    assert not migration_done.wait(0.15)
    proceed.set();t1.join(5);t2.join(5)
    assert not t1.is_alive() and not t2.is_alive()
    with connect(path) as c:
      rows=[dict(r) for r in c.execute('SELECT id,canonical_key FROM events')]
    print(json.dumps({'fixed':{'upsert_notify':out['notify'],'event_count':len(rows),
      'migration_completed':migration_done.is_set(),'rows':rows}},indent=2))
    assert out['notify'] is False and len(rows)==1 and migration_done.is_set()

if __name__=='__main__': fixed_interleaving()