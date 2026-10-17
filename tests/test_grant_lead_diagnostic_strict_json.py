"""JSONL source schema must reject ambiguous, nonfinite and pathological records."""
import json
import subprocess
import sys
import unittest


class StrictJsonlInput(unittest.TestCase):
    def run_record(self, line):
        return subprocess.run([sys.executable, '-m', 'core.grant_lead_diagnostics'],
                              input=line, text=True, capture_output=True, timeout=12)

    def assert_rejected(self, text, marker=None):
        result = self.run_record(text)
        self.assertEqual(result.returncode, 2, result.stderr[:300])
        self.assertEqual(result.stdout, '')
        self.assertIn('INVALID_INPUT', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        if marker:
            self.assertNotIn(marker, result.stderr)

    def test_nonfinite_numbers_are_not_json(self):
        for constant in ('NaN','Infinity','-Infinity'):
            with self.subTest(constant=constant):
                self.assert_rejected('{"text":"Unrelated news", "metadata":{"confidence":' + constant + '}}\n')

    def test_wrong_type_authoritative_text_is_not_silently_ignored(self):
        for bad in (False, 1, [], {}):
            with self.subTest(bad=bad):
                literal = bad if isinstance(bad,str) else json.dumps(bad)
                self.assert_rejected('{"text":' + literal + ', "title":"Developer grants for open source maintainers", "summary":"Applications open, award $500"}\n')

    def test_absent_or_null_optional_text_allows_title_summary(self):
        for value in ({'title':'Public article','summary':'Public'},
                      {'text':None,'title':'Public article','summary':'Public'}):
            with self.subTest(value=value):
                result = self.run_record(json.dumps(value) + '\n')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)['records'],1)

    def test_extreme_json_nesting_is_invalid_input_not_traceback(self):
        payload='{'+'"text":"Public news", "metadata":'+ '['*11000 + 'null' + ']'*11000+'}\n'
        self.assert_rejected(payload)

    def test_bad_later_record_never_emits_partial_results(self):
        self.assert_rejected('{"text":"Public developer grant applications open, award $800"}\n'
                             '{"text":"Public unrelated", "metadata":NaN}\n')

if __name__ == '__main__': unittest.main()
