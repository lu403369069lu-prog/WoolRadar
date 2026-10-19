"""Durable throttling through the actual notifier boundary; synthetic IO only."""
import io,json,tempfile,urllib.error,unittest
from datetime import datetime,timezone
from email.utils import format_datetime
from pathlib import Path
from unittest.mock import patch
from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue

class TelegramCooldownBoundaryTests(unittest.TestCase):
    def run_case(self, error=None, body=None):
        with tempfile.TemporaryDirectory() as td:
            db=Database(Path(td)/'outbox.db');queue=NotificationQueue(db)
            event=db.upsert_candidate(Candidate('n','test','Cooldown','https://vendor.example/offer')).event_id
            queue.enqueue(event,'','telegram','synthetic')
            class Response:
                def __enter__(self):return self
                def __exit__(self,*args):return False
                def read(self,*args):return json.dumps(body).encode()
            def send(_):raise error
            with patch('core.notify.time.time',return_value=30000.0):
                if error is not None:result=queue.flush({'telegram_send_enabled':True},sender=send,retry_seconds=5)
                else:
                    with patch.dict('os.environ',{'WOOLRADAR_TELEGRAM_BOT_TOKEN':'SYNTHETIC_TOKEN','WOOLRADAR_TELEGRAM_CHAT_ID':'SYNTHETIC_CHAT'}),patch('core.notify.urllib.request.urlopen',return_value=Response()):
                        result=queue.flush({'telegram_send_enabled':True},retry_seconds=5)
            with db.connect() as c:row=dict(c.execute('SELECT * FROM notifications').fetchone())
            self.assertEqual(row['result'],'RETRY');self.assertEqual(result['retry'],1)
            self.assertNotIn('SYNTHETIC_TOKEN',repr(row))
            # A fresh queue and connection must obey the persisted cooldown.
            with patch('core.notify.time.time',return_value=30001.0):
                self.assertEqual(NotificationQueue(Database(db.path)).flush({'telegram_send_enabled':True},sender=lambda _:self.fail('early retry'))['sent'],0)
            return row

    def test_long_retry_after_is_not_shortened_to_one_hour(self):
        row=self.run_case(error=urllib.error.HTTPError('https://example.test/',429,'limited',{'Retry-After':'7200'},None))
        self.assertEqual(row['next_attempt'],37200.0)

    def test_http_date_cooldown_survives_queue_restart(self):
        date=format_datetime(datetime.fromtimestamp(37200,timezone.utc),usegmt=True)
        row=self.run_case(error=urllib.error.HTTPError('https://example.test/',429,'limited',{'Retry-After':date},None))
        self.assertEqual(row['next_attempt'],37200.0)

    def test_http_429_json_retry_after_without_header(self):
        body=io.BytesIO(json.dumps({'ok':False,'error_code':429,'parameters':{'retry_after':7200}}).encode())
        row=self.run_case(error=urllib.error.HTTPError('https://example.test/',429,'limited',{},body))
        self.assertEqual(row['next_attempt'],37200.0)

    def test_actual_notifier_preserves_structured_rate_limit(self):
        row=self.run_case(body={'ok':False,'error_code':429,'parameters':{'retry_after':7200}})
        self.assertEqual(row['next_attempt'],37200.0)

    def test_conflicting_server_delays_take_longest_safe_cooldown(self):
        body=io.BytesIO(json.dumps({'parameters':{'retry_after':7200}}).encode())
        row=self.run_case(error=urllib.error.HTTPError('https://example.test/',429,'limited',{'Retry-After':'120'},body))
        self.assertEqual(row['next_attempt'],37200.0)
