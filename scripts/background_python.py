"""Task-only entry, preserving CLI arguments and recording console allocation."""
import ctypes
import json
import os
import runpy
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root).casefold() != r'C:\WoolRadar'.casefold():
    raise SystemExit(64)
tag = 'report'
if 'run-node' in sys.argv:
    tag = sys.argv[sys.argv.index('run-node') + 1]
if tag not in {'report','twitter-monitor','openmagpie','digest-ai-agent','clawradar','linuxdo-monitor'}:
    raise SystemExit(64)
record = {'started_at':datetime.now(timezone.utc).isoformat(),'python_pid':os.getpid(), 'parent_pid':os.getppid(),
          'python_has_console':bool(ctypes.windll.kernel32.GetConsoleWindow()),'running':True}
receipt = root/'logs'/('python-console-'+tag+'.json')
def write_receipt():
    try:
        receipt.write_text(json.dumps(record),encoding='utf-8')
    except OSError:
        pass
write_receipt()
sys.path.insert(0,str(root))
try:
    runpy.run_module('core.cli',run_name='__main__')
except SystemExit as exc:
    record.update(exit_code=exc.code)
    raise
except BaseException as exc:
    record.update(exit_code=1,error_type=type(exc).__name__)
    raise
else:
    record.update(exit_code=0)
finally:
    record.update(running=False,finished_at=datetime.now(timezone.utc).isoformat())
    write_receipt()
