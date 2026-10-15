import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from coordination import relay

try:
    from coordination.relay_git import GitStateStore
except ImportError:
    GitStateStore = None


class GitConcurrencyTests(unittest.TestCase):
    def test_two_real_writers_and_crash_replay(self):
        self.assertIsNotNone(GitStateStore, 'Git state transport required')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / 'remote.git'
            subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
            first = GitStateStore(root / 'one', str(remote))
            second = GitStateStore(root / 'two', str(remote))
            state = relay.empty_state()
            state['tasks']['WoolRadar/R-1'] = relay.new_task('WoolRadar', 'R-1', 'a'*40,
                                                          ['coordination/'], 'Review checkpoint')
            sha = first.initialize(state)
            self.assertEqual(second.read()[0], sha)
            event = dict(project='WoolRadar', task_id='R-1', head_sha='a'*40,
                         event_type='claim', actor='codex', expected_version=0,
                         lease_seconds=60, now=10, fencing_token=None, data={})
            a, _ = relay.apply_event(state, event)
            b, _ = relay.apply_event(state, dict(event, actor='chatgpt'))
            accepted = first.publish(sha, a)
            with self.assertRaisesRegex(ValueError, 'CONFLICT'):
                second.publish(sha, b)
            current, actual = second.read()
            self.assertEqual(current, accepted)
            self.assertEqual(actual['tasks']['WoolRadar/R-1']['owner'], 'codex')
            # Lost acknowledgement: resend after a successful commit, without a new commit.
            self.assertEqual(second.deliver(event)['result'], 'duplicate_noop')
            self.assertEqual(second.read()[0], accepted)
            # Checksum tampering is rejected before a state can be used.
            with self.assertRaises(ValueError):
                first.publish(accepted, dict(a, schema_version=5))


if __name__ == '__main__':
    unittest.main()
