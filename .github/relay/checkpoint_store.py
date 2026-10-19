"""Local crash recovery for the existing relay files; remote Git CAS remains authoritative."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import time


def atomic_bytes(path, content):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(content);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def save(path,obj):
    atomic_bytes(path,(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+'\n').encode('utf-8'))


@contextmanager
def persist_lock(root,timeout=10):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    lock=root/'.relay-persist.lock'
    if lock.is_symlink():
        raise ValueError('LOCK_PATH_ALIAS_DENIED')
    with lock.open('a+b') as stream:
        if stream.seek(0,2)==0:
            stream.write(b'0');stream.flush()
        deadline=time.monotonic()+timeout
        while True:
            stream.seek(0)
            try:
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except (OSError,BlockingIOError):
                if time.monotonic()>=deadline:
                    raise TimeoutError('LOCAL_CHECKPOINT_BUSY')
                time.sleep(.025)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(),fcntl.LOCK_UN)


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))


def read_history(root):
    history=Path(root)/'history.jsonl'
    if history.is_symlink():
        raise ValueError('HISTORY_PATH_ALIAS_DENIED')
    if history.exists() and history.stat().st_size>8*1024*1024:
        raise ValueError('HISTORY_REQUIRES_REVIEWED_ROTATION')
    raw=history.read_bytes() if history.exists() else b''
    rows=[json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    if any(not isinstance(row,dict) for row in rows):
        raise ValueError('CORRUPT_HISTORY')
    return history,raw,rows


def verify_replay(root,receipt):
    _,_,rows=read_history(root)
    matches=[row for row in rows if row.get('run_key')==receipt['run_key']]
    if len(matches)!=1 or canonical(matches[0])!=canonical(receipt):
        raise ValueError('REPLAY_CONTENT_CONFLICT')


def recover_history(root,state,save_state):
    """The engine retains one validated receipt until its history write is durable."""
    pending=state.get('pending_history_receipt')
    if pending is None:
        return
    if (not isinstance(pending,dict) or pending.get('run_key')!=state.get('last_run_key')
            or pending.get('source_commit')!=state.get('last_source_commit')
            or pending.get('run_key') not in state.get('processed_run_keys',[])):
        raise ValueError('CORRUPT_PENDING_HISTORY')
    history,raw,rows=read_history(root)
    matches=[row for row in rows if row.get('run_key')==pending['run_key']]
    if len(matches)>1 or matches and canonical(matches[0])!=canonical(pending):
        raise ValueError('HISTORY_REPLAY_CONTENT_CONFLICT')
    if not matches:
        prefix=raw+(b'\n' if raw and not raw.endswith(b'\n') else b'')
        atomic_bytes(history,prefix+(json.dumps(pending,sort_keys=True,ensure_ascii=False)+'\n').encode('utf-8'))
    state.pop('pending_history_receipt')
    save_state(Path(root)/'engine.json',state)
