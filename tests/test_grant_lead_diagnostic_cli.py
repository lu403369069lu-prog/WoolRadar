"""Real subprocess checks for no-network stdin-only grant diagnostic CLI."""
import json
import subprocess
import sys
import unittest

class SafeGrantDiagnosticCli(unittest.TestCase):
    def run_cli(self, payload, *args):
        return subprocess.run(
            [sys.executable,'-m','core.grant_lead_diagnostics',*args],
            input=payload,text=True,capture_output=True,timeout=10)

    def test_aggregate_only_no_source_data_in_stdout(self):
        positive='Open-source developer grants for maintainers. Applications are now open. Grant amount: $500.'
        private='synthetic-access-token-NEVER-DISCLOSE'
        data='\n'.join(json.dumps(x) for x in [
            {'text':positive,'url':'https://example.org/secret/'+private},
            {'title':'Discussion','summary':'No program open','secret':private}
        ])+'\n'
        output=self.run_cli(data)
        self.assertEqual(output.returncode,0,output.stderr)
        result=json.loads(output.stdout)
        self.assertEqual(result['records'],2)
        self.assertEqual(result['candidate_leads'],1)
        self.assertNotIn(private,output.stdout)
        self.assertNotIn('Open-source',output.stdout)
        self.assertEqual(output.stderr,'')

    def test_broken_json_denied_without_echoing_contents(self):
        marker='malformed-secret-value'
        output=self.run_cli('{"token":"'+marker+'"\n')
        self.assertNotEqual(output.returncode,0)
        self.assertNotIn(marker,output.stdout+output.stderr)

    def test_non_json_object_fails_closed(self):
        output=self.run_cli('["synthetic data"]\n')
        self.assertNotEqual(output.returncode,0)

    def test_unknown_command_option_refused(self):
        output=self.run_cli('', '--export-raw')
        self.assertNotEqual(output.returncode,0)
        self.assertNotIn('export',output.stdout.lower())

if __name__=='__main__':unittest.main()
