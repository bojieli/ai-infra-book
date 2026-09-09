#!/usr/bin/env python3
"""Analyze transferred completed run; --recompute independently rebuilds FP64 oracle."""
import os
for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='4'
import pathlib,json,hashlib,argparse
import numpy as np
from reference import metrics,reference
B=pathlib.Path(__file__).resolve().parent;R=B/'results'
ap=argparse.ArgumentParser();ap.add_argument('--recompute',action='store_true');args=ap.parse_args()
sup=json.loads((R/'supervisor.json').read_text());assert sup['exit_code']==0,sup
cases=json.loads((R/'cases.json').read_text());summary={};errs={};failures=[]
raw=np.load(R/'raw_checkpoint.npz')
manifest=json.loads((R/'selected_tensors.json').read_text())
for ent in manifest:
 name=f"{ent['local_expert']}_{ent['key'].split('.')[-2]}_{ent['key'].split('.')[-1]}"
 assert hashlib.sha256(raw[name].tobytes()).hexdigest()==ent['raw_sha256']
assembled=np.load(R/'assembled.npz')
for key in ['w13_packed','w2_packed','w13_scale','w2_scale']:
 parts=[]
 for e in range(6):
  kind='weight' if key.endswith('packed') else 'scale'
  a=np.concatenate([raw[f'{e}_w1_{kind}'],raw[f'{e}_w3_{kind}']],axis=0) if key.startswith('w13') else raw[f'{e}_w2_{kind}']
  if kind=='scale':
   from reference import E8
   a=E8[a].astype(np.float32)
  parts.append(a)
 assert np.array_equal(np.stack(parts),assembled[key]),key
for source in json.loads((R/'source_hashes.json').read_text()):
 assert hashlib.sha256((R/'sources'/pathlib.Path(source['path']).name).read_bytes()).hexdigest()==source['sha256']
for name,cfg in cases.items():
 d=np.load(R/f'{name}.npz');y=d['output'].astype(np.float64);r=d['reference'];recompute_equal=None
 if args.recompute:
  oracle=reference(d['input'].astype(np.float64),d['ids'],d['routing'],raw,cfg['H'],cfg['I'],cfg['clamp'],cfg['factor'])
  recompute_equal={k:bool(np.array_equal(v,d[k])) for k,v in oracle.items()}
 summary[name]=metrics(y,r);summary[name]['recomputed_stages_equal']=recompute_equal
 errs[name+'_signed']=y-r;errs[name+'_tolerance']=.02*np.abs(r)+.002*np.sqrt(np.mean(r*r))
 # Include differences even for passing elements, not just aggregate statistics.
 errs[name+'_failed']=(np.abs(y-r)>errs[name+'_tolerance'])|~np.isfinite(y)|~np.isfinite(r)
 for i,j in summary[name]['failing_indices']:
  tol=float(errs[name+'_tolerance'][i,j])
  failures.append(dict(case=name,token=i,channel=j,output=float(y[i,j]),reference=float(r[i,j]),signed_error=float(y[i,j]-r[i,j]),tolerance=tol,error_over_tolerance=float(abs(y[i,j]-r[i,j])/tol)))
np.savez(R/'all_element_errors.npz',**errs)
(R/'failures.json').write_text(json.dumps(failures,indent=2))
def out(n):return np.load(R/f'{n}.npz')['output']
controls=dict(zero_routes_exact_zero=bool(np.all(out('zero_routes')==0)),padded_equals_zeroed=bool(np.array_equal(out('padded_slot'),out('zero_slot'))),slot_permutation_bitwise=bool(np.array_equal(out('permuted_slots'),out('main_m8'))))
for name in ['offloader','profile']:
 f=R/f'{name}_output.npy'
 controls[name+'_bitwise']=bool(np.array_equal(np.load(f),out('main_m8'))) if f.exists() else None
act=np.load(R/'active_clamp.npz')['first'];I=cases['active_clamp']['I']
clamp_counts=dict(gate_above=int((act[:,:,:I]>.005).sum()),gate_below_negative_limit_not_clamped=int((act[:,:,:I]<-.005).sum()),up_above=int((act[:,:,I:]>.005).sum()),up_below=int((act[:,:,I:]<-.005).sum()))
kernels=[]
if (R/'profile.json').exists():
 trace=json.loads((R/'profile.json').read_text())
 from collections import Counter
 cnt=Counter(e.get('name') for e in trace['traceEvents'] if e.get('cat')=='kernel')
 kernels=[dict(name=k,count=v) for k,v in cnt.items()]
(R/'kernel_events.json').write_text(json.dumps(kernels,indent=2))
report=dict(cases=summary,controls=controls,active_clamp_counts=clamp_counts,all_numerical_cases_pass=all(v['pass_criteria'] for v in summary.values()),all_exact_controls_pass=all(v is True for v in controls.values()),peak_gpu_mib=sup['peak_gpu_mib'],peak_rss_tree_bytes=sup['peak_rss_tree_bytes'],exit_code=sup['exit_code'])
(R/'analysis.json').write_text(json.dumps(report,indent=2,allow_nan=False))
lines=['| Case | relative L2 | max abs | failing elements | pass |','|---|---:|---:|---:|---|']
for n,v in summary.items():lines.append(f"| {n} | {v['relative_l2']:.6g} | {v['max_abs']:.6g} | {v['bad_elements']}/{v['elements']} | {v['pass_criteria']} |")
(R/'summary.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(report,indent=2))
