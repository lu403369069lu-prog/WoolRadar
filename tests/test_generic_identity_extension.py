import unittest
from core.dedup import canonical_key
from core.models import Candidate


def make(url, title, *, metadata=None):
    return Candidate('synthetic', 'public', title, url, metadata=metadata or {})


class ExtendedGenericIdentityTests(unittest.TestCase):
    def test_ai_credits_are_not_a_vendor_identity(self):
        self.assertNotEqual(canonical_key(make('https://one.example/ai', 'Free AI credits')),
                            canonical_key(make('https://two.example/ai', 'Free AI credits')))

    def test_numeric_resource_specs_are_not_a_vendor_identity(self):
        self.assertNotEqual(canonical_key(make('https://one.example/vps', 'Free VPS 1 GB')),
                            canonical_key(make('https://two.example/vps', 'Free VPS 1 GB')))

    def test_two_specs_on_same_url_stay_distinct(self):
        self.assertNotEqual(canonical_key(make('https://vendor.example/offers', 'Free VPS 1 GB')),
                            canonical_key(make('https://vendor.example/offers', 'Free VPS 2 GB')))

    def test_tracking_parameters_do_not_split_generic_numeric_offer(self):
        self.assertEqual(canonical_key(make('https://vendor.example/vps?utm_source=one#fragment', 'Free VPS 1 GB')),
                         canonical_key(make('https://vendor.example/vps?utm_campaign=two', 'Free VPS 1 GB')))

    def test_branded_title_cross_posts_still_merge(self):
        self.assertEqual(canonical_key(make('https://forum-one.example/a', 'RackNerd Free VPS Giveaway')),
                         canonical_key(make('https://forum-two.example/b', 'RackNerd Free VPS Giveaway')))

    def test_brand_with_resource_size_does_not_become_generic(self):
        self.assertEqual(canonical_key(make('https://forum-one.example/a', 'RackNerd Free VPS 1 GB')),
                         canonical_key(make('https://forum-two.example/b', 'RackNerd Free VPS 1 GB')))

    def test_specific_year_batch_retains_cross_post_identity(self):
        self.assertEqual(canonical_key(make('https://forum-one.example/a', 'Free VPS 2026 GB')),
                         canonical_key(make('https://forum-two.example/b', 'Free VPS 2026 GB')))

    def test_existing_generic_url_only_key_is_preserved(self):
        self.assertEqual(canonical_key(make('https://vendor.example/api', 'Free API credits')),
                         canonical_key(make('https://vendor.example/api?utm_source=news', 'Free API credits')))

    def test_explicit_browser_verified_review_still_unifies(self):
        a='https://one.example/ai'; b='https://two.example/ai'; title='Free AI credits'
        review=dict(method='normal_browser_read', campaign_url='https://gleam.io/Ab123', member_urls=[a,b], member_titles={a:title,b:title})
        self.assertEqual(canonical_key(make(a,title,metadata={'campaign_review':review})),
                         canonical_key(make(b,title,metadata={'campaign_review':review})))


if __name__=='__main__': unittest.main()
