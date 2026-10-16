"""Independent synthetic preview boundary contracts; never reads real reports."""
import copy,hashlib,json,os,sys,unittest
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(os.environ['REVIEW_WOOL_ROOT'])/'independent-quality/delivery-bridge-20261016'))
from redact_daily import public_url,timestamp
from consume_preview import validate,UnsafePreview
from test_consume_preview import payload,ROW,NOW
class PreviewBoundary(unittest.TestCase):
 def test_percent_encoded_denied_route_is_not_public(self):
  self.assertIsNone(public_url('https://vendor.example/log%69n/promo'))
 def test_encoded_account_route_is_not_public(self):
  self.assertIsNone(public_url('https://vendor.example/%61ccount/profile'))
 def test_clean_public_route_remains_allowed(self):
  self.assertEqual(public_url('https://vendor.example/public-offer'),'https://vendor.example/public-offer')
 def test_consumer_rejects_nested_private_claim_fields(self):
  p=payload(dict(ROW,official_evidence=[dict(url='https://vendor.example/offer',checked_at='2026-10-16T00:00:00Z',claims={'public':True,'private_note':'synthetic-private-field'})]))
  raw=json.dumps(p).encode()
  with self.assertRaises(UnsafePreview):validate(raw,hashlib.sha256(raw).hexdigest(),now=NOW)
 def test_consumer_rejects_credential_bearing_public_url(self):
  p=payload(dict(ROW,public_url='https://synthetic:example@vendor.example/offer'));raw=json.dumps(p).encode()
  with self.assertRaises(UnsafePreview):validate(raw,hashlib.sha256(raw).hexdigest(),now=NOW)
 def test_extreme_timestamp_is_controlled_invalid_input(self):
  self.assertIsNone(timestamp('0001-01-01T00:00:00+14:00'))
if __name__=='__main__':unittest.main(verbosity=2)
