import unittest
try:
    from coordination.quota import policy
except ImportError:
    policy = None

class QuotaTests(unittest.TestCase):
    def test_official_windows_and_unknown(self):
        self.assertIsNotNone(policy,'quota policy required')
        self.assertEqual(policy(None)['stage'],'unknown')
        self.assertEqual(policy({'primary':{'usedPercent':81}})['stage'],'quota_risk')
        self.assertEqual(policy({'primary':{'usedPercent':91}})['stage'],'quota_critical')
        self.assertEqual(policy({'primary':{'usedPercent':2},'secondary':{'usedPercent':63}})['remaining_percent'],37)
        self.assertEqual(policy({'limit_reached':True})['stage'],'quota_paused')
        self.assertFalse(policy({'limit_reached':True})['allow_new_model_tasks'])
        self.assertFalse(policy({'primary':{'usedPercent':True}})['allow_large_task'])

if __name__=='__main__':
    unittest.main()
