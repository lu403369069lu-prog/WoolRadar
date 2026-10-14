import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from core.holdout_eval import evaluate


class HoldoutEvaluationTests(unittest.TestCase):
    def fixture(self, directory: Path):
        (directory / 'config').mkdir()
        (directory / 'data' / 'public-corpus').mkdir(parents=True)
        source = {'id': 'fixture', 'owner_node': 'openmagpie', 'platform': 'Example',
                  'official': False, 'kind': 'rss', 'auth': 'public_feed'}
        (directory / 'config' / 'sources.yaml').write_text(json.dumps(
            {'schema_version': 1, 'sources': [source]}), encoding='utf-8')
        inputs = [
            ('Free API credits', 'https://a.example/offer', True, True, 'campaign-a'),
            ('Free API credits', 'https://b.example/offer', True, True, 'campaign-b'),
            ('VPS giveaway', 'https://c.example/offer', True, True, 'campaign-c'),
            ('Free VPS promo today', 'https://c.example/second', True, True, 'campaign-c'),
            ('How to request a coupon', 'https://d.example/help', True, False, None),
            ('Free offer unrecognized', 'https://e.example/offer', False, True, 'campaign-e'),
            ('Price comparison', 'https://f.example/a', False, False, None),
            ('Unclear archived item', 'https://g.example/a', True, None, None),
        ]
        rows = [{'index': i, 'title': title, 'url': url, 'summary': '', 'published_at': '',
                 'accepted': selected} for i, (title, url, selected, _, _) in enumerate(inputs)]
        snapshot = {'schema_version': 1, 'source_id': 'fixture', 'sampled_at': '2026-10-15T00:00:00Z',
                    'rows': rows, 'fetched_count': len(rows), 'stored_count': len(rows),
                    'rows_truncated': False}
        snapshot_bytes = json.dumps(snapshot).encode('utf-8')
        (directory / 'data/public-corpus/fixture.json').write_bytes(snapshot_bytes)
        labels = {'schema_version': 1, 'split': 'holdout', 'frozen_code_ref': 'fixture-commit',
                  'snapshots': [{'source_id': 'fixture', 'sampled_at': snapshot['sampled_at'],
                                 'sha256': hashlib.sha256(snapshot_bytes).hexdigest(),
                                 'labels': [{'index': i, 'offer': offer, 'campaign_id': campaign}
                                            for i, (_, _, _, offer, campaign) in enumerate(inputs)]}]}
        label_path = directory / 'labels.json'
        label_path.write_text(json.dumps(labels), encoding='utf-8')
        return label_path

    def test_explicit_denominators_and_title_collision(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.fixture(root)
            result = evaluate(root, path)
            self.assertEqual(result['counts'], {'labeled': 7, 'unknown': 1, 'tp': 4,
                                                'fp': 1, 'fn': 1, 'tn': 1})
            self.assertEqual(result['lead_precision'], .8)
            self.assertEqual(result['lead_recall'], .8)
            self.assertEqual(result['dedup_pairs'], {'true_positive': 0, 'predicted': 1,
                                                     'true': 1, 'false_merge': 1, 'false_split': 1})
            self.assertEqual(result['dedup_pair_precision'], 0)
            self.assertEqual(result['dedup_pair_recall'], 0)

    def test_rejects_incomplete_corpus(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.fixture(root)
            corpus = root / 'data/public-corpus/fixture.json'
            sample = json.loads(corpus.read_text())
            sample['rows_truncated'] = True
            changed = json.dumps(sample).encode('utf-8')
            corpus.write_bytes(changed)
            labels = json.loads(path.read_text())
            labels['snapshots'][0]['sha256'] = hashlib.sha256(changed).hexdigest()
            path.write_text(json.dumps(labels))
            with self.assertRaisesRegex(ValueError, 'INCOMPLETE_OR_MISMATCHED_CORPUS'):
                evaluate(root, path)

    def test_rejects_label_snapshot_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.fixture(root)
            labels = json.loads(path.read_text())
            labels['snapshots'][0]['sampled_at'] = '2027-01-01T00:00:00Z'
            path.write_text(json.dumps(labels))
            with self.assertRaisesRegex(ValueError, 'INCOMPLETE_OR_MISMATCHED_CORPUS'):
                evaluate(root, path)

    def test_rejects_missing_labels_or_campaign_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.fixture(root)
            labels = json.loads(path.read_text())
            labels['snapshots'][0]['labels'].pop()
            path.write_text(json.dumps(labels))
            with self.assertRaisesRegex(ValueError, 'EVERY_SAMPLED_ROW_REQUIRES_ONE_LABEL'):
                evaluate(root, path)
            labels['snapshots'][0]['labels'].append({'index': 7, 'offer': None})
            labels['snapshots'][0]['labels'][0].pop('campaign_id')
            path.write_text(json.dumps(labels))
            with self.assertRaisesRegex(ValueError, 'POSITIVE_OFFER_REQUIRES_CAMPAIGN_ID'):
                evaluate(root, path)


    def test_rejects_wrong_expected_code_ref(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.fixture(root)
            labels = json.loads(path.read_text(encoding='utf-8'))
            labels['frozen_code_ref'] = 'a' * 40
            path.write_text(json.dumps(labels), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'FROZEN_CODE_REF_MISMATCH'):
                evaluate(root, path, expected_code_ref='b' * 40)

    def test_rejects_invalid_expected_code_ref(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.fixture(root)
            with self.assertRaisesRegex(ValueError, 'EXPECTED_CODE_REF_MUST_BE_FULL_SHA'):
                evaluate(root, path, expected_code_ref='fixture-commit')

    def test_accepts_matching_expected_code_ref(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.fixture(root)
            labels = json.loads(path.read_text(encoding='utf-8'))
            labels['frozen_code_ref'] = 'a' * 40
            path.write_text(json.dumps(labels), encoding='utf-8')
            result = evaluate(root, path, expected_code_ref='A' * 40)
            self.assertEqual(result['counts']['tp'], 4)

if __name__ == '__main__':
    unittest.main()

