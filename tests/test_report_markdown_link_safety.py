"""Synthetic report rendering regressions; no external accounts or network."""
import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate
from core.report import ReportGenerator, _safe_markdown_link


class ReportMarkdownLinkSafetyTests(unittest.TestCase):
    def test_harvested_title_cannot_forge_secondary_clickable_link(self):
        label = 'Benefit](https://phishing.example/claim) [Official'
        safe = _safe_markdown_link(label, 'https://official.example/offer')
        self.assertIn(r'Benefit\]', safe)
        self.assertIn(r'\[Official', safe)
        self.assertTrue(safe.endswith('](https://official.example/offer)'))
        self.assertEqual(safe.count('](https://official.example/offer)'), 1)

    def test_disallowed_schemes_and_account_spoofing_do_not_become_links(self):
        for url in (
            'javascript:alert(1)', 'data:text/html,hello',
            'https://owner@evil.example/path', 'https://bad.example/hello\nnext',
            'https://[unterminated', ''
        ):
            with self.subTest(url=url):
                safe = _safe_markdown_link('Official offer', url)
                self.assertEqual(safe, 'Official offer')

    def test_valid_parentheses_are_encoded_and_html_title_is_inert(self):
        safe = _safe_markdown_link('<img src=x> win',
                                   'https://official.example/offer(a)')
        self.assertIn('&lt;img src=x\\> win', safe)
        self.assertIn('(https://official.example/offer%28a%29)', safe)
        self.assertNotIn('<img', safe)

    def test_generated_markdown_preserves_json_and_renders_safe_link(self):
        with tempfile.TemporaryDirectory(prefix='wool-md-fixture-') as tmp:
            root = Path(tmp)
            db = Database(root / 'fixture.sqlite')
            title = 'Free](https://phishing.example/claim) [Official'
            db.upsert_candidate(Candidate('synthetic', 'fixture', title,
                                          'https://official.example/offer'))
            report = ReportGenerator(db, root / 'reports').generate('2026-10-19')
            text = report.markdown.read_text(encoding='utf-8')
            self.assertIn(r'Free\]', text)
            self.assertIn(r'\[Official', text)
            self.assertIn('](https://official.example/offer)', text)
            self.assertTrue(report.json.exists())


if __name__ == '__main__':
    unittest.main()
