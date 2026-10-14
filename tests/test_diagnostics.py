import json
import tempfile
import unittest
import subprocess
from pathlib import Path

from core.db import Database
from core.models import Candidate
from core.diagnostics import status_summary


class DiagnosticsTests(unittest.TestCase):
    def test_report_wrapper_rotates_log_and_propagates_failure(self):
        root = Path(__file__).parents[1]
        wrapper = root / 'scripts' / 'Run-Report.ps1'
        self.assertTrue(wrapper.exists(), 'report schedule needs a logged wrapper')
        with tempfile.TemporaryDirectory(dir=root / '.test-tmp') as td:
            folder = Path(td)
            (folder / 'logs').mkdir()
            (folder / 'logs' / 'report.log').write_text('x' * 20, encoding='ascii')
            (folder / 'fail.cmd').write_text('@echo report-failed\n@exit /b 7\n', encoding='ascii')
            common = (root / 'scripts' / 'Common.ps1').read_text(encoding='utf-8')
            common += "\nfunction Get-WoolRadarRoot { param($Root) return $Root }\nfunction Get-WoolRadarPython { return (Join-Path $PSScriptRoot 'fail.cmd') }\n"
            (folder / 'Common.ps1').write_text(common, encoding='utf-8-sig')
            (folder / 'Run-Report.ps1').write_text(wrapper.read_text(encoding='utf-8'), encoding='utf-8-sig')
            result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(folder / 'Run-Report.ps1'), '-Root', td, '-MaxLogBytes', '10'], capture_output=True)
            self.assertEqual(result.returncode, 7)
            self.assertEqual((folder / 'logs' / 'report.log.1').read_text(), 'x' * 20)
            self.assertIn('report-failed', (folder / 'logs' / 'report.log').read_text(encoding='utf-16'))

    def test_diagnostic_propagates_python_failure(self):
        root = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory(dir=root / '.test-tmp') as td:
            folder = Path(td)
            (folder / 'fail.cmd').write_text('@exit /b 7\n', encoding='ascii')
            (folder / 'Common.ps1').write_text("function Get-WoolRadarRoot { param($Root) return $Root }\nfunction Get-WoolRadarPython { return (Join-Path $PSScriptRoot 'fail.cmd') }\n", encoding='utf-8')
            (folder / 'Diagnose-WoolRadar.ps1').write_text((root / 'scripts' / 'Diagnose-WoolRadar.ps1').read_text(encoding='utf-8'), encoding='utf-8')
            result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(folder / 'Diagnose-WoolRadar.ps1'), '-Root', td], capture_output=True)
            self.assertEqual(result.returncode, 7, result.stdout.decode(errors='replace') + result.stderr.decode(errors='replace'))

    def test_summary_excludes_payload_and_raw_source_contents(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[1] / '.test-tmp') as td:
            db = Database(Path(td) / 'radar.db')
            db.upsert_candidate(Candidate('node', 'rss', 'private test content', 'https://example.test/raw'))
            db.record_node_run('node', 'PARTIAL', 2, 'CAPTCHA_REQUIRED', 'raw content should not be printed')
            result = status_summary(db)
            self.assertEqual(result['event_count'], 1)
            self.assertEqual(result['nodes'][0]['items'], 2)
            self.assertEqual(result['nodes'][0]['error_code'], 'CAPTCHA_REQUIRED')
            self.assertNotIn('raw content', json.dumps(result))
            self.assertNotIn('private test content', json.dumps(result))
            self.assertNotIn('example.test', json.dumps(result))

    def test_empty_summary_is_valid(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[1] / '.test-tmp') as td:
            result = status_summary(Database(Path(td) / 'radar.db'))
            self.assertEqual(result['event_count'], 0)
            self.assertEqual(result['nodes'], [])
