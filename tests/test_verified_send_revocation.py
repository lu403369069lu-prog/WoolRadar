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
TEMP.mkdir(exist_ok=True)


class VerifiedSendRevocationTests(TestCase):
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
