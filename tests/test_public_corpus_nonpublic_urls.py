"""Synthetic host-scope regression: no local/metadata hostname in a public corpus."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import record_public_sample, _clean_url_identity

PUBLIC = {'id': 'scope-feed', 'auth': 'public_feed', 'kind': 'rss', 'platform': 'test'}
PRIVATE_HOSTS = (
    'http://127.0.0.1:8181/admin',
    'http://10.0.0.4/private',
    'https://192.168.20.30/app',
    'http://169.254.169.254/latest/meta-data',
    'http://0.0.0.0/admin',
    'http://[::1]/private',
    'http://[fd00::1]/private',
    'http://localhost/admin',
    'https://svc.local/admin',
    'https://ops.internal/admin',
    'http://router.home.arpa/',
    'http://printer.lan/page',
    'https://service.onion/internal',
    'http://intranet/private',
    'https://www.invalid/secret',
    'https://source.test/fake',
    'https://archive.example/private',
    'http://8.8.8.8:80/',
    'https://[2606:4700:4700::1111]/',
)

class NonPublicProducerIdentity(unittest.TestCase):
    def render(self, url, *, text=False):
        with tempfile.TemporaryDirectory() as d:
            row = {'url': url, 'title': ('Visit ' + url if text else 'Public test'),
                   'summary': ('Reference ' + url if text else 'No links')}
            path = record_public_sample(Path(d), 'synthetic', PUBLIC, [row], [False])
            return json.loads(path.read_text(encoding='utf8'))['rows'][0]

    def test_private_ip_and_local_names_have_no_identity(self):
        for url in PRIVATE_HOSTS:
            with self.subTest(url=url):
                row = self.render(url)
                self.assertFalse(row['url_identity_preserved'])
                self.assertEqual(row['url'], '[non-public host redacted]')
                self.assertNotIn(url, json.dumps(row))

    def test_private_urls_embedded_in_title_and_summary_are_redacted(self):
        for url in ('http://127.0.0.1:8888/path', 'https://svc.internal/path'):
            with self.subTest(url=url):
                row = self.render(url, text=True)
                self.assertNotIn(url, json.dumps(row))
                self.assertTrue(row['text_url_redacted'])
                self.assertFalse(row['url_identity_preserved'])

    def test_public_dns_hostname_retained(self):
        for url in ('https://example.org/offers?batch=alpha', 'https://www.wikipedia.org/',
                    'https://subdomain.example.com/public'):
            with self.subTest(url=url):
                self.assertEqual(_clean_url_identity(url), (url, True))

    def test_private_netloc_with_dot_and_port_is_redacted(self):
        row = self.render('http://localhost.:8118/secret?token=synthetic-only')
        self.assertEqual(row['url'], '[non-public host redacted]')
        self.assertFalse(row['url_identity_preserved'])

    def test_public_tracking_cleanup_remains_identity_preserving(self):
        row = self.render('https://example.org/view?batch=beta&utm_source=ads')
        self.assertEqual(row['url'], 'https://example.org/view?batch=beta')
        self.assertTrue(row['url_identity_preserved'])

    def test_metadata_service_does_not_become_public_sample(self):
        row = self.render('http://169.254.169.254/latest/meta-data/credentials?batch=1')
        self.assertFalse(row['url_identity_preserved'])
        self.assertTrue(row['url_sanitized'])
        self.assertNotIn('169.254.169.254', json.dumps(row))

if __name__ == '__main__':
    unittest.main()
