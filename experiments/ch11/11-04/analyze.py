"""Offline proof from SQLite snapshots, worker tokens and manager transactions."""
import argparse,hashlib,json,sqlite3
from pathlib import Path
from transformers import AutoTokenizer
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--name',required=True);a=p.parse_args();root=B/a.name
meta=json.loads((B/'model-identity.json').read_text());tok=AutoTokenizer.from_pretrained(meta['snapshot'],local_files_only=True);checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)));assert ok,name
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []
def no_duplicate(pairs):
 out={}
 for k,v in pairs:
  if k in out:raise ValueError('duplicate key')
  out[k]=v
 return out
def quality(text,expected):
 try:actual=json.loads(text,object_pairs_hook=no_duplicate)
 except (ValueError,TypeError):return False
 if isinstance(expected,list):return isinstance(actual,list) and all(type(v)is int for v in actual) and actual==expected
 return isinstance(actual,dict) and list(actual)==list(expected) and actual==expected and all(type(v)is str for v in actual.values())
for n,h in read(root/'source-sha.json').items():check('source_'+n,hashlib.sha256((B/n).read_bytes()).hexdigest()==h)
config=read(Path(meta['snapshot'])/'config.json');eos_config=config['eos_token_id'];eos_ids=set(eos_config if isinstance(eos_config,list) else [eos_config]);results=[]
for job in read(root/'plan.json'):
 d=root/job['request_id'];db=sqlite3.connect(f'file:{d/"manager-snapshot.sqlite"}?mode=ro',uri=True);records=db.execute('SELECT seq,token,eos,attempt FROM tokens ORDER BY seq').fetchall();metadata=dict(db.execute('SELECT key,value FROM meta'));db.close();ids=[r[1] for r in records];text=tok.decode([r[1] for r in records if not r[2]],skip_special_tokens=False);events=lines(d/'manager-events.jsonl');commits=[e for e in events if e['kind']=='committed'];conflicts=[e for e in events if e['kind']=='conflict'];exe=read(d/'execution.json');complete=read(d/'completion.json');workers=[]
 first_commits={e['seq']:e for e in commits if not e['duplicate']}
 check(job['request_id']+'_DB_matches_first_commit',len(first_commits)==len(records) and all(r[0] in first_commits and (r[1],bool(r[2]),r[3])==(first_commits[r[0]]['token'],first_commits[r[0]]['eos'],first_commits[r[0]]['attempt']) for r in records))
 check(job['request_id']+'_true_EOS',all(bool(r[2])==(r[1] in eos_ids) for r in records))
 frozen_prompt=tok.apply_chat_template([{'role':'user','content':job['task']['prompt']}],tokenize=True,add_generation_prompt=True,enable_thinking=False,return_dict=False)
 check(job['request_id']+'_prompt_from_task',json.loads(metadata['prompt_ids'])==frozen_prompt and metadata['prompt_sha']==hashlib.sha256(json.dumps(frozen_prompt,separators=(',',':')).encode()).hexdigest())
 check(job['request_id']+'_identity',metadata['request_id']==job['request_id'] and metadata['model_revision']==job['model_revision']);check(job['request_id']+'_contiguous',list(range(len(records)))==[r[0] for r in records]);check(job['request_id']+'_EOS_position',sum(r[2] for r in records)<=1 and all(not r[2] or r[0]==len(records)-1 for r in records))
 for proc in exe:
  attempt=proc['attempt'];w=d/f'attempt-{attempt}';env=read(w/'environment.json');generated=lines(w/'generated.jsonl');acks=lines(w/'acks.jsonl');calls=lines(w/'calls.jsonl');check(job['request_id']+f'_worker{attempt}',proc['pid']==env['pid'] and env['pgid']==proc['pid'] and not proc['leftover']);check(job['request_id']+f'_prefix{attempt}',env['preserved_prefix']==(ids[:job['cut']] if attempt==1 and job['strategy']=='preserve' else []))
  check(job['request_id']+f'_worker_prompt{attempt}',env['prompt_ids']==frozen_prompt and env['prompt_sha']==metadata['prompt_sha'])
  startseq=job['cut'] if attempt==1 and job['strategy']=='preserve' else 0
  check(job['request_id']+f'_worker_seq{attempt}',[g['seq'] for g in generated]==list(range(startseq,startseq+len(generated))))
  for e in [x for x in commits if x['attempt']==attempt]:
   match=[g for g in generated if g['seq']==e['seq']];check(job['request_id']+f'_commit{attempt}_{e["seq"]}',len(match)==1 and match[0]['token']==e['token'] and match[0]['eos']==e['eos'] and e['generated']<=e['commit_start']<=e['commit_complete']<=e['time'])
  if proc['killed'] is not None:
   cut=[e for e in commits if e['attempt']==attempt and e['cut']];check(job['request_id']+'_actual_commit_before_kill',len(cut)==1 and cut[0]['seq']==job['cut']-1 and cut[0]['commit_complete']<=proc['killed'] and proc['returncode']==-9);check(job['request_id']+'_no_ACK_at_cut',not any(e['seq']==job['cut']-1 for e in acks));check(job['request_id']+'_no_ahead_generation',len(generated)==job['cut'] and generated[-1]['seq']==job['cut']-1)
  else:check(job['request_id']+f'_clean{attempt}',proc['returncode']==0 and (w/'completion.json').exists())
  check(job['request_id']+f'_prefill{attempt}',sum(c['input_tokens'] for c in calls if c['kind']=='prompt_prefill')==len(env['prompt_ids']));check(job['request_id']+f'_rebuild{attempt}',sum(c['input_tokens'] for c in calls if c['kind']=='prefix_rebuild')==len(env['preserved_prefix']))
  offset=0
  for i,c in enumerate(calls):offset+=c['input_tokens'];check(job['request_id']+f'_cache{attempt}_{i}',all(v==offset for v in c['offsets']) and c['end']>=c['start'])
  workers.append(dict(attempt=attempt,pid=proc['pid'],load_s=env['load_s'],sampled_tokens=len(generated),prompt_prefill_tokens=sum(c['input_tokens'] for c in calls if c['kind']=='prompt_prefill'),prefix_rebuild_tokens=sum(c['input_tokens'] for c in calls if c['kind']=='prefix_rebuild'),decode_input_tokens=sum(c['input_tokens'] for c in calls if c['kind']=='decode'),model_call_s=sum(c['end']-c['start'] for c in calls),prefill_s=sum(c['end']-c['start'] for c in calls if c['kind']=='prompt_prefill'),rebuild_s=sum(c['end']-c['start'] for c in calls if c['kind']=='prefix_rebuild'),decode_s=sum(c['end']-c['start'] for c in calls if c['kind']=='decode')))
 if complete['preempted']:
  check(job['request_id']+'_new_PID',len(exe)==2 and exe[0]['pid']!=exe[1]['pid'] and exe[0]['end']<=exe[1]['start'])
  check(job['request_id']+'_persistent_highwater',[e['count'] for e in events if e['kind']=='state_read']==[0,job['cut']])
 reason=complete['finishes'][-1]['reason'];natural=reason=='stop' and bool(records) and records[-1][2]==1;passed=natural and quality(text,job['task']['expected'])
 results.append(dict(request_id=job['request_id'],task=job['task']['id'],cut=job['cut'],strategy=job['strategy'],preempted=complete['preempted'],reason=reason,token_ids=ids,text=text,quality_passed=passed,unique_tokens=len(ids),sampled_tokens=sum(w['sampled_tokens'] for w in workers),duplicate_deliveries=sum(e['duplicate'] for e in commits),conflicts=len(conflicts),wall_s=complete['wall_s'],peak_rss_bytes=complete['max_rss_bytes'],workers=workers))
for r in results:
 base=next(x for x in results if x['task']==r['task'] and x['cut']==r['cut'] and x['strategy']=='baseline');r['tokens_equal_baseline']=r['token_ids']==base['token_ids'];r['extra_sampled_vs_baseline']=r['sampled_tokens']-base['sampled_tokens']
summary=dict(name=a.name,paths=len(results),checks=len(checks),all_mechanism_checks_passed=True,quality_passed=sum(r['quality_passed'] for r in results),exact_baseline_paths=sum(r['tokens_equal_baseline'] for r in results),results=results)
(root/'checks.json').write_text(json.dumps(checks,indent=2)+'\n');(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='results'}));print([(r['request_id'],r['quality_passed'],r['unique_tokens'],r['duplicate_deliveries'],r['tokens_equal_baseline']) for r in results])
