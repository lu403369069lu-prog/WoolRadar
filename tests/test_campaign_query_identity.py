import unittest
from core.dedup import normalize_url, canonical_key
from core.models import Candidate

class MarketingCampaignIdentityTests(unittest.TestCase):
    def candidate(self, url):
        return Candidate('node','synthetic','Free API credits',url)

    def test_campaign_parameter_distinguishes_business_rounds(self):
        a='https://vendor.example/claim?utm_campaign=fall'
        b='https://vendor.example/claim?utm_campaign=winter'
        self.assertNotEqual(normalize_url(a), normalize_url(b))
        self.assertNotEqual(canonical_key(self.candidate(a)), canonical_key(self.candidate(b)))

    def test_known_marketing_params_remain_disposable(self):
        baseline='https://vendor.example/claim?utm_campaign=fall'
        tracker='https://vendor.example/claim?utm_campaign=fall&utm_source=feed&utm_medium=email&utm_term=free&utm_content=card'
        self.assertEqual(normalize_url(baseline),normalize_url(tracker))

    def test_normal_query_keys_remain_preserved(self):
        self.assertNotEqual(normalize_url('https://vendor.example/claim?batch=one'),
                            normalize_url('https://vendor.example/claim?batch=two'))

if __name__ == '__main__':
    unittest.main()
