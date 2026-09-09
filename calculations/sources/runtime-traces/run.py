#!/usr/bin/env python3
"""Qwen3-8B-shaped FFN: eager, activation fusion, graphs, padding and microbatches."""
import argparse
import json
import math
import platform
import random
import statistics
import subprocess
import time
from pathlib import Path
import torch
import triton
import triton.language as tl


@triton.jit
def activation(G, U, A, N: tl.constexpr, BLOCK: tl.constexpr):
    i = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    g = tl.load(G+i, i<N, 0).to(tl.float32)
    u = tl.load(U+i, i<N, 0).to(tl.float32)
    s = (g / (1 + tl.exp(-g))).to(A.dtype.element_ty).to(tl.float32)
    tl.store(A+i, s*u, i<N)


def snapshot():
    return subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version,memory.used,utilization.gpu,temperature.gpu,power.draw,clocks.sm", "--format=csv"],text=True).strip()


class Chain:
    def __init__(self, x, weights, fused):
        self.x, self.weights, self.fused = x, weights, fused
        m = x.shape[0]
        self.g = torch.empty((m,12288),device="cuda",dtype=torch.bfloat16)
        self.u, self.a = torch.empty_like(self.g), torch.empty_like(self.g)
        self.s = None if fused else torch.empty_like(self.g)
        self.y = torch.empty((m,4096),device="cuda",dtype=torch.bfloat16)
        self.graph = None
        self.capture_ms = 0
        self.graph_memory_delta = 0

    def eager(self):
        wg, wu, wd = self.weights
        torch.mm(self.x, wg, out=self.g)
        torch.mm(self.x, wu, out=self.u)
        if self.fused:
            activation[(triton.cdiv(self.g.numel(),1024),)](self.g,self.u,self.a,self.g.numel(),1024)
        else:
            torch.ops.aten.silu.out(self.g, out=self.s)
            torch.mul(self.s,self.u,out=self.a)
        torch.mm(self.a,wd,out=self.y)

    def capture(self):
        # Capture only after GEMM selection and Triton JIT are warmed on a side stream.
        stream = torch.cuda.Stream()
        stream.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(stream):
            for _ in range(5): self.eager()
        torch.cuda.current_stream().wait_stream(stream)
        torch.cuda.synchronize()
        before = torch.cuda.memory_allocated()
        start = time.perf_counter()
        self.graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(self.graph): self.eager()
        self.graph.replay()
        torch.cuda.synchronize()
        self.capture_ms = (time.perf_counter()-start)*1000
        self.graph_memory_delta = torch.cuda.memory_allocated()-before

    def tensor_bytes(self):
        return sum(t.numel()*t.element_size() for t in [self.x,self.g,self.u,self.a,self.s,self.y] if t is not None)


def make_case(x, weights, label, fused=False, graph=False, pad=None, copy_input=False, chunks=1):
    actual = x.shape[0]
    executed = pad or actual
    padded = torch.zeros((executed,4096),device="cuda",dtype=x.dtype)
    padded[:actual].copy_(x)
    assert executed % chunks == 0
    chains = [Chain(part, weights, fused) for part in padded.chunk(chunks)]
    for chain in chains:
        for _ in range(5): chain.eager()
        if graph: chain.capture()
    def invoke():
        if copy_input: padded[:actual].copy_(x)
        for chain in chains:
            if graph: chain.graph.replay()
            else: chain.eager()
    def output():
        return torch.cat([c.y for c in chains])[:actual]
    row = {"label":label,"tokens":actual,"executed_tokens":executed,"chunks":chunks,
           "fused":fused,"graph":graph,"copy_input":copy_input,
           "capture_instantiate_first_replay_ms":sum(c.capture_ms for c in chains),
           "pytorch_allocated_graph_delta_bytes":sum(c.graph_memory_delta for c in chains),
           "live_io_intermediate_bytes":sum(c.tensor_bytes() for c in chains),
           "input_copy_payload_bytes": x.numel()*2 if copy_input else 0,
           "samples_us":[],"host_submit_samples_us":[]}
    return invoke, output, row, chains


def reference(x, weights):
    # Independent FP32 complete chain, with TF32 disabled; no BF16 intermediates.
    wg,wu,wd=weights
    return (torch.nn.functional.silu(x.float() @ wg.float()) * (x.float() @ wu.float())) @ wd.float()


def main(trace_only, trials, repeats):
    torch.manual_seed(508)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.cuda.init()
    rng=random.Random(508)
    report={"environment":{"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
            "torch":torch.__version__,"triton":triton.__version__,"host":platform.node(),
            "gpu":torch.cuda.get_device_name(),"before":snapshot(),"shared_gpu":True},
            "method":{"trials":trials,"repeats":repeats,"dtype":"BF16","seed":508,
            "weights":"Random variance-scaled weights, Qwen3-8B FFN dimensions; not a model checkpoint",
            "weight_shapes":[[4096,12288],[4096,12288],[12288,4096]],
            "weight_bytes":301989888,"cache":"Reused fixed buffers; no L2 flush",
            "device_time":"CUDA events around repeated host submissions; includes exposed submission gaps",
            "host_time":"CPU time to submit repeated operations, without final synchronization",
            "capture_time":"Capture, instantiate, first replay and synchronize; excludes warmup and JIT",
            "reference":"Independent FP32 full chain, TF32 off, rtol=0.04 atol=0.025",
            "comparison":"Against BF16 eager chain additionally rtol=0.02 atol=0.008"},"rows":[]}
    weights=[(torch.randn(shape,device="cuda",dtype=torch.bfloat16)/math.sqrt(shape[0])).bfloat16()
             for shape in [(4096,12288),(4096,12288),(12288,4096)]]
    trace_cases=[]
    for m in ([32] if trace_only else [1,32,257]):
        x=torch.randn((m,4096),device="cuda",dtype=torch.bfloat16)
        ref=reference(x,weights)
        negative_ref=reference(-x,weights)
        cases=[make_case(x,weights,"eager"),make_case(x,weights,"fused",fused=True),
               make_case(x,weights,"graph",graph=True),make_case(x,weights,"fused_graph",fused=True,graph=True),
               make_case(x,weights,"fused_graph_copy",fused=True,graph=True,copy_input=True)]
        if m==257:
            cases.extend([make_case(x,weights,"graph_pad512",graph=True,pad=512),
                          make_case(x,weights,"fused_graph_pad512",fused=True,graph=True,pad=512)])
        if m==32:
            for chunks in [4,8]:
                cases.extend([make_case(x,weights,f"eager_micro{chunks}",chunks=chunks),
                              make_case(x,weights,f"fused_graph_micro{chunks}",chunks=chunks,fused=True,graph=True)])
        cases[0][0]()
        eager_ref=cases[0][1]().clone()
        for invoke, output, row, chains in cases:
            invoke()
            torch.testing.assert_close(output().float(),ref,rtol=.04,atol=.025)
            torch.testing.assert_close(output(),eager_ref,rtol=.02,atol=.008)
            row["fp32_max_abs_error"]=float((output().float()-ref).abs().max())
            row["bf16_eager_max_abs_error"]=float((output().float()-eager_ref.float()).abs().max())
            row["correctness"]="passed"
            # Validate fresh data at the captured addresses, including the external-copy boundary.
            targets=[x] if row["copy_input"] else [c.x for c in chains]
            backups=[t.clone() for t in targets]
            for target in targets: target.neg_()
            invoke()
            torch.testing.assert_close(output().float(),negative_ref,rtol=.04,atol=.025)
            for target in targets: target.zero_()
            invoke()
            assert torch.count_nonzero(output()).item()==0
            for target,backup in zip(targets,backups): target.copy_(backup)
            invoke()
            torch.testing.assert_close(output().float(),ref,rtol=.04,atol=.025)
            row["input_update_checks"]=["negative_input_matches_fp32","zero_input_exact","restored_input_matches_fp32"]
            for _ in range(10): invoke()
        torch.cuda.synchronize()
        if trace_only:
            trace_cases=cases
            break
        for _ in range(trials):
            order=list(cases);rng.shuffle(order)
            for invoke, output, row, chains in order:
                a,b=torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True)
                a.record()
                start=time.perf_counter()
                for _ in range(repeats): invoke()
                host_us=(time.perf_counter()-start)*1e6/repeats
                b.record();b.synchronize()
                row["samples_us"].append(a.elapsed_time(b)*1000/repeats)
                row["host_submit_samples_us"].append(host_us)
        for invoke,output,row,chains in cases:
            row["median_us"]=statistics.median(row["samples_us"])
            row["host_submit_median_us"]=statistics.median(row["host_submit_samples_us"])
            report["rows"].append(row)
            print(m,row["label"],round(row["median_us"],3),flush=True)
        # Graphs are released before the next shape to bound residency.
        del cases,order,invoke,output,chains,eager_ref,ref,x
        torch.cuda.synchronize()
    if trace_only:
        torch.cuda.profiler.start()
        for invoke,output,row,chains in trace_cases:
            torch.cuda.nvtx.range_push("exp5_8:"+row["label"])
            for _ in range(3): invoke()
            torch.cuda.synchronize()
            torch.cuda.nvtx.range_pop()
        torch.cuda.profiler.stop()
        print("Trace ranges completed",flush=True)
    else:
        report["environment"]["after"]=snapshot()
        out=Path(__file__).resolve().parent/"results"
        out.mkdir(exist_ok=True)
        (out/"results.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--trace-only",action="store_true")
    p.add_argument("--trials",type=int,default=11)
    p.add_argument("--repeats",type=int,default=20)
    args=p.parse_args()
    if args.trials<3 or args.repeats<1:p.error("at least 3 trials and 1 repeat required")
    main(args.trace_only,args.trials,args.repeats)
