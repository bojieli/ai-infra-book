"""Same fixtures and wall-clock boundaries on MPS/CUDA; no theoretical simulation."""
import argparse,contextlib,hashlib,json,platform,random,time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F


def sha(t):return hashlib.sha256(t.contiguous().numpy().tobytes()).hexdigest()
def fixture(n,offset):
    x=((torch.arange(n*128,dtype=torch.int64)+offset)*1664525+1013904223)&0xffffffff
    return ((((x>>16)%97)-48).float()/64).reshape(1,1,n,128).half()
def run(device,out):
    if out.exists():raise RuntimeError('Use a fresh output directory')
    out.mkdir(parents=True)
    torch.set_num_threads(1)
    if device=='cuda':
        torch.backends.cuda.matmul.allow_tf32=False
        sync=torch.cuda.synchronize
    else:
        assert torch.backends.mps.is_available()
        sync=torch.mps.synchronize
    rng=random.Random(406)
    results=[];arrays={}
    for n,decode in [(128,False),(257,False),(512,False),(2048,False),(2048,True)]:
        label=f'{"decode" if decode else "prefill"}-{n}'
        qc,kc,vc=[fixture(n,o) for o in (20000,10000,30000)]
        if decode:qc=qc[:,:,-1:,:].contiguous()
        score=qc.double()@kc.double().transpose(-1,-2)/(128**.5)
        if not decode:score.masked_fill_(torch.ones(n,n,dtype=torch.bool).triu(1),float('-inf'))
        ref=score.softmax(-1)@vc.double()
        q,k,v=[t.to(device) for t in (qc,kc,vc)]
        mask=None if decode else torch.ones(n,n,device=device,dtype=torch.bool).triu(1)
        def explicit():
            s=q.float()@k.float().transpose(-1,-2)/(128**.5)
            if mask is not None:s=s.masked_fill(mask,float('-inf'))
            return (s.softmax(-1)@v.float()).half()
        def sdpa():return F.scaled_dot_product_attention(q,k,v,is_causal=not decode,dropout_p=0.)
        calls={'explicit_fp32_intermediates':explicit,'sdpa_default':sdpa}
        row=dict(case=label,n=n,q_length=q.shape[-2],input_sha256={name:sha(t) for name,t in zip(('q','k','v'),(qc,kc,vc))},paths={})
        for name,t in zip(('q','k','v'),(qc,kc,vc)):arrays[f'{label}_{name}']=t.numpy()
        arrays[f'{label}_reference']=ref.numpy()
        for name,fn in calls.items():
            for _ in range(5):y=fn()
            sync();actual=y.cpu();sync()
            torch.testing.assert_close(actual.double(),ref,atol=.002,rtol=.01)
            arrays[f'{label}_{name}']=actual.numpy()
            row['paths'][name]=dict(max_abs_error=float((actual.double()-ref).abs().max()),samples_wall_us=[])
        for trial in range(11):
            order=list(calls);rng.shuffle(order)
            for name in order:
                sync();start=time.perf_counter()
                for _ in range(10):y=calls[name]()
                sync();elapsed=(time.perf_counter()-start)*1e6/10
                row['paths'][name]['samples_wall_us'].append(elapsed)
        # A future-value perturbation must not affect the first half of causal outputs.
        if not decode:
            original=v.clone();before=sdpa().cpu();v[:,:,n//2:,:]+=4
            after=sdpa().cpu();v.copy_(original);sync()
            assert torch.equal(before[:,:,:n//2],after[:,:,:n//2])
            row['causal_future_value_check']='passed'
        # CPU dispatcher evidence only: these names are not GPU kernel timing evidence.
        if n==512:
            with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as prof:
                y=sdpa();sync()
            row['sdpa_cpu_dispatch_operators']=[dict(name=e.key,count=e.count) for e in prof.key_averages()]
        results.append(row);print(label,'completed',flush=True)
    np.savez_compressed(out/'tensors.npz',**arrays)
    env=dict(device=device,torch=torch.__version__,python=platform.python_version(),platform=platform.platform(),
             source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             device_name=torch.cuda.get_device_name() if device=='cuda' else 'Apple M2 Max',
             timing='Host wall per operation: 10 eager calls then device synchronization; 11 shuffled path trials; 5 warmups. No GPU event timing.',
             dtype='FP16 input/output; explicit path promotes score/softmax/value to FP32; SDPA default dispatcher',
             reference='CPU FP64 explicit causal score-softmax-value, atol=.002 rtol=.01',
             decode='Single final-position query with all previous keys; causal=False intentionally permits all keys',
             fallback_env=__import__('os').environ.get('PYTORCH_ENABLE_MPS_FALLBACK','unset'))
    (out/'results.json').write_text(json.dumps(dict(environment=env,rows=results),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--device',choices=['mps','cuda'],required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.device,a.output)
