import json
import io
import urllib.error
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs

from core.collector import fetch_reddit_oauth, SourcePaused

ROOT = Path(__file__).parents[1]


class RedditApplicationReadTests(unittest.TestCase):
    def test_default_call_rejects_authenticated_redirect_without_an_explicit_budget(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.test-tmp') as folder:
            root=Path(folder)
            self.credentials(root,auth_mode='application_only')
            redirect=urllib.error.HTTPError('https://www.reddit.com/api/v1/access_token',301,'redirect',
                {'Location':'https://other.example/steal'},io.BytesIO())
            with patch('core.collector.urllib.request.build_opener') as build, patch(
                    'core.collector.urllib.request.urlopen',side_effect=AssertionError('UNGUARDED_AUTH_REQUEST')):
                build.return_value.open.side_effect=redirect
                with self.assertRaisesRegex(SourcePaused,'AUTHENTICATED_REDIRECT_REJECTED'):
                    fetch_reddit_oauth(root,{'id':'reddit-oauth'})
                self.assertEqual(build.return_value.open.call_count,1)

    def credentials(self, root, **extra):
        path = root/'nodes/clawradar/credentials.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'client_id':'fake-client','client_secret':'fake-secret',**extra}))

    def test_application_only_uses_client_grant_and_only_gets_public_hot_posts(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.test-tmp') as folder:
            root=Path(folder)
            self.credentials(root,auth_mode='application_only')
            calls=[]
            def read(request,budget):
                calls.append(request)
                if len(calls)==1:
                    return b'{"access_token":"fake-app-token","scope":"*"}'
                return json.dumps({'data':{'children':[{'data':{'title':'Public giveaway','selftext':'Public details','permalink':'/r/freebies/comments/abc/offer/','created_utc':0}}]}}).encode()
            budget=object()
            with patch('core.collector.budgeted_read',side_effect=read) as guarded:
                rows=fetch_reddit_oauth(root,{'id':'reddit-oauth'},budget)
            self.assertEqual(parse_qs(calls[0].data.decode()),{'grant_type':['client_credentials']})
            self.assertEqual(calls[1].get_method(),'GET')
            self.assertTrue(calls[1].full_url.startswith('https://oauth.reddit.com/r/freebies+vps+webhosting/hot?'))
            self.assertEqual(rows[0]['url'],'https://www.reddit.com/r/freebies/comments/abc/offer/')
            self.assertTrue(all(call.args[1] is budget for call in guarded.call_args_list))

    def test_application_only_requires_app_secret_before_network(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.test-tmp') as folder:
            root=Path(folder)
            self.credentials(root,auth_mode='application_only',client_secret='')
            with patch('core.collector.budgeted_read') as read:
                with self.assertRaises(SourcePaused): fetch_reddit_oauth(root,{'id':'reddit-oauth'})
                read.assert_not_called()

    def test_user_refresh_token_does_not_accept_app_wildcard_scope(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.test-tmp') as folder:
            root=Path(folder)
            self.credentials(root,refresh_token='fake-refresh')
            with patch('core.collector.budgeted_read',return_value=b'{"access_token":"fake-user-token","scope":"*"}') as read:
                with self.assertRaisesRegex(SourcePaused,'OAUTH_READ_SCOPE_REQUIRED'):
                    fetch_reddit_oauth(root,{'id':'reddit-oauth'})
                self.assertEqual(read.call_count,1)

    def test_unknown_auth_mode_never_falls_back_to_another_flow(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.test-tmp') as folder:
            root=Path(folder)
            self.credentials(root,auth_mode='google_cookie',refresh_token='fake-refresh')
            with patch('core.collector.budgeted_read') as read:
                with self.assertRaisesRegex(SourcePaused,'OAUTH_AUTH_MODE_UNSUPPORTED'):
                    fetch_reddit_oauth(root,{'id':'reddit-oauth'})
                read.assert_not_called()
