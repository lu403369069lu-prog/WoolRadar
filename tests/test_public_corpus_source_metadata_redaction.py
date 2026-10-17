"""Even source metadata must not leak local or credential-bearing URLs."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import record_public_sample

BASE={'id':'synthetic-source-metadata','auth':'public_feed','kind':'rss','platform':'rss'}

class SourceMetadataRedaction(unittest.TestCase):
    def render(self,node,platform):
        with tempfile.TemporaryDirectory() as root:
            src=dict(BASE,platform=platform)
            file=record_public_sample(Path(root),node,src,
                [{'url':'https://example.org/offer','title':'Public','summary':'Synthetic'}],[False])
            return json.loads(file.read_text('utf8'))

    def test_node_reference_to_local_admin_is_redacted(self):
        url='http://127.0.0.1:9000/admin'
        doc=self.render('collector '+url,'rss')
        self.assertNotIn(url,json.dumps(doc))
        self.assertIn('[non-public host redacted]',doc['node'])

    def test_platform_must_not_record_url_with_secret_path(self):
        url='https://example.org/api-key/synthetic-not-real'
        doc=self.render('collector','Source '+url)
        self.assertNotIn('synthetic-not-real',json.dumps(doc))
        self.assertIn('[sensitive path redacted]',doc['platform'])

    def test_ordinary_platform_metadata_is_preserved(self):
        doc=self.render('rss','github-public-rss')
        self.assertEqual(doc['node'],'rss')
        self.assertEqual(doc['platform'],'github-public-rss')

if __name__=='__main__':unittest.main()
