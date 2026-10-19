"""Synthetic, offline integration checks. Product source is read-only."""
import sys, json, hashlib, sqlite3, tempfile, io, email.utils, unittest
from pathlib import Path
from contextlib import contextmanager, closing
from unittest.mock import patch
from urllib.error import HTTPError

REPO = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.dont_write_bytecode = True
from core.db import Database
from core.notify import NotificationQueue
from core.models import Candidate
import socket
from core.collector import _connect_public_peer, SourcePaused

NOW = 1800000000
results = []
def record(name, **data):
    results.append(dict(name=name, **data))

def notice(db, channel='telegram'):
    q = NotificationQueue(db)
    q.enqueue(None, 'synthetic-batch', channel, 'synthetic message')
    return q

class Response:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self):
        return json.dumps({'ok':False, 'error_code':429,
                           'parameters': {'retry_after':7200}}).encode()

def main():
    hashes_before={n:hashlib.sha256((REPO/'core'/n).read_bytes()).hexdigest()
                   for n in ['db.py','notify.py','collector.py','official_trace.py','dedup.py']}
    with tempfile.TemporaryDirectory(prefix='independent-', dir=OUT) as folder:
        folder = Path(folder)
        tempfile.tempdir = str(folder)
        for name, mode, header, minimum in [
            ('http429_delta_7200', 'error', '7200', 7200),
            ('http429_date_7200', 'error', email.utils.formatdate(NOW+7200, usegmt=True), 7200),
            ('http429_telegram_body', 'error', None, 7200),
            ('telegram_json429_response', 'json', None, 7200),
            ('http429_delta_120', 'error', '120', 300),
        ]:
            db=Database(folder/(name+'.db')); q=notice(db)
            exc=HTTPError('https://synthetic.invalid/',429,'synthetic',
                          {'Retry-After':header} if header else {},
                          io.BytesIO(b'{"ok":false,"error_code":429,"parameters":{"retry_after":7200}}'))
            transport=Response() if mode=='json' else None
            with patch('core.notify.os.getenv', return_value='synthetic'), \
                 patch('core.notify.time.time', return_value=NOW), \
                 patch('core.notify.urllib.request.urlopen', **({'return_value':transport} if mode=='json' else {'side_effect':exc})) as mocked:
                summary=q.flush({'telegram_send_enabled':True})
            with db.connect() as conn: row=dict(conn.execute('SELECT * FROM notifications').fetchone())
            delay=row['next_attempt']-NOW
            record(name, result=row['result'], delay=delay, required_minimum=minimum,
                   passed=delay>=minimum, transport_calls=mocked.call_count, summary=summary)
            exc.close()

        path=folder/'version-race.db'
        Database(path)
        class RacingDatabase(Database):
            @contextmanager
            def connect(self):
                if not getattr(self, 'injected', False):
                    self.injected=True
                    with closing(sqlite3.connect(self.path)) as writer:
                        writer.execute('PRAGMA user_version=2'); writer.commit()
                with super().connect() as conn: yield conn
        rejected=False
        try: RacingDatabase(path)
        except RuntimeError: rejected=True
        with closing(sqlite3.connect(path)) as conn:
            version=conn.execute('PRAGMA user_version').fetchone()[0]
        record('schema_version_changed_after_inspection', rejected=rejected,
               version_after=version, passed=rejected and version==2,
               schedule='independent SQLite writer commits version=2 after read-only inspection, before migration connection')

        db=Database(folder/'receipt.db'); q=notice(db, 'local-health'); receipts=folder/'receipts'
        original_connect=sqlite3.connect
        failures=[]
        class FailCommit(sqlite3.Connection):
            def commit(self):
                row=self.execute('SELECT result FROM notifications LIMIT 1').fetchone()
                if row and row[0]=='SENT' and not failures:
                    failures.append('injected precommit failure')
                    raise sqlite3.OperationalError('SYNTHETIC_COMMIT_FAILURE')
                return super().commit()
        def failing_connect(*args, **kwargs):
            return original_connect(*args, **dict(kwargs, factory=FailCommit))
        with patch('core.db.sqlite3.connect', side_effect=failing_connect):
            first=q.flush({}, retry_seconds=0, local_dir=receipts)
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in receipts.glob('*.json')}
        second=q.flush({},retry_seconds=0,local_dir=receipts)
        after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in receipts.glob('*.json')}
        with db.connect() as conn: final=dict(conn.execute('SELECT * FROM notifications').fetchone())
        record('local_receipt_commit_failure_retry', first=first, second=second,
               result=final['result'], receipt_count=len(after), stable_receipt=before==after,
               temporary_count=len(list(receipts.glob('*.tmp'))),
               passed=bool(failures) and final['result']=='SENT' and before==after and len(after)==1)

        for state, deadline in [('SENT',0),('CLAIMED',NOW+1000),('RETRY',NOW+7200),('UNCERTAIN',NOW+7200)]:
            db=Database(folder/('merge-'+state+'.db'))
            a=db.upsert_candidate(Candidate('synthetic','a','Acme StudentPack Launch 2026','https://a.example/offer')).event_id
            with db.connect() as conn:
                conn.execute("UPDATE events SET canonical_key='synthetic-legacy-key' WHERE id=?",(a,))
            b=db.upsert_candidate(Candidate('synthetic','b','Acme StudentPack Launch 2026','https://b.example/offer')).event_id
            q=NotificationQueue(db)
            q.enqueue(a,'','telegram','synthetic survivor'); q.enqueue(b,'','telegram','synthetic loser')
            with db.connect() as conn:
                conn.execute("UPDATE notifications SET result='RETRY',next_attempt=? WHERE event_id=?",(NOW+300,a))
                conn.execute('UPDATE notifications SET result=?,next_attempt=?,attempts=2 WHERE event_id=?',(state,deadline,b))
            db.reindex()
            with db.connect() as conn:
                rows=[dict(r) for r in conn.execute('SELECT result,next_attempt,attempts FROM notifications')]
            row=rows[0]
            passed=(row['result']=='SENT' if state=='SENT' else row['next_attempt']>=deadline)
            record('merge_loser_'+state, merged_notices=rows, required_deadline=deadline,passed=passed)

        db=Database(folder/'active-ack.db')
        a=db.upsert_candidate(Candidate('n','a','Acme StudentPack Launch 2026','https://a.example/offer')).event_id
        with db.connect() as conn: conn.execute("UPDATE events SET canonical_key='synthetic-old' WHERE id=?",(a,))
        b=db.upsert_candidate(Candidate('n','b','Acme StudentPack Launch 2026','https://b.example/offer')).event_id
        q=NotificationQueue(db);q.enqueue(a,'','telegram','survivor');q.enqueue(b,'','telegram','loser')
        with db.connect() as conn:
            conn.execute("UPDATE notifications SET result='RETRY',attempts=2,next_attempt=? WHERE event_id=?",(NOW+7200,b))
        sent=[]
        def in_flight_sender(payload):
            sent.append(payload);db.reindex();return 'SENT'
        with patch('core.notify.time.time',return_value=NOW):
            first=q.flush({'telegram_send_enabled':True},sender=in_flight_sender)
        with db.connect() as conn: row=dict(conn.execute('SELECT * FROM notifications').fetchone())
        with patch('core.notify.time.time',return_value=NOW+400):
            second=q.flush({'telegram_send_enabled':True},sender=lambda _:sent.append('unexpected'))
        record('active_claim_merge_invalidates_old_ack',first=first,second=second,
               result=row['result'],deadline=row['next_attempt'],attempts=row['attempts'],
               sender_calls=len(sent),passed=first.get('uncertain')==1 and first['sent']==0 and
                 row['result']=='CLAIMED' and row['next_attempt']==NOW+7200 and len(sent)==1)

        ddl_path=folder/'ddl-fault.db'
        class DDLFailure(sqlite3.Connection):
            def execute(self,sql,*args,**kwargs):
                if sql.strip().upper().startswith('CREATE TABLE IF NOT EXISTS EVIDENCE'):
                    raise sqlite3.OperationalError('SYNTHETIC_DDL_FAILURE')
                return super().execute(sql,*args,**kwargs)
        def failing_ddl_connect(*args,**kwargs):
            return original_connect(*args,**dict(kwargs,factory=DDLFailure))
        fault_seen=False
        with patch('core.db.sqlite3.connect',side_effect=failing_ddl_connect):
            try: Database(ddl_path)
            except sqlite3.OperationalError as exc: fault_seen=str(exc)=='SYNTHETIC_DDL_FAILURE'
        with closing(original_connect(ddl_path)) as conn:
            tables=conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            version=conn.execute('PRAGMA user_version').fetchone()[0]
        Database(ddl_path)
        record('fresh_schema_ddl_fault_rollback_and_retry',fault_seen=fault_seen,
               tables_after_failure=tables,version_after_failure=version,
               passed=fault_seen and not tables and version==0)

        # Offline socket boundary: no real resolver/socket executes.
        endpoints=lambda ip:[(socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP,'',(ip,443))]
        for name, answers, blocked in [('public',endpoints('8.8.8.8'),False),
                ('private',endpoints('127.0.0.1'),True),
                ('mixed',endpoints('8.8.8.8')+endpoints('127.0.0.1'),True)]:
            from unittest.mock import MagicMock
            fake_socket=MagicMock(); denied=False
            with patch('core.collector.socket.getaddrinfo',return_value=answers) as dns, \
                    patch('core.collector.socket.socket',return_value=fake_socket) as factory:
                try: _connect_public_peer(('synthetic.example',443),timeout=1)
                except SourcePaused: denied=True
            expected=answers[0][4]
            record('w5_'+name, blocked=denied, dns_calls=dns.call_count,
                   socket_calls=factory.call_count,
                   passed=denied==blocked and dns.call_count==1 and
                     (factory.call_count==0 if blocked else fake_socket.connect.call_args.args==(expected,)))

        # Load narrowly selected existing contracts; redirect their test temp ROOT
        # to this review directory so no product/worktree writes occur.
        import importlib.util
        suite=unittest.TestSuite()
        for name in ['test_schema_version_guard','test_schema_migration_atomic',
                     'test_notice_sent_monotonic','test_notice_retry_restart',
                     'test_notify_reindex_transaction', 'test_telegram_rate_limit',
                     'test_reindex_backup_atomic','test_schema_cooldown_interleavings']:
            spec=importlib.util.spec_from_file_location(name, REPO/'tests'/(name+'.py'))
            mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            if hasattr(mod,'ROOT'): mod.ROOT=folder
            mod.__file__=str(folder/'tests'/(name+'.py'))
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(mod))
        stream=io.StringIO()
        run=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
        record('focused_existing_contracts', tests=run.testsRun, failures=len(run.failures),
               errors=len(run.errors), skipped=len(run.skipped), passed=run.wasSuccessful(),
               output=stream.getvalue())
    hashes={n:hashlib.sha256((REPO/'core'/n).read_bytes()).hexdigest()
            for n in ['db.py','notify.py','collector.py','official_trace.py','dedup.py']}
    report={'command':'python -B independent_checks.py <read-only-worktree>',
            'network':'mocked urlopen and socket only; no real transport',
            'source_sha256_before':hashes_before,'source_sha256':hashes,
            'source_stable':hashes_before==hashes,'checks':results}
    target=OUT/'rereview-check-results.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    readback=json.loads(target.read_text(encoding='utf-8'))
    print(json.dumps({'source_sha256':hashes,'checks':[
        {k:v for k,v in item.items() if k!='output'} for item in readback['checks']]},ensure_ascii=False,indent=2))
    return 0  # Findings are observations; existing-contract failures are explicit.

if __name__=='__main__': sys.exit(main())
