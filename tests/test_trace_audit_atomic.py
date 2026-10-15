"""Concurrent audit publication must never expose a partial immutable record."""
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from core.official_trace import OfficialTracer

class TraceAuditPublicationTests(unittest.TestCase):
    def test_identical_concurrent_records_are_complete_and_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            tracer=OfficialTracer.__new__(OfficialTracer);tracer.root=Path(td)
            record={'checked_at':'2026-10-16T00:00:00Z','event_id':1,'references':[],'status':'UNKNOWN'}
            paused,release=threading.Event(),threading.Event();errors=[]
            original_open=Path.open;original_fdopen=os.fdopen
            class SlowWriter:
                def __init__(self,handle):self.handle=handle
                def __getattr__(self,name):return getattr(self.handle,name)
                def __enter__(self):self.handle.__enter__();return self
                def __exit__(self,*args):return self.handle.__exit__(*args)
                def write(self,value):
                    paused.set()
                    if not release.wait(5):raise TimeoutError('first writer not released')
                    return self.handle.write(value)
            def wrap(handle,mode):
                return SlowWriter(handle) if threading.current_thread().name=='slow-audit' and any(k in mode for k in ('x','w')) else handle
            def open_file(path,mode='r',*args,**kwargs):return wrap(original_open(path,mode,*args,**kwargs),mode)
            def open_fd(fd,mode='r',*args,**kwargs):return wrap(original_fdopen(fd,mode,*args,**kwargs),mode)
            def first():
                try:tracer._write_record(1,record)
                except BaseException as exc:errors.append(repr(exc))
            with patch.object(Path,'open',open_file),patch('os.fdopen',side_effect=open_fd):
                worker=threading.Thread(target=first,name='slow-audit');worker.start()
                try:
                    self.assertTrue(paused.wait(5))
                    tracer._write_record(1,record)
                    history=list((tracer.root/'evidence/official-trace/history').glob('*.json'))
                    self.assertEqual(len(history),1)
                    self.assertEqual(json.loads(history[0].read_text(encoding='utf-8')),record)
                finally:release.set();worker.join(5)
            self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
            self.assertEqual(json.loads((tracer.root/'evidence/official-trace/1.json').read_text(encoding='utf-8')),record)
            self.assertEqual(list((tracer.root/'evidence/official-trace').rglob('*.tmp')),[])

if __name__=='__main__':unittest.main()
