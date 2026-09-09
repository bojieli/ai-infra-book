"""Reconstruct real rank shards and compare with independent global-batch AdamW."""
import json,hashlib
from pathlib import Path
import torch
from model import FFN,data
R=Path(__file__).resolve().parent
torch.set_num_threads(1);torch.manual_seed(1001);model=FFN();opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.01,foreach=False)
refs=[]
for step in range(3):
 opt.zero_grad(set_to_none=True);x,y=data(step);loss=(model(x)-y).square().mean();loss.backward();opt.step();row={}
 for name,param in model.named_parameters():
  row['param/'+name]=param.detach().clone();row['grad/'+name]=param.grad.detach().clone()
  for key,v in opt.state[param].items():row['optimizer/'+name+'/'+key]=v.detach().clone() if torch.is_tensor(v) else v
 refs.append(row)
torch.save(refs,R/'reference.pt')
executions=json.loads((R/'results/execution.json').read_text());assert len(executions)==4
reports=[]
for c in executions:
 assert c['exit_code']==0
 world=c['world'];case=R/'results'/f"world{world}-reshard{c['reshard']}";checks=[];memory=[]
 for rank in range(world):
  root=case/f'rank{rank}';done=json.loads((root/'completion.json').read_text());assert done['status']=='complete' and done['steps']==3
  assert all(hashlib.sha256((R/k).read_bytes()).hexdigest()==v for k,v in done['source_sha256'].items())
  snapshots=json.loads((root/'snapshots.json').read_text());assert len(snapshots)==16
  for s in snapshots:
   for t in s['states']:
    if t['name'].startswith('param/'):
     expected=t['global_shape'].copy()
     if s['stage']!='inside_forward' and not (s['stage']=='after_forward' and not c['reshard']):expected[0]//=world
     assert t['local_shape']==expected,(case,rank,s['stage'],t)
  events=json.loads((root/'trace.json').read_text())['traceEvents'];allocs=[e for e in events if e.get('name')=='[memory]'];assert allocs
  regions=[e for e in events if e.get('ph')=='X' and e.get('name','').startswith('training_step_')]
  training_allocs=[e for e in allocs if any(r['ts']<=e['ts']<=r['ts']+r['dur'] for r in regions)];assert training_allocs
  names=sorted({e.get('name','') for e in events if any(k in e.get('name','').lower() for k in ['allgather','all_gather','reduce_scatter','reduce-scatter'])})
  memory.append(dict(rank=rank,max_profiler_total_allocated=max(e['args']['Total Allocated'] for e in allocs),training_region_peak_bytes=max(e['args']['Total Allocated'] for e in training_allocs),max_visible_storage=max(s['unique_visible_storage_bytes'] for s in snapshots),collective_event_names=names,snapshots=[{k:s[k] for k in ['stage','step','unique_visible_storage_bytes']} for s in snapshots]))
 for step in range(3):
  shards=[torch.load(case/f'rank{r}'/f'step{step}.pt',weights_only=True) for r in range(world)]
  assert all(set(sh)==set(refs[step]) for sh in shards)
  worst=0.;worst_key=None
  for key,expected in refs[step].items():
   if expected.ndim==0:
    assert all(torch.equal(sh[key],expected) for sh in shards);actual=shards[0][key]
   else:actual=torch.cat([sh[key] for sh in shards],dim=0)
   assert actual.shape==expected.shape
   err=float((actual-expected).abs().max())
   if err>worst:worst=err;worst_key=key
   torch.testing.assert_close(actual,expected,atol=2e-6,rtol=1e-4,msg=lambda m:key+' '+m)
  checks.append(dict(step=step,tensors_checked=len(refs[step]),max_abs=worst,worst_key=worst_key))
 reports.append(dict(world=world,reshard=bool(c['reshard']),checks=checks,memory=memory))
summary=dict(status='passed',cases=reports,scope='Actual CPU FSDP2; profiler tracked allocations include evidence serialization; no GPU peak or performance claim')
(R/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps([{k:r[k] for k in ['world','reshard','checks']} for r in reports],indent=2))
