import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

from core.db import Database
from core.models import Candidate,Evidence
from core.report import ReportGenerator
from core.noise_audit import NoiseAudit


class NoiseAuditTests(unittest.TestCase):
    def test_repeated_real_ingest_only_refreshing_time_remains_excluded(self):
        from core.pipeline import Pipeline
        inbox=self.root/'data/inbox/openmagpie.jsonl'
        inbox.parent.mkdir(parents=True)
        candidate=Candidate('openmagpie','fixture','Diagnostic discussion','https://example.test/diag',summary='Question only')
        inbox.write_text(json.dumps(candidate.to_dict()),encoding='utf-8')
        pipeline=Pipeline(self.root)
        with patch('core.models.utc_now',return_value='2026-10-15T01:00:00Z'):
            pipeline.ingest_node('openmagpie')
        self.event_id=next(e['id'] for e in self.db.list_events() if e['primary_url']==candidate.url)
        self.exclude()
        # Evidence's default factory is bound to utc_now; replace just the clock-bearing constructor.
        real=Evidence
        with patch('core.pipeline.Evidence',side_effect=lambda *a,**k:real(*a,checked_at='2026-10-16T01:00:00Z',**k)):
            pipeline.ingest_node('openmagpie')
        self.assertTrue(self.audit.decision(self.snapshot())['excluded'])

    def test_one_report_uses_one_validated_ledger_snapshot(self):
        self.exclude()
        other_id=self.db.upsert_candidate(Candidate('n','fixture','Second noise','https://example.test/second',
            discovered_at='2026-10-15T00:00:00Z')).event_id
        other=self.db.get_event(other_id)
        other['evidence']=[]
        self.audit.record(other,'exclude','Second diagnostic','fixture-reviewer')
        old=self.audit._load()
        self.audit.record(self.snapshot(),'restore','Correction','fixture-reviewer')
        self.audit.record(other,'restore','Correction','fixture-reviewer')
        new=self.audit._load()
        calls=[]
        def changing():
            calls.append(1)
            return old if len(calls)<=2 else new
        with patch.object(self.audit,'_load',side_effect=changing):
            paths=ReportGenerator(self.db,self.root/'reports',noise_audit=self.audit).generate('2026-10-15')
        payload=json.loads(paths.json.read_text(encoding='utf-8'))
        self.assertEqual(payload['noise_audit']['excluded'],2)
        self.assertEqual(len(calls),1)

    def test_process_exit_releases_writer_lock_and_live_writer_blocks(self):
        cwd=Path(__file__).resolve().parents[1]
        code='from pathlib import Path; import os,sys; from core.noise_audit import NoiseAudit; a=NoiseAudit(Path(sys.argv[1]));\nwith a._writer_lock(): os._exit(17)'
        run=subprocess.run([sys.executable,'-c',code,str(self.audit.path)],cwd=cwd,capture_output=True,text=True)
        self.assertEqual(run.returncode,17,run.stderr)
        self.assertTrue(self.exclude())
        with self.audit._writer_lock():
            with self.assertRaisesRegex(ValueError,'NOISE_AUDIT_BUSY'):
                self.audit.record(self.snapshot(),'restore','Correction','fixture-reviewer')
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.db=Database(self.root/'data/woolradar.db')
        self.event_id=self.db.upsert_candidate(Candidate('n','fixture','Old diagnostic noise',
            'https://example.test/old',discovered_at='2026-10-15T01:00:00Z')).event_id
        self.db.add_evidence(self.event_id,Evidence('community','https://example.test/old','fixture',
            checked_at='2026-10-15T01:00:00Z',excerpt='Old diagnostic request'))
        self.audit=NoiseAudit(self.root/'data/noise-audit.json')

    def snapshot(self):
        event=self.db.get_event(self.event_id)
        event['evidence']=[asdict(e) for e in self.db.get_evidence(self.event_id)]
        return event

    def exclude(self):
        return self.audit.record(self.snapshot(),'exclude','Reviewed diagnostic, no offer','fixture-reviewer')

    def test_exclusion_preserves_events_and_evidence_and_has_report_trace(self):
        before=self.snapshot()
        self.exclude()
        paths=ReportGenerator(self.db,self.root/'reports',noise_audit=self.audit).generate('2026-10-15')
        payload=json.loads(paths.json.read_text(encoding='utf-8'))
        self.assertEqual(self.snapshot(),before)
        self.assertEqual(len(payload['events']),1)
        self.assertTrue(payload['events'][0]['report_audit']['excluded'])
        self.assertEqual(payload['noise_audit']['excluded'],1)
        text=paths.markdown.read_text(encoding='utf-8')
        main,trace=text.split('## 历史噪声审计',1)
        self.assertNotIn('Old diagnostic noise',main)
        self.assertIn('Old diagnostic noise',trace)
        self.assertIn('fixture-reviewer',trace)

    def test_fresh_evidence_invalidates_old_exclusion(self):
        self.exclude()
        self.db.add_evidence(self.event_id,Evidence('official','https://example.test/new','official',
            checked_at='2026-10-15T02:00:00Z',claims={'open':True,'public':True}))
        paths=ReportGenerator(self.db,self.root/'reports',noise_audit=self.audit).generate('2026-10-15')
        event=json.loads(paths.json.read_text(encoding='utf-8'))['events'][0]
        self.assertFalse(event['report_audit']['excluded'])
        self.assertEqual(event['report_audit']['state'],'stale')
        self.assertIn('Old diagnostic noise',paths.markdown.read_text(encoding='utf-8').split('## 历史噪声审计')[0])

    def test_unchanged_repost_does_not_reopen_but_new_batch_does(self):
        self.exclude()
        self.db.upsert_candidate(Candidate('n','fixture','Old diagnostic noise','https://example.test/old',
            discovered_at='2026-10-15T03:00:00Z'))
        self.assertTrue(self.audit.decision(self.snapshot())['excluded'])
        new_id=self.db.upsert_candidate(Candidate('n','fixture','Old diagnostic noise','https://example.test/old',
            batch_id='reopened-2027',discovered_at='2026-10-15T04:00:00Z')).event_id
        new=self.db.get_event(new_id)
        new['evidence']=[]
        self.assertFalse(self.audit.decision(new)['excluded'])

    def test_restore_appends_history_and_identical_decision_is_idempotent(self):
        self.assertTrue(self.exclude())
        self.assertFalse(self.exclude())
        self.assertTrue(self.audit.record(self.snapshot(),'restore','Manual correction','fixture-reviewer'))
        self.assertFalse(self.audit.decision(self.snapshot())['excluded'])
        ledger=json.loads(self.audit.path.read_text(encoding='utf-8'))
        self.assertEqual([x['decision'] for x in ledger['records']],['exclude','restore'])

    def test_corrupt_ledger_stops_filtered_report(self):
        self.audit.path.write_text('{',encoding='utf-8')
        with self.assertRaises(ValueError):
            ReportGenerator(self.db,self.root/'reports',noise_audit=self.audit).generate('2026-10-15')
        self.assertFalse((self.root/'reports/2026-10-15-daily.json').exists())

    def test_real_cli_explicit_opt_in_and_default_report_unchanged(self):
        cwd=Path(__file__).resolve().parents[1]
        args=[sys.executable,'-m','core.cli','--root',str(self.root)]
        marked=subprocess.run(args+['audit-noise',str(self.event_id),'--decision','exclude',
            '--reason','Diagnostic only','--reviewer','fixture-reviewer'],cwd=cwd,capture_output=True,text=True)
        self.assertEqual(marked.returncode,0,marked.stderr)
        filtered=subprocess.run(args+['report','--date','2026-10-15','--noise-audit',str(self.audit.path)],
            cwd=cwd,capture_output=True,text=True)
        self.assertEqual(filtered.returncode,0,filtered.stderr)
        payload=json.loads((self.root/'reports/2026-10-15-daily.json').read_text(encoding='utf-8'))
        self.assertTrue(payload['events'][0]['report_audit']['excluded'])
        unfiltered=subprocess.run(args+['report','--date','2026-10-15'],cwd=cwd,capture_output=True,text=True)
        self.assertEqual(unfiltered.returncode,0,unfiltered.stderr)
        payload=json.loads((self.root/'reports/2026-10-15-daily.json').read_text(encoding='utf-8'))
        self.assertNotIn('noise_audit',payload)

    def test_mutating_audit_command_requires_explicit_root(self):
        run=subprocess.run([sys.executable,'-m','core.cli','audit-noise','1','--decision','exclude',
            '--reason','Test','--reviewer','fixture-reviewer'],cwd=Path(__file__).resolve().parents[1],
            capture_output=True,text=True)
        self.assertEqual(run.returncode,2)
        self.assertIn('explicit --root',run.stderr)


if __name__=='__main__': unittest.main()
