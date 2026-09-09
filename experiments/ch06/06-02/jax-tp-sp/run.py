"""Actual XLA CPU collectives; no network simulator or GPU speed claim."""
import os
os.environ['JAX_PLATFORMS']='cpu'
os.environ['XLA_FLAGS']='--xla_force_host_platform_device_count=4 --xla_cpu_multi_thread_eigen=false'
import argparse, hashlib, json, platform, random, sys, time, traceback
from pathlib import Path
import jax, jax.numpy as jnp, numpy as np
from jax.sharding import Mesh, NamedSharding, PartitionSpec as P

ROOT=Path(__file__).resolve().parent
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def shards(a):
 return [dict(device=str(s.device),index=str(s.index),shape=list(s.data.shape),bytes=s.data.size*s.data.dtype.itemsize) for s in a.addressable_shards]
def ffn(x,g,u,d):return (jax.nn.silu(x@g)*(x@u))@d
def reference(x,g,u,d):
 a=x.astype(np.float64)@g.astype(np.float64)
 b=x.astype(np.float64)@u.astype(np.float64)
 return ((a/(1+np.exp(-a)))*b)@d.astype(np.float64)
def main(args):
 out=ROOT/args.output;out.mkdir(exist_ok=False)
 try:
  (out/'run-source.py').write_bytes(Path(__file__).read_bytes())
  (out/'protocol-at-run.md').write_bytes((ROOT/'PROTOCOL.md').read_bytes())
  h,i=(64,192) if args.smoke else (4096,12288)
  config=json.loads((ROOT/'model-config.json').read_text())
  if not args.smoke:assert (h,i)==(config['hidden_size'],config['intermediate_size'])
  rng=np.random.default_rng(602)
  g=rng.standard_normal((h,i),dtype=np.float32)/np.sqrt(np.float32(h))
  u=rng.standard_normal((h,i),dtype=np.float32)/np.sqrt(np.float32(h))
  d=rng.standard_normal((i,h),dtype=np.float32)/np.sqrt(np.float32(i))
  xs={n:rng.standard_normal((n,h),dtype=np.float32) for n in (8,32)}
  np.savez(out/'inputs.npz',g=g,u=u,d=d,**{f'x{n}':x for n,x in xs.items()})
  refs={n:reference(x,g,u,d) for n,x in xs.items()}
  np.savez(out/'reference.npz',**{f'y{n}':y for n,y in refs.items()})
  save(out/'environment.json',dict(platform=platform.platform(),python=sys.version,jax=jax.__version__,numpy=np.__version__,devices=[str(x) for x in jax.devices()],xla_flags=os.environ['XLA_FLAGS'],source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),hidden=h,intermediate=i,seed=602))
  assert len(jax.devices())==4
  order=[(n,p,kind) for n in xs for p in (2,4) for kind in ('tp','sp')]
  random.Random(602).shuffle(order);save(out/'order.json',order)
  rows=[]
  for n,p,kind in order:
   name=f't{n}-p{p}-{kind}'; print('START',name,flush=True)
   mesh=Mesh(np.array(jax.devices()[:p]),('tp',))
   xspec=P('tp',None) if kind=='sp' else P()
   specs=(xspec,P(None,'tp'),P(None,'tp'),P('tp',None))
   def local(x,g,u,d):
    if kind=='sp':x=jax.lax.all_gather(x,'tp',axis=0,tiled=True)
    y=ffn(x,g,u,d)
    if kind=='sp':return jax.lax.psum_scatter(y,'tp',scatter_dimension=0,tiled=True)
    return jax.lax.psum(y,'tp')
   mapped=jax.shard_map(local,mesh=mesh,in_specs=specs,out_specs=xspec)
   inputs=tuple(jax.device_put(a,NamedSharding(mesh,s)) for a,s in zip((xs[n],g,u,d),specs))
   jax.block_until_ready(inputs)
   t=time.perf_counter();lowered=jax.jit(mapped).lower(*inputs);compiled=lowered.compile();compile_s=time.perf_counter()-t
   (out/f'{name}.stablehlo.txt').write_text(str(lowered.compiler_ir()))
   (out/f'{name}.hlo.txt').write_text(compiled.as_text())
   y=compiled(*inputs);y.block_until_ready()
   times=[]
   for _ in range(5):
    t=time.perf_counter(); y=compiled(*inputs); y.block_until_ready();times.append(time.perf_counter()-t)
   if n==8 and p==4:
    with jax.profiler.trace(str(out/f'{name}-trace')):
     compiled(*inputs).block_until_ready()
   got=np.asarray(y); np.save(out/f'{name}.npy',got)
   ref=refs[n];diff=got.astype(np.float64)-ref
   correct=bool(np.allclose(got,ref,atol=1e-4,rtol=1e-3))
   row=dict(name=name,tokens=n,tp=p,policy=kind,compile_s=compile_s,times_s=times,correct=correct,max_abs=float(np.max(np.abs(diff))),relative_l2=float(np.linalg.norm(diff)/np.linalg.norm(ref)),input_shards={k:shards(v) for k,v in zip(('x','gate','up','down'),inputs)},output_shards=shards(y))
   rows.append(row);save(out/'raw.json',rows)
   print(json.dumps({k:row[k] for k in ('name','correct','max_abs','relative_l2','times_s')}),flush=True)
   assert correct,name
   del inputs,y,got,compiled,lowered,mapped
  save(out/'completion.json',dict(status='complete',conditions=len(rows),samples=sum(len(r['times_s']) for r in rows)))
 except BaseException as e:
  save(out/'failure.json',dict(error=repr(e),traceback=traceback.format_exc()));raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--smoke',action='store_true');p.add_argument('--output',required=True);main(p.parse_args())
