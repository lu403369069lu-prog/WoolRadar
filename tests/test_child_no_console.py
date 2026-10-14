import json
import os
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

@unittest.skipUnless(os.name=='nt','Windows process creation contract')
class ChildNoConsoleTests(unittest.TestCase):
    def assert_hidden(self,run):
        self.assertEqual(run.call_args.kwargs.get('creationflags',0),subprocess.CREATE_NO_WINDOW)

    def test_digest_provider_child_is_created_without_console(self):
        from core.collector import fetch_digest_rss
        with patch('core.collector.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps({'rows':[]}))) as run:
            fetch_digest_rss(Path(r'C:\WoolRadar'),{'endpoint':'https://public.example/feed'})
            self.assert_hidden(run)

    def test_browser_provider_child_is_created_without_console(self):
        from core.collector import fetch_x_browser
        with patch('core.collector.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='[]')) as run:
            fetch_x_browser(Path(r'C:\WoolRadar'))
            self.assert_hidden(run)

    def test_browser_owner_diagnostic_child_is_created_without_console(self):
        from core.browser_guard import assert_dedicated_listener
        profile=r'C:\WoolRadar\data\dedicated-profile'
        response={'name':'chrome.exe','command':'chrome.exe --user-data-dir="'+profile+'"'}
        with patch('core.browser_guard.subprocess.run',return_value=SimpleNamespace(stdout=json.dumps(response))) as run:
            assert_dedicated_listener(profile)
            self.assert_hidden(run)

    def test_orchestrator_child_is_created_without_console(self):
        from core.orchestrator import run_all
        with patch('core.orchestrator.Pipeline'), patch('core.orchestrator.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='',stderr='')) as run:
            run_all(Path(r'C:\WoolRadar'))
            self.assert_hidden(run)
