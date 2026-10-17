"""Fail-closed diagnostic JSONL CLI: bounded input and no partial disclosure."""
import json
import subprocess
import sys
import unittest


class StreamingCliSafety(unittest.TestCase):
    def invoke(self, text):
        return subprocess.run([sys.executable,'-m','core.grant_lead_diagnostics'],
                              input=text,text=True,capture_output=True,timeout=12)

    def test_large_line_cannot_be_accepted_as_normal_diagnostic_row(self):
        marker='SYNTHETIC_PRIVATE_ROW_' + 'q'*40000
        out=self.invoke(json.dumps({'text':marker})+'\n')
        self.assertNotEqual(out.returncode,0)
        self.assertEqual(out.stdout,'')
        self.assertNotIn('SYNTHETIC_PRIVATE_ROW',out.stderr)
        self.assertIn('INVALID_INPUT',out.stderr)

    def test_non_string_title_must_not_enter_classification(self):
        private={'secret':'SYNTHETIC-PRIVATE-CLASSIFIER-STRING'}
        out=self.invoke(json.dumps({'title':private,'summary':'Open-source developer grant applications are open and offer $500.'})+'\n')
        self.assertNotEqual(out.returncode,0)
        self.assertEqual(out.stdout,'')
        self.assertNotIn(private['secret'],out.stderr)

    def test_invalid_later_line_never_prints_partial_aggregate(self):
        good=json.dumps({'text':'Developer grants: open applications, award $1000 for open-source maintainers.'})
        out=self.invoke(good+'\n'+json.dumps({'title':[],'summary':'valid'})+'\n')
        self.assertNotEqual(out.returncode,0)
        self.assertEqual(out.stdout,'')

    def test_many_rows_aggregate_only_and_preserve_counts(self):
        data=''.join(json.dumps({'text':'Unrelated public article','url':'https://example.org/n'})+'\n' for _ in range(125))
        out=self.invoke(data)
        self.assertEqual(out.returncode,0,out.stderr)
        result=json.loads(out.stdout)
        self.assertEqual(result['records'],125)
        self.assertEqual(result['candidate_leads'],0)
        self.assertNotIn('Unrelated',out.stdout)

    def test_null_optional_summary_still_means_absent_not_invalid(self):
        row={'title':'Developer grants for open-source maintainers', 'summary':None}
        out=self.invoke(json.dumps(row)+'\n')
        self.assertEqual(out.returncode,0,out.stderr)
        self.assertEqual(json.loads(out.stdout)['records'],1)

    def test_valid_title_summary_fallback_still_supported(self):
        s=json.dumps({'title':'Developer grants for open-source maintainers',
                      'summary':'Applications open. Award: $500.'})+'\n'
        out=self.invoke(s)
        self.assertEqual(out.returncode,0,out.stderr)
        self.assertEqual(json.loads(out.stdout)['records'],1)

if __name__=='__main__':unittest.main()
