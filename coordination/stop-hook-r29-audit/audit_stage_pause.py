"""Audit exact stage-pause phrases separately from conditional future requests."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
base_spec=importlib.util.spec_from_file_location('base_audit',Path(__file__).with_name('audit_stop_resume.py'))
base=importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(base)

CASES = base.CASES + [
    ('direct_stage_pause', 'active', ['继续', '阶段性停止'], 'allow'),
    ('prefixed_stage_pause', 'active', ['继续', '先阶段性停止'], 'allow'),
    ('now_stage_pause', 'active', ['继续', '现在阶段性停止'], 'allow'),
    ('stage_pause_with_reason', 'active', ['继续', '阶段性停止，保留待办'], 'allow'),
    ('conditional_quota_pause', 'active', ['继续', '5h额度到45%时控制其他对话进入阶段性停止，包括你'], 'block'),
    ('stage_pause_question', 'active', ['阶段性停止了吗？继续干'], 'block'),
]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('module',type=Path)
    parser.add_argument('--expect-mismatch',type=int,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('stage_gate',args.module)
    gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    rows=[base.evaluate(gate,*c) for c in CASES]
    bad=sum(not r['correct'] for r in rows)
    report={'source_sha256':hashlib.sha256(args.module.read_bytes()).hexdigest(),
            'count':len(rows),'mismatches':bad,'expected_mismatches':args.expect_mismatch,
            'cases':rows,'synthetic_only':True,'global_hook_installed':False}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'count':len(rows),'mismatches':bad,'expected_mismatches':args.expect_mismatch}))
    raise SystemExit(0 if bad==args.expect_mismatch else 1)
