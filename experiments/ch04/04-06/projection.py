import argparse,hashlib,json,platform,random,time
from pathlib import Path
import numpy as np
import torch

def fixture(count,offset):
    x=((torch.arange(count,dtype=torch.int64)+offset)*1664525+1013904223)&0xffffffff
    return ((((x>>16)%97)-48).float()/64).bfloat16()
def main(device,out):
    if out.exists():raise RuntimeError('Use a fresh output directory')
    out.mkdir(parents=True);torch.set_num_threads(1)
    if device=='cuda':
        torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=False
        sync=torch.cuda.synchronize
    else:
        assert torch.backends.mps.is_available();sync=torch.mps.synchronize
    bcpu=fixture(4096**2,10000).reshape(4096,4096)
    weights=[bcpu.to(device).clone() for _ in range(16)]
    assert len({t.data_ptr() for t in weights})==16
    arrays={'weight':bcpu.float().numpy()};rows=[];rng=random.Random(4064096)
    for m in [1,256]:
        acpu=fixture(m*4096,20000).reshape(m,4096);a=acpu.to(device)
        ref=acpu.double()@bcpu.double();c=torch.empty((m,4096),device=device,dtype=torch.bfloat16)
        arrays[f'a_{m}']=acpu.float().numpy();arrays[f'ref_{m}']=ref.numpy()
        for i,w in enumerate(weights):
            torch.mm(a,w,out=c);sync();actual=c.float().cpu()
            torch.testing.assert_close(actual.double(),ref,atol=.01,rtol=.01)
            if i in [0,15]:arrays[f'output_{m}_{i}']=actual.numpy()
        row=dict(m=m,n=4096,k=4096,max_abs_error=float((actual.double()-ref).abs().max()),all_16_weight_buffers_checked=True,
                 input_sha256=hashlib.sha256(acpu.float().numpy().tobytes()).hexdigest(),paths={})
        def batch(mode):
            for i in range(16):torch.mm(a,weights[0 if mode=='reused' else i],out=c)
        for mode in ['reused','rotating']:
            for _ in range(3):batch(mode)
            sync();row['paths'][mode]={'wall_us':[],'cuda_event_us':[]}
        for trial in range(11):
            order=['reused','rotating'];rng.shuffle(order)
            for mode in order:
                sync()
                if device=='cuda':
                    start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True)
                t=time.perf_counter()
                if device=='cuda':start.record()
                batch(mode)
                if device=='cuda':end.record()
                sync();elapsed=(time.perf_counter()-t)*1e6/16
                row['paths'][mode]['wall_us'].append(elapsed)
                if device=='cuda':row['paths'][mode]['cuda_event_us'].append(start.elapsed_time(end)*1000/16)
        rows.append(row);print('completed',device,m,flush=True)
    np.savez_compressed(out/'tensors.npz',**arrays)
    result=dict(environment=dict(torch=torch.__version__,python=platform.python_version(),device=device,platform=platform.platform(),
               source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               weight_sha256=hashlib.sha256(bcpu.float().numpy().tobytes()).hexdigest(),weight_buffers=16,weight_buffer_bytes=bcpu.numel()*bcpu.element_size(),
               weight_addresses=[t.data_ptr() for t in weights],bf16_reduced_precision_reduction=False if device=='cuda' else 'not exposed by MPS API',
               fallback_env=__import__('os').environ.get('PYTORCH_ENABLE_MPS_FALLBACK','unset')),
               method='BF16 input/output; identical-valued independent weight buffers, repeated vs 16-address rotation. 11 trials x16 calls; 3 warm batches. Wall includes submit and sync; CUDA events include submission gaps. Rotation is not verified cold DRAM.',rows=rows)
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--device',choices=['mps','cuda'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.device,a.output)
