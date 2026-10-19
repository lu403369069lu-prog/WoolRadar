"""R2-006: revoke public eligibility after claim but before transport.

All I/O uses isolated SQLite and a synthetic sender. This does not authorize a
real Telegram send, and the test does not prove network-time revocation safety.
"""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock

from core.db import Database
from core.models import Candidate, Evidence
from core.notify import NotificationQueue


TEMP = Path(__file__).parents[1] / '.test-tmp'


class VerifiedSendRevocationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        TEMP.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        # Preserve a pre-existing shared test directory if other suites use it.
        try:
            TEMP.rmdir()
        except OSError:
            pass

    def test_inflight_revocation_cannot_undo_confirmed_send(self):
        with TemporaryDirectory(dir=TEMP) as temp:
            db = Database(Path(temp) / 'inflight.sqlite')
            event = db.upsert_candidate(Candidate(
                'n', 'rss', 'Synthetic grant',
                'https://publisher.example/inflight-2026',
            )).event_id
            db.add_evidence(event, Evidence(
                'official', 'https://official.example/inflight', 'inflight-evidence',
                claims={'open': True, 'public': True},
            ))
            outbox = NotificationQueue(db)
            self.assertTrue(outbox.enqueue(event, 'b1', 'telegram-verified', 'synthetic'))
            sends = []

            def sender_during_revocation(message):
                sends.append(message)
                with db.connect() as conn:
                    conn.execute('DELETE FROM evidence WHERE event_id=?', (event,))
                    conn.execute("UPDATE events SET status='EXPIRED' WHERE id=?", (event,))
                return 'SENT'  # Remote sender already accepted the message.

            summary = outbox.flush({'telegram_send_enabled': True}, sender=sender_during_revocation)
            self.assertEqual(sends, ['synthetic'])
            self.assertEqual(summary['sent'], 1)
            with db.connect() as conn:
                self.assertEqual(conn.execute(
                    'SELECT result FROM notifications WHERE event_id=?', (event,),
                ).fetchone()['result'], 'SENT')

    def test_inflight_timeout_after_revocation_remains_uncertain(self):
        with TemporaryDirectory(dir=TEMP) as temp:
            db = Database(Path(temp) / 'timeout.sqlite')
            event = db.upsert_candidate(Candidate(
                'n', 'rss', 'Synthetic grant',
                'https://publisher.example/timeout-2026',
            )).event_id
            db.add_evidence(event, Evidence(
                'official', 'https://official.example/timeout', 'timeout-evidence',
                claims={'open': True, 'public': True},
            ))
            outbox = NotificationQueue(db)
            self.assertTrue(outbox.enqueue(event, 'b1', 'telegram-verified', 'synthetic'))

            def ambiguous_sender(_message):
                with db.connect() as conn:
                    conn.execute('DELETE FROM evidence WHERE event_id=?', (event,))
                    conn.execute("UPDATE events SET status='EXPIRED' WHERE id=?", (event,))
                raise TimeoutError('simulated timeout after possible remote acceptance')

            summary = outbox.flush({'telegram_send_enabled': True}, sender=ambiguous_sender)
            self.assertEqual(summary['sent'], 0)
            self.assertEqual(summary.get('uncertain'), 1)
            with db.connect() as conn:
                self.assertEqual(conn.execute(
                    'SELECT result FROM notifications WHERE event_id=?', (event,),
                ).fetchone()['result'], 'UNCERTAIN')

    def test_local_verified_revoked_during_file_write_cannot_publish_receipt(self):
        with TemporaryDirectory(dir=TEMP) as temp:
            db = Database(Path(temp) / "local-revoke.sqlite")
            event = db.upsert_candidate(Candidate(
                "n", "rss", "Synthetic public developer grant",
                "https://publisher.example/local-program-2026",
            )).event_id
            db.add_evidence(event, Evidence(
                "official", "https://official.example/local-program",
                "official-2026-local", claims={"open": True, "public": True},
            ))
            queue = NotificationQueue(db)
            self.assertTrue(queue.enqueue(
                event, "b1", "local-verified", "synthetic local notification",
            ))
            output = Path(temp) / "receipts"
            original_write = Path.write_text
            revoked = []

            def revoke_after_temporary_file(path, text, *args, **kwargs):
                written = original_write(path, text, *args, **kwargs)
                if path.suffix == ".tmp" and not revoked:
                    revoked.append(True)
                    with db.connect() as conn:
                        conn.execute("DELETE FROM evidence WHERE event_id=?", (event,))
                        conn.execute("UPDATE events SET status='EXPIRED' WHERE id=?", (event,))
                return written

            with mock.patch.object(Path, "write_text", new=revoke_after_temporary_file):
                summary = queue.flush({}, local_dir=output)

            self.assertEqual(revoked, [True])
            self.assertEqual(summary["local"], 0)
            self.assertEqual(list(output.glob("notification-*.json")), [])
            with db.connect() as conn:
                result = conn.execute(
                    "SELECT result FROM notifications WHERE event_id=?", (event,),
                ).fetchone()["result"]
            self.assertEqual(result, "STALE")

    def test_evidence_revoked_after_claim_never_reaches_sender(self):
        with TemporaryDirectory(dir=TEMP) as temp:
            db = Database(Path(temp) / "revoke.sqlite")
            event = db.upsert_candidate(Candidate(
                "n", "rss", "Synthetic public developer grant",
                "https://publisher.example/program-2026",
            )).event_id
            db.add_evidence(event, Evidence(
                "official", "https://official.example/program",
                "official-2026", claims={"open": True, "public": True},
            ))
            outbox = NotificationQueue(db)
            self.assertTrue(outbox.enqueue(
                event, "b1", "telegram-verified", "synthetic notification",
            ))

            transaction = db.candidate_transaction
            revoked = []
            sent = []

            @contextmanager
            def revoke_after_first_claim():
                with transaction():
                    yield
                # Deterministic interleaving at the exact claim/transport gap.
                # This mutates only this test's isolated temporary database.
                if not revoked:
                    revoked.append(True)
                    with db.connect() as conn:
                        conn.execute("DELETE FROM evidence WHERE event_id=?", (event,))
                        conn.execute(
                            "UPDATE events SET status='EXPIRED' WHERE id=?", (event,),
                        )

            def fake_sender(payload):
                sent.append(payload)
                return "SENT"

            with mock.patch.object(
                db, "candidate_transaction", side_effect=revoke_after_first_claim
            ):
                summary = outbox.flush(
                    {"telegram_send_enabled": True}, sender=fake_sender
                )

            self.assertEqual(revoked, [True])
            self.assertEqual(sent, [], "revoked offer reached external sender")
            self.assertEqual(summary["sent"], 0)
            with db.connect() as conn:
                row = conn.execute(
                    "SELECT result FROM notifications WHERE event_id=?", (event,)
                ).fetchone()
                self.assertEqual(row["result"], "STALE")
