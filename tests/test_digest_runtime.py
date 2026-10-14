import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PYTHON = Path('C:/WoolRadar/nodes/digest-ai-agent/upstream/.venv/Scripts/python.exe')


class DigestRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(PYTHON.exists(), 'installed upstream runtime required')
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
