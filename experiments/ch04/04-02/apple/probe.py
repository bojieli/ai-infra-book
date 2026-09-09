import json
from pathlib import Path
import mlx.core as mx
import numpy as np
mx.set_default_device(mx.gpu)
rng=np.random.default_rng(402)
w=mx.array((rng.normal(size=(32,64))/8).astype(np.float16));x=mx.array(rng.normal(size=(1,64)).astype(np.float16))
q,s,b=mx.quantize(w,group_size=64,bits=4,mode='affine')
dq=mx.dequantize(q,s,b,group_size=64,bits=4,mode='affine',dtype=mx.float16)
a=mx.quantized_matmul(x,q,s,b,transpose=True,group_size=64,bits=4,mode='affine');c=x@dq.T
mx.eval(q,s,b,dq,a,c);mx.synchronize()
ref=np.array(x).astype(np.float64)@np.array(dq).astype(np.float64).T
result=dict(device=mx.device_info(),shapes=[list(z.shape) for z in [q,s,b,dq,a]],dtypes=[str(z.dtype) for z in [q,s,b,dq,a]],direct_pass=bool(np.allclose(np.array(a),ref,atol=.01,rtol=.01)),expanded_pass=bool(np.allclose(np.array(c),ref,atol=.01,rtol=.01)),direct_max_abs=float(np.max(np.abs(np.array(a)-ref))))
Path('probe.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
