"""Offline independent checks: reconstruct byte positions; compare every saved state tensor."""
import argparse,hashlib,json,math
from pathlib import Path
import torch
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--name',required=True);a=p.parse_args();root=B/a.name
checks=[]
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail));assert ok,(name,detail)
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(s) for s in p.read_text().splitlines()]
def equal(a,b):
 if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and a.dtype==b.dtype and a.shape==b.shape and torch.equal(a,b)
 if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return a==b
def numt(x):
 if isinstance(x,torch.Tensor):return 1
 if isinstance(x,dict):return sum(numt(v) for v in x.values())
 if isinstance(x,(tuple,list)):return sum(numt(v) for v in x)
 return 0
source=(B/'data/input.txt').read_bytes();env=read(root/'environment.json');runs=read(root/'execution.json');observations=[];negative=[]
check('source_sha',hashlib.sha256(source).hexdigest()==env['source_sha256']['data/input.txt'])
for s,h in env['source_sha256'].items():check('frozen_'+s,hashlib.sha256((B/s).read_bytes()).hexdigest()==h)
for run in runs:
 d=root/run['name'];rows=lines(d/'steps.jsonl');idn=read(d/'identity.json');check(run['name']+'_pid',idn['pid']==run['pid'])
 check(run['name']+'_terminal',run['exit_code']==(-15 if run['stop']>=0 else 0) and not run['leftover'])
 for row in rows:
  ids=row['positions'];raw=bytes(row['input_bytes']);check(run['name']+f'_step{row["step"]}_actual_bytes',raw==bytes(source[i] for i in ids) and len(raw)==129 and hashlib.sha256(raw).hexdigest()==row['input_sha256'])
  check(run['name']+f'_step{row["step"]}_actual_update',math.isfinite(row['loss']) and math.isfinite(row['gradient']) and row['gradient']>0 and row['end']>row['start'])
  if run['control']=='correct':check(run['name']+f'_step{row["step"]}_position',ids==list(range((row['step']-1)*128,row['step']*128+1)))
 if run['stop']<0:
  final=torch.load(d/'final.pt',weights_only=True);check(run['name']+'_Adam_steps',all(v['step'].item()==env['steps'] for v in final['optimizer']['state'].values()))
for seed in env['seeds']:
 bd=root/f'seed{seed}-baseline';base=lines(bd/'steps.jsonl');bf=torch.load(bd/'final.pt',weights_only=True)
 check(f'{seed}_baseline_complete',len(base)==env['steps'])
 for cut in env['checkpoints']:
  prefix=root/f'seed{seed}-cut{cut}-prefix';resume=root/f'seed{seed}-cut{cut}-resume';pr=lines(prefix/'steps.jsonl');rr=lines(resume/'steps.jsonl');ready=read(prefix/'ready.json');cp=torch.load(prefix/'checkpoint.pt',weights_only=True);rf=torch.load(resume/'final.pt',weights_only=True)
  check(f'{seed}_{cut}_fixed_cut',ready['step']==cut and cp['step']==cut and len(pr)==cut and len(rr)==env['steps']-cut)
  check(f'{seed}_{cut}_nonempty_prefetch',ready['buffer_bytes']>1 and bool(ready['pending']) and bool(ready['completed_unconsumed']) and set(ready['completed_unconsumed'])<=set(ready['pending']))
  dispatch=[r['record'] for r in lines(prefix/'dispatch.jsonl') if r['time']<=ready['save_start']]
  consumed=[r['record'] for r in lines(prefix/'consume.jsonl') if r['time']<=ready['save_start']]
  completed=[r['record'] for p in prefix.glob('worker-*.jsonl') for r in lines(p) if r['time']<=ready['save_start']]
  check(f'{seed}_{cut}_raw_prefetch_proof',consumed==list(range(cp['cursor'])) and sorted(set(dispatch)-set(consumed))==ready['pending'] and set(ready['completed_unconsumed'])<=set(completed)-set(consumed))
  check(f'{seed}_{cut}_two_actual_workers',len(list(prefix.glob('worker-*.jsonl')))==2 and len(list(resume.glob('worker-*.jsonl')))==2)
  check(f'{seed}_{cut}_packing',cp['positions']==list(range(cut*128,cut*128+len(cp['buffer']))) and cp['buffer']==bytes(source[i] for i in cp['positions']))
  check(f'{seed}_{cut}_buffer_source_end',sum(257+2*(i%7) for i in range(cp['cursor']))==cut*128+len(cp['buffer']))
  for x,y in zip(base,pr+rr):check(f'{seed}_{cut}_step{x["step"]}_baseline_exact',all(x[k]==y[k] for k in ['step','loss','gradient','positions','input_bytes','input_sha256','buffer_bytes','cursor']))
  for key in ['model','optimizer','rng','loader_rng','cursor','buffer','positions','step']:check(f'{seed}_{cut}_full_{key}',equal(bf[key],rf[key]))
  before=read(prefix/'identity.json');after=read(resume/'identity.json');check(f'{seed}_{cut}_new_process',before['pid']!=after['pid'])
  revents=[e for p in resume.glob('worker-*.jsonl') for e in lines(p)];reread=sorted(set(e['record'] for e in revents)&set(ready['pending']))
  check(f'{seed}_{cut}_prefetch_reread',bool(reread) and min(e['record'] for e in revents)==cp['cursor'])
  run=next(v for v in runs if v['name']==prefix.name);observations.append(dict(seed=seed,cut=cut,buffer_bytes=len(cp['buffer']),cursor=cp['cursor'],pending=ready['pending'],completed_unconsumed=ready['completed_unconsumed'],reread=reread,save_s=ready['save_complete']-ready['save_start'],terminate_time=run['termination'],first_resume_update_start=rr[0]['start'],first_resume_update_end=rr[0]['end'],resume_delay_s=rr[0]['end']-run['termination'],checkpoint_bytes=ready['checkpoint_bytes'],state_tensors_compared=numt(bf),new_pid=after['pid']))
for control in ['omit_buffer','dispatch_cursor']:
 d=root/f'seed1061-cut17-{control}';rows=lines(d/'steps.jsonl');bf=torch.load(root/'seed1061-baseline/final.pt',weights_only=True);nf=torch.load(d/'final.pt',weights_only=True)
 bad=[r['step'] for r in rows if r['positions']!=list(range((r['step']-1)*128,r['step']*128+1))]
 check(control+'_position_detected',bool(bad));check(control+'_model_difference',not equal(bf['model'],nf['model']));check(control+'_Adam_difference',not equal(bf['optimizer'],nf['optimizer']))
 negative.append(dict(control=control,first_bad_step=min(bad),bad_steps=len(bad),final_model_differs=True,final_Adam_differs=True))
resource=read(root/'resources.json');summary=dict(name=a.name,runs=len(runs),checks=len(checks),all_passed=True,observations=observations,negative_controls=negative,peak_process_group_rss_bytes=max(r['rss_bytes'] for r in resource),rss_scope='training process and its DataLoader workers/resource tracker; controller not included',total_wall_s=read(root/'completion.json')['wall_s'])
(root/'checks.json').write_text(json.dumps(checks,indent=2)+'\n');(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
