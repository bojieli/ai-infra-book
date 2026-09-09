"""One real CPU path. Executed only by explicit launch.py --execute."""
import argparse,ctypes,hashlib,json,os,time
from pathlib import Path
B=Path(__file__).resolve().parent

def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def tensor_sha(t):
 t=t.detach().contiguous();return hashlib.sha256((ctypes.c_char*(t.numel()*t.element_size())).from_address(t.data_ptr())).hexdigest()

def main(a):
 started=time.monotonic();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
 spec=json.loads((B/'checkpoint-inputs.json').read_text());historical=Path(a.historical_root)
 for name,expected in spec['files'].items():
  p=historical/name;assert p.stat().st_size==expected['bytes'] and digest(p)==expected['sha256'],name
 import torch
 import torch.distributed.checkpoint as dcp
 assert torch.__version__=='2.10.0+cu128',torch.__version__
 torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.manual_seed(1007)
 model=torch.nn.Sequential(torch.nn.Linear(1024,1024),torch.nn.Tanh(),torch.nn.Dropout(.1));opt=torch.optim.AdamW(model.parameters(),lr=.001);gen=torch.Generator().manual_seed(107)
 assert all(p.dtype==torch.float32 and p.device.type=='cpu' for p in model.parameters());expected=json.loads((B/'historical/expected.json').read_text());checks=[];cursor=0;load=None;install=None
 def check(name,ok):
  checks.append(dict(name=name,passed=bool(ok)));dump(out/'checks.json',checks);assert ok,name
 def snapshot(step):
  s={f'model.{k}':v for k,v in model.state_dict().items()}
  for i,p in enumerate(model.parameters()):
   for k,v in opt.state[p].items():s[f'optim.{i}.{k}']=v
  return dict(s,rng=torch.get_rng_state(),data_rng=gen.get_state(),cursor=torch.tensor(step))
 def hashes(state):return {k:tensor_sha(v) for k,v in state.items()}
 if a.mode!='from_seed':
  cp=historical/('results/fault/checkpoint-1' if a.mode=='from_fault3' else 'results/normal/checkpoint-2')
  t=time.monotonic();meta=dcp.FileSystemReader(cp).read_metadata();target={k:torch.zeros(v.size,dtype=v.properties.dtype) for k,v in meta.state_dict_metadata.items()};template_end=time.monotonic();dcp.load(target,checkpoint_id=cp,no_dist=True);loaded=time.monotonic();load=dict(metadata_and_zero_template_start=t,load_start=template_end,load_end=loaded,load_s=loaded-template_end)
  cursor=int(target['cursor']);check('loaded_cursor',cursor==(3 if a.mode=='from_fault3' else 23));check('loaded_historical_hashes',hashes(target)==expected['checkpoint-1' if cursor==3 else 'checkpoint-2'])
  t=time.monotonic();model.load_state_dict({k:v for k,v in ((name.removeprefix('model.'),value) for name,value in target.items() if name.startswith('model.'))})
  for i,param in enumerate(model.parameters()):
   for key in ['step','exp_avg','exp_avg_sq']:opt.state[param][key]=target[f'optim.{i}.{key}'].clone()
  gen.set_state(target['data_rng']);torch.set_rng_state(target['rng']);install=dict(start=t,end=time.monotonic());check('installed_full_state',hashes(snapshot(cursor))==hashes(target))
  torch.save(snapshot(cursor),out/f'state-{cursor:02}.pt')
 dump(out/'environment.json',dict(mode=a.mode,pid=os.getpid(),pgid=os.getpgrp(),affinity=sorted(os.sched_getaffinity(0)),torch=torch.__version__,threads=torch.get_num_threads(),interop=torch.get_num_interop_threads(),device='cpu',cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),optimizer_groups=[{k:v for k,v in g.items() if k!='params'} for g in opt.param_groups],checkpoint_root=str(historical),start_cursor=cursor,process_entry=started,load=load,install=install,torch_config=torch.__config__.show(),source_sha256={n:digest(B/n) for n in ['run_worker.py','launch.py','PROTOCOL.md','checkpoint-inputs.json','historical/original_run.py']}))
 train_start=time.monotonic();rows=[]
 while cursor<43:
  update_start=time.monotonic();x=torch.randn(16,1024,generator=gen);target=torch.randn(16,1024,generator=gen);opt.zero_grad(set_to_none=True);loss=(model(x)-target).square().mean();loss.backward();opt.step();update_end=time.monotonic();cursor+=1
  state=snapshot(cursor);hs=hashes(state);row=dict(step=cursor,start=update_start,end=update_end,update_s=update_end-update_start,loss=loss.item(),input_sha256=tensor_sha(x),target_sha256=tensor_sha(target),state_sha256=hs)
  rows.append(row)
  with (out/'steps.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  if cursor in (3,23,43):
   torch.save(state,out/f'state-{cursor:02}.pt')
   if cursor in (3,23):check(f'historical_state_{cursor}',hs==expected['checkpoint-1' if cursor==3 else 'checkpoint-2'])
   if cursor==23:check('historical_loss_23',loss.item()==1.2358448505401611)
   if cursor==43:check('historical_loss_43',loss.item()==1.2407095432281494)
 dump(out/'completion.json',dict(done=True,mode=a.mode,pid=os.getpid(),first_step=rows[0]['step'],last_step=43,updates=len(rows),training_window_start=train_start,last_update_end=rows[-1]['end'],training_window_s=rows[-1]['end']-train_start,update_s_sum=sum(r['update_s'] for r in rows),first_update_end=rows[0]['end'],process_entry=started,worker_finish=time.monotonic(),load=load,install=install,all_checks=all(c['passed'] for c in checks)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['from_seed','from_fault3','from_normal23'],required=True);p.add_argument('--output',required=True);p.add_argument('--historical-root',required=True);main(p.parse_args())
