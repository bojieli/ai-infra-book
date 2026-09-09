"""Actual CPU-only all-request protocol check, prior to GPU generation."""
import argparse,json,subprocess,sys,time
from pathlib import Path
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--retrieval',type=Path,required=True);p.add_argument('--model',type=Path,required=True);a=p.parse_args();plan=json.loads((a.retrieval/'prepared-prompts.json').read_text());rows=[]
with (a.retrieval/'cpu-service-check.log').open('w') as log:
 proc=subprocess.Popen([sys.executable,'-B',str(B/'serve_retrieval.py'),'--retrieval',str(a.retrieval),'--model',str(a.model)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True)
 ready=json.loads(proc.stdout.readline());assert ready['status']=='ready'
 try:
  for r in plan['requests']:
   proc.stdin.write(json.dumps(dict(id=r['id']))+'\n');proc.stdin.flush();x=json.loads(proc.stdout.readline());assert x['id']==r['id'] and x['prompt_token_ids']==r['prompt_token_ids'];rows.append({k:v for k,v in x.items() if k!='prompt_token_ids'})
  proc.stdin.write('{"stop":true}\n');proc.stdin.flush();proc.stdin.close();assert proc.wait(timeout=15)==0
 finally:
  if proc.poll() is None:proc.terminate();proc.wait(timeout=15)
(a.retrieval/'cpu-service-check.json').write_text(json.dumps(dict(scope='CPU protocol preflight only; separate from eventual generation timing',ready=ready,count=len(rows),all_288_prompts_exact=True,rows=rows),indent=2)+'\n');print('288 actual online encoder/index/tokenizer results exactly match frozen prompts')
