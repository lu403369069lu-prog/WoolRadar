from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .pipeline import Pipeline


NODES = ['twitter-monitor', 'openmagpie', 'digest-ai-agent', 'clawradar', 'linuxdo-monitor']


@dataclass(slots=True)
class NodeExecution:
    node: str
    exit_code: int
    stdout: str
    stderr: str


def run_all(root: Path, force: bool = False, timeout: int = 180) -> list[NodeExecution]:
    root = Path(root).resolve()
    pipeline = Pipeline(root)
    results = []
    for node in NODES:
        script = root / 'nodes' / node / 'run.py'
        command = [sys.executable, str(script), '--root', str(root)]
        if force:
            command.append('--force')
        try:
            proc = subprocess.run(command, cwd=root, text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=timeout,
                                  creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            result = NodeExecution(node, proc.returncode, proc.stdout, proc.stderr)
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or ''
            if isinstance(output, bytes):
                output = output.decode('utf-8', errors='replace')
            result = NodeExecution(node, 124, output, 'TIMEOUT')
        except OSError:
            result = NodeExecution(node, 127, '', 'PROCESS_START_FAILED')
        results.append(result)
        if result.exit_code not in (0, 2):
            pipeline.db.record_node_run(node, 'FAILED', error_code='PROCESS_FAILED', detail=result.stderr[:1000])
            pipeline.notifications.record_health(node, 'FAILED', 'PROCESS_FAILED')
            pipeline.notifications.flush(pipeline.notification_policy(), local_dir=root / 'reports' / 'notifications')
    return results
