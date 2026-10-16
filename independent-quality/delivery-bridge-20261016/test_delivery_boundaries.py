"""Producer/consumer privacy and same-identity revision contracts, offline only."""
import copy,hashlib,json,unittest
from datetime import datetime,timezone,timedelta
from redact_daily import build_preview,public_url,timestamp
from consume_preview import validate,review_delta,UnsafePreview
NOW=datetime(2026,10,16,1,tzinfo=timezone.utc)
ROW={'title':'Public cloud developer benefit','primary_url':'https://benefit.example/offer','status':'UNKNOWN','batch_id':'round1','first_seen':'2026-10-16T00:00:00Z','evidence':[]}
def preview(row=None):return build_preview({'date':'2026-10-16','events':[copy.deepcopy(row or ROW)]},'b'*64,NOW)
def checked(obj):
    raw=json.dumps(obj,ensure_ascii=False).encode();return validate(raw,hashlib.sha256(raw).hexdigest(),now=NOW)
class DeliveryBoundaryTests(unittest.TestCase):
    def test_exporter_rejects_encoded_identity_and_sensitive_routes(self):
        for path in ['/users/synthetic%40example.com','/%61ccount/synthetic-user','/%74oken/SYNTHETIC_ONLY_VALUE','/%2561ccount/user','/safe%5caccount/user','/log%69n/promo']:
            with self.subTest(path=path):
                url='https://benefit.example'+path
                self.assertIsNone(public_url(url))
                self.assertEqual(preview(dict(ROW,primary_url=url))['events'],[])
    def test_consumer_rejects_unsafe_event_urls(self):
        for value in ['https://me:synthetic@benefit.example/offer','http://benefit.example/offer','https://localhost/offer','https://benefit.example/%61ccount/user']:
            p=preview();p['events'][0]['public_url']=value
            with self.subTest(value=value),self.assertRaises(UnsafePreview):checked(p)
    def test_consumer_rejects_private_title_values(self):
        for value in ['Contact synthetic@example.com','password SYNTHETIC_ONLY','my api_key value','']:
            p=preview();p['events'][0]['title']=value
            with self.subTest(value=value),self.assertRaises(UnsafePreview):checked(p)
    def test_consumer_rejects_unwhitelisted_or_wrong_claim_values(self):
        for claims in [{'account_id':'synthetic'},{'token':'SYNTHETIC_ONLY'},{'open':'true'},{'remaining':-1},{'remaining':True},{'region':'synthetic@example.com'},{'expires_at':'not-a-time'}]:
            p=preview();p['events'][0]['official_evidence']=[{'url':'https://benefit.example/terms','checked_at':'2026-10-16T00:00:00Z','claims':claims}]
            with self.subTest(claims=claims),self.assertRaises(UnsafePreview):checked(p)
    def test_consumer_rejects_bad_proof_url_values(self):
        for value in [{},'https://localhost/terms','https://benefit.example/terms?token=synthetic']:
            p=preview();p['events'][0]['official_evidence']=[{'url':value,'checked_at':'2026-10-16T00:00:00Z','claims':{}}]
            with self.subTest(value=value),self.assertRaises(UnsafePreview):checked(p)
    def test_same_identity_status_change_requires_recheck(self):
        old=preview();old['generated_at']=(NOW-timedelta(seconds=1)).isoformat();old=checked(old);new=checked(preview(dict(ROW,status='CLAIMABLE')))
        self.assertEqual(review_delta(new,old)['candidate_keys'],[new['events'][0]['event_key']])
        self.assertFalse(new['public_application_live_verified'])
    def test_same_identity_title_change_requires_recheck(self):
        old=preview();old['generated_at']=(NOW-timedelta(seconds=1)).isoformat();old=checked(old);new=checked(preview(dict(ROW,title='Updated public developer benefit')))
        self.assertEqual(review_delta(new,old)['candidate_keys'],[new['events'][0]['event_key']])
    def test_same_identity_official_proof_change_requires_recheck(self):
        old=preview();old['generated_at']=(NOW-timedelta(seconds=1)).isoformat();old=checked(old);row=dict(ROW,evidence=[{'kind':'official','url':'https://benefit.example/terms','checked_at':'2026-10-16T00:00:00Z','claims':{'remaining':7,'open':True}}]);new=checked(preview(row))
        result=review_delta(new,old)
        self.assertEqual(result['candidate_keys'],[new['events'][0]['event_key']])
        self.assertEqual(result['status'],'MANUAL_SOURCE_RECHECK_REQUIRED')
        self.assertNotIn('CLAIMABLE',json.dumps(result))
    def test_unchanged_rows_or_proof_order_do_not_make_new_candidates(self):
        p=preview(dict(ROW,evidence=[{'kind':'official','url':u,'checked_at':'2026-10-16T00:00:00Z','claims':{'open':True}} for u in ['https://benefit.example/a','https://benefit.example/b']]))
        old=checked(p);new=copy.deepcopy(p);new['events'][0]['official_evidence'].reverse()
        new['generated_at']=(NOW-timedelta(seconds=1)).isoformat()
        self.assertEqual(review_delta(checked(new),old)['candidate_keys'],[])
    def test_timestamp_extremes_are_rejected_without_crashing(self):
        for value in ['0001-01-01T00:00:00+14:00','9999-12-31T23:59:59-14:00']:
            with self.subTest(value=value):
                self.assertIsNone(timestamp(value))
                p=preview();p['events'][0]['first_seen']=value
                with self.assertRaises(UnsafePreview):checked(p)
    def test_safe_public_values_still_pass(self):
        row=dict(ROW,evidence=[{'kind':'official','url':'https://benefit.example/terms','checked_at':'2026-10-16T00:00:00Z','claims':{'region':'GLOBAL','card_required':False,'remaining':7,'expires_at':'2026-10-17T00:00:00Z'}}])
        p=checked(preview(row));self.assertEqual(len(p['events']),1)
        self.assertEqual(p['events'][0]['official_evidence'][0]['claims']['remaining'],7)
        self.assertEqual(public_url('https://benefit.example/docs/cloud-offer'),'https://benefit.example/docs/cloud-offer')
    def test_local_paths_never_survive_titles(self):
        for value in [r'Free grant at C:\Users\SyntheticUser\Private\daily.json',r'Free grant at \\host\Private\daily.json','Free grant at /home/synthetic/private.json']:
            with self.subTest(value=value):
                self.assertEqual(preview(dict(ROW,title=value))['events'],[])
                p=preview();p['events'][0]['title']=value
                with self.assertRaises(UnsafePreview):checked(p)
    def test_check_time_refresh_alone_is_not_a_new_offer_candidate(self):
        row=dict(ROW,evidence=[{'kind':'official','url':'https://benefit.example/terms','checked_at':'2026-10-16T00:00:00Z','claims':{'open':True}}])
        old=checked(preview(row));new=copy.deepcopy(old)
        new['events'][0]['official_evidence'][0]['checked_at']='2026-10-16T00:01:00Z'
        self.assertEqual(review_delta(checked(new),old)['candidate_keys'],[])
    def test_same_second_semantic_revisions_need_sequence_proof(self):
        old=checked(preview())
        for changed in [dict(ROW,status='CLAIMABLE'),dict(ROW,title='Updated public developer benefit'),dict(ROW,evidence=[{'kind':'official','url':'https://benefit.example/terms','checked_at':'2026-10-16T00:00:00Z','claims':{'remaining':7}}])]:
            with self.subTest(row=changed):
                result=review_delta(checked(preview(changed)),old)
                self.assertEqual(result['status'],'SNAPSHOT_ORDER_AMBIGUOUS')
                self.assertEqual(result['candidate_keys'],[])
                self.assertEqual(result['withdrawn_keys'],[])
    def test_baseline_is_still_zero_candidates(self):
        p=checked(preview());self.assertEqual(review_delta(p)['candidate_keys'],[])
if __name__=='__main__':unittest.main()
