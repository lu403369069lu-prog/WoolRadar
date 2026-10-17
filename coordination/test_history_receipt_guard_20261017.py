import unittest
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('history_receipt_guard', Path(__file__).with_name('HISTORICAL_CODEX_RECEIPT_GUARD_20261017.py'))
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def record(proj='coord'):
    return {'project':proj, 'repo_head':h.HEADS[proj], 'schema':1,
            'source':'local-disposable-codex',
            'results':[{'batch':batch,'exit_code':0,'log_sha256':'0'*64,
                        'counts':{'tests_reported':7 if batch!='S-BUILD' else None,
                                  'passed':7 if batch!='S-BUILD' else None,
                                  'failed':0 if batch!='S-BUILD' else None,
                                  'skipped':0 if batch!='S-BUILD' else None}}
                       for batch in sorted(h.BATCHES[proj])]}


class Guard(unittest.TestCase):
    def test_valid_groups(self):
        for p in h.HEADS:
            with self.subTest(project=p):
                self.assertTrue(h.review(record(p))['local_suite_receipt_accepted'])
    def test_bad_head(self):
        x=record();x['repo_head']='a'*40
        self.assertIn('HEAD_MISMATCH',h.review(x)['errors'])
    def test_duplicate(self):
        x=record();x['results'].append(x['results'][0])
        self.assertIn('DUPLICATE_BATCH',h.review(x)['errors'])
    def test_no_count(self):
        x=record();x['results'][0]['counts']['tests_reported']=0
        self.assertIn('NO_TEST_COUNT',h.review(x)['errors'])
    def test_nonzero(self):
        x=record();x['results'][0]['exit_code']=1
        self.assertFalse(h.review(x)['local_suite_receipt_accepted'])
    def test_skip_is_not_complete(self):
        x=record();x['results'][0]['counts']['skipped']=1
        self.assertIn('SKIPPED_NOT_FULLY_ACCEPTED',h.review(x)['errors'])
    def test_missing_pass_count(self):
        x=record();x['results'][0]['counts']['passed']=None
        self.assertIn('INVALID_TEST_OUTCOME',h.review(x)['errors'])
    def test_never_claims_business_green(self):
        x=record();r=h.review(x)
        self.assertFalse(r['business_gold_accepted'])
        self.assertFalse(r['historical_recovery_closed'])


if __name__ == '__main__':unittest.main()
