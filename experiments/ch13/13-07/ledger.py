"""Append actual observations; keep the original null-valued prediction immutable."""
import argparse,datetime,hashlib,json,statistics
from pathlib import Path
B=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def forecast():
 p=B/'prediction.json';assert digest(p)==(B/'prediction.sha256').read_text().strip();v=read(p);assert v['observation'] is None and v['revision'] is None;return v

def status(asof=None):
 f=forecast();event_lines=(B/'events.jsonl').read_text().splitlines()
 for i,line in enumerate(event_lines):
  event=json.loads(line)
  if i:
   assert event['previous_event_sha256']==hashlib.sha256(event_lines[i-1].encode()).hexdigest()
   assert digest(B/event['file'])==event['sha256']
   assert digest(B/event['revision_file'])==event['revision_sha256']
 when=datetime.datetime.fromisoformat(asof or now());obs=sorted((B/'observations').glob('*.json'))
 if obs:return {'state':read(obs[-1])['verdict'],'observation_file':str(obs[-1].relative_to(B)),'observation':read(obs[-1]),'initial_prediction_unchanged':True}
 return {'state':'expired_unobserved' if when>datetime.datetime.fromisoformat(f['deadline_utc']) else 'pending_unobserved','observation':None,'initial_prediction_unchanged':True}

def record(run):
 f=forecast();root=B/run;provenance=read(root/'provenance.json');completion=read(root/'completion.json');summary=read(root/'summary.json');plan=read(root/'plan.json');expected=read(B/'future-plan.json')
 assert plan==expected and summary['paths']==30 and completion['done'];assert provenance['prediction_sha256']==(B/'prediction.sha256').read_text().strip();assert datetime.datetime.fromisoformat(provenance['started_utc'])>datetime.datetime.fromisoformat(f['created_utc']);assert summary['all_mechanism_checks_passed'];assert all(c['passed'] for c in read(root/'checks.json'))
 assert not any(read(p).get('source_sha256',{}).get('summary.json')==digest(root/'summary.json') for p in (B/'observations').glob('*.json')),'Already recorded this actual result'
 environments=[read(p) for p in root.glob('*/attempt-*/environment.json')];in_scope=all(e['versions']['mlx']=='0.32.2' and e['versions']['mlx-lm']=='0.31.3' and e['versions']['transformers']=='5.16.1' and e['device']['device_name']=='Apple M2 Max' and e['model']==read(B/'model-identity.json')['revision'] for e in environments)
 assert read(root/'source-sha.json')==f['frozen_files_sha256']
 for n,h in f['frozen_files_sha256'].items():assert digest(B/n)==h,n
 results=summary['results'];assert set(r['request_id'] for r in results)==set(j['request_id'] for j in expected);pairs=[]
 for trial in range(5):
  for task in ['sequence','extract']:
   group={r['strategy']:r for r in results if r['trial']==trial and r['task']==task};assert len(group)==3
   pairs.append(dict(trial=trial,task=task,restart_wall_s=group['restart']['wall_s'],preserve_wall_s=group['preserve']['wall_s'],ratio=group['preserve']['wall_s']/group['restart']['wall_s']))
 restored=[r for r in results if r['strategy']!='baseline'];quality=all(r['quality_passed'] and r['tokens_equal_baseline'] and r['preempted'] for r in restored);ratio=statistics.median(p['ratio'] for p in pairs);within=f['interval'][0]<=ratio<=f['interval'][1];late=datetime.datetime.fromisoformat(completion['completed_utc'])>datetime.datetime.fromisoformat(f['deadline_utc'])
 result={'recorded_utc':now(),'prediction_sha256':provenance['prediction_sha256'],'run':run,'execution_started_utc':provenance['started_utc'],'execution_completed_utc':completion['completed_utc'],'metric':ratio,'interval':f['interval'],'interval_met':within,'quality_gate_met':quality,'restored_quality_passed':sum(r['quality_passed'] for r in restored),'restored_tokens_equal':sum(r['tokens_equal_baseline'] for r in restored),'pairs':pairs,'late':late,'in_scope':in_scope,'environment_records':len(environments),'verdict':('late_' if late else '')+('out_of_scope' if not in_scope else ('supported_in_scope' if quality and within else 'refuted_in_scope')),'evaluator_source_sha256':digest(Path(__file__)),'source_sha256':{n:digest(root/n) for n in ['summary.json','checks.json','plan.json','provenance.json','completion.json']}}
 key='quality_failure' if not quality else ('ratio_above_1' if ratio>1 else ('ratio_below_0_70' if ratio<.7 else 'interval_supported'));result['model_revision_rule']=f['revision_rules'][key] if in_scope else 'Do not use this changed environment to validate v1; register the changed condition separately.'
 target=B/'observations'/f'{len(list((B/"observations").glob("*.json")))+1:04}.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n')
 revisions=B/'revisions';revisions.mkdir(exist_ok=True);revision=revisions/target.name;assert not revision.exists();revision.write_text(json.dumps({'created_utc':result['recorded_utc'],'observation':str(target.relative_to(B)),'original_prediction_sha256':result['prediction_sha256'],'verdict':result['verdict'],'model_revision_rule_applied':result['model_revision_rule'],'original_interval_unchanged':True,'new_forecast':None},indent=2)+'\n')
 eventfile=B/'events.jsonl';last=eventfile.read_text().splitlines()[-1];event={'event':'actual_observation_recorded','created_utc':result['recorded_utc'],'file':str(target.relative_to(B)),'sha256':digest(target),'revision_file':str(revision.relative_to(B)),'revision_sha256':digest(revision),'previous_event_sha256':hashlib.sha256(last.encode()).hexdigest()}
 with eventfile.open('a') as stream:stream.write(json.dumps(event)+'\n')
 return status()
if __name__=='__main__':
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True);q=sub.add_parser('status');q.add_argument('--as-of');q=sub.add_parser('record');q.add_argument('--run',required=True);a=p.parse_args();print(json.dumps(record(a.run) if a.command=='record' else status(a.as_of),indent=2))
