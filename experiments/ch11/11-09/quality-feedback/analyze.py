"""Offline evidence audit and isolated original 1013-check invocation; no GPU/network."""
import ast, hashlib,json,os,resource,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;RAW=R/'raw'
sys.dont_write_bytecode=True
sys.path.insert(0,str(R));import fixture

def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def limits():
 fixture.limits();resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,1024**2))
def main():
 start=time.monotonic();checks=[]
 def check(ok,label):
  if not ok:raise AssertionError(label)
  checks.append(label)
 for n,h in read(R/'run.lock.json').items():check(sha((R/n).read_bytes())==h,'frozen '+n)
 repo=R.parents[3]
 for n,h in read(R/'sources.lock.json').items():check(sha((repo/n).read_bytes())==h,'read-only source '+n)
 end=read(RAW/'exit.json');check(end['returncode']==0 and end['watchdog_reason'] is None and not end['remaining_owned'],'clean model group exit')
 before={int(l.split(',')[0]) for l in (RAW/'services-before.csv').read_text().splitlines()};after={int(l.split(',')[0]) for l in (RAW/'services-after.csv').read_text().splitlines()}
 check(len(before)==5 and before==after,'original five GPU processes preserved')
 resources=[json.loads(l) for l in (RAW/'resources.jsonl').read_text().splitlines()]
 check(all(r['gpu_mib']<=24576 for r in resources),'sampled owned GPU <=24GiB')
 check(all((r['rss_kib'] if r['engine_ready'] else r['anon_kib'])<=10*1024**2 for r in resources),'pre-registered sampled RSS boundary')
 check(all(p['affinity']=='8-11' for r in resources for p in r['processes']),'owned processes affinity 8-11')
 check(end['elapsed_s']<=1200,'model wall budget')
 records=[];firstprompts=[]
 for i,arm in enumerate(['baseline','feedback','feedback','baseline']):
  d=RAW/f'{i}-{arm}';begin=read(d/'start.json');check(begin['reset_prefix_cache'] is True,f'{i} APC reset')
  for name,text in [('intervals.py',fixture.INITIAL),('SPEC.txt',fixture.SPEC),('test_intervals.py',fixture.CHECKER)]:check(begin['initial_hashes'][name]==sha(text.encode()),f'{i} initial {name}')
  check((d/'workspace/SPEC.txt').read_text()==fixture.SPEC and (d/'workspace/test_intervals.py').read_text()==fixture.CHECKER,f'{i} immutable fixtures')
  rows=[json.loads(l) for l in (d/'rounds.jsonl').read_text().splitlines()];check(1<=len(rows)<=12,f'{i} round budget')
  messages=read(R/'initial-messages.json');code=fixture.INITIAL;diag_count=0;validations=[]
  firstprompts.append(rows[0]['prompt_token_ids'])
  for j,row in enumerate(rows):
   check(row['turn']==j and row['messages']==messages,f'{i}/{j} message continuity')
   check(row['code_before']==code,f'{i}/{j} code continuity')
   code=(d/f'code-{j:02}.py').read_text();check(sha(code.encode())==row['file_sha256'],f'{i}/{j} code hash')
   check(sha(row['output_text'].encode())==row['output_sha256'],f'{i}/{j} output hash')
   for name,h in row['hashes'].items():check(sha(json.dumps(row[name],sort_keys=True).encode())==h,f'{i}/{j} {name} hash')
   check(len(row['output_token_ids'])<=1200 and row['output_events'][-1]['token_count']==len(row['output_token_ids']),f'{i}/{j} output count')
   check(all(a['t_s']<=b['t_s'] and a['token_count']<=b['token_count'] for a,b in zip(row['output_events'],row['output_events'][1:])),f'{i}/{j} streaming events monotonic')
   reply=row['tool_result'];action=row['action']
   if action['tool']=='write_file':check(code==action['content'],f'{i}/{j} actual model written code')
   else:check(code==row['code_before'],f'{i}/{j} no unrequested code change')
   if action['tool']=='run_tests':
    check(all(reply[k]==row['tool_audit']['original_result'][k] for k in ['returncode','stdout','stderr']),f'{i}/{j} original feedback retained')
    if reply['returncode']==0:
     v=json.loads(reply['stdout']);check(len(v['cases'])==6 and v['passed']==all(x['passed'] for x in v['cases']),f'{i}/{j} six-case semantics');validations.append(sum(x['passed'] for x in v['cases']))
     if arm=='feedback' and not v['passed']:
      diag_count+=1;diags=reply['diagnostics'];failed=[x for x in v['cases'] if not x['passed']]
      check(len(diags)==len(failed),f'{i}/{j} diagnostic failed cases')
      for a,b in zip(diags,failed):
       check(a['input_before']==b['input'] and a['passed']==b['passed'],f'{i}/{j} diagnostic matches original input/pass')
       if 'actual' in b:check(a['actual']==b['actual'] and a['expected']==b['expected'] and a['unchanged']==b['unchanged'] and a['unchanged']==(a['input_before']==a['input_after']),f'{i}/{j} diagnostic measured values')
    if arm=='baseline':check(set(reply)=={'returncode','stdout','stderr'},f'{i}/{j} baseline unchanged feedback structure')
   messages=messages+[dict(role='assistant',content=row['output_text']),dict(role='user',content='Tool result: '+json.dumps(reply))]
  final=read(d/'final.json');check(final['final_code']==code==(d/'workspace/intervals.py').read_text(),f'{i} final code continuity')
  check(final['agent_finished']==(rows[-1]['action']['tool']=='finish'),f'{i} finish flag')
  holdout=read(d/'independent-checks.json')
  check(holdout['code_sha256']==sha(code.encode()) and holdout['checker_sha256']==sha((R/'check_code.py').read_bytes()),f'{i} holdout input hashes')
  v=json.loads(final['validation']['stdout']);h=json.loads(holdout['stdout']) if holdout['returncode']==0 else {}
  check(h.get('cases')==1013,f'{i} independent 1013 count')
  check(h['passed']==h['value_and_input_passed']-h['additional_alias_failures'],f'{i} separate alias accounting')
  records.append(dict(index=i,arm=arm,rounds=len(rows),six_passed=sum(x['passed'] for x in v['cases']),agent_finished=final['agent_finished'],qualified=bool(v['passed'] and final['agent_finished']),holdout_passed=h['passed'],holdout_cases=h['cases'],value_and_input_passed=h['value_and_input_passed'],additional_alias_failures=h['additional_alias_failures'],qualified_and_holdout=bool(v['passed'] and final['agent_finished'] and h['passed']==1013),diagnostic_calls=diag_count,observed_six_progress=validations,input_tokens=sum(len(x['prompt_token_ids']) for x in rows),output_tokens=sum(len(x['output_token_ids']) for x in rows),cached_tokens=sum(x['cached_tokens'] for x in rows),elapsed_s=final['elapsed_s'],model_s=sum(x['model_end_s']-x['model_start_s'] for x in rows),tool_s=sum(x['tool_end_s']-x['tool_start_s'] for x in rows),code_sha256=sha(code.encode())))
 check(all(p==firstprompts[0] for p in firstprompts),'four identical first request token IDs')
 check(sum(f.stat().st_size for f in RAW.rglob('*') if f.is_file())<=100*1024**2,'raw <=100MiB')
 summary=dict(attempts=records,resource=dict(samples=len(resources),peak_gpu_mib=max(x['gpu_mib'] for x in resources),peak_total_rss_mib=max(x['rss_kib'] for x in resources)/1024,peak_anon_rss_mib=max(x['anon_kib'] for x in resources)/1024,peak_ready_rss_mib=max(x['rss_kib'] for x in resources if x['engine_ready'])/1024,model_job_s=end['elapsed_s'],five_services_preserved=True),scope='One task, four attempts, diagnostic feedback intervention; not matched resource comparison or model-wide quality.')
 dump(R/'summary.json',summary);dump(R/'checks.json',dict(passed=True,checks=checks,wall_s=time.monotonic()-start,local_platform=sys.platform,local_ru_maxrss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
