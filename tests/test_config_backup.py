import json
import tempfile
import unittest
from pathlib import Path

from core.config_backup import backup_config, restore_config


ROOT = Path(__file__).parents[1]


class ConfigBackupTests(unittest.TestCase):
    def test_valid_backup_repairs_corrupt_current_config_and_preserves_rescue(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            root = self.make_root(folder)
            backup = backup_config(root)
            original = (root / 'config/keywords.json').read_bytes()
            (root / 'config/keywords.json').write_text('{')
            result = restore_config(root, backup)
            self.assertEqual((root / 'config/keywords.json').read_bytes(), original)
            rescue = Path(result['rescue_backup'])
            self.assertEqual((rescue / 'keywords.json').read_text(), '{')
            with self.assertRaises(ValueError):
                restore_config(root, rescue)

    def test_valid_backup_repairs_missing_current_config(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            root = self.make_root(folder)
            backup = backup_config(root)
            original = (root / 'config/keywords.json').read_bytes()
            (root / 'config/keywords.json').unlink()
            restore_config(root, backup)
            self.assertEqual((root / 'config/keywords.json').read_bytes(), original)

    def make_root(self, folder):
        root = Path(folder)
        (root / 'config').mkdir()
        for name in ('sources.yaml', 'keywords.json', 'official-trace.json', 'security-policy.json'):
            (root / 'config' / name).write_bytes((ROOT / 'config' / name).read_bytes())
        return root

    def test_restore_recovers_config_without_touching_runtime(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            root = self.make_root(folder)
            (root / 'data').mkdir()
            (root / 'data' / 'untouched.txt').write_text('runtime')
            original = (root / 'config/keywords.json').read_bytes()
            backup = backup_config(root)
            (root / 'config/keywords.json').write_text('{"keywords":[]}')
            restore_config(root, backup)
            self.assertEqual((root / 'config/keywords.json').read_bytes(), original)
            self.assertEqual((root / 'data/untouched.txt').read_text(), 'runtime')

    def test_corrupt_backup_is_rejected_before_any_config_changes(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            root = self.make_root(folder)
            backup = backup_config(root)
            original = (root / 'config/keywords.json').read_bytes()
            (backup / 'keywords.json').write_text('{}')
            with self.assertRaises(ValueError):
                restore_config(root, backup)
            self.assertEqual((root / 'config/keywords.json').read_bytes(), original)

    def test_snapshot_cannot_enable_forbidden_actions_or_authenticated_sources(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            root = self.make_root(folder)
            policy = root / 'config/security-policy.json'
            value = json.loads(policy.read_text())
            value['allow_claim'] = True
            policy.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                backup_config(root)

    def test_restore_rejects_backup_outside_project_directory(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            root = self.make_root(folder)
            with self.assertRaises(ValueError):
                restore_config(root, ROOT / 'config')
