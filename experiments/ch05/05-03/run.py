#!/usr/bin/env python3
"""Actual CUDA SDPA backends, independently runnable; no analytical tile model."""
import argparse
import gc
import json
import platform
import random
import statistics
import subprocess
import time
from pathlib import Path
import torch
import torch.nn.functional as F
from torch.nn.attention import SDPBackend, sdpa_kernel

BACKENDS={"math":SDPBackend.MATH,"flash":SDPBackend.FLASH_ATTENTION}


def snapshot():
    return subprocess.check_output(["nvidia-smi","--query-gpu=name,driver_version,memory.used,utilization.gpu,temperature.gpu,power.draw,clocks.sm","--format=csv"],text=True).strip()


def inputs(length, device="cuda", dtype=torch.bfloat16):
    # Reset per shape so profiled and unprofiled runs see identical inputs.
    torch.manual_seed(503+length)
    return [torch.randn((1,1,length,128),device=device,dtype=dtype) for _ in range(3)]


def attend(q,k,v,backend):
    with sdpa_kernel(BACKENDS[backend]):
        return F.scaled_dot_product_attention(q,k,v,is_causal=True,dropout_p=0.0)


def reference(q,k,v):
    # Independent explicit FP32 score matrix and causal softmax, not the tested dispatcher.
    length=q.shape[-2]
    scores=q.float() @ k.float().transpose(-1,-2) / (128**.5)
    causal=torch.ones((length,length),device=q.device,dtype=torch.bool).triu(1)
    scores.masked_fill_(causal,float("-inf"))
    return scores.softmax(dim=-1) @ v.float()


def profile_one(length,backend):
    q,k,v=inputs(length)
    for _ in range(5): y=attend(q,k,v,backend)
    torch.cuda.synchronize()
    torch.cuda.profiler.start()
    y=attend(q,k,v,backend)
    torch.cuda.synchronize()
    torch.cuda.profiler.stop()
    assert torch.isfinite(y).all()
    print("Profiled",backend,length,flush=True)


def run(trials,repeats):
    out=Path(__file__).resolve().parent/"results"
    out.mkdir(exist_ok=True)
    report={"environment":{"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
            "host":platform.node(),"torch":torch.__version__,"gpu":torch.cuda.get_device_name(),
            "capability":list(torch.cuda.get_device_capability()),"before":snapshot(),"shared_gpu":True},
            "method":{"trials":trials,"repeats":repeats,"warmup":10,"seed":"503 + sequence length",
            "shape":"[B=1, H=1, N, D=128]","dtype":"BF16","causal":True,"dropout":0,
            "backend":"Forced math or FlashAttention; fallback to another backend disabled",
            "cache":"Warm repeated inputs, no cache flushing or clock locking",
            "timing":"CUDA event interval divided by repeats; eager includes host submission gaps; graph contains repeated operators",
            "memory":"Incremental PyTorch peak allocated over live Q/K/V before one eager call; not total process VRAM",
            "reference":"Independent FP32 materialized score-softmax-value chain, TF32 off; atol=.008 rtol=.02"},
            "rows":[],"edge_checks":[]}
    rng=random.Random(503)
    for n in [128,257,512,2048,8192]:
        q,k,v=inputs(n)
        ref=reference(q,k,v)
        # Copy reference to host and free its GPU storage before measuring allocation.
        ref_cpu=ref.cpu();del ref
        gc.collect();torch.cuda.synchronize()
        cases=[]
        for backend in BACKENDS:
            for _ in range(10): y=attend(q,k,v,backend)
            torch.cuda.synchronize();del y
            before=torch.cuda.memory_allocated()
            torch.cuda.reset_peak_memory_stats()
            y=attend(q,k,v,backend)
            torch.cuda.synchronize()
            peak_delta=torch.cuda.max_memory_allocated()-before
            output_bytes=y.numel()*y.element_size()
            actual=y.float().cpu()
            torch.testing.assert_close(actual,ref_cpu,rtol=.02,atol=.008)
            row={"n":n,"backend":backend,"peak_increment_bytes":peak_delta,"output_bytes":output_bytes,
                 "qkv_tensor_bytes":sum(t.numel()*t.element_size() for t in [q,k,v]),
                 "max_abs_error":float((actual-ref_cpu).abs().max()),"correctness":"passed",
                 "eager_samples_us":[],"graph_samples_us":[]}
            del y,actual
            # Holding only the last output allows the allocator to reuse intermediates.
            g=torch.cuda.CUDAGraph()
            stream=torch.cuda.Stream();stream.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(stream):
                for _ in range(5): y=attend(q,k,v,backend)
            torch.cuda.current_stream().wait_stream(stream);torch.cuda.synchronize();del y
            with torch.cuda.graph(g):
                for _ in range(repeats): y=attend(q,k,v,backend)
            for _ in range(5): g.replay()
            torch.cuda.synchronize()
            torch.testing.assert_close(y.float().cpu(),ref_cpu,rtol=.02,atol=.008)
            cases.append((backend,row,g,y))
        torch.cuda.synchronize()
        for _ in range(trials):
            order=[(case,mode) for case in cases for mode in ["eager","graph"]]
            rng.shuffle(order)
            for (backend,row,g,y),mode in order:
                a,b=torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True)
                a.record()
                if mode=="graph":g.replay()
                else:
                    for _ in range(repeats): temp=attend(q,k,v,backend)
                b.record();b.synchronize()
                row[mode+"_samples_us"].append(a.elapsed_time(b)*1000/repeats)
        for backend,row,g,y in cases:
            row["eager_median_us"]=statistics.median(row["eager_samples_us"])
            row["graph_median_us"]=statistics.median(row["graph_samples_us"])
            report["rows"].append(row)
            print(n,backend,round(row["graph_median_us"],3),row["peak_increment_bytes"],flush=True)
        del q,k,v,ref_cpu,cases,order,g,y,temp
        gc.collect();torch.cuda.synchronize()
    # Causal semantics, odd lengths, sharp distributions and input changes.
    for n in [1,17,129]:
        for scale in [0.0,1.0,6.0]:
            q,k,v=inputs(n)
            q.mul_(scale);k.mul_(scale)
            ref=reference(q,k,v)
            for backend in BACKENDS:
                y=attend(q,k,v,backend)
                torch.testing.assert_close(y.float(),ref,rtol=.03,atol=.016)
                # First causal position can only use V[0], independently of Q/K.
                torch.testing.assert_close(y[:,:,0],v[:,:,0],rtol=0,atol=0)
                report["edge_checks"].append({"n":n,"qk_scale":scale,"backend":backend,
                    "max_abs_error":float((y.float()-ref).abs().max()),"first_position_exact":True,"passed":True})
    report["environment"]["after"]=snapshot()
    (out/"results.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--profile-only",action="store_true")
    parser.add_argument("--length",type=int,default=8192)
    parser.add_argument("--backend",choices=list(BACKENDS),default="flash")
    parser.add_argument("--trials",type=int,default=11)
    parser.add_argument("--repeats",type=int,default=10)
    args=parser.parse_args()
    if args.length<1 or args.trials<3 or args.repeats<1:
        parser.error("positive length/repeats and at least 3 trials required")
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    if args.profile_only:profile_one(args.length,args.backend)
    else:run(args.trials,args.repeats)
