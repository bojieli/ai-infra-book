import argparse,hashlib,json,platform,subprocess,time
from pathlib import Path
import torch

def main(out):
    if out.exists():raise RuntimeError('Use fresh output directory')
    out.mkdir(parents=True)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    def values(count,offset):
        x=(torch.arange(count,dtype=torch.int64)+offset)*1664525+1013904223
        x=(x & 0xffffffff)>>16
        return ((x%97)-48).float()/64
    def measure(fn,repeats):
        for _ in range(10):fn()
        torch.cuda.synchronize()
        graph=torch.cuda.CUDAGraph()
        with torch.cuda.graph(graph):
            for _ in range(repeats):fn()
        for _ in range(3):graph.replay()
        torch.cuda.synchronize();samples=[]
        for _ in range(11):
            start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True)
            wall=time.perf_counter();start.record();graph.replay();end.record();end.synchronize()
            samples.append(dict(gpu_s=start.elapsed_time(end)/1000/repeats,wall_s=(time.perf_counter()-wall)/repeats))
        return samples
    results=[]
    for m in [1,32,256]:
        k=n=512
        acpu=values(m*k,20000).reshape(m,k);bcpu=values(k*n,10000).reshape(k,n)
        a=acpu.cuda();b=bcpu.cuda();c=torch.empty((m,n),device='cuda',dtype=torch.float32)
        samples=measure(lambda:torch.mm(a,b,out=c),50)
        reference=acpu.double()@bcpu.double()
        error=(c.cpu().double()-reference).abs().max().item();assert error==0
        results.append(dict(kind='matmul',m=m,k=k,n=n,samples=samples,max_abs_error_fp64=error,reference_elements=m*n))
    for mib in [16,64,256]:
        size=mib*1024**2
        # Periodic byte fixture identical to the Swift source, without a huge int64 temporary.
        pattern=((torch.arange(256,dtype=torch.int32)*17+11)%256).to(torch.uint8)
        source=pattern.repeat(size//256).cuda();target=torch.empty_like(source)
        samples=measure(lambda:target.copy_(source),20)
        assert torch.equal(source,target)
        results.append(dict(kind='copy',payload_bytes=size,samples=samples,all_bytes_match=True))
    (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    env=dict(torch=torch.__version__,python=platform.python_version(),device=torch.cuda.get_device_name(),tf32=False,
        gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv'],text=True),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='FP32 GEMM, TF32 disabled; CUDA Graph with 50 GEMMs or 20 device copies per replay. Warm reused buffers. CUDA events, no DRAM counters; wall excludes graph construction.')
    (out/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
    print('completed',len(results),'configurations')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
