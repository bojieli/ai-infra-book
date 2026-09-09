import hashlib,json,statistics
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent;R=P/'results';env=json.loads((R/'environment.json').read_text());cfg=env['config']
assert env['source_sha256']==hashlib.sha256((P/'run.py').read_bytes()).hexdigest()
assert json.loads((R/'completion.json').read_text())==dict(completed=True,timed_operations=780)
a=np.load(R/'inputs.npz');outputs=np.load(R/'outputs.npz')
packed=a['packed'];codes=((packed[:,:,None]>>np.arange(0,32,4,dtype=np.uint32))&15).reshape(768,2048)
manual=(codes.astype(np.float32)*np.repeat(a['scales'].astype(np.float32),64,axis=1)+np.repeat(a['biases'].astype(np.float32),64,axis=1)).astype(np.float16)
def error(y,ref):
 d=y.astype(np.float64)-ref.astype(np.float64)
 return dict(max_abs=float(np.max(np.abs(d))),rmse=float(np.sqrt(np.mean(d*d))),relative_l2=float(np.linalg.norm(d)/np.linalg.norm(ref)))
decoded=error(a['dequantized'],manual);decoded['passed']=bool(np.allclose(a['dequantized'],manual,atol=cfg['decode_atol'],rtol=cfg['decode_rtol']))
quality=[]
for batch in cfg['batches']:
 ref=a['x32'][:batch].astype(np.float16).astype(np.float64)@a['dequantized'].astype(np.float64).T
 original=a['x32'][:batch].astype(np.float64)@a['w32'].astype(np.float64).T
 for name in ['direct','cached_expanded_matmul','decode_matmul','cast_direct','cast_decode_matmul']:
  y=outputs[f'{name}_{batch}'];quality.append(dict(batch=batch,operation=name,same_quant_reference=error(y,ref),original_fp32_reference=error(y,original),passed=bool(np.allclose(y,ref,atol=cfg['atol'],rtol=cfg['rtol']))))
np.savez(R/'independent-decode.npz',decoded=manual)
(R/'quality.json').write_text(json.dumps(dict(independent_decode=decoded,outputs=quality),indent=2)+'\n')
rows=[json.loads(x) for x in (R/'timings.jsonl').read_text().splitlines()];assert len(rows)==780
summary=[]
for name,batch in sorted({(r['operation'],r['batch']) for r in rows}):
 g=[r for r in rows if r['operation']==name and r['batch']==batch];assert sorted(r['trial'] for r in g)==list(range(30))
 for r in g:assert r['end_ns']-r['start_ns']==r['elapsed_ns']>0
 summary.append(dict(operation=name,batch=batch,median_ms=statistics.median(r['elapsed_ns']/1e6 for r in g),min_ms=min(r['elapsed_ns']/1e6 for r in g),max_ms=max(r['elapsed_ns']/1e6 for r in g),median_peak_increment_bytes=statistics.median(r['peak']-r['active_before'] for r in g)))
(R/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Independent decode:',decoded);print('Output gates:',sum(r['passed'] for r in quality),'/',len(quality))
for r in summary:print(r)
