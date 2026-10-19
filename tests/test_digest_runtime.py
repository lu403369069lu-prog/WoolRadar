import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
VENV = ROOT / 'nodes' / 'digest-ai-agent' / 'upstream' / '.venv'
PYTHON = Path(os.environ['WOOLRADAR_DIGEST_TEST_PYTHON']) if os.environ.get(
    'WOOLRADAR_DIGEST_TEST_PYTHON') else VENV / (
        'Scripts/python.exe' if os.name == 'nt' else 'bin/python')


class DigestRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(PYTHON.is_file(),
        'Pinned upstream runtime required: run scripts/prepare_digest_upstream.py')
    def test_upstream_provider_http_is_budgeted_across_process_invocations(self):
        script = ROOT / 'nodes/digest-ai-agent/rss_collect.py'
        code = '''import sys,runpy,httpx
from unittest.mock import patch
url,root,script=sys.argv[1:]
calls=[]
def handler(request):
 calls.append(str(request.url))
 return httpx.Response(200,text='<rss><channel><item><title>Free credits</title><link>https://vendor.example/offer</link></item></channel></rss>')
original=httpx.Client
class LocalClient(original):
 def __init__(self,*args,**kwargs):
  kwargs['transport']=httpx.MockTransport(handler)
  super().__init__(*args,**kwargs)
sys.argv=[script,url,root]
with patch('httpx.Client',LocalClient):
 module=runpy.run_path(script)
 module['main']()
 module['main']()
print('transport_count='+str(len(calls)))
'''
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as td:
            result = subprocess.run([str(PYTHON), '-X', 'utf8', '-c', code, 'https://rss.example/feed', td, str(script)], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = result.stdout.splitlines()
            self.assertEqual(json.loads(lines[0])['error'], {})
            self.assertEqual(json.loads(lines[1])['error']['error_code'], 'REQUEST_BUDGET')
            self.assertEqual(lines[2], 'transport_count=1')

    def test_missing_upstream_executable_reports_pause(self):
        from unittest.mock import patch
        from core.collector import SourcePaused, fetch_digest_rss

        with patch('core.collector.subprocess.run', side_effect=FileNotFoundError):
            with self.assertRaisesRegex(SourcePaused, 'UPSTREAM_RUNTIME_NOT_INSTALLED'):
                fetch_digest_rss(ROOT, {'endpoint': 'https://rss.example/feed'})

    def test_upstream_executable_path_is_platform_relative(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from core.collector import fetch_digest_rss

        expected = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        with patch('core.collector.subprocess.run',
                   return_value=SimpleNamespace(returncode=0, stdout='{"rows":[]}')) as run:
            self.assertEqual(fetch_digest_rss(ROOT, {'endpoint': 'https://rss.example/feed'}), [])
        self.assertEqual(run.call_args.args[0][0], str(expected))
