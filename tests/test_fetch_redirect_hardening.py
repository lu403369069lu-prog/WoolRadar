"""W5 public-fetch URL/redirect fail-closed behavior, using mocked transports."""

import io
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from core.collector import SourcePaused, _safe_public_fetch_url, budgeted_read


class FetchRedirectHardeningTests(unittest.TestCase):
    def test_standard_https_port_remains_approved(self):
        self.assertTrue(_safe_public_fetch_url('https://public.example/feed'))
        self.assertTrue(_safe_public_fetch_url('https://public.example:443/feed'))

    def test_nonstandard_https_ports_are_rejected_before_network(self):
        for port in (22, 80, 444, 8443, 65535):
            with self.subTest(port=port), patch('core.collector.urllib.request.build_opener') as opener:
                with self.assertRaisesRegex(SourcePaused, 'UNAPPROVED_REFERENCE_URL'):
                    budgeted_read(urllib.request.Request(f'https://public.example:{port}/feed'))
                opener.assert_not_called()

        # A standard-port first hop must not turn into arbitrary TCP port access.
        error = urllib.error.HTTPError('https://public.example/feed', 302, 'redirect',
                                       {'Location': 'https://cdn.example:8443/feed'}, io.BytesIO())
        try:
            with patch('core.collector.urllib.request.build_opener') as opener:
                opener.return_value.open.side_effect = [error, AssertionError('unexpected second open')]
                with self.assertRaisesRegex(SourcePaused, 'UNAPPROVED_REFERENCE_REDIRECT'):
                    budgeted_read(urllib.request.Request('https://public.example/feed'))
                self.assertEqual(opener.return_value.open.call_count, 1)
        finally:
            error.close()

    def test_credential_headers_block_redirect_instead_of_following(self):
        for name in ('Cookie', 'Cookie2', 'Proxy-Authorization', 'X-Api-Key', 'X-Auth-Token'):
            with self.subTest(header=name):
                request = urllib.request.Request('https://public.example/feed',
                                                 headers={name: 'synthetic-secret'})
                error = urllib.error.HTTPError(request.full_url, 302, 'redirect',
                                               {'Location': 'https://cdn.example/feed'}, io.BytesIO())
                try:
                    with patch('core.collector.urllib.request.build_opener') as opener, \
                            patch('core.collector.time.sleep'):
                        opener.return_value.open.side_effect = [error, AssertionError('unexpected second open')]
                        with self.assertRaisesRegex(SourcePaused, 'AUTHENTICATED_REDIRECT_REJECTED'):
                            budgeted_read(request)
                        self.assertEqual(opener.return_value.open.call_count, 1)
                finally:
                    error.close()

    def test_unredirected_credential_header_blocks_redirect(self):
        request = urllib.request.Request('https://public.example/feed')
        request.add_unredirected_header('x-api-key', 'synthetic-secret')
        error = urllib.error.HTTPError(request.full_url, 302, 'redirect',
                                       {'Location': 'https://cdn.example/feed'}, io.BytesIO())
        try:
            with patch('core.collector.urllib.request.build_opener') as opener:
                opener.return_value.open.side_effect = [error, AssertionError('unexpected second open')]
                with self.assertRaisesRegex(SourcePaused, 'AUTHENTICATED_REDIRECT_REJECTED'):
                    budgeted_read(request)
                self.assertEqual(opener.return_value.open.call_count, 1)
        finally:
            error.close()


if __name__ == '__main__':
    unittest.main()
