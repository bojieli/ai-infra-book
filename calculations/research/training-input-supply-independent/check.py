"""Independent packing, serialization, capacity and event invariants; research only."""
from pathlib import Path
from fractions import Fraction as F
import importlib.util,sys,json,hashlib,itertools
HERE=Path(__file__).resolve().parent;CALC=HERE.parents[1];CAND=CALC/'research/training-input-supply'
spec=importlib.util.spec_from_file_location('supply_candidate',CAND/'calculate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from infra_calc.sources import model_config
checks=[]
def check(label,ok):
 checks.append({'check':label,'passed':bool(ok)})
 assert ok,label
c=model_config('qwen3-8b');H=c['hidden_size'];L=c['num_hidden_layers'];D=c['head_dim'];Q=c['num_attention_heads']*D;K=c['num_key_value_heads']*D;V=c['vocab_size'];W=c['intermediate_size']
P=2*H*V+L*(2*H*Q+2*H*K+3*H*W+2*H+2*D)+H
check('Independent official parameter formula',P==8190735360)
# One host/device slot with 1s R,P,H,C per full pack: C ends 4,7,10,13.
args=dict(samples=[dict(tokens=1,stored_bytes=21,cpu_ns=10**9) for _ in range(4)],pack_tokens=1,host_slots=1,device_slots=1,storage_bytes_per_second=21,h2d_bytes_per_second=21,packing_ns=0,consume_ns=10**9,checkpoint_every=0)
r=m.calculate(**args);e={x['id']:x for x in r['events']}
check('Independent no-checkpoint four-pack timeline',[F(e[f'C{i}']['end_exact']) for i in range(4)]==[4,7,10,13])
check('Device residual startup and input wait',F(r['summary']['device_wait_exact'])==9)
# Nontrivial next-fit sample order: [3,2] / [4] / [2,1], no bin-packing reordering.
r=m.calculate(samples=[dict(tokens=t,stored_bytes=t+7,cpu_ns=t*19) for t in [3,2,4,2,1]],pack_tokens=5,checkpoint_every=0)
check('Independent next-fit identities',[p['samples'] for p in r['packs']]==[[0,1],[2],[3,4]])
check('21B includes padding',r['summary']['h2d_bytes']==3*5*21 and r['summary']['padding_tokens']==3)
for shared,hs,ds,ss,every in itertools.product([True,False],[1,2],[1,3],[1,2],[0,1,3]):
 kw=dict(shared_storage=shared,host_slots=hs,device_slots=ds,snapshot_slots=ss,checkpoint_every=every)
 r=m.calculate(**kw);tag=str(tuple(kw.values()));events={x['id']:x for x in r['events']};s=r['summary'];n=s['packs']
 check(tag+' exact checkpoint layout',s['checkpoint_bytes_each']==14*P and s['checkpoint_write_bytes']==(n//every if every else 0)*14*P)
 check(tag+' no sample loss',[i for p in r['packs'] for i in p['samples']]==list(range(s['samples'])))
 check(tag+' storage byte conservation',sum(F(x['service_exact'])*r['scenario']['storage_bytes_per_second'] for x in events.values() if x['id'].startswith('R'))==s['input_storage_bytes'])
 for name,x in events.items():
  start,end=F(x['start_exact']),F(x['end_exact'])
  check(tag+name+' exact duration',end-start==F(x['service_exact']))
  check(tag+name+' dependencies',all(start>=F(events[d]['end_exact']) for d in x['deps']))
 for resource in {x['resource'] for x in events.values()}:
  jobs=sorted((F(x['start_exact']),F(x['end_exact'])) for x in events.values() if x['resource']==resource and F(x['end_exact'])>F(x['start_exact']))
  check(tag+resource+' exclusive',all(a[1]<=b[0] for a,b in zip(jobs,jobs[1:])))
 for pool,slots in [('host',hs),('device',ds),('snapshot',ss)]:
  rows=r['lifetimes'][pool];points=sorted({F(x[k]) for x in rows for k in ['start_exact','end_exact']})
  peak=0;area=F(0)
  for a,b in zip(points,points[1:]):
   active=[x for x in rows if F(x['start_exact'])<=(a+b)/2<F(x['end_exact'])];value=sum(x['bytes'] for x in active)
   peak=max(peak,value);area+=value*(b-a)
   check(tag+pool+str(a)+' finite slots',len(active)<=slots)
  check(tag+pool+' independent peak and integral',peak==r['buffers'][pool]['peak_reserved_bytes'] and area==F(r['buffers'][pool]['byte_seconds_exact']))
 check(tag+' device time decomposition',F(s['training_end_exact'])==F(s['device_compute_service_exact'])+F(s['snapshot_service_before_training_end_exact'])+F(s['device_wait_exact']))
 check(tag+' training and durable separate',F(s['all_durable_exact'])>=F(s['training_end_exact']))
# Completed-zero services are legitimate but rates/slots remain strictly positive.
r=m.calculate(packing_ns=0,consume_ns=0,snapshot_ns=0)
check('Zero consumption no infinite target',r['summary']['target_sample_rate_exact'] is None)
for kw in [dict(shared_storage=1),dict(host_slots=True),dict(storage_bytes_per_second=0),dict(pack_tokens=2,samples=[dict(tokens=3,stored_bytes=1,cpu_ns=0)])]:
 try:m.calculate(**kw)
 except ValueError:check('reject '+str(kw),True)
 else:check('reject '+str(kw),False)
for scene in json.loads((CAND/'scenarios.json').read_text()):
 r=m.calculate(**{k:v for k,v in scene.items() if k!='id'});check(scene['id']+' replay',r==json.loads((CAND/'results'/(scene['id']+'.json')).read_text()))
raw=(CAND/'calculate.py').read_bytes();(HERE/'candidate.snapshot.py').write_bytes(raw)
output=dict(candidate_sha256=hashlib.sha256(raw).hexdigest(),parameter_formula=P,checks=len(checks),passed=sum(x['passed'] for x in checks),failed=[x for x in checks if not x['passed']])
(HERE/'verification.json').write_text(json.dumps(output,indent=2)+'\n');(HERE/'checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(output,indent=2))
