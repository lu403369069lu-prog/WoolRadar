"""Run a byte-identical wrapper with R29 in a disposable local folder.

This invokes a real PowerShell process with synthetic stdin, not Codex host Stop.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
WRAPPER = Path.home() / '.codex/hooks/stop_verify.ps1'
INSTALLED = Path.home() / '.codex/hooks/stop_verify.py'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    before = {str(p.name): digest(p) for p in (WRAPPER, INSTALLED)}
    spec = importlib.util.spec_from_file_location('scenario_definitions', HERE/'audit_stage_pause.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cases = []
    with tempfile.TemporaryDirectory(prefix='wrapper-r29-', dir=HERE) as tmp:
        root = Path(tmp)
        shutil.copyfile(WRAPPER, root/'stop_verify.ps1')
        shutil.copyfile(HERE/'stop_verify_r30_candidate.py', root/'stop_verify.py')
        assert digest(root/'stop_verify.ps1') == before['stop_verify.ps1']
        for name, disposition, messages, expected in module.CASES:
            cwd = root/name
            (cwd/'_outbox').mkdir(parents=True)
            transcript = cwd/'rollout.jsonl'
            transcript.write_text(''.join(json.dumps({'type':'event_msg','payload':{
                'type':'user_message','message':m}}, ensure_ascii=False)+'\n' for m in messages),encoding='utf-8')
            entry = {'schema_version':1,'disposition':disposition,'project':str(cwd),
                     'pending_requirements':['VERIFY-1'],'actionable_tasks':['Continue isolated test']}
            if disposition == 'paused':
                entry['user_pause_evidence'] = {'text':'先暂停','date':'2026-10-22'}
            (cwd/'_outbox/stop-continuity-handoff.json').write_text(json.dumps({
                'sessions':{'synthetic-sid':entry}},ensure_ascii=False),encoding='utf-8')
            event = {'session_id':'synthetic-sid','cwd':str(cwd),'hook_event_name':'Stop',
                     'transcript_path':str(transcript)}
            proc = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive',
                                   '-ExecutionPolicy','Bypass','-File',str(root/'stop_verify.ps1')],
                                  cwd=cwd, input=json.dumps(event,ensure_ascii=False).encode('utf-8'),
                                  capture_output=True,timeout=30)
            answer = json.loads(proc.stdout.decode('utf-8-sig'))
            observed = 'block' if answer.get('decision') == 'block' else 'allow'
            cases.append({'case':name,'expected':expected,'observed':observed,
                          'exit_code':proc.returncode,'stderr_empty':not proc.stderr.strip(),
                          'correct':observed == expected and proc.returncode == 0 and not proc.stderr.strip()})
    after = {str(p.name): digest(p) for p in (WRAPPER, INSTALLED)}
    report = {'kind':'isolated-powershell-r30-wrapper-synthetic-stdin','count':len(cases),
              'correct':sum(c['correct'] for c in cases),'cases':cases,
              'installed_before':before,'installed_after':after,'installed_unchanged':before == after,
              'real_codex_host_stop_callback':False,'global_candidate_installed':False}
    (HERE/'r30-wrapper-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['correct'] == len(cases) and before == after else 1

if __name__ == '__main__':
    raise SystemExit(main())
