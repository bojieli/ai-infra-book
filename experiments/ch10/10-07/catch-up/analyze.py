"""Offline: every historical anchor, actual tensor and overlapping update is checked."""
import argparse,ctypes,hashlib,json
from pathlib import Path
import torch
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--name',required=True);a=p.parse_args();root=B/a.name
checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)));assert ok,name
def read(p):return json.loads(p.read_text())
def sha(t):
 t=t.contiguous();return hashlib.sha256((ctypes.c_char*(t.numel()*t.element_size())).from_address(t.data_ptr())).hexdigest()
def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]
expected=read(B/'historical/expected.json');paths={};states={};timing=[];execution=read(root/'execution.json')
for mode,start,count in [('from_seed',0,43),('from_fault3',3,40),('from_normal23',23,20)]:
 d=root/mode;env=read(d/'environment.json');r=rows(d/'steps.jsonl');paths[mode]=r;comp=read(d/'completion.json');proc=next(x for x in execution if x['mode']==mode)
 check(mode+'_completed',comp['done'] and comp['updates']==count and len(r)==count and proc['returncode']==0 and not proc['leftovers']);check(mode+'_environment',env['torch']=='2.10.0+cu128' and env['affinity']==[8,9] and env['threads']==1 and env['interop']==1 and env['cuda_visible_devices']=='')
 for name,h in env['source_sha256'].items():check(mode+'_source_'+name,hashlib.sha256((B/name).read_bytes()).hexdigest()==h)
 for i,row in enumerate(r):check(mode+f'_step_{i}_cursor',row['step']==start+i+1 and row['end']>row['start'] and row['update_s']==row['end']-row['start'])
 states[mode]={}
 for f in sorted(d.glob('state-*.pt')):
  step=int(f.stem.split('-')[1]);state=torch.load(f,weights_only=True,map_location='cpu');states[mode][step]=state;hs={k:sha(v) for k,v in state.items()};check(mode+f'_state_{step}_shape',len(state)==11 and state['model.0.weight'].shape==(1024,1024) and state['model.0.weight'].dtype==torch.float32 and int(state['cursor'])==step)
  check(mode+f'_state_{step}_Adam',state['optim.0.step'].item()==step and state['optim.1.step'].item()==step)
  if step in (3,23):check(mode+f'_historical_{step}',hs==expected['checkpoint-1' if step==3 else 'checkpoint-2'])
  if step>start:check(mode+f'_state_{step}_record',hs==next(x for x in r if x['step']==step)['state_sha256'])
 for step,loss in [(23,1.2358448505401611),(43,1.2407095432281494)]:
  selected=[x for x in r if x['step']==step]
  if selected:check(mode+f'_historical_loss_{step}',selected[0]['loss']==loss)
 check(mode+'_update_time_sum',sum(x['update_s'] for x in r)==comp['update_s_sum'])
 timing.append(dict(mode=mode,updates=count,load_s=comp['load']['load_s'] if comp['load'] else None,install_s=comp['install']['end']-comp['install']['start'] if comp['install'] else None,actual_update_s=comp['update_s_sum'],observed_window_s=comp['training_window_s'],first_update_since_process_start_s=comp['first_update_end']-proc['start'],process_wall_s=proc['end']-proc['start']))
base={x['step']:x for x in paths['from_seed']}
for mode in ['from_fault3','from_normal23']:
 for row in paths[mode]:
  ref=base[row['step']]
  for key in ['input_sha256','target_sha256','loss','state_sha256']:check(mode+f'_step{row["step"]}_'+key,row[key]==ref[key])
 for k,v in states['from_seed'][43].items():check(mode+'_tensor43_'+k,torch.equal(v,states[mode][43][k]) and v.dtype==states[mode][43][k].dtype)
resource=read(root/'resources.json');check('resources',max(x['rss_bytes'] for x in resource)<=1024**3 and min(x['mem_available_bytes'] for x in resource)>25*1024**3)
summary=dict(all_passed=True,checks=len(checks),timing=timing,paths=3,actual_updates=103,final_tensors_per_path=11,peak_rss_bytes=max(x['rss_bytes'] for x in resource),min_mem_available_bytes=min(x['mem_available_bytes'] for x in resource),historical_full_state_steps=[3,23],historical_loss_steps=[23,43],new_full_state_reference_step=43)
(root/'checks.json').write_text(json.dumps(checks,indent=2)+'\n');(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
