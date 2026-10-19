"""R2-004: concurrent independent enqueues must produce one durable event notice.

Only disposable SQLite database and local output, no network delivery.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue


class ConcurrentEnqueueTests(unittest.TestCase):
    def test_independent_processes_share_exact_one_outbox_identity(self):
        with tempfile.TemporaryDirectory(prefix="wr-r2-enqueue-") as td:
            root = Path(td)
            db = Database(root / "store.db")
            event_id = db.upsert_candidate(Candidate(
                "local", "synthetic", "Free test", "https://example.test/w1-enqueue"
            )).event_id
            gate = root / "start.signal"
            script = (
                "import sys,time\n"
                "from pathlib import Path\n"
                "from core.db import Database\n"
                "from core.notify import NotificationQueue\n"
                "g=Path(sys.argv[2])\n"
                "deadline=time.monotonic()+15\n"
                "while not g.exists() and time.monotonic()<deadline: time.sleep(.005)\n"
                "if not g.exists(): sys.exit(21)\n"
                "accepted=NotificationQueue(Database(Path(sys.argv[1]))).enqueue("
                "int(sys.argv[3]),'','local',sys.argv[4])\n"
                "print('ONE' if accepted else 'ZERO')\n"
            )
            children = [
                subprocess.Popen([sys.executable, "-c", script, str(db.path),
                                  str(gate), str(event_id), "message-" + str(i)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for i in range(2)
            ]
            try:
                gate.write_text("go", encoding="utf-8")
                results = [child.communicate(timeout=25) for child in children]
                for child, (_, stderr) in zip(children, results):
                    self.assertEqual(child.returncode, 0, stderr)
                self.assertEqual(sorted(stdout.strip() for stdout, _ in results),
                                 ["ONE", "ZERO"])
                with db.connect() as conn:
                    rows = [dict(r) for r in conn.execute(
                        "SELECT * FROM notifications WHERE event_id=?", (event_id,))]
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["attempts"], 0)
                self.assertEqual(rows[0]["result"], "PENDING")
                q = NotificationQueue(Database(db.path))
                self.assertEqual(q.flush({}, local_dir=root / "local")["local"], 1)
                self.assertEqual(len(list((root / "local").glob("notification-*.json"))), 1)
                self.assertFalse(q.enqueue(event_id, "", "local", "another duplicate"))
            finally:
                for child in children:
                    if child.poll() is None:
                        child.kill()
                        child.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
