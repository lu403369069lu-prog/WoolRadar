"""Run five bounded isolated acceptance rounds; never claims simulated AI is live."""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from coordination.relay import atomic_checkpoint


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent.parent
    tmp=root/'.test-tmp'
    tmp.mkdir(exist_ok=True)
    env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp),PYTHONIOENCODING='utf-8')
    env['PYTHONPATH']=str(root/'tests')+os.pathsep+str(root)
    rounds=[
        ('normal_collaboration',['test_relay.RelayContractTests.test_transition_needs_evidence_and_independent_review'],
         'partial','Live independent ChatGPT read and draft PR are separate pending evidence'),
        ('quota_unavailable',['test_relay_faults.FaultRecoveryTests.test_quota_unavailable_cold_recovery_uses_no_model',
         'test_relay_faults.FaultRecoveryTests.test_process_exit_preserves_last_checkpoint_and_queue'],
         'isolated_pass','Model unavailability is injected; no AI calls occur in this runner'),
        ('concurrency',['test_relay_git.GitConcurrencyTests.test_two_real_writers_and_crash_replay',
         'test_relay.RelayContractTests.test_exclusive_claim_and_fenced_old_owner'],
         'isolated_pass','Real local Git non-fast-forward conflict; live GitHub CAS reported separately'),
        ('fault_recovery',['test_relay_faults','test_relay.RelayContractTests.test_outbox_stops_after_transient_failure',
         'test_relay.RelayContractTests.test_replay_queue_retries_permission_rate_and_crash_after_ack',
         'test_relay.RelayContractTests.test_retry_ceiling_and_changed_queue_content',
         'test_dispatcher.DispatcherTests.test_corrupt_database_preserves_original_error'],
         'isolated_pass','Network/API faults injected; process interruption and Git operations are real local commands'),
        ('closed_loop',['test_relay_git.GitConcurrencyTests.test_synthetic_closed_loop_with_new_sha_and_local_conflict'],
         'partial','Remote actor is ordinary Python, not ChatGPT; synthetic SHAs are fixtures, not real business commits')]
    results=[]
    for number,(name,tests,scope,limits) in enumerate(rounds,1):
        cmd=[sys.executable,'-m','unittest','-v',*tests]
        run=subprocess.run(cmd,cwd=root,capture_output=True,text=True,encoding='utf-8',env=env,timeout=90)
        log=(run.stdout+run.stderr).replace(str(root),'<isolated-checkout>').replace(str(Path.home()),'<USER>')
        match=re.search(r'Ran (\d+) tests?',log)
        results.append(dict(round=number,name=name,command='python -m unittest -v '+' '.join(tests),
            exit_code=run.returncode,tests=int(match[1]) if match else None,
            status=scope if run.returncode==0 else 'failed',limitations=limits,log=log))
        print(json.dumps({'round':number,'exit_code':run.returncode,'status':results[-1]['status']}),flush=True)
    report=dict(schema_version=1,at=datetime.now(timezone.utc).isoformat(),environment='Windows / isolated synthetic data',
                rounds=results,overall='partial' if all(x['exit_code']==0 for x in results) else 'failed',
                live_chatgpt_takeover='unverified',deployed=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return 0 if report['overall']=='partial' else 1


if __name__=='__main__':
    raise SystemExit(main())
