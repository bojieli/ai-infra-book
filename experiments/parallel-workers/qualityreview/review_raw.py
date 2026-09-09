"""Read-only evidence audit. No imports/execution of experiment or generated code."""
import ast, copy, hashlib, itertools, json, random
from pathlib import Path
OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
R=REPO/'experiments/ch11/11-09/quality-feedback'
checks=[]; issues=[]
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def htext(s): return hashlib.sha256(s.encode()).hexdigest()
def ck(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok: issues.append(label)
def literal(source,name):
 return next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
manifest=read(R/'manifest.json')
actual_files={str(p.relative_to(R)) for p in R.rglob('*') if p.is_file() and p!=R/'manifest.json'}
ck(len(manifest['files'])==109,'109 manifest entries')
ck(actual_files==set(manifest['files']),'manifest exact file coverage')
for name,rec in manifest['files'].items():
 p=R/name; ck(p.is_file() and sha(p)==rec['sha256'] and p.stat().st_size==rec['bytes'],'manifest '+name)
s=manifest['status']; p=REPO/s['path']; ck(sha(p)==s['sha256'] and p.stat().st_size==s['bytes'],'sealed status hash and bytes')
for lock,base in [('run.lock.json',R),('sources.lock.json',REPO)]:
 for name,h in read(R/lock).items(): ck(sha(base/name)==h,lock+' '+name)
fixture=(R/'fixture.py').read_text(); initial=literal(fixture,'INITIAL'); spec=literal(fixture,'SPEC'); checker=literal(fixture,'CHECKER'); six=literal(checker,'cases')
old=(REPO/'experiments/ch11/11-01/run.py').read_text()
for name,value in [('INITIAL',initial),('SPEC',spec),('CHECKER',checker)]: ck(literal(old,name)==value,'original 11-01 '+name+' identical')
# Handwritten semantic reproductions of the two inspected, finite implementations.
# The raw code is only parsed and compared; never exec/compile/import/runpy.
final_text='''def merge_intervals(intervals):
    if not intervals:
        return []
    intervals.sort()
    result = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = result[-1]
        if start <= last_end:
            result[-1][1] = max(last_end, end)
        else:
            result.append([start, end])
    return result'''
def simulate(data,final):
 data.sort()
 if final:
  if not data: return []
  result=[data[0]]
  for pair in data[1:]:
   if pair[0]<=result[-1][1]: result[-1][1]=max(result[-1][1],pair[1])
   else: result.append([pair[0],pair[1]])
 else:
  result=[]
  for a,b in data:
   if result and a<result[-1][1]: result[-1][1]=b
   else: result.append([a,b])
 return result

def six_result(final):
 rows=[];diags=[]
 for original,expected in six:
  data=copy.deepcopy(original);actual=simulate(data,final)
  passed=actual==expected and data==original
  rows.append(dict(input=original,expected=expected,actual=copy.deepcopy(actual),unchanged=data==original,passed=passed))
  if not passed: diags.append(dict(input_before=original,expected=expected,actual=copy.deepcopy(actual),input_after=copy.deepcopy(data),unchanged=data==original,passed=False,output_is_input=actual is data,nested_aliases=[dict(output_index=i,input_index=j) for i,x in enumerate(actual) for j,y in enumerate(data) if x is y]))
 return dict(passed=all(x['passed'] for x in rows),cases=rows),diags
# A separate sorted-union oracle; does not use check_code.py's graph algorithm.
def oracle(original):
 result=[]
 for a,b in sorted(original):
  if result and a<=result[-1][1]: result[-1][1]=max(result[-1][1],b)
  else: result.append([a,b])
 return result
intervals=[[a,b] for a in range(-3,4) for b in range(a,4)]
cases=[[]]+[[x] for x in intervals]+[list(x) for x in itertools.product(intervals,repeat=2)]
rng=random.Random(304);cases += [[rng.choice(intervals) for _ in range(rng.randrange(3,8))] for _ in range(200)]
failures=[];value_pass=alias_fail=0
for original in cases:
 data=copy.deepcopy(original);expected=oracle(original);actual=simulate(data,True)
 passed=actual==expected and data==original; value_pass+=int(passed)
 if actual:
  actual[0][0]-=100; aliased=data!=original
  alias_fail+=int(passed and aliased); passed=passed and not aliased
 if not passed: failures.append(dict(input=original,expected=expected))
hcalc=dict(cases=len(cases),passed=len(cases)-len(failures),value_and_input_passed=value_pass,additional_alias_failures=alias_fail,failures=failures)
ck([len(intervals),len(cases),value_pass,alias_fail,hcalc['passed']]==[28,1013,315,314,1],'independent 1013 reconstruction including alias mutation')
summary=read(R/'summary.json'); attempts=[]; first=[]; finishes=[]; total=0
for i,arm in enumerate(['baseline','feedback','feedback','baseline']):
 d=R/'raw'/f'{i}-{arm}'; start=read(d/'start.json'); rows=[json.loads(x) for x in (d/'rounds.jsonl').read_text().splitlines()]
 ck(start['index']==i and start['arm']==arm and start['reset_prefix_cache'] is True,f'{i} ABBA start and cache reset')
 for name,value in [('intervals.py',initial),('SPEC.txt',spec),('test_intervals.py',checker)]: ck(start['initial_hashes'][name]==htext(value),f'{i} initial hash {name}')
 ck((d/'workspace/SPEC.txt').read_text()==spec and (d/'workspace/test_intervals.py').read_text()==checker,f'{i} immutable fixture')
 messages=read(R/'initial-messages.json');ck(read(d/'initial-messages.json')==messages,f'{i} initial messages')
 ck(json.loads(read(d/'baseline.json')['result']['stdout'])==six_result(False)[0],f'{i} initial six raw matches hand simulation')
 code=initial;diags=0;progress=[];first.append(rows[0]['prompt_token_ids'])
 for j,row in enumerate(rows):
  label=f'{i}/{j} '
  ck(row['turn']==j and row['arm']==arm and row['messages']==messages,label+'message chain')
  ck(row['code_before']==code,label+'code before chain')
  action=row['action'];reply=row['tool_result']; new=(d/f'code-{j:02}.py').read_text()
  ck(json.loads(row['output_text'])==action,label+'raw output action')
  ck(new==(action['content'] if action['tool']=='write_file' else code),label+'actual writes')
  code=new;ck(code in [initial,final_text],label+'only inspected finite implementation')
  ck(row['file_sha256']==htext(code) and row['output_sha256']==htext(row['output_text']),label+'code and output SHA')
  for key,h in row['hashes'].items(): ck(htext(json.dumps(row[key],sort_keys=True))==h,label+'hash '+key)
  ev=row['output_events'];ck(ev[-1]['text']==row['output_text'] and ev[-1]['token_count']==len(row['output_token_ids'])<=1200,label+'stream final text and tokens')
  ck(all(a['t_s']<=b['t_s'] and a['token_count']<=b['token_count'] for a,b in zip(ev,ev[1:])),label+'stream monotonic')
  ck(row['model_start_s']<=row['model_end_s']<=row['tool_start_s']<=row['tool_end_s'],label+'timing order')
  if j: ck(rows[j-1]['tool_end_s']<=row['model_start_s'],label+'serial timing')
  if action['tool']=='run_tests':
   ck({k:reply[k] for k in ['returncode','stdout','stderr']}==row['tool_audit']['original_result'],label+'original result retained')
   expected,diagnostics=six_result(code==final_text)
   ck(reply['returncode']==0 and json.loads(reply['stdout'])==expected,label+'raw six results fully recomputed')
   progress.append(sum(x['passed'] for x in expected['cases']))
   if arm=='feedback':
    diags+=1;proc=reply['diagnostics_process'];ck(proc['returncode']==0 and json.loads(proc['stdout'])==reply['diagnostics']==diagnostics,label+'full diagnostic values and object aliases recomputed')
   else: ck(set(reply)=={'returncode','stdout','stderr'},label+'baseline feedback fields')
  messages += [dict(role='assistant',content=row['output_text']),dict(role='user',content='Tool result: '+json.dumps(reply))]
 final=read(d/'final.json');validation=json.loads(final['validation']['stdout'])
 ck(final['final_code']==code==final_text==(d/'workspace/intervals.py').read_text(),f'{i} final code exact match')
 ck(final['validation']['returncode']==0 and validation==six_result(True)[0],f'{i} final raw six recomputed')
 finished=rows[-1]['action']['tool']=='finish';ck(final['agent_finished']==finished and final['rounds']==len(rows),f'{i} finish separated from validation')
 if finished: finishes.append(rows[-1]['action']['answer'])
 holdout=read(d/'independent-checks.json');h= json.loads(holdout['stdout'])
 ck(holdout['returncode']==0 and holdout['code_sha256']==htext(code) and holdout['checker_sha256']==sha(R/'check_code.py'),f'{i} holdout hashes and exit')
 ck(all(h[k]==v for k,v in hcalc.items()),f'{i} all 1012 holdout failure records and counts independently reproduced')
 ck(holdout['platform']=='linux' and holdout['affinity']==[8,9,10,11] and holdout['limits']==dict(cpu_s=2,address_space_bytes=512*1024**2,wall_s=5,file_bytes=1024**2),f'{i} saved holdout resource limits')
 rec=dict(index=i,arm=arm,rounds=len(rows),six_passed=sum(x['passed'] for x in validation['cases']),agent_finished=finished,qualified=finished and validation['passed'],holdout_passed=h['passed'],holdout_cases=h['cases'],value_and_input_passed=h['value_and_input_passed'],additional_alias_failures=h['additional_alias_failures'],diagnostic_calls=diags,observed_six_progress=progress,input_tokens=sum(len(x['prompt_token_ids']) for x in rows),output_tokens=sum(len(x['output_token_ids']) for x in rows),cached_tokens=sum(x['cached_tokens'] for x in rows),elapsed_s=final['elapsed_s'],model_s=sum(x['model_end_s']-x['model_start_s'] for x in rows),tool_s=sum(x['tool_end_s']-x['tool_start_s'] for x in rows),code_sha256=htext(code))
 for k,v in rec.items():ck(summary['attempts'][i][k]==v,f'{i} summary derived {k}')
 attempts.append(rec);total+=len(rows)
ck(total==46 and [a['rounds'] for a in attempts]==[12,11,11,12],'46 requests and 12/11/11/12 rounds')
ck(all(x==first[0] for x in first),'identical initial prompt token IDs')
ck(len(finishes)==2 and finishes[0]==finishes[1] and 'still failing' in finishes[0],'feedback finish acknowledges failure')
oldcode=(REPO/'experiments/ch11/11-01/results/workspace/intervals.py')
ck(sha(oldcode)==htext(final_text),'same failed final code as 11-01')
raw=R/'raw';resources=[json.loads(x) for x in (raw/'resources.jsonl').read_text().splitlines()];group=read(raw/'owned-group.json');end=read(raw/'exit.json')
for j,r in enumerate(resources):
 ps=r['processes'];ids={p['pid'] for p in ps}
 ck(r['rss_kib']==sum(p['rss_kib'] for p in ps) and r['anon_kib']==sum(p['anon_kib'] for p in ps),f'sample {j} RSS aggregation')
 gpu=sum(int(line.split(',')[1]) for line in r['gpu_raw'].splitlines() if int(line.split(',')[0]) in ids)
 ck(gpu==r['gpu_mib'] and all(p['pgrp']==group['pgid'] and p['affinity']=='8-11' for p in ps),f'sample {j} owned GPU aggregation and affinity')
 ck(gpu<=24576 and (r['rss_kib'] if r['engine_ready'] else r['anon_kib'])<=10*1024**2,f'sample {j} preregistered limits')
res=dict(samples=len(resources),peak_gpu_mib=max(x['gpu_mib'] for x in resources),peak_total_rss_mib=max(x['rss_kib'] for x in resources)/1024,peak_anon_rss_mib=max(x['anon_kib'] for x in resources)/1024,peak_ready_rss_mib=max(x['rss_kib'] for x in resources if x['engine_ready'])/1024,model_job_s=end['elapsed_s'])
for k,v in res.items():ck(summary['resource'][k]==v,'summary resources '+k)
res['max_sample_interval_s']=max(b['t_s']-a['t_s'] for a,b in zip(resources,resources[1:]))
res['initial_free_mib']=group['free_mib'];res['gpu_fresh_samples']=sum(x['gpu_fresh'] for x in resources)
ck(group['free_mib']>=26*1024 and end['returncode']==0 and end['watchdog_reason'] is None and end['remaining_owned']==[] and end['elapsed_s']<1200,'initial headroom and clean bounded exit')
before={int(x.split(',')[0]) for x in (raw/'services-before.csv').read_text().splitlines()}; after={int(x.split(',')[0]) for x in (raw/'services-after.csv').read_text().splitlines()}
ck(before==after=={5875,1219611,1953199,1970308,3614304},'five original service PIDs preserved')
log=(raw/'model.log').read_text();events=[json.loads(x) for x in log.splitlines() if x.startswith('{"index"')]
ck(events==[dict(index=i,arm=a,attempt_ended=True) for i,a in enumerate(['baseline','feedback','feedback','baseline'])] and log.count('Successfully reset prefix cache')==4,'model log ABBA completion and four resets')
env=read(raw/'environment.json');cfg=env['config']
ck(cfg['model'].endswith('b968826d9c46dd6066d109eabc6255188de91218') and cfg['kv_cache_memory_bytes']==2*1024**3 and cfg['max_model_len']==8192 and cfg['max_num_seqs']==1 and cfg['max_num_batched_tokens']==512 and cfg['seed']==304 and cfg['dtype']=='bfloat16' and cfg['async_scheduling'] is False and cfg['enable_prefix_caching'] is True and cfg['enforce_eager'] is True,'raw common model configuration')
ck(env['torch']=='2.11.0+cu130' and env['vllm']=='0.23.0' and env['transformers']=='5.12.1' and env['affinity']==[8,9,10,11] and all(env['env'][x]=='1' for x in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS']),'raw versions and thread environment')
rawbytes=sum(p.stat().st_size for p in raw.rglob('*') if p.is_file());ck(rawbytes<100*1024**2,'raw under 100MiB')
readme=(R/'README.md').read_text()
for a in attempts:
 quality=f"| {a['index']} {a['arm']} | {a['rounds']} | 2/6 | {'是' if a['agent_finished'] else '否'} | 315/1013 | 314 | 1/1013 | 否 |"
 costs=f"| {a['index']} {a['arm']} | {a['input_tokens']} | {a['output_tokens']} | {a['cached_tokens']} | {a['elapsed_s']:.6f} | {a['model_s']:.6f} | {a['tool_s']:.6f} |"
 ck(quality in readme and costs in readme,f"README quality and cost row {a['index']}")
for token in ['46 次实际模型请求',htext(final_text),f"{res['model_job_s']:.6f}",'334次',f"{res['max_sample_interval_s']:.3f}",'18560 MiB',f"{res['peak_total_rss_mib']:.3f}",f"{res['peak_anon_rss_mib']:.3f}",f"{res['peak_ready_rss_mib']:.3f}"]:
 ck(token in readme,'README measured value '+token)
ck(read(R/'checks.json')['passed'] and len(read(R/'checks.json')['checks'])==722,'archived analyzer records 722 assertions (not rerun)')
report=dict(verdict='consistent_negative' if not issues else 'inconsistencies_found',source=str(R.relative_to(REPO)),method='Own read-only audit of all manifest bytes, all 46 raw rounds, original six-case stdout, diagnostics, holdout failure lists and process samples. Generated code was never executed; two statically inspected implementations were reproduced by handwritten finite logic; independent sorted-union oracle reconstructed the holdout. analyze.py read but not executed.',manifest=dict(entries=len(manifest['files']),actual_files_excluding_manifest=len(actual_files),raw_bytes=rawbytes,status_verified=True),attempts=attempts,total_model_requests=total,resources=res,holdout=dict(composition={'empty':1,'single':28,'double':784,'random_seed304':200},**{k:v for k,v in hcalc.items() if k!='failures'}),inconsistencies=issues,limitations=['Manifest establishes current byte integrity, not an external timestamp or proof of pre-registration chronology.','Raw logs and source support 46 recorded requests and fixed ABBA; no external provider-level request ledger is available.','Resources are sampled process-group measurements, not instantaneous peaks or cgroup limits; shared RSS pages may be counted more than once.','Torch intra/inter-op=1 and NUMEXPR=1 are supported by frozen runner/supervisor source, not separate runtime thread getter records.','No model, GPU, actual Agent task, original generated Python, or external network was run. No calculations paths accessed.'],checks_total=len(checks),checks_passed=sum(x['passed'] for x in checks),checks=checks)
(OUT/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['checks','attempts']},ensure_ascii=False,indent=2))
