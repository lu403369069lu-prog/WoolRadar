from pathlib import Path
import subprocess,json,os,concurrent.futures
root=Path(__file__).resolve().parents[2];out=Path(__file__).parent;env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never')
targets=[('WoolRadar',23,'af199e6e74655d184575d171a68321e0fb670628','relay-return.git'),('WoolRadar',28,'dfe21a0991735f940cc283bb38cc94eaa2dbd61f','relay-return.git'),('WoolRadar',29,'87be0c915531701cb63ec577ac08433bcf18a303','relay-return.git'),('WoolRadar',32,'2fc34f77472880d2a6a024d5ad8520c4af9f5830','relay-return.git'),('YinQieJi',5,'4b68619686350cbb1fe2f64753a72a654558e6ec','sam-review.git'),('YinQieJi',9,'a033f86387855c0f206f67980c3c82f67ba895e5','sam-review.git')]
def group(repo):
 records=[]
 for r,n,sha,bare in [t for t in targets if t[0]==repo]:
  work=root/f'_work/qa2-{repo.lower()}-{n}'
  def run(args):
   p=subprocess.run(args,cwd=root,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120);records.append(dict(command=args,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));(out/f'fetch-{repo}.json').write_text(json.dumps(records,indent=2),encoding='utf-8');assert p.returncode==0,p.stderr;return p.stdout.strip()
  prefix=['git','--git-dir',str(root/'_work'/bare)]
  run(prefix+['fetch','--no-tags','https://github.com/lu403369069lu-prog/'+repo+'.git',f'refs/pull/{n}/head'])
  actual=run(prefix+['rev-parse','FETCH_HEAD']);assert actual==sha,('STALE',n,actual,sha)
  if not work.exists():run(prefix+['worktree','add','--detach',str(work),sha])
  assert run(['git','-C',str(work),'rev-parse','HEAD'])==sha
  print(json.dumps(dict(repo=repo,pr=n,sha=sha,work=str(work))),flush=True)
with concurrent.futures.ThreadPoolExecutor(2) as ex:list(ex.map(group,['WoolRadar','YinQieJi']))
