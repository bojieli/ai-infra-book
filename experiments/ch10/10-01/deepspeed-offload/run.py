"""Actual serial gradient offload, cast, CPUAdam and updated-weight H2D."""
import argparse, contextlib, gc, hashlib, json, os, platform, random, subprocess, time
from pathlib import Path
import torch
import deepspeed
from deepspeed.ops.adam import DeepSpeedCPUAdam

def digest(t):
    return hashlib.sha256(t.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()

def info(t):
    return dict(shape=list(t.shape), dtype=str(t.dtype), device=str(t.device),
                pinned=t.is_pinned(), storage_bytes=t.untyped_storage().nbytes())

def check(a,b):
    # Chunk validation bounds temporary allocations without weakening full coverage.
    aa,bb=a.detach().flatten(),b.detach().flatten()
    maximum=0.; failures=0
    for lo in range(0,aa.numel(),1048576):
        x,y=aa[lo:lo+1048576],bb[lo:lo+1048576]
        err=(x-y).abs()
        maximum=max(maximum,err.max().item())
        failures+=int((err > 2e-6 + 1e-4*y.abs()).sum())
    return dict(max_abs=maximum, failing_elements=failures, elements=aa.numel())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--smoke',action='store_true'); args=ap.parse_args()
    out=args.out; out.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.manual_seed(10101)
    shape=(768,256) if args.smoke else (12288,4096)
    initial=torch.randn(shape,dtype=torch.float32)/shape[1]**.5
    inputs=[]
    for step in range(3):
        g=torch.Generator().manual_seed(10110+step)
        inputs.append((torch.randn(32,shape[1],generator=g).bfloat16(),
                       (torch.randn(32,shape[0],generator=g)/32).bfloat16()))
    torch.save(dict(initial=initial,inputs=inputs),out/'fixture.pt')
    def gpu():
        return subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv'],text=True)
    env=dict(torch=torch.__version__,deepspeed=deepspeed.__version__,python=platform.python_version(),
             shape=shape,smoke=args.smoke,pid=os.getpid(),threads=torch.get_num_threads(),
             gpu=torch.cuda.get_device_name(),gpu_before=gpu(),
             cuda_home=os.environ.get('CUDA_HOME'),initial_sha=digest(initial),
             source_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             cpu_affinity=sorted(os.sched_getaffinity(0)))
    (out/'environment.json').write_text(json.dumps(env,indent=2))
    groups=[('warmup',p,0) for p in ['cpu_cast','gpu_cast']]
    formal=[('formal',p,t) for p in ['cpu_cast','gpu_cast'] for t in range(1 if args.smoke else 5)]
    random.Random(10102).shuffle(formal); groups+=formal
    if not args.smoke: groups += [('profile',p,0) for p in ['cpu_cast','gpu_cast']]
    stream=open(out/'records.jsonl','w',buffering=1)
    for phase,policy,trial in groups:
        gc.collect(); torch.cuda.empty_cache()
        master=torch.nn.Parameter(initial.clone())
        reference=torch.nn.Parameter(initial.clone())
        opt=DeepSpeedCPUAdam([master],lr=.001,weight_decay=.01,adamw_mode=True)
        refopt=torch.optim.AdamW([reference],lr=.001,weight_decay=.01,foreach=False)
        weight=torch.nn.Parameter(initial.to('cuda',dtype=torch.bfloat16))
        host_grad=torch.empty(shape,dtype=torch.float32,pin_memory=True)
        host_bf16=torch.empty(shape,dtype=torch.bfloat16,pin_memory=True) if policy=='cpu_cast' else None
        device_fp32=torch.empty(shape,dtype=torch.float32,device='cuda') if policy=='gpu_cast' else None
        host_weight=torch.empty(shape,dtype=torch.bfloat16,pin_memory=True)
        master.grad=host_grad
        profiler=torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA],profile_memory=True) if phase=='profile' else contextlib.nullcontext()
        with profiler as prof:
            for step,(xx,yy) in enumerate(inputs):
                weight.grad=None
                x,y=xx.cuda(),yy.cuda()
                loss=(torch.nn.functional.linear(x,weight)*y).float().sum()
                loss.backward(); torch.cuda.synchronize()
                grad=weight.grad
                # Independent reference uses original gradient, before either path.
                reference.grad=grad.float().cpu()
                torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
                stage={}
                start=time.perf_counter_ns()
                def measure(name,fn):
                    tick=time.perf_counter_ns()
                    with torch.profiler.record_function(name): fn()
                    stage[name]=(time.perf_counter_ns()-tick)/1e6
                def transfer():
                    if policy=='cpu_cast': host_bf16.copy_(grad,non_blocking=True)
                    else: host_grad.copy_(device_fp32,non_blocking=True)
                    torch.cuda.synchronize()
                if policy=='gpu_cast':
                    def cast_gpu():
                        device_fp32.copy_(grad); torch.cuda.synchronize()
                    measure('gpu_cast',cast_gpu)
                measure('D2H',transfer)
                if policy=='cpu_cast': measure('cpu_cast',lambda:host_grad.copy_(host_bf16))
                measure('CPUAdam',opt.step)
                measure('weight_cpu_cast',lambda:host_weight.copy_(master.detach()))
                def back():
                    with torch.no_grad(): weight.copy_(host_weight,non_blocking=True)
                    torch.cuda.synchronize()
                measure('weight_H2D',back)
                elapsed=(time.perf_counter_ns()-start)/1e6
                peak=torch.cuda.max_memory_allocated()
                refopt.step()
                results={'parameter':check(master,reference)}
                for name in ['exp_avg','exp_avg_sq']:
                    results[name]=check(opt.state[master][name],refopt.state[reference][name])
                grad_exact=torch.equal(host_grad,reference.grad)
                weight_exact=torch.equal(weight.detach().cpu(),host_weight)
                tensors={'master':master,'host_grad':host_grad,'host_weight':host_weight,
                         'device_weight':weight,'device_gradient':grad,
                         'moment1':opt.state[master]['exp_avg'],'moment2':opt.state[master]['exp_avg_sq']}
                if host_bf16 is not None: tensors['host_bf16']=host_bf16
                if device_fp32 is not None: tensors['device_fp32']=device_fp32
                record=dict(phase=phase,policy=policy,trial=trial,step=step+1,
                    wall_ms=elapsed,stage_ms=stage,cuda_peak_allocated_bytes=peak,
                    tensors={k:info(v) for k,v in tensors.items()},checks=results,
                    gradient_exact=grad_exact,weight_transfer_exact=weight_exact,
                    gradient_sha=digest(host_grad),parameter_sha=digest(master),
                    moment1_sha=digest(opt.state[master]['exp_avg']),moment2_sha=digest(opt.state[master]['exp_avg_sq']))
                stream.write(json.dumps(record)+'\n')
                assert grad_exact and weight_exact and all(v['failing_elements']==0 for v in results.values()), record
                del tensors,x,y,loss,grad
        if phase=='profile': prof.export_chrome_trace(str(out/f'{policy}-trace.json'))
        del master,reference,opt,refopt,weight,host_grad,host_bf16,device_fp32,host_weight,profiler,prof
    stream.close()
    (out/'completion.json').write_text(json.dumps(dict(completed=True,groups=len(groups),steps=len(groups)*3,gpu_at_end=gpu()),indent=2))

if __name__=='__main__': main()
