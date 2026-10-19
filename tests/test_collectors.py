import json
import socket
import unittest
import tempfile
import io
import urllib.error
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

from core.collector import classify_exception, contains_keyword, parse_feed, row_allowed, RequestBudget, SourcePaused, _request, fetch_digest_rss, _fetch_source
from core.config import load_sources


ROOT = Path(__file__).parents[1]


class CollectorTests(unittest.TestCase):
    def test_captcha_in_http_503_pauses_actual_host(self):
        from core.collector import budgeted_read
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            budget = RequestBudget(Path(td))
            error = urllib.error.HTTPError('https://actual.example/', 503, 'challenge', {}, io.BytesIO(b'cf-chl-captcha'))
            with patch('core.collector.urllib.request.build_opener') as build:
                build.return_value.open.side_effect = error
                with self.assertRaises(urllib.error.HTTPError):
                    budgeted_read(urllib.request.Request('https://actual.example/'), budget)
            with self.assertRaises(SourcePaused):
                RequestBudget(Path(td)).acquire_http('https://actual.example/other')
            error.close()

    def test_oauth_refresh_429_remains_temporary_http_error(self):
        from core.collector import fetch_reddit_oauth
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            root = Path(td)
            credentials = root / 'nodes/clawradar/credentials.json'
            credentials.parent.mkdir(parents=True)
            credentials.write_text(json.dumps({'client_id': 'test-only', 'refresh_token': 'test-only'}))
            error = urllib.error.HTTPError('https://www.reddit.com/api/v1/access_token', 429, 'rate', {'Retry-After': '1800'}, io.BytesIO())
            with patch('core.collector.budgeted_read', side_effect=error):
                with self.assertRaises(urllib.error.HTTPError):
                    fetch_reddit_oauth(root, {}, RequestBudget(root / 'state'))
            error.close()

    def test_oauth_refresh_503_remains_recoverable_failure(self):
        from core.collector import fetch_reddit_oauth
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            root = Path(td)
            credentials = root / 'nodes/clawradar/credentials.json'
            credentials.parent.mkdir(parents=True)
            credentials.write_text(json.dumps({'client_id': 'test-only', 'refresh_token': 'test-only'}))
            error = urllib.error.HTTPError('https://www.reddit.com/api/v1/access_token', 503, 'unavailable', {}, io.BytesIO())
            with patch('core.collector.budgeted_read', side_effect=error):
                with self.assertRaises(urllib.error.HTTPError):
                    fetch_reddit_oauth(root, {}, RequestBudget(root / 'state'))
            error.close()

    def test_authenticated_redirect_is_rejected_without_forwarding_secret(self):
        from core.collector import budgeted_read
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            budget = RequestBudget(Path(td))
            request = urllib.request.Request('https://api.example/token', data=b'private', headers={'Authorization': 'Basic private'})
            error = urllib.error.HTTPError(request.full_url, 302, 'redirect', {'Location': 'https://other.example/'}, io.BytesIO())
            with patch('core.collector.urllib.request.build_opener') as build:
                build.return_value.open.side_effect = error
                with self.assertRaises(SourcePaused) as captured:
                    budgeted_read(request, budget)
                self.assertEqual(str(captured.exception), 'AUTHENTICATED_REDIRECT_REJECTED')
                self.assertEqual(build.return_value.open.call_count, 1)
            error.close()

    def test_http_error_pauses_actual_response_host(self):
        from core.collector import budgeted_read
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            budget = RequestBudget(Path(td))
            error = urllib.error.HTTPError('https://actual.example/feed', 429, 'rate', {'Retry-After': '1800'}, io.BytesIO())
            with patch('core.collector.urllib.request.build_opener') as build:
                build.return_value.open.side_effect = error
                with self.assertRaises(urllib.error.HTTPError):
                    budgeted_read(urllib.request.Request('https://actual.example/feed'), budget)
            with self.assertRaises(SourcePaused):
                RequestBudget(Path(td)).acquire_http('https://actual.example/another')
            error.close()

    def test_redirect_to_paused_host_never_reaches_transport(self):
        from core.collector import budgeted_read
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            budget = RequestBudget(Path(td))
            budget.pause({'id': 'blocked', 'endpoint': 'https://blocked.example/'}, 'CAPTCHA_REQUIRED')
            redirect = urllib.error.HTTPError('https://entry.example/feed', 302, 'redirect', {'Location': 'https://blocked.example/feed'}, io.BytesIO())
            with patch('core.collector.urllib.request.build_opener') as build, patch('core.collector.time.sleep'):
                build.return_value.open.side_effect = redirect
                with self.assertRaises(SourcePaused):
                    budgeted_read(urllib.request.Request('https://entry.example/feed'), budget)
                self.assertEqual(build.return_value.open.call_count, 1)
            redirect.close()

    def test_redirect_to_private_or_non_https_target_never_reaches_transport(self):
        from core.collector import budgeted_read
        for target in ('https://127.0.0.1/admin', 'https://[::1]/admin',
                       'https://localhost/admin', 'http://other.example/feed',
                       'https://user:pass@other.example/feed'):
            with self.subTest(target=target), tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
                error = urllib.error.HTTPError('https://entry.example/feed', 302, 'redirect',
                                               {'Location': target}, io.BytesIO())
                with patch('core.collector.urllib.request.build_opener') as build, patch('core.collector.time.sleep'):
                    build.return_value.open.side_effect = [error, AssertionError('unsafe second request')]
                    with self.assertRaises(SourcePaused):
                        budgeted_read(urllib.request.Request('https://entry.example/feed'), RequestBudget(Path(td)))
                    self.assertEqual(build.return_value.open.call_count, 1)
                error.close()

    def test_direct_private_or_invalid_network_target_is_rejected_before_transport(self):
        from core.collector import budgeted_read
        for target in ('http://public.example/feed', 'https://127.0.0.1/private',
                       'https://[::ffff:127.0.0.1]/private', 'https://localhost/feed',
                       'https://user:pass@public.example/feed'):
            with self.subTest(target=target), patch('core.collector.urllib.request.build_opener') as build:
                with self.assertRaises(SourcePaused):
                    budgeted_read(urllib.request.Request(target))
                build.assert_not_called()

    def test_dns_private_or_mixed_answers_never_open_a_socket(self):
        from core.collector import _connect_public_peer, SourcePaused
        public = (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))
        private = (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))
        for answers in ([private], [public, private], []):
            with self.subTest(answers=answers):
                with patch('core.collector.socket.getaddrinfo', return_value=answers), \
                     patch('core.collector.socket.socket') as create_socket:
                    with self.assertRaisesRegex(SourcePaused, 'NON_PUBLIC_RESOLVED_PEER'):
                        _connect_public_peer(('public.example', 443), timeout=5)
                    create_socket.assert_not_called()

    def test_dns_public_address_is_pinned_for_tls_connection(self):
        from core.collector import _PublicPeerHTTPSConnection
        from unittest.mock import Mock
        target = ('8.8.8.8', 443)
        endpoint = (socket.AF_INET, socket.SOCK_STREAM, 6, '', target)
        context = Mock()
        with patch('core.collector.socket.getaddrinfo', return_value=[endpoint]) as resolve, \
             patch('core.collector.socket.socket') as create_socket:
            connection = _PublicPeerHTTPSConnection('public.example', timeout=5, context=context)
            connection.connect()
            resolve.assert_called_once_with('public.example', 443, type=socket.SOCK_STREAM)
            create_socket.return_value.connect.assert_called_once_with(target)
            context.wrap_socket.assert_called_once()
            self.assertEqual(context.wrap_socket.call_args.kwargs['server_hostname'], 'public.example')

    def test_budgeted_fetch_disables_environment_connect_proxies(self):
        from core.collector import budgeted_read
        from urllib.request import ProxyHandler
        with patch('core.collector.urllib.request.build_opener') as build:
            build.return_value.open.return_value.__enter__.return_value.read.return_value = b'example'
            self.assertEqual(budgeted_read(urllib.request.Request('https://public.example/')), b'example')
            handlers = build.call_args.args
            proxy_handlers = [handler for handler in handlers if isinstance(handler, ProxyHandler)]
            self.assertEqual(len(proxy_handlers), 1)
            self.assertEqual(proxy_handlers[0].proxies, {})

    def test_public_https_redirect_still_succeeds_with_each_hop_checked(self):
        from core.collector import budgeted_read
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            error = urllib.error.HTTPError('https://entry.example/feed', 302, 'redirect',
                                           {'Location': 'https://cdn.example/feed'}, io.BytesIO())
            with patch('core.collector.urllib.request.build_opener') as build, patch('core.collector.time.sleep'):
                build.return_value.open.side_effect = [error, io.BytesIO(b'public-feed')]
                payload = budgeted_read(urllib.request.Request('https://entry.example/feed'), RequestBudget(Path(td)))
                self.assertEqual(payload, b'public-feed')
                self.assertEqual(build.return_value.open.call_count, 2)
            error.close()

    def test_401_recovers_and_429_cooldown_cannot_be_forced(self):
        from core.collector import collect_for_node
        source = {'id': 'test', 'kind': 'rss', 'platform': 'Test', 'endpoint': 'https://test.example/feed', 'owner_node': 'openmagpie', 'interval_minutes': 1}
        for status in (401, 429):
            with self.subTest(status=status), tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
                error = urllib.error.HTTPError(source['endpoint'], status, 'test', {'Retry-After': '1800'}, io.BytesIO(b'no secrets'))
                with patch('core.collector.load_sources', return_value=[source]), patch('core.collector.load_keywords', return_value=['free']), patch('core.collector.time.time', return_value=1000), patch('core.collector._fetch_source', side_effect=error):
                    result = collect_for_node(Path(td), 'openmagpie')
                    self.assertEqual(result.sources[0].status, 'PAUSED' if status == 429 else 'FAILED')
                error.close()
                with patch('core.collector.load_sources', return_value=[source]), patch('core.collector.load_keywords', return_value=['free']), patch('core.collector.time.time', return_value=1100), patch('core.collector._fetch_source', return_value=[]) as fetch:
                    result = collect_for_node(Path(td), 'openmagpie', force=True)
                    self.assertEqual(fetch.call_count, 0 if status == 429 else 1)
                with patch('core.collector.load_sources', return_value=[source]), patch('core.collector.load_keywords', return_value=['free']), patch('core.collector.time.time', return_value=3000), patch('core.collector._fetch_source', return_value=[]):
                    self.assertEqual(collect_for_node(Path(td), 'openmagpie').sources[0].status, 'OK')

    def test_hn_resume_reuses_successful_item_after_network_failure(self):
        from core.collector import _fetch_hn
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            budget = RequestBudget(Path(td))
            source = {'id': 'hn', 'endpoint': 'https://hacker-news.firebaseio.com/v0/topstories.json'}
            first = [b'[1,2]', b'{"title":"Free VPS", "url":"https://vendor.example/offer"}', TimeoutError('offline')]
            with patch('core.collector._request', side_effect=first), patch('core.collector.time.sleep'), patch('core.collector.time.time', return_value=1000):
                with self.assertRaises(TimeoutError):
                    _fetch_hn(source, budget=budget)
            with patch('core.collector._request', side_effect=[b'{"title":"Free credits"}']) as request, patch('core.collector.time.sleep'), patch('core.collector.time.time', return_value=4601):
                rows = _fetch_hn(source, budget=RequestBudget(Path(td)))
                self.assertEqual(len(rows), 2)
                self.assertEqual(request.call_count, 1)
                self.assertTrue(request.call_args.args[0].endswith('/2.json'))

    def test_http_budget_persists_hourly_cap_and_spacing(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            with patch('core.collector.time.time', return_value=1000):
                budget = RequestBudget(Path(td))
                self.assertTrue(budget.acquire_http('https://hn.example/list', max_per_hour=2))
                self.assertFalse(budget.acquire_http('https://hn.example/item/1', max_per_hour=2))
            with patch('core.collector.time.time', return_value=1002):
                self.assertTrue(RequestBudget(Path(td)).acquire_http('https://hn.example/item/1', max_per_hour=2))
            with patch('core.collector.time.time', return_value=1004):
                self.assertFalse(RequestBudget(Path(td)).acquire_http('https://hn.example/item/2', max_per_hour=2))
            with patch('core.collector.time.time', return_value=4601):
                self.assertTrue(RequestBudget(Path(td)).acquire_http('https://hn.example/item/2', max_per_hour=2))

    def test_each_hn_http_request_is_budgeted_before_network(self):
        from core.collector import _fetch_hn
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            budget = RequestBudget(Path(td))
            source = {'id': 'hn', 'endpoint': 'https://hacker-news.firebaseio.com/v0/topstories.json'}
            with patch('core.collector.time.time', return_value=1000), patch('core.collector.urllib.request.build_opener') as build:
                network = build.return_value.open
                network.return_value.__enter__.return_value.read.return_value = b'[1,2]'
                with self.assertRaises(SourcePaused) as captured:
                    _fetch_hn(source, budget=budget)
                self.assertEqual(str(captured.exception), 'REQUEST_BUDGET')
                self.assertEqual(network.call_count, 1)

    def test_http_budget_respects_existing_host_barrier(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            budget = RequestBudget(Path(td))
            budget.pause({'id': 'hn', 'endpoint': 'https://hn.example/list'}, 'CAPTCHA_REQUIRED')
            with self.assertRaises(SourcePaused):
                budget.acquire_http('https://hn.example/item/1')

    def test_new_cooldown_never_weakens_existing_host_challenge_pause(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            budget = RequestBudget(Path(td))
            budget.pause({'id': 'a', 'endpoint': 'https://vendor.example/a'}, 'CAPTCHA_REQUIRED')
            budget.pause({'id': 'b', 'endpoint': 'https://vendor.example/b'}, 'RATE_LIMITED_429', 1800)
            import sqlite3
            from contextlib import closing
            with closing(sqlite3.connect(budget.db_path)) as conn:
                row = conn.execute("SELECT until_epoch,pause_reason FROM budget WHERE key='host:vendor.example'").fetchone()
            self.assertEqual(row, (0, 'CAPTCHA_REQUIRED'))

    def test_platform_pause_applies_to_other_adapters_on_same_host(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            budget = RequestBudget(Path(td))
            budget.pause({'id': 'feed', 'endpoint': 'https://vendor.example/feed'}, 'CAPTCHA_REQUIRED')
            with self.assertRaises(SourcePaused):
                budget.acquire({'id': 'official-page', 'endpoint': 'https://vendor.example/offer'}, force=True)

    def test_html_response_at_rss_url_is_explicit_structure_failure(self):
        with self.assertRaises(ValueError):
            parse_feed(b'<html><body>New landing page</body></html>', 'rss')

    def test_feed_preserves_official_reference_without_tracking_query(self):
        from core.collector import build_candidate
        rows = parse_feed(b'''<rss><channel><item><title>Free credits</title><link>https://forum.example/post</link>
            <description><![CDATA[See <a href="https://cursor.com/changelog/promo?utm_source=forum">official page</a>]]></description>
            </item></channel></rss>''', 'forum')
        candidate = build_candidate(rows[0], {'id': 'forum', 'platform': 'Forum'}, 'n')
        self.assertIn('https://cursor.com/changelog/promo', candidate.metadata['official_references'])

    def test_captcha_library_on_normal_page_is_not_a_challenge(self):
        from core.verifier import VerificationEngine
        body = '<html><script src="https://www.google.com/recaptcha/api.js"></script><a href="/offer">Free trial</a></html>'
        self.assertEqual(VerificationEngine.classify_fetch_failure(200, body), 'HTTP_200')

    def test_changed_html_layout_is_not_silent_success(self):
        with patch('core.collector._request', return_value=b'<html><body>layout changed</body></html>'):
            with self.assertRaises(ValueError):
                _fetch_source({'id': 'vendor', 'kind': 'html', 'endpoint': 'https://vendor.example/'})

    def test_budget_recovers_across_instances_without_resetting_limits(self):
        temp_root = ROOT / '.test-tmp'
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as td:
            source = {'id': 'vendor', 'endpoint': 'https://vendor.example/feed', 'interval_minutes': 60}
            self.assertTrue(RequestBudget(Path(td)).acquire(source))
            self.assertFalse(RequestBudget(Path(td)).acquire(source))
            self.assertFalse(RequestBudget(Path(td)).acquire(source, force=True))
    def test_upstream_rss_barrier_is_explicit_pause(self):
        for code in ('BLOCKED_403', 'RATE_LIMITED_429', 'CAPTCHA_REQUIRED', 'REQUEST_BUDGET'):
            with patch('core.collector.subprocess.run', return_value=SimpleNamespace(returncode=2,
                stdout=json.dumps({'rows': [], 'error': {'error_code': code, 'retry_seconds': 1800}}))):
                with self.assertRaises(SourcePaused) as captured:
                    fetch_digest_rss(ROOT, {'endpoint': 'https://example.test/feed'})
                self.assertEqual(str(captured.exception), code)
    def test_pause_persists_and_force_does_not_bypass_it(self):
        temp_root = ROOT / '.test-tmp'
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as td:
            source = {'id': 'blocked', 'endpoint': 'https://blocked.example/feed'}
            budget = RequestBudget(Path(td))
            budget.pause(source, 'CAPTCHA_REQUIRED')
            with self.assertRaises(SourcePaused):
                RequestBudget(Path(td)).acquire(source, force=True)

    def test_success_http_challenge_is_not_parsed_as_empty_feed(self):
        with patch('core.collector.urllib.request.build_opener') as mocked:
            mocked.return_value.open.return_value.__enter__.return_value.read.return_value = b'<html>cf-chl-captcha</html>'
            with self.assertRaises(SourcePaused):
                _request('https://example.test/', 'text/html')
    def test_parses_rss_and_preserves_original_link(self):
        payload = b'''<?xml version="1.0"?><rss><channel><item>
          <title>Free API credits for developers</title>
          <link>https://vendor.example/promo</link>
          <pubDate>Sat, 11 Oct 2026 08:00:00 GMT</pubDate>
          <description>Developer perks</description>
        </item></channel></rss>'''
        items = parse_feed(payload, 'rss-test')
        self.assertEqual(items[0]['url'], 'https://vendor.example/promo')
        self.assertEqual(items[0]['title'], 'Free API credits for developers')

    def test_bilingual_keyword_filter(self):
        self.assertTrue(contains_keyword('限量免费服务器兑换码', ['free VPS', '免费服务器', '兑换码']))
        self.assertTrue(contains_keyword('New AI credits giveaway', ['AI credits']))
        self.assertFalse(contains_keyword('ordinary release notes', ['free VPS', '免费额度']))

    def test_brand_name_alone_is_not_a_wool_signal(self):
        keywords = ['Claude', 'Gemini', 'Grok', 'GitHub', 'giveaway', '免费额度']
        self.assertFalse(contains_keyword('Claude Haiku is now available in a new region', keywords))
        self.assertTrue(contains_keyword('Claude developer giveaway with free credits', keywords))

    def test_sources_include_every_required_platform(self):
        sources = load_sources(ROOT / 'config' / 'sources.yaml')
        platforms = {item['platform'] for item in sources}
        required = {
            'X / Twitter', 'Reddit', 'Linux.do', 'NodeSeek', 'V2EX',
            'LowEndTalk Giveaways', 'LowEndBox', 'Hostloc', 'Hacker News',
            'Product Hunt', 'DevHunt Perks', 'FreeStuff.dev', 'GitHub free-for-dev',
            'GitHub Education', 'MLH', 'Google Cloud', 'AWS', 'Cursor',
            'Cloudflare Developer Platform',
        }
        self.assertEqual(required - platforms, set())

    def test_sources_never_enable_challenge_bypass(self):
        sources = load_sources(ROOT / 'config' / 'sources.yaml')
        self.assertFalse(any(item.get('challenge_bypass') for item in sources))

    def test_html_source_path_and_host_constraints(self):
        source = {
            'endpoint': 'https://www.cursor.com/changelog',
            'allowed_hosts': ['cursor.com', 'www.cursor.com'],
            'include_path_regex': '^/changelog/',
        }
        self.assertTrue(row_allowed({'url': 'https://www.cursor.com/changelog/free-trial'}, source))
        self.assertFalse(row_allowed({'url': 'https://www.cursor.com/terms'}, source))
        self.assertFalse(row_allowed({'url': 'https://x.ai/grok'}, source))

    def test_corrected_sources_use_verified_public_pages(self):
        sources = {item['id']: item for item in load_sources(ROOT / 'config' / 'sources.yaml')}
        self.assertEqual(sources['devhunt']['endpoint'], 'https://devhunt.org/perks')
        self.assertEqual(sources['devhunt']['kind'], 'html')
        self.assertEqual(
            sources['lowendtalk-giveaways']['endpoint'],
            'https://lowendtalk.com/categories/giveaways-freebies/feed.rss',
        )
        self.assertEqual(
            sources['google-cloud']['endpoint'],
            'https://cloud.google.com/blog/topics/inside-google-cloud/whats-new-google-cloud',
        )

    def test_network_and_parser_failures_are_explicit(self):
        self.assertEqual(classify_exception(TimeoutError('timed out')), 'NETWORK_TIMEOUT')
        self.assertEqual(classify_exception(socket.timeout('timed out')), 'NETWORK_TIMEOUT')
        self.assertEqual(classify_exception(ValueError('bad payload')), 'PARSE_OR_SOURCE_CHANGED')


if __name__ == '__main__':
    unittest.main()
