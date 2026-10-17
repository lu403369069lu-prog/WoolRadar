"""Synthetic child execution: default allowlist excludes runtime credentials/preloads."""
from __future__ import annotations
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('runner_env',Path(__file__).with_name('HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py'))
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class EnvironmentIsolation(unittest.TestCase):
    def command(self, script: str):
        key='e'*64
        cmd={'argv':[sys.executable,'-c',script],'cwd':Path(tempfile.gettempdir()),
             'key_sha256':key,'command':'synthetic'}
        rows=[{'family_id':'F-SAFE','source_blob':'synthetic','command_key':key}]
        return cmd,rows

    def test_token_and_preload_env_not_inherited(self):
        script='import os; print("CHECK="+str(any(k in os.environ for k in ("OPENAI_API_KEY","GH_TOKEN","NODE_OPTIONS","PYTHONPATH")))); print("Ran 1 test in 0.001s\\nOK")'
        c,m=self.command(script)
        with patch.dict(os.environ,{'OPENAI_API_KEY':'synthetic','GH_TOKEN':'synthetic',
                                    'NODE_OPTIONS':'--import /tmp/fake.mjs','PYTHONPATH':'/tmp/sneaky'}):
            rc,r,folder=runner.run_commands([c],m,'fixed','wool')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        self.assertEqual(rc,0)
        log=(folder/('e'*64+'.log')).read_text('utf8')
        self.assertIn('CHECK=False',log)
        self.assertNotIn('synthetic',log)
        self.assertFalse(any(p.name.startswith('child-') for p in folder.iterdir()))

    def test_home_is_disposable_and_not_host_home(self):
        script='import os; from pathlib import Path; print("HOME_VALID="+str(os.environ["HOME"]==os.environ["TMP"] and Path(os.environ["HOME"]).is_dir())); print("Ran 1 test in 0.001s\\nOK")'
        c,m=self.command(script)
        rc,r,folder=runner.run_commands([c],m,'fixed','wool')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        self.assertEqual(rc,0)
        self.assertIn('HOME_VALID=True',(folder/('e'*64+'.log')).read_text('utf8'))

    def test_original_os_path_preserved_for_command(self):
        home=Path(tempfile.gettempdir())
        env=runner._isolated_test_env(home)
        if 'PATH' in os.environ: self.assertEqual(env.get('PATH'),os.environ['PATH'])
        self.assertEqual(env['PYTHONDONTWRITEBYTECODE'],'1')
        self.assertNotIn('GIT_ASKPASS',env)
        self.assertNotIn('SSH_AUTH_SOCK',env)
        self.assertNotIn('NODE_OPTIONS',env)

if __name__=='__main__':unittest.main()
