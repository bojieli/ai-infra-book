"""Independent all-element reference and saved sharding/IR checks."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np

def main(root):
 raw=json.loads((root/'raw.json').read_text()); assert len(raw)==8
 done=json.loads((root/'completion.json').read_text());assert done==dict(status='complete',conditions=8,samples=40)
 env=json.loads((root/'environment.json').read_text());h=env['hidden'];i=env['intermediate']
 assert env['source_sha256']==hashlib.sha256((root/'run-source.py').read_bytes()).hexdigest()
 f=np.load(root/'inputs.npz'); refs={}
 for n in (8,32):
  x=f[f'x{n}'].astype(np.float64)
  gate=x@f['g'].astype(np.float64); up=x@f['u'].astype(np.float64)
  refs[n]=((gate/(1+np.exp(-gate)))*up)@f['d'].astype(np.float64)
 rows=[]
 assert {(r['tokens'],r['tp'],r['policy']) for r in raw}=={(n,p,k) for n in (8,32) for p in (2,4) for k in ('tp','sp')}
 for r in raw:
  n,p,k=r['tokens'],r['tp'],r['policy']; got=np.load(root/f"{r['name']}.npy")
  assert got.shape==(n,h) and got.dtype==np.float32
  assert np.allclose(got,refs[n],atol=1e-4,rtol=1e-3),r['name']
  expected={'x':(n//p if k=='sp' else n,h),'gate':(h,i//p),'up':(h,i//p),'down':(i//p,h)}
  for name,shape in expected.items():
   shards=r['input_shards'][name];assert len(shards)==p
   assert all(tuple(s['shape'])==shape and s['bytes']==np.prod(shape)*4 for s in shards)
  assert len(r['output_shards'])==p
  assert all(tuple(s['shape'])==expected['x'] for s in r['output_shards'])
  text=(root/f"{r['name']}.stablehlo.txt").read_text()
  counts={s:text.count('stablehlo.'+s) for s in ('all_gather','all_reduce','reduce_scatter')}
  assert counts==({'all_gather':1,'all_reduce':0,'reduce_scatter':1} if k=='sp' else {'all_gather':0,'all_reduce':1,'reduce_scatter':0}),counts
  assert len(r['times_s'])==5 and all(t>0 for t in r['times_s'])
  rows.append(dict(name=r['name'],max_abs=float(np.max(np.abs(got-refs[n]))),relative_l2=float(np.linalg.norm(got-refs[n])/np.linalg.norm(refs[n])),median_ms=float(np.median(r['times_s'])*1000),collectives=counts,activation_bytes_per_rank=r['output_shards'][0]['bytes']))
 summary=dict(status='passed',conditions=len(rows),scope='CPU logical devices; FFN sublayer; random weights; no GPU scaling or model quality claim',results=rows)
 (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);main(p.parse_args().directory)
