"""Independent read-only review of 13-7; writes only into its own directory."""
import collections,datetime,hashlib,json,random,sqlite3,statistics,tempfile,shutil
from pathlib import Path
B=Path(__file__).resolve().parents[2]/'ch13/13-07';OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=read(B/'prediction.json');checks=[]
def check(n,v):
 checks.append(dict(name=n,passed=bool(v)))
 assert v,n
check('prediction SHA matches immutable checksum',sha(B/'prediction.json')==(B/'prediction.sha256').read_text().strip())
check('original observation and revision remain null',f['observation'] is None and f['revision'] is None)
for n,h in f['frozen_files_sha256'].items():check('frozen source '+n,sha(B/n)==h)
for n,h in read(B/'freeze-view-sha.json').items():check('original view '+n,sha(B/n)==h)
plan=read(B/'future-plan.json');run=B/'formal';check('executed plan equals original',read(run/'plan.json')==plan)
check('30 distinct paths',len(plan)==30 and len({x['request_id'] for x in plan})==30)
check('ten triples complete',collections.Counter((x['trial'],x['task']['id'],x['strategy']) for x in plan)==collections.Counter({(t,task,s):1 for t in range(5) for task in ['sequence','extract'] for s in ['baseline','restart','preserve']}))
check('K192 only with same max tokens',all(x['cut']==192 and x['max_tokens']==768 for x in plan))
# No task mutation across paths or original 11-4 prompt/expected values.
tasks={x['task']['id']:x['task'] for x in plan};check('each task is identical in every path',all(x['task']==tasks[x['task']['id']] for x in plan))
original_tasks=read(B.parents[1]/'ch11/11-04/tasks.json')['formal']
check('unchanged original 11-4 task prompts and expected answers',tasks=={x['id']:x for x in original_tasks})
rng=random.Random(1307);expected_order=[]
for trial in range(5):
 batch=[f't{trial}-{task["id"]}-k192-{st}' for task in original_tasks for st in ['baseline','restart','preserve']]
 rng.shuffle(batch);expected_order.extend(batch)
check('frozen order matches five sequential RNG shuffles',expected_order==[j['request_id'] for j in plan])
prior=read(B/'known-evidence/11-4-summary.json');old=prior['results'];check('K192 absent in known historical result',all(x['cut']!=192 for x in old))
known=f['strongest_known_counterexample'];hist={r['strategy']:r for r in old if r['task']=='sequence' and r['cut']==96}
check('strongest counterexample ratio exact',hist['preserve']['wall_s']/hist['restart']['wall_s']==known['ratio'])
check('known example slower preserve',known['ratio']>1)
prov=read(run/'provenance.json');done=read(run/'completion.json');obs=read(B/'observations/0001.json');s=read(run/'summary.json');results={r['request_id']:r for r in s['results']}
check('recorded freeze before execution before completion',datetime.datetime.fromisoformat(f['created_utc'])<datetime.datetime.fromisoformat(prov['started_utc'])<datetime.datetime.fromisoformat(done['completed_utc'])<datetime.datetime.fromisoformat(f['deadline_utc']))
check('all paths complete',done['done'] and done['paths']==30 and len(results)==30)
windows={};ids={};env_count=0
for job in plan:
 d=run/job['request_id'];check('executed job '+job['request_id'],read(d/'job.json')==job)
 exe=read(d/'execution.json');comp=read(d/'completion.json');wall=exe[-1]['end']-exe[0]['start'];windows[job['request_id']]=wall
 check('raw window '+job['request_id'],wall==comp['wall_s']==results[job['request_id']]['wall_s'])
 with tempfile.TemporaryDirectory(dir=OUT) as tmp:
  dest=Path(tmp)/'snapshot.sqlite';shutil.copyfile(d/'manager-snapshot.sqlite',dest)
  wal=d/'manager-snapshot.sqlite-wal'
  if wal.exists():shutil.copyfile(wal,str(dest)+'-wal')
  con=sqlite3.connect(dest);rows=con.execute('select seq,token,eos,attempt from tokens order by seq').fetchall();con.close()
 ids[job['request_id']]=[r[1] for r in rows]
 check('raw DB contiguous and IDs '+job['request_id'],[r[0] for r in rows]==list(range(len(rows))) and ids[job['request_id']]==results[job['request_id']]['token_ids'])
 check('natural final EOS '+job['request_id'],comp['finishes'][-1]['reason']=='stop' and rows[-1][2]==1 and sum(r[2] for r in rows)==1)
 def unique(pairs):
  d={}
  for k,v in pairs:
   if k in d:raise ValueError('duplicate key')
   d[k]=v
  return d
 actual=json.loads(results[job['request_id']]['text'],object_pairs_hook=unique);expected=job['task']['expected']
 check('strict answer '+job['request_id'],actual==expected and (all(type(x)is int for x in actual) if isinstance(expected,list) else list(actual)==list(expected)))
 events=[json.loads(l) for l in (d/'manager-events.jsonl').read_text().splitlines()]
 if job['strategy']!='baseline':
  check('two distinct workers '+job['request_id'],len(exe)==2 and exe[0]['pid']!=exe[1]['pid'] and exe[0]['end']<=exe[1]['start'])
  cut=[e for e in events if e['kind']=='committed' and e['cut']]
  check('actual cut after committed token 191 '+job['request_id'],len(cut)==1 and cut[0]['seq']==191 and cut[0]['commit_complete']<=exe[0]['killed'] and exe[0]['returncode']==-9)
 for e in exe:
  env=read(d/f'attempt-{e["attempt"]}'/'environment.json');env_count+=1
  check('worker environment '+str(e['pid']),env['model']==job['model_revision'] and env['device']['device_name']=='Apple M2 Max' and env['versions']['mlx']=='0.32.2' and env['versions']['mlx-lm']=='0.31.3' and env['versions']['transformers']=='5.16.1')
ratios=[]
for t in range(5):
 for task in ['sequence','extract']:
  key=lambda st:f't{t}-{task}-k192-{st}'
  check('restored full tokens equal baseline '+key('baseline'),ids[key('baseline')]==ids[key('restart')]==ids[key('preserve')])
  ratios.append(windows[key('preserve')]/windows[key('restart')])
metric=statistics.median(ratios)
check('ten paired-ratio median matches observation',len(ratios)==10 and metric==obs['metric'])
check('interval miss honestly refuted despite favorable direction',metric<.7 and obs['interval_met'] is False and obs['quality_gate_met'] is True and obs['verdict']=='refuted_in_scope')
check('all 50 worker environments covered',env_count==50 and obs['environment_records']==50)
for n,h in obs['source_sha256'].items():check('observation source '+n,sha(run/n)==h)
events=(B/'events.jsonl').read_text().splitlines();check('first event freeze hash',json.loads(events[0])['prediction_sha256']==sha(B/'prediction.json'))
for i in range(1,len(events)):
 e=json.loads(events[i]);check('event chain '+str(i),e['previous_event_sha256']==hashlib.sha256(events[i-1].encode()).hexdigest() and sha(B/e['file'])==e['sha256'] and sha(B/e['revision_file'])==e['revision_sha256'])
report=dict(status='pass',checks=len(checks),prediction_sha256=sha(B/'prediction.json'),metric=metric,ratios=ratios,observed_quality='all 20 restored paths natural EOS/strict answer/full token equality',verdict=obs['verdict'],checks_detail=checks,limits=['File hashes and recorded timestamps establish internal provenance consistency, not externally timestamped notarization.','Same-host warm filesystem and variable contention are fixed scope; paired ratios are descriptive, not a calibrated confidence interval.','Current ledger evaluator is observation-time code; original frozen numerical interval/quality rule and executed analyzer remain unmodified.'])
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['checks_detail','ratios']}))
