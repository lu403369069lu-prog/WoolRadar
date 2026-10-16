from pathlib import Path
import subprocess,sys,os,json,re,concurrent.futures,time
root=Path(__file__).resolve().parents[2];out=Path(__file__).parent;(out/'temp').mkdir(exist_ok=True)
node='USER_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
env=dict(os.environ,TEMP=str(out/'temp'),TMP=str(out/'temp'),PYTHONDONTWRITEBYTECODE='1')
env['PYTHONPATH']=os.pathsep.join([str(root/'_work/qa2-woolradar-29/core'),str(root/'_work/qa2-woolradar-32')])
jobs=[('wool28-combined',root/'_work/qa2-woolradar-28',[sys.executable,'-X','utf8','-B','independent-quality/delivery-bridge-20261016/run_combined_tests.py']),('wool29-full',root/'_work/qa2-woolradar-29',[sys.executable,'-X','utf8','-B','-m','unittest','discover','-s','tests','-v']),('wool29-matcher',root/'_work/qa2-woolradar-29/independent-quality/developer-grant-20261016',[sys.executable,'-X','utf8','-B','-m','unittest','discover','-s','.','-v']),('wool32-sampler',root/'_work/qa2-woolradar-32/independent-quality/public-corpus-blind-dedup-20261016',[sys.executable,'-X','utf8','-B','-m','unittest','discover','-s','.','-v'])]
sam=root/'_work/qa2-yinqieji-9/SAM/independent-review/20261016-0904-audit-coverage'
jobs.append(('sam9-review',sam,[node,'--test',*[p.name for p in sorted(sam.glob('*.test.mjs'))]]))
def run(job):
 name,cwd,cmd=job;sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=cwd,text=True).strip();start=time.monotonic()
 try:
  r=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);log=r.stdout+'\n'+r.stderr;code=r.returncode
 except subprocess.TimeoutExpired as e:log=str(e);code='TIMEOUT'
 (out/(name+'.log')).write_text(log,encoding='utf-8');result=dict(label=name,command=cmd,cwd=str(cwd),source_sha=sha,exit_code=code,seconds=round(time.monotonic()-start,3),log=name+'.log')
 m=re.search(r'Ran (\d+) tests?',log)
 if m:
  total=int(m[1]);counts={k:int(v) for k,v in re.findall(r'(failures|errors|skipped)=(\d+)',log)};result.update(total=total,failed=counts.get('failures',0),errors=counts.get('errors',0),skipped=counts.get('skipped',0));result['passed']=total-result['failed']-result['errors']-result['skipped']
 for k in ['tests','pass','fail','skipped']:
  m=re.search(r'^[#ℹ]\s*'+k+r' (\d+)',log,re.M)
  if m:result[k]=int(m[1])
 (out/(name+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
 return result
jobs=[j for j in jobs if j[0] in ['wool29-matcher','wool32-sampler']]
with concurrent.futures.ThreadPoolExecutor(2) as ex:results=list(ex.map(run,jobs))
(out/'corrected-path-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
