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

    def test_unbranded_year_batch_does_not_merge_unaudited_posts(self):
        self.assertNotEqual(canonical_key(make('https://forum-one.example/a', 'Free VPS 2026 GB')),
                            canonical_key(make('https://forum-two.example/b', 'Free VPS 2026 GB')))

    def test_reviewed_year_batch_can_merge_verified_campaign_members(self):
        a = 'https://forum-one.example/a'
        b = 'https://forum-two.example/b'
        title = 'Free VPS 2026 GB'
        review = dict(method='normal_browser_read', campaign_url='https://gleam.io/Ab123',
                      member_urls=[a,b], member_titles={a:title,b:title})
        self.assertEqual(canonical_key(make(a,title,metadata={'campaign_review':review})),
                         canonical_key(make(b,title,metadata={'campaign_review':review})))

    def test_existing_generic_url_only_key_is_preserved(self):
        self.assertEqual(canonical_key(make('https://vendor.example/api', 'Free API credits')),
                         canonical_key(make('https://vendor.example/api?utm_source=news', 'Free API credits')))

    def test_equivalent_query_key_orders_do_not_split_offer(self):
        a=make('https://vendor.example/offer?sku=1&region=us', 'Free API credits')
        b=make('https://vendor.example/offer?region=us&sku=1', 'Free API credits')
        self.assertEqual(canonical_key(a), canonical_key(b))

    def test_source_campaign_identifier_is_not_automatically_tracking(self):
        a=make('https://vendor.example/offer?source_campaign=alpha', 'Free API credits')
        b=make('https://vendor.example/offer?source_campaign=beta', 'Free API credits')
        self.assertNotEqual(canonical_key(a), canonical_key(b))

    def test_reference_identifier_does_not_get_prefix_stripped(self):
        a=make('https://vendor.example/offer?reference_id=alpha', 'Free API credits')
        b=make('https://vendor.example/offer?reference_id=beta', 'Free API credits')
        self.assertNotEqual(canonical_key(a), canonical_key(b))

    def test_simple_tracking_source_ref_and_utm_still_removed(self):
        a=make('https://vendor.example/offer?utm_source=rss&ref=a&source=b', 'Free API credits')
        b=make('https://vendor.example/offer', 'Free API credits')
        self.assertEqual(canonical_key(a), canonical_key(b))

    def test_duplicate_query_values_retain_meaningful_relative_order(self):
        a=make('https://vendor.example/offer?sku=1&sku=2&region=us', 'Free API credits')
        b=make('https://vendor.example/offer?region=us&sku=1&sku=2', 'Free API credits')
        c=make('https://vendor.example/offer?region=us&sku=2&sku=1', 'Free API credits')
        self.assertEqual(canonical_key(a), canonical_key(b))
        self.assertNotEqual(canonical_key(a), canonical_key(c))

    def test_explicit_browser_verified_review_still_unifies(self):
        a='https://one.example/ai'; b='https://two.example/ai'; title='Free AI credits'
        review=dict(method='normal_browser_read', campaign_url='https://gleam.io/Ab123', member_urls=[a,b], member_titles={a:title,b:title})
        self.assertEqual(canonical_key(make(a,title,metadata={'campaign_review':review})),
                         canonical_key(make(b,title,metadata={'campaign_review':review})))


if __name__=='__main__': unittest.main()
