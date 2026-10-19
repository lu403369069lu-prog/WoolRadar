"""Immutable source pins must constrain both execution and receipt acceptance."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import test_worker as fixtures

worker = fixtures.worker


class PinnedSourceIdentityTests(unittest.TestCase):
    def test_scheduled_checkout_matches_reviewed_queue_pin(self):
        q = fixtures.RelaySafetyTests().queue()
        workflow = Path(__file__).parent.parent / 'workflows/historical-family-relay.yml'
        self.assertRegex(q['source_ref'], r'^[a-f0-9]{40}$')
        self.assertIn('ref: ' + q['source_ref'], workflow.read_text(encoding='utf-8'))

    def pinned_queue(self):
        q = fixtures.RelaySafetyTests().queue()
        q['source_ref'] = 'a' * 40
        return q

    def test_wrong_checkout_is_rejected_before_any_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);q = self.pinned_queue()
            worker.save(root/'queue.json', q)
            worker.save(root/'engine.json', fixtures.RelaySafetyTests().initial(q['repo']))
            args = SimpleNamespace(queue=str(root/'queue.json'), state=tmp,
                                   source=tmp, repo=q['repo'], limit=1, output=str(root/'result.json'))
            with patch.object(worker, 'source_sha', return_value='b'*40), \
                 patch.object(worker, 'test', return_value={'status':'PASS','total':1,'exit_code':0}) as run:
                with self.assertRaisesRegex(ValueError, 'pinned source SHA'):
                    worker.evaluate(args)
                run.assert_not_called()

    def test_self_consistent_wrong_sha_receipt_is_rejected(self):
        q = self.pinned_queue();fixture = fixtures.RelaySafetyTests()
        receipt = fixture.receipt(q);receipt['source_commit'] = 'b'*40
        original = worker.load
        def trusted_queue(path):
            return q if Path(path).as_posix() == '.github/relay/queue.json' else original(path)
        with tempfile.TemporaryDirectory() as tmp, patch.object(worker, 'load', side_effect=trusted_queue):
            with self.assertRaisesRegex(ValueError, 'pinned source SHA'):
                fixture.run_persist(Path(tmp), q, receipt, integration_sha='b'*40)

    def test_matching_sha_receipt_remains_valid(self):
        q = self.pinned_queue();fixture = fixtures.RelaySafetyTests();original = worker.load
        def trusted_queue(path):
            return q if Path(path).as_posix() == '.github/relay/queue.json' else original(path)
        with tempfile.TemporaryDirectory() as tmp, patch.object(worker, 'load', side_effect=trusted_queue):
            state = fixture.run_persist(Path(tmp), q, fixture.receipt(q), integration_sha='a'*40)
            self.assertEqual(state['revision'], 1)
