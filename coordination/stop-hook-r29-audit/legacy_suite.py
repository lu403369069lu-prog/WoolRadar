import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = Path(sys.argv.pop(1)) if len(sys.argv)>1 and not sys.argv[1].startswith('-') else Path.home()/'.codex/hooks/stop_verify.py'
spec = importlib.util.spec_from_file_location('stop_gate', TARGET)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class StopGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.entry = {'schema_version':1, 'disposition':'active', 'pending_requirements':['full-audit'], 'actionable_tasks':['F01-independent-review']}
        self.event = {'hook_event_name':'Stop', 'session_id':'audit-session', 'cwd':str(self.root), 'last_assistant_message':'任务归属登记已完成，整体审计仍未闭环'}
        self.save()
    def tearDown(self): self.tmp.cleanup()
    def save(self):
        path = self.root/gate.HANDOFF
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps({'sessions':{'audit-session':self.entry}}), encoding='utf-8')
    def block(self): self.assertEqual(gate.decide(self.event).get('decision'), 'block')
    def test_coordination_receipt_does_not_finish_original(self): self.block()
    def test_already_continued_flag_does_not_bypass_pending(self):
        self.event['stop_hook_active']=True; self.block()
    def test_other_session_not_blocked(self):
        self.event['session_id']='other'; self.assertEqual(gate.decide(self.event),{})
    def test_running_executor_keeps_review_pending(self):
        self.entry['actionable_tasks']=['poll-returned-artifacts']; self.save(); self.block()
    def test_false_complete_with_pending_rejected(self):
        self.entry['disposition']='complete'; self.entry['verification_record']='report.md'; self.save(); self.block()
    def test_complete_and_record_allows(self):
        (self.root/'tested-report.md').write_text('verified', encoding='utf-8'); self.entry.update(disposition='complete', pending_requirements=[],actionable_tasks=[],verification_record='tested-report.md'); self.save(); self.assertEqual(gate.decide(self.event),{})
    def test_user_question_is_not_whole_task_completion(self):
        self.entry.update(disposition='waiting_for_user',required_question='missing identity'); self.save(); self.block()
    def test_actual_blocker_and_no_actions_allows_honest_report(self):
        (self.root/'blocked.json').write_text('{"error":"permission denied"}', encoding='utf-8'); self.entry.update(disposition='externally_blocked',actionable_tasks=[],blocker_evidence='blocked.json'); self.save(); self.assertEqual(gate.decide(self.event),{})
    def test_pause_with_explicit_evidence(self):
        self.entry.update(disposition='paused',user_pause_evidence='human request'); self.save(); self.assertEqual(gate.decide(self.event),{})
    def transcript(self, texts):
        p=self.root/'rollout.jsonl'
        p.write_text('\n'.join(json.dumps({'type':'response_item','payload':{'type':'message','role':'user','content':[{'type':'input_text','text':t}]}},ensure_ascii=False) for t in texts),encoding='utf-8')
        self.event['transcript_path']=str(p)
    def test_live_explicit_pause_overrides_stale_active_contract(self):
        self.transcript(['继续','可以先停了，额度用完了']); self.assertEqual(gate.decide(self.event),{})
    def test_resume_revokes_historical_pause(self):
        self.transcript(['可以先停了','恢复，你可以干']); self.block()
    def test_delegation_cannot_authorize_pause(self):
        self.transcript(['继续','<codex_delegation>暂停</codex_delegation>']); self.block()
    def test_default_without_contract_allows(self):
        (self.root/gate.HANDOFF).unlink(); self.assertEqual(gate.decide(self.event),{})
    def test_unbound_explicit_same_task_resume_is_blocked(self):
        self.entry['continuity_terms']=['woolrad', 'P06']; self.save()
        self.event['session_id']='resumed-session'
        self.transcript(['/init woolrada任务，去读交接文档','继续干，没干完'])
        self.block()
    def test_unbound_other_task_continue_does_not_claim_session(self):
        self.entry['continuity_terms']=['woolrad','P06']; self.save()
        self.event['session_id']='unrelated-session'
        self.transcript(['继续别的项目，写一个无关程序'])
        self.assertEqual(gate.decide(self.event),{})
    def test_unbound_explicit_pause_overrides_binding_warning(self):
        self.entry['continuity_terms']=['woolrad']; self.save()
        self.event['session_id']='resumed-session'
        self.transcript(['/init woolrada任务，去读交接文档','可以暂停'])
        self.assertEqual(gate.decide(self.event),{})
    def test_unbound_resume_survives_large_tool_only_transcript_tail(self):
        self.entry['continuity_terms']=['woolrad']; self.save()
        self.event['session_id']='resumed-session'
        self.transcript(['/init woolrada任务，去读交接文档','继续干，没干完'])
        with Path(self.event['transcript_path']).open('a', encoding='utf-8') as f:
            f.write('\n'+json.dumps({'type':'tool_result','payload':{'text':'X'*1500000}})+'\n')
        self.block()
    def test_unbound_generic_continue_with_same_project_contract_blocks(self):
        self.entry['project']=str(self.root)
        self.entry['continuity_terms']=['woolrad','P06']; self.save()
        self.event['session_id']='resumed-session'
        self.transcript(['继续'])
        self.block()
    def test_unbound_no_transcript_blocks_when_project_field_missing_but_next_action_is_scoped(self):
        self.entry.pop('project', None)
        self.entry['continuity_terms']=['woolrad','P06']
        next_file=self.root/'_outbox'/'stop-next-audit-session.json'
        next_file.parent.mkdir(exist_ok=True)
        next_file.write_text(json.dumps({'session_id':'audit-session','goal':'WoolRadar P06','next_actions':['Continue P06'],'stop_condition':'All gates verified'}),encoding='utf-8')
        self.entry['next_action_file']=str(next_file)
        self.save()
        self.event['session_id']='fresh-session'
        self.event.pop('transcript_path', None)
        self.block()

    def test_unbound_no_transcript_same_project_contract_blocks(self):
        self.entry['project']=str(self.root)
        self.entry['continuity_terms']=['woolrad']; self.save()
        self.event['session_id']='resumed-session'
        self.block()
    def test_unbound_no_transcript_other_project_contract_allows(self):
        self.entry['project']=str(self.root/'other-project')
        self.entry['continuity_terms']=['woolrad']; self.save()
        self.event['session_id']='resumed-session'
        self.assertEqual(gate.decide(self.event),{})
    def test_unbound_generic_continue_with_explicit_other_project_allows(self):
        self.entry['project']=str(self.root)
        self.entry['continuity_terms']=['woolrad']; self.save()
        self.event['session_id']='resumed-session'
        self.transcript(['继续别的项目，写一个无关程序'])
        self.assertEqual(gate.decide(self.event),{})
    def test_unbound_generic_continue_then_pause_allows(self):
        self.entry['project']=str(self.root)
        self.entry['continuity_terms']=['woolrad']; self.save()
        self.event['session_id']='resumed-session'
        self.transcript(['继续','可以先停了'])
        self.assertEqual(gate.decide(self.event),{})
    def test_unbound_generic_continue_with_mismatched_cwd_allows(self):
        self.entry['project']=str(self.root/'another-project')
        self.entry['continuity_terms']=['woolrad']; self.save()
        self.event['session_id']='resumed-session'
        self.transcript(['继续'])
        self.assertEqual(gate.decide(self.event),{})
    def test_unbound_named_term_but_other_project_allows(self):
        self.entry['project']=str(self.root/'another-project')
        self.entry['continuity_terms']=['woolrad']; self.save()
        self.event['session_id']='resumed-session'
        self.transcript(['/init woolrada任务','继续'])
        self.assertEqual(gate.decide(self.event),{})
    def test_pause_question_followed_by_continue_does_not_override_active_contract(self):
        self.transcript(['继续','停了？继续干'])
        self.block()

    def test_latest_pause_survives_large_tool_only_transcript_tail(self):
        self.entry['continuity_terms']=['woolrad']; self.save()
        self.event['session_id']='resumed-session'
        self.transcript(['/init woolrada任务','继续','可以暂停'])
        with Path(self.event['transcript_path']).open('a', encoding='utf-8') as f:
            f.write('\n'+json.dumps({'type':'tool_result','payload':{'text':'Y'*1500000}})+'\n')
        self.assertEqual(gate.decide(self.event),{})
    def test_cli_outputs_parseable_json_and_actual_block(self):
        r=subprocess.run([sys.executable,'-X','utf8','-B',str(TARGET)],input=json.dumps(self.event),text=True,encoding='utf-8',capture_output=True)
        self.assertEqual(r.returncode,0); self.assertEqual(json.loads(r.stdout)['decision'],'block')

if __name__=='__main__': unittest.main()
