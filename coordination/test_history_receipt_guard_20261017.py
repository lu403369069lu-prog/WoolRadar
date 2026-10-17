import unittest
import importlib.util
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

spec = importlib.util.spec_from_file_location('history_receipt_guard', Path(__file__).with_name('HISTORICAL_CODEX_RECEIPT_GUARD_20261017.py'))
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


MOCK_LOG = b'synthetic offline log for structural tests\n'


def record(proj='coord'):
    return {'project':proj, 'repo_head':h.HEADS[proj], 'schema':1,
            'source':'local-disposable-codex', 'no_live_gold_claim':True,
            'production_modified':False,
            'results':[{'batch':batch,'exit_code':0,'log_sha256':hashlib.sha256(MOCK_LOG).hexdigest(),
                        'counts':{'tests_reported':7 if batch!='S-BUILD' else None,
                                  'passed':7 if batch!='S-BUILD' else None,
                                  'failed':0 if batch!='S-BUILD' else None,
                                  'skipped':0 if batch!='S-BUILD' else None}}
                       for batch in sorted(h.BATCHES[proj])]}


def checked(data: dict) -> dict:
    with TemporaryDirectory(prefix='historical-guard-synthetic-') as folder:
        for row in data.get('results', []):
            if isinstance(row, dict) and isinstance(row.get('batch'), str):
                (Path(folder) / (row['batch'] + '.log')).write_bytes(MOCK_LOG)
        return h.review(data, Path(folder))


class Guard(unittest.TestCase):
    def test_valid_groups(self):
        for p in h.HEADS:
            with self.subTest(project=p):
                self.assertTrue(checked(record(p))['local_suite_receipt_accepted'])
    def test_bad_head(self):
        x=record();x['repo_head']='a'*40
        self.assertIn('HEAD_MISMATCH',checked(x)['errors'])
    def test_duplicate(self):
        x=record();x['results'].append(x['results'][0])
        self.assertIn('DUPLICATE_BATCH',checked(x)['errors'])
    def test_no_count(self):
        x=record();x['results'][0]['counts']['tests_reported']=0
        self.assertIn('NO_TEST_COUNT',checked(x)['errors'])
    def test_nonzero(self):
        x=record();x['results'][0]['exit_code']=1
        self.assertFalse(checked(x)['local_suite_receipt_accepted'])
    def test_skip_is_not_complete(self):
        x=record();x['results'][0]['counts']['skipped']=1
        self.assertIn('SKIPPED_NOT_FULLY_ACCEPTED',checked(x)['errors'])
    def test_missing_pass_count(self):
        x=record();x['results'][0]['counts']['passed']=None
        self.assertIn('INVALID_TEST_OUTCOME',checked(x)['errors'])
    def test_missing_real_log_directory_must_block(self):
        self.assertIn('LOG_BYTES_NOT_VERIFIED', h.review(record())['errors'])

    def test_tampered_raw_log_digest_is_rejected(self):
        with TemporaryDirectory() as folder:
            data = record()
            (Path(folder) / 'C-ALL.log').write_bytes(b'synthetic TAMPERED log\n')
            self.assertIn('LOG_DIGEST_MISMATCH', h.review(data, Path(folder))['errors'])

    def test_missing_original_log_is_rejected(self):
        with TemporaryDirectory() as folder:
            self.assertIn('MISSING_BATCH_LOG', h.review(record(), Path(folder))['errors'])

    def test_impossible_count_sums_are_rejected(self):
        for counts in (
            {'tests_reported':7,'passed':6,'failed':0,'skipped':0},
            {'tests_reported':7,'passed':8,'failed':0,'skipped':0},
            {'tests_reported':7,'passed':-1,'failed':0,'skipped':0},
            {'tests_reported':7,'passed':7,'failed':-1,'skipped':1},
        ):
            with self.subTest(counts=counts):
                data = record()
                data['results'][0]['counts'] = counts
                self.assertIn('INVALID_TEST_OUTCOME', checked(data)['errors'])

    def test_no_genuine_safety_declaration_is_rejected(self):
        for field, value, error in (
            ('no_live_gold_claim', False, 'UNSAFE_GOLD_CLAIM'),
            ('production_modified', True, 'PRODUCTION_MODIFICATION_NOT_DENIED'),
        ):
            with self.subTest(field=field):
                data = record()
                data[field] = value
                self.assertIn(error, checked(data)['errors'])

    def test_malformed_batch_and_project_rejected_without_crash(self):
        data = record()
        data['results'][0]['batch'] = ['malformed']
        self.assertIn('INVALID_BATCH_NAME', checked(data)['errors'])
        data = record()
        data['project'] = ['bad']
        self.assertIn('UNKNOWN_PROJECT', checked(data)['errors'])

    def test_never_claims_business_green(self):
        x=record();r=checked(x)
        self.assertFalse(r['business_gold_accepted'])
        self.assertFalse(r['historical_recovery_closed'])


if __name__ == '__main__':unittest.main()
