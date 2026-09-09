"""Independent raw tensor, saved-reference and allocator-event checks."""
import argparse,collections,json,pickle
from pathlib import Path
import torch
ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();r=args.run/'rank-0';checks=0
x=torch.load(r/'elementwise.pt',map_location='cpu',weights_only=True);maximum=0.;exact_grad=exact_updated=0
for name,p in x['parameters'].items():
 for a,b in [('gradient','reference_gradient'),('updated','reference_updated')]:
  assert p[a].shape==p[b].shape and torch.isfinite(p[a]).all() and torch.isfinite(p[b]).all()
  diff=(p[a]-p[b]).abs();assert torch.all(diff<=1e-6+1e-5*p[b].abs());maximum=max(maximum,diff.max().item());checks+=1
 exact_grad+=int(torch.equal(p['gradient'],p['reference_gradient']));exact_updated+=int(torch.equal(p['updated'],p['reference_updated']))
 assert torch.all((p['updated']-(p['initial']-.01*p['gradient'])).abs()<=1e-6+1e-5*p['updated'].abs());checks+=1
assert len(x['outputs'])==8
for i,y in x['outputs']:
 assert torch.equal(y,x['reference_outputs'][i]);checks+=1
rows=[json.loads(t) for t in (r/'lifetime.jsonl').read_text().splitlines()];ids={};refs=collections.Counter();sizes={};points=[];saved=released=unpacked=0;start=rows[0]['host_monotonic_ns'];mb=[];begins={}
for e in rows:
 kind=e['kind']
 if kind=='autograd_save':
  assert e['id'] not in ids;ids[e['id']]=e;saved+=1
  if not e['parameter_storage']:
   ptr=e['storage_ptr'];refs[ptr]+=1;sizes[ptr]=e['storage_bytes']
 elif kind=='autograd_release':
  old=ids.pop(e['id']);released+=1
  if not old['parameter_storage']:
   refs[old['storage_ptr']]-=1;assert refs[old['storage_ptr']]>=0
 elif kind=='autograd_unpack':assert e['id'] in ids;unpacked+=1
 elif kind=='forward_begin':begins[e['microbatch']]=e['host_monotonic_ns']
 elif kind=='forward_end':mb.append(dict(microbatch=e['microbatch'],start_ms=(begins[e['microbatch']]-start)/1e6,end_ms=(e['host_monotonic_ns']-start)/1e6))
 points.append([(e['host_monotonic_ns']-start)/1e6,sum(sizes[p] for p,n in refs.items() if n>0)])
 checks+=1
assert not ids and saved==released and len(mb)==8
snap=pickle.load((r/'allocator_snapshot.pickle').open('rb'));actions=collections.Counter(e['action'] for d in snap['device_traces'] for e in d)
trace=json.loads((r/'trace.json').read_text());kernels=[e for e in trace['traceEvents'] if e.get('cat')=='kernel' and e.get('ph')=='X'];base=min(e['ts'] for e in kernels)
report=json.loads((r/'checks.json').read_text());assert report['finite'] and report['output_ok'];checks+=1
result=dict(checks=checks,parameter_tensors=len(x['parameters']),parameter_elements=sum(p['initial'].numel() for p in x['parameters'].values()),gradient_exact_tensors=exact_grad,updated_exact_tensors=exact_updated,max_tensor_abs_error=maximum,outputs_exact=8,saved=saved,unpacked=unpacked,released=released,final_saved_references=0,peak_saved_nonparameter_storage_bytes=max(p[1] for p in points),saved_reference_curve=points,host_forward_intervals=mb,cuda_kernel_count=len(kernels),cuda_kernel_sum_ms=sum(e['dur'] for e in kernels)/1000,cuda_kernel_span_ms=(max(e['ts']+e['dur'] for e in kernels)-base)/1000,cuda_kernel_intervals_ms=[[(e['ts']-base)/1000,e['dur']/1000] for e in kernels],allocator_actions=dict(actions),allocator_final_segments=len(snap['segments']),cuda_peak_allocated_bytes=report['cuda_peak_allocated_bytes'],cuda_peak_reserved_bytes=report['cuda_peak_reserved_bytes'],scope='Single-process official no-pipeline GPU baseline; nonparameter saved storages include input views; host and GPU clocks not aligned; reference release is not allocator free or driver return.')
args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['saved_reference_curve','host_forward_intervals','cuda_kernel_intervals_ms']}))
