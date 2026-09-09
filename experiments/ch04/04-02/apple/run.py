import hashlib,importlib.metadata,json,platform,random,time
from pathlib import Path
import mlx.core as mx
import numpy as np
P=Path(__file__).resolve().parent; R=P/'results';R.mkdir(exist_ok=False)
mx.set_default_device(mx.gpu)
rng=np.random.default_rng(402)
w32=(rng.normal(size=(768,2048))/np.sqrt(2048)).astype(np.float32)
x32=rng.normal(size=(512,2048)).astype(np.float32)
w=mx.array(w32.astype(np.float16));xf=mx.array(x32)
q,s,b=mx.quantize(w,group_size=64,bits=4,mode='affine')
dq=mx.dequantize(q,s,b,group_size=64,bits=4,mode='affine',dtype=mx.float16)
x=xf.astype(mx.float16)
mx.eval(w,xf,q,s,b,dq,x);mx.synchronize()
np.savez(R/'inputs.npz',w32=w32,x32=x32,packed=np.array(q),scales=np.array(s),biases=np.array(b),dequantized=np.array(dq))
config=dict(seed=402,weight_shape=list(w.shape),batches=[1,8,64,512],group_size=64,bits=4,mode='affine',atol=.01,rtol=.01,decode_atol=.0001,decode_rtol=.001)
(R/'environment.json').write_text(json.dumps(dict(config=config,mlx=importlib.metadata.version('mlx'),numpy=np.__version__,python=platform.python_version(),platform=platform.platform(),device=mx.device_info(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),arrays={name:dict(shape=list(z.shape),dtype=str(z.dtype),bytes=z.nbytes) for name,z in [('weight_fp16',w),('weight_packed',q),('scales',s),('biases',b),('weight_expanded',dq),('activation_fp32_all',xf),('activation_fp16_all',x)]}),indent=2)+'\n')

def direct(z):return mx.quantized_matmul(z,q,s,b,transpose=True,group_size=64,bits=4,mode='affine')
def decode():return mx.dequantize(q,s,b,group_size=64,bits=4,mode='affine',dtype=mx.float16)
operations={('quantize',0):lambda:mx.quantize(w,group_size=64,bits=4,mode='affine'),('dequantize',0):decode}
for batch in config['batches']:
 z=x[:batch];zf=xf[:batch];mx.eval(z,zf)
 operations.update({('activation_cast',batch):lambda zf=zf:zf.astype(mx.float16),
 ('direct',batch):lambda z=z:direct(z),
 ('cached_expanded_matmul',batch):lambda z=z:z@dq.T,
 ('decode_matmul',batch):lambda z=z:z@decode().T,
 ('cast_direct',batch):lambda zf=zf:direct(zf.astype(mx.float16)),
 ('cast_decode_matmul',batch):lambda zf=zf:zf.astype(mx.float16)@decode().T})
# Five evaluated warmups per operation, then interleaved formal measurements.
for key,op in operations.items():
 for _ in range(5):
  value=op();mx.eval(value);mx.synchronize();del value
plan=[(trial,*key) for trial in range(30) for key in operations];random.Random(402).shuffle(plan)
with (R/'timings.jsonl').open('x') as f:
 for trial,name,batch in plan:
  mx.synchronize();mx.reset_peak_memory();active=mx.get_active_memory();cache=mx.get_cache_memory()
  start=time.perf_counter_ns();value=operations[(name,batch)]();mx.eval(value);mx.synchronize();end=time.perf_counter_ns()
  row=dict(trial=trial,operation=name,batch=batch,start_ns=start,end_ns=end,elapsed_ns=end-start,active_before=active,active_after=mx.get_active_memory(),peak=mx.get_peak_memory(),cache_before=cache,cache_after=mx.get_cache_memory())
  f.write(json.dumps(row)+'\n');del value
outputs={}
for batch in config['batches']:
 for name in ['direct','cached_expanded_matmul','decode_matmul','cast_direct','cast_decode_matmul']:
  value=operations[(name,batch)]();mx.eval(value);mx.synchronize();outputs[f'{name}_{batch}']=np.array(value)
np.savez(R/'outputs.npz',**outputs)
(R/'completion.json').write_text(json.dumps(dict(completed=True,timed_operations=len(plan)))+'\n')
print('Completed',len(plan),'synchronized timings.')
