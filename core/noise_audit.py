"""Explicit, snapshot-bound human noise decisions; never delete source evidence."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .models import utc_now


def _digest(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
    return hashlib.sha256(raw).hexdigest()


def _identity(event):
    fields={key:event[key] for key in ('canonical_key','batch_id','primary_url')}
    if any(not isinstance(v,str) for v in fields.values()) or not fields['canonical_key'] or not fields['primary_url']:
        raise ValueError('NOISE_EVENT_IDENTITY_REQUIRED')
    return _digest(fields)


def _fingerprint(event):
    # Observation times/status recalculation do not turn an unchanged repost into new proof.
    payload={key:event[key] for key in ('canonical_key','batch_id','title','primary_url','source','node','published_at')}
    payload['metadata']=json.loads(event['metadata_json'])
    evidence=[{k:v for k,v in e.items() if k!='checked_at'} for e in event['evidence']]
    payload['evidence']=sorted(evidence,key=lambda e:json.dumps(e,sort_keys=True,ensure_ascii=True))
    return _digest(payload)


class NoiseAudit:
    def __init__(self,path:Path):
        self.path=Path(path)

    def _load(self):
        if not self.path.exists(): return {'schema_version':1,'records':[]}
        try:
            data=json.loads(self.path.read_text(encoding='utf-8'))
            if (not isinstance(data,dict) or set(data)!={'schema_version','records'} or
                    type(data['schema_version']) is not int or data['schema_version']!=1 or not isinstance(data['records'],list)):
                raise ValueError('NOISE_AUDIT_SCHEMA')
            fields={'event_key','fingerprint','decision','reason','reviewer','reviewed_at'}
            for row in data['records']:
                if not isinstance(row,dict) or set(row)!=fields: raise ValueError('NOISE_AUDIT_RECORD')
                if any(not isinstance(row[k],str) for k in fields): raise ValueError('NOISE_AUDIT_RECORD')
                if any(not re.fullmatch('[0-9a-f]{64}',row[k]) for k in ('event_key','fingerprint')):
                    raise ValueError('NOISE_AUDIT_DIGEST')
                if row['decision'] not in {'exclude','restore'}: raise ValueError('NOISE_AUDIT_DECISION')
                if not 1<=len(row['reason'].strip())<=2048 or not 1<=len(row['reviewer'].strip())<=160:
                    raise ValueError('NOISE_AUDIT_ATTRIBUTION')
                if datetime.fromisoformat(row['reviewed_at'].replace('Z','+00:00')).tzinfo is None:
                    raise ValueError('NOISE_AUDIT_TIMEZONE')
            return data
        except (OSError,TypeError,KeyError,json.JSONDecodeError) as error:
            raise ValueError('NOISE_AUDIT_UNREADABLE') from error

    def validate(self):
        self._load()

    def snapshot(self):
        return _Snapshot(self._load())

    @contextmanager
    def _writer_lock(self):
        # Kernel-owned lock releases even on abrupt process exit. Do not unlink the
        # lock inode: replacing it would let a second writer lock a different file.
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.with_name(self.path.name+'.lock').open('a+b') as guard:
            guard.seek(0,os.SEEK_END)
            if guard.tell()==0:
                guard.write(b'0')
                guard.flush()
            guard.seek(0)
            try:
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(guard.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            except OSError as error:
                raise ValueError('NOISE_AUDIT_BUSY') from error
            try:
                yield
            finally:
                guard.seek(0)
                if os.name=='nt': msvcrt.locking(guard.fileno(),msvcrt.LK_UNLCK,1)
                else: fcntl.flock(guard.fileno(),fcntl.LOCK_UN)

    def record(self,event,decision,reason,reviewer):
        if decision not in {'exclude','restore'}: raise ValueError('NOISE_AUDIT_DECISION')
        if (not isinstance(reason,str) or not 1<=len(reason.strip())<=2048 or
                not isinstance(reviewer,str) or not 1<=len(reviewer.strip())<=160):
            raise ValueError('NOISE_AUDIT_ATTRIBUTION')
        row=dict(event_key=_identity(event),fingerprint=_fingerprint(event),decision=decision,
            reason=reason.strip(),reviewer=reviewer.strip(),reviewed_at=utc_now())
        with self._writer_lock():
            data=self._load()
            prior=next((item for item in reversed(data['records']) if item['event_key']==row['event_key']),None)
            if prior and all(prior[k]==row[k] for k in row if k!='reviewed_at'): return False
            data['records'].append(row)
            fd,name=tempfile.mkstemp(prefix=self.path.name+'.',dir=self.path.parent)
            try:
                with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as stream:
                    json.dump(data,stream,ensure_ascii=False,indent=2,allow_nan=False)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(name,self.path)
                return True
            finally:
                if os.path.exists(name): os.unlink(name)

    def decision(self,event):
        return self.snapshot().decision(event)


class _Snapshot:
    def __init__(self,data):
        self._records=tuple(dict(row) for row in data['records'])
        self.digest=_digest(data)

    def decision(self,event):
        key=_identity(event)
        row=next((item for item in reversed(self._records) if item['event_key']==key),None)
        if row is None: return dict(excluded=False,state='unreviewed')
        current=row['fingerprint']==_fingerprint(event)
        return dict(excluded=current and row['decision']=='exclude',
            state=('excluded' if row['decision']=='exclude' else 'restored') if current else 'stale',
            **row)
