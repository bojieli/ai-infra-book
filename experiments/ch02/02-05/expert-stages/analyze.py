#!/usr/bin/env python3
"""CPU-only analysis after raw execution AND transfer exit. Never imports Torch."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='4'
import sys,pathlib,json,hashlib,time
import numpy as np
B=pathlib.Path(__file__).resolve().parent; O=B/'results'; P=B.parent/'expert-preflight';R=P/'results'
sys.dont_write_bytecode=True;sys.path.insert(0,str(P))
from reference import reference,bf,dequant,metrics
A=B/'analysis';A.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(n,x):(A/n).write_text(json.dumps(x,indent=2,allow_nan=False))
assert json.loads((O/'supervisor.json').read_text())['exit_code']==0
assert json.loads((B/'transfer.json').read_text())['exit_code']==0
for rec in json.loads((O/'raw_manifest.json').read_text()):assert sha(B/rec['path'])==rec['sha256']
for rec in json.loads((O/'input_sources.json').read_text()):
 p=pathlib.Path(rec['path']); local=P/p.relative_to('/home/ubuntu/ai-infra-book-experiments/ch02/02-05/expert-preflight') if '/expert-preflight/' in str(p) else O/p.name
 assert sha(local)==rec['sha256'],str(local)
s=np.load(O/'stages.npz');old=np.load(R/'main_m8.npz');raw=np.load(R/'raw_checkpoint.npz')
x=s['input'];ids=s['ids'];routing=s['routing']; M,T=ids.shape;I=2048;H=4096
assert x.tobytes()==old['input'].tobytes() and ids.tobytes()==old['ids'].tobytes() and routing.tobytes()==old['routing'].tobytes()
g={k:s[k].astype(np.float64).reshape(M,T,-1) for k in ['first','activated','down','masked','product']}
g['reduce']=s['reduce'].astype(np.float64);g['output']=s['output'].astype(np.float64)
r=reference(x,ids,routing,raw,H,I,10.,1.5)
assert all(np.array_equal(r[k],old[k]) for k in r)
r['masked']=r['down'];r['reduce']=bf(r['product'].sum(1));r['output']=r['reference']
def act(first):
 gate=np.minimum(first[:,:,:I],10.);up=np.clip(first[:,:,I:],-10.,10.)
 return bf(gate/(1+np.exp(-gate))*up)
def down(a):
 out=np.zeros((M,T,H))
 for e in range(6):
  rows,slots=np.where(ids==e);d=dequant(raw[f'{e}_w2_weight'],raw[f'{e}_w2_scale'])
  out[rows,slots]=bf(a[rows,slots]@d.T)
 return out
def product(d):return bf(bf(d*(ids>=0)[:,:,None])*bf(routing)[:,:,None])
def finish(p):return bf(bf(p.sum(1))*1.5)
local={'first':r['first'],'activated':act(g['first']),'down':down(g['activated']),'masked':bf(g['down']*(ids>=0)[:,:,None]),'product':bf(g['masked']*bf(routing)[:,:,None]),'reduce':bf(g['product'].sum(1)),'output':bf(g['reduce']*1.5)}
# Ordered interventions: use observed boundary, then original FP64 suffix.
# Consecutive differences telescope exactly; order-dependent causal bookkeeping.
hy={'reference':r['output'],'first':finish(product(down(act(g['first'])))), 'activated':finish(product(local['down'])),'down':finish(product(g['down'])),'masked':finish(bf(g['masked']*bf(routing)[:,:,None])),'product':finish(g['product']),'reduce':bf(g['reduce']*1.5),'output':g['output']}
report={}
for k in g:
 report[k]=dict(vs_original_fp64=metrics(g[k],r[k]),vs_cpu_from_actual_previous=metrics(g[k],local[k]),different_from_original=int(np.count_nonzero(g[k]!=r[k])),different_from_local=int(np.count_nonzero(g[k]!=local[k])))
np.savez(A/'cpu_stages.npz',**{f'ref_{k}':r[k] for k in g},**{f'local_{k}':v for k,v in local.items()},**{f'suffix_{k}':v for k,v in hy.items()})
tol=.02*np.abs(r['output'])+.002*np.sqrt(np.mean(r['output']**2));err=g['output']-r['output']
np.savez(A/'element_errors.npz',error=err,tolerance=tol,fail=np.abs(err)>tol,old_error=old['output']-r['output'])
failures=[]
for f in json.loads((R/'failures.json').read_text()):
 if f['case']!='main_m8':continue
 m,c=f['token'],f['channel']; rec=dict(old=f,new_output=float(g['output'][m,c]),new_fails=bool(abs(err[m,c])>tol[m,c]),suffix_outputs={k:float(v[m,c]) for k,v in hy.items()},increments={},slots=[])
 prev=hy['reference'][m,c]
 for k,v in list(hy.items())[1:]:rec['increments'][k]=float(v[m,c]-prev);prev=v[m,c]
 assert sum(rec['increments'].values())==float(err[m,c])
 for slot in range(T):
  rec['slots'].append(dict(slot=slot,expert=int(ids[m,slot]),routing=float(routing[m,slot]),stages={k:dict(reference=float(r[k][m,slot,c]),actual=float(g[k][m,slot,c]),cpu_from_actual_previous=float(local[k][m,slot,c])) for k in ['down','masked','product']},first_differing_channels=np.flatnonzero(g['first'][m,slot]!=r['first'][m,slot]).tolist(),activation_local_differing_channels=np.flatnonzero(g['activated'][m,slot]!=local['activated'][m,slot]).tolist()))
 failures.append(rec)
js('failures.json',failures)
# Exact FP64 sums at discrepant projection stores, with BF16 adjacent bracket.
projection=[]
for e in range(6):
 rows,slots=np.where(ids==e)
 for stage,names,a in [('first',['w1','w3'],x[rows].astype(np.float64)),('down',['w2'],g['activated'][rows,slots])]:
  for j,name in enumerate(names):
   d=dequant(raw[f'{e}_{name}_weight'],raw[f'{e}_{name}_scale']);exact=a@d.T; offset=j*I if stage=='first' else 0
   actual=g[stage][rows,slots,offset:offset+exact.shape[1]];cpu=bf(exact)
   for row,ch in np.argwhere(actual!=cpu):
    av=float(actual[row,ch]);cv=float(cpu[row,ch]);ev=float(exact[row,ch]);mid=(av+cv)/2
    projection.append(dict(stage=stage,token=int(rows[row]),slot=int(slots[row]),expert=e,channel=int(ch+offset),exact_fp64=ev,cpu_bf16=cv,gpu_bf16=av,midpoint=mid,exact_minus_midpoint=ev-mid,gpu_minus_cpu=av-cv))
js('projection_discrepancies.json',projection)
plain=np.load(O/'plain_output.npy')
summary=dict(analysis_time=time.time(),original_reference_recomputed_equal=True,input_equal=True,old_output_bitwise_equal=s['output'].tobytes()==old['output'].tobytes(),old_output_different_elements=int(np.count_nonzero(s['output']!=old['output'])),unobserved_output_bitwise_equal=plain.tobytes()==s['output'].tobytes(),numerical=metrics(g['output'],r['output']),stages=report,hybrid_numerical={k:metrics(v,r['output']) for k,v in hy.items()},projection_discrepancies=len(projection),limitations=['Ordered suffix increments depend on intervention order; not a unique additive physical attribution.','FP32 internal GEMV accumulators and old autotune config were not captured; no proof of instruction-level root cause.','Stage metrics reuse fixed formula descriptively; final original FP64 criteria determine pass/fail.'])
js('summary.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k not in ['stages','hybrid_numerical']},indent=2))
# Local activation discrepancies: independent one-coordinate interventions.
activation_records=[]; baseline=hy['first']; joint=hy['activated']
for m,slot,ch in np.argwhere(g['activated']!=local['activated']):
 gate=float(g['first'][m,slot,ch]);up=float(g['first'][m,slot,ch+I]);exact=gate/(1+np.exp(-gate))*up
 gate32=np.float32(gate);up32=np.float32(up)
 silu32=np.float32(gate32/np.float32(1+np.exp(-gate32)));p32=np.float32(silu32*up32)
 a=local['activated'].copy();a[m,slot,ch]=g['activated'][m,slot,ch]
 out=finish(product(down(a)))
 links=[]
 for f in failures:
  t,c=f['old']['token'],f['old']['channel'];delta=float(out[t,c]-baseline[t,c])
  if delta:links.append(dict(token=t,channel=c,output_delta=delta,joint_delta=float(joint[t,c]-baseline[t,c])))
 activation_records.append(dict(token=int(m),slot=int(slot),expert=int(ids[m,slot]),channel=int(ch),gate=gate,up=up,fp64_pre_store=float(exact),cpu_fp64_boundary=float(local['activated'][m,slot,ch]),actual_boundary=float(g['activated'][m,slot,ch]),numpy_fp32_silu=float(silu32),numpy_fp32_product=float(p32),numpy_fp32_boundary=float(bf(p32)),failed_output_links=links))
js('activation_discrepancies.json',activation_records)
print('ACTIVATION',json.dumps(activation_records,indent=2))
