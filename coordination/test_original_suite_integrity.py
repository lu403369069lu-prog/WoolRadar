import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_original_suite import verify


class OriginalSuiteIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        source = Path(__file__).resolve().parent.parent
        self.manifest = self.root / 'coordination/original-tests/SOURCE_MANIFEST.json'
        rows = json.loads((source / self.manifest.relative_to(self.root)).read_bytes())
        for row in rows:
            target = self.root / row['target']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / row['target'], target)
        self.manifest.write_text(json.dumps(rows), encoding='utf-8')

    def test_reviewed_bytes_pass(self):
        self.assertEqual(verify(self.root), 11)

    def test_changed_source_fails(self):
        with (self.root / 'coordination/relay.py').open('ab') as stream:
            stream.write(b'\n# drift\n')
        with self.assertRaisesRegex(ValueError, 'BYTES_MISMATCH'):
            verify(self.root)

    def test_duplicate_row_cannot_replace_missing_test(self):
        rows = json.loads(self.manifest.read_bytes())
        rows[0] = rows[1]
        self.manifest.write_text(json.dumps(rows), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'SCOPE_MISMATCH'):
            verify(self.root)

    def test_unreviewed_source_identity_fails(self):
        rows = json.loads(self.manifest.read_bytes())
        rows[0]['source_commit'] = 'a' * 40
        self.manifest.write_text(json.dumps(rows), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'SOURCE_MISMATCH'):
            verify(self.root)
