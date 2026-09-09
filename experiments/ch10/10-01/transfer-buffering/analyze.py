import array,hashlib,json,statistics
from pathlib import Path
import torch
R=Path(__file__).resolve().parent;D=R/'results';env=json.loads((D/'environment.json').read_text())
assert hashlib.sha256((R/'run.py').read_bytes()).hexdigest()==env['source_sha256']
assert json.loads((D/'completion.json').read_text())==dict(status='complete',groups=27,blocks=216)
fixture=torch.load(D/'fixture.pt',weights_only=True);assert fixture['shape']==[8192,4096]
def repeated_sha(row):
 b=array.array('h',row.view(torch.int16).tolist()).tobytes();h=hashlib.sha256()
 for _ in range(8192):h.update(b)
 return h.hexdigest()
for i,row in enumerate(fixture['input_rows']):
 expected=(row.double()*torch.rsqrt(row.double().square().mean()+1e-6)).to(torch.bfloat16)
 assert torch.equal(expected,fixture['reference_rows'][i])
 assert repeated_sha(row)==env['source_input_sha256'][i]
 assert repeated_sha(expected)==env['reference_sha256'][i]
raw=json.loads((D/'raw.json').read_text());assert len(raw)==27
assert len(set(env['reference_sha256']))==8
formal=[r for r in raw if r['kind']=='formal'];assert len(formal)==21
assert [(r['policy'],r['trial']) for r in formal]==[tuple(x) for x in json.loads((D/'order.json').read_text())]
def intersection(a,b):return max(0,min(a[1],b[1])-max(a[0],b[0]))
for r in raw:
 assert len(r['quality'])==len(r['stages'])==8 and r['wall_ms']>0
 for q in r['quality']:
  assert q['passed'] and q['max_abs']<=1/128
  assert q['exact'] and q['sha256']==q['reference_sha256']==env['reference_sha256'][q['block']]
 stages=r['stages'];assert [s['block'] for s in stages]==list(range(8))
 for i,s in enumerate(stages):
  assert s['wait_start_ns']<=s['prepare_start_ns']<=s['prepared_ns']
  assert s['h2d_start_ms']<=s['h2d_end_ms']<=s['consume_start_ms']<=s['consume_end_ms']
  prior=i-r['device_slots']
  if prior>=0:assert s['h2d_start_ms']+0.001>=stages[prior]['consume_end_ms']
 r['event_overlap_ms']=sum(intersection((a['h2d_start_ms'],a['h2d_end_ms']),(b['consume_start_ms'],b['consume_end_ms'])) for a in stages for b in stages)
summary=[];traces=[]
for policy in ['serial','one_device','double']:
 rs=[r for r in formal if r['policy']==policy];assert sorted(r['trial'] for r in rs)==list(range(7))
 summary.append(dict(policy=policy,median_wall_ms=statistics.median(r['wall_ms'] for r in rs),median_h2d_sum_ms=statistics.median(sum(s['h2d_end_ms']-s['h2d_start_ms'] for s in r['stages']) for r in rs),median_consume_sum_ms=statistics.median(sum(s['consume_end_ms']-s['consume_start_ms'] for s in r['stages']) for r in rs),median_event_overlap_ms=statistics.median(r['event_overlap_ms'] for r in rs),pinned_live_bytes=rs[0]['pinned_live_bytes'],device_input_bytes=rs[0]['device_input_bytes'],scratch_bytes=rs[0]['scratch_bytes'],retained_output_bytes=rs[0]['retained_output_bytes'],peak_allocated_bytes=max(r['peak_allocated'] for r in rs)))
 events=json.loads((D/f'{policy}-trace.json').read_text())['traceEvents']
 copies=[e for e in events if e.get('cat')=='gpu_memcpy' and e.get('name')=='Memcpy HtoD (Pinned -> Device)'];kernels=[e for e in events if e.get('cat')=='kernel']
 assert len(copies)==8 and all(e['args']['bytes']==64*2**20 for e in copies)
 assert kernels
 prepares=[e for e in events if e.get('ph')=='X' and e.get('name','').startswith('cpu_prepare_')];assert len(prepares)==8
 cpu_overlap=sum(intersection((a['ts'],a['ts']+a['dur']),(b['ts'],b['ts']+b['dur'])) for a in copies for b in prepares)/1000
 overlap=sum(intersection((a['ts'],a['ts']+a['dur']),(b['ts'],b['ts']+b['dur'])) for a in copies for b in kernels)/1000
 traces.append(dict(policy=policy,h2d_calls=len(copies),kernel_calls=len(kernels),actual_h2d_kernel_overlap_ms=overlap,cpu_prepare_h2d_overlap_ms=cpu_overlap))
report=dict(status='passed',all_blocks_exact=216,formal_groups=21,summary=summary,profiler=traces,scope='Shared GPU; event ranges and actual kernel overlap distinguished; validation D2H excluded from measured wall')
(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
