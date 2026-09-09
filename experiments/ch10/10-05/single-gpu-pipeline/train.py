"""Single-GPU four-process experiment using unmodified Megatron Core scheduling.
Gloo CUDA-tensor communication; not a four-device throughput experiment.
"""
import os
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
import argparse, gc, hashlib, json, pathlib, resource, time
import torch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    ap.add_argument('--stages', type=int, choices=[1,4], default=4)
    ap.add_argument('--backend', choices=['nccl','gloo'], default='gloo')
    args = ap.parse_args()
    # Fail before any device initialization on the present Mac.
    if not torch.cuda.is_available() or not torch.distributed.is_gloo_available():
        raise SystemExit('BLOCKED: CUDA and Gloo required')
    from megatron.core import parallel_state
    from megatron.core.enums import ModelType
    from megatron.core.transformer.transformer_config import TransformerConfig
    from megatron.core.pipeline_parallel.schedules import get_forward_backward_func
    import megatron.core.pipeline_parallel.schedules as schedules
    import megatron.core.pipeline_parallel.p2p_communication as p2p

    root = pathlib.Path(__file__).resolve().parent
    manifest = json.loads((root/'sources/manifest.json').read_text())
    for module in (schedules, p2p):
        name = 'megatron/core/pipeline_parallel/' + pathlib.Path(module.__file__).name
        expected = next(x['sha256'] for x in manifest['files'] if x['path'] == name)
        assert hashlib.sha256(pathlib.Path(module.__file__).read_bytes()).hexdigest() == expected, name
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    rank = int(os.environ['RANK'])
    assert int(os.environ['WORLD_SIZE']) == args.stages
    torch.cuda.set_device(0)
    torch.distributed.init_process_group(args.backend)
    parallel_state.initialize_model_parallel(tensor_model_parallel_size=1, pipeline_model_parallel_size=args.stages)
    torch.manual_seed(105)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)
    out = pathlib.Path(args.output)/f'rank-{rank}'
    out.mkdir(parents=True, exist_ok=False)
    events = []
    def event(kind, **kw):
        events.append(dict(kind=kind,host_monotonic_ns=time.monotonic_ns(),rank=rank,**kw))
    config = TransformerConfig(num_layers=36,hidden_size=16,num_attention_heads=1,
        pipeline_model_parallel_size=args.stages,pipeline_dtype=torch.float32,
        hidden_dropout=0.0,attention_dropout=0.0,deallocate_pipeline_outputs=False,
        batch_p2p_comm=True,overlap_p2p_comm=False)

    class Block(torch.nn.Module):
        def __init__(self, layer):
            super().__init__()
            g = torch.Generator(device='cpu').manual_seed(105000+layer)
            self.weight = torch.nn.Parameter(torch.randn(16,16,generator=g)*0.02)
            self.bias = torch.nn.Parameter(torch.randn(16,generator=g)*0.01)
        def forward(self, x):
            return x + torch.tanh(torch.nn.functional.linear(x,self.weight,self.bias))*0.1

    class Model(torch.nn.Module):
        def __init__(self, indices):
            super().__init__()
            self.config = config
            self.model_type = ModelType.encoder_or_decoder
            self.layers = torch.nn.ModuleDict({str(i):Block(i) for i in indices})
            self.input_tensor = None
        def set_input_tensor(self, value):
            self.input_tensor = value[0] if isinstance(value,list) else value
        def forward(self, x):
            for layer in self.layers.values():
                x = layer(x)
            return x

    g = torch.Generator().manual_seed(105)
    inputs = torch.randn(8,8,1,16,generator=g).cuda()
    targets = torch.randn(8,8,1,16,generator=g).cuda()
    # Same eight samples/microbatches, exact per-layer initialization and loss denominator.
    reference = Model(range(36)).cuda()
    ref_outputs = []
    for i in range(8):
        y = reference(inputs[i])
        ref_outputs.append(y.detach().cpu())
        ((y-targets[i]).square().mean()/8).backward()
    expected = {n:p.grad.detach().cpu().clone() for n,p in reference.named_parameters()}
    expected_updated = {n:(p.detach()-0.01*p.grad).cpu().clone() for n,p in reference.named_parameters()}
    del reference, y
    gc.collect()
    torch.cuda.empty_cache()
    model = Model(range(rank*(36//args.stages),(rank+1)*(36//args.stages))).cuda()
    initial = {n:p.detach().cpu().clone() for n,p in model.named_parameters()}
    optimizer = torch.optim.SGD(model.parameters(),lr=0.01)
    param_ptrs = {p.untyped_storage().data_ptr() for p in model.parameters()}
    # These wrappers own the real tensors required by autograd, no shadow byte model.
    class Saved:
        def __init__(self,t):
            self.tensor = t
            self.ident = len(events)
            self.ptr = t.untyped_storage().data_ptr()
            event('autograd_save',id=self.ident,storage_ptr=self.ptr,
                  storage_bytes=t.untyped_storage().nbytes(),tensor_bytes=t.numel()*t.element_size(),
                  parameter_storage=self.ptr in param_ptrs)
        def __del__(self):
            event('autograd_release',id=self.ident,storage_ptr=self.ptr)
    def unpack(s):
        event('autograd_unpack',id=s.ident)
        return s.tensor
    observed = []
    def forward_step(iterator, part):
        i = next(iterator)
        event('forward_begin',microbatch=i)
        with torch.profiler.record_function(f'forward/rank{rank}/mb{i}'):
            x = inputs[i] if rank == 0 else part.input_tensor
            y = part(x)
            y.register_hook(lambda grad, i=i: (event('output_gradient_ready',microbatch=i),grad)[1])
        event('forward_end',microbatch=i)
        def loss(z):
            observed.append((i,z.detach().cpu()))
            l = (z-targets[i]).square().mean()
            return l, {'loss':l.detach()}
        return y, loss
    schedule = get_forward_backward_func()
    assert schedule.__name__ == ('forward_backward_no_pipelining' if args.stages==1 else 'forward_backward_pipelining_without_interleaving')
    (out/'environment.json').write_text(json.dumps(dict(torch=torch.__version__,cuda=torch.version.cuda,backend=args.backend,stages=args.stages,device_index=0,
        gpu=torch.cuda.get_device_name(),schedule=schedule.__name__,source_commit=manifest['commit'],
        intraop_threads=torch.get_num_threads(),interop_threads=torch.get_num_interop_threads(),
        coexistence='All input/target tensors, stage weights, optimizer and autograd states coexist; CPU reference results retained. One or four processes use CUDA:0, stages/backend explicitly recorded; other services coexist. No physical four-GPU timing interpretation.'),indent=2))
    torch.distributed.barrier()
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.memory._record_memory_history(max_entries=100000)
    try:
        with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA],
                profile_memory=True,record_shapes=True,with_stack=True) as prof:
            with torch.autograd.graph.saved_tensors_hooks(Saved,unpack):
                schedule(forward_step_func=forward_step,data_iterator=iter(range(8)),model=model,
                    num_microbatches=8,seq_length=8,micro_batch_size=1,forward_only=False)
            optimizer.step()
            torch.cuda.synchronize()
        prof.export_chrome_trace(str(out/'trace.json'))
        torch.cuda.memory._dump_snapshot(str(out/'allocator_snapshot.pickle'))
        checks = []
        actual = {}
        for name, p in model.named_parameters():
            grad = p.grad.detach().cpu()
            updated = p.detach().cpu()
            actual[name] = dict(initial=initial[name],gradient=grad,updated=updated,
                reference_gradient=expected[name],reference_updated=expected_updated[name])
            checks.append(dict(name=name,elements=p.numel(),gradient_ok=torch.allclose(grad,expected[name],atol=1e-6,rtol=1e-5),
                updated_ok=torch.allclose(updated,expected_updated[name],atol=1e-6,rtol=1e-5),
                max_gradient_abs_error=(grad-expected[name]).abs().max().item()))
        output_ok = rank != args.stages-1 or (len(observed)==8 and all(torch.allclose(v,ref_outputs[i],atol=1e-6,rtol=1e-5) for i,v in observed))
        torch.save(dict(parameters=actual,outputs=observed,reference_outputs=ref_outputs),out/'elementwise.pt')
        report = dict(checks=checks,output_ok=output_ok,finite=all(torch.isfinite(p).all().item() and torch.isfinite(p.grad).all().item() for p in model.parameters()),
            cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            process_max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        (out/'checks.json').write_text(json.dumps(report,indent=2))
        assert output_ok and report['finite'] and all(c['gradient_ok'] and c['updated_ok'] for c in checks)
    finally:
        (out/'lifetime.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
        torch.cuda.memory._record_memory_history(enabled=None)
        parallel_state.destroy_model_parallel()
        torch.distributed.destroy_process_group()

if __name__ == '__main__':
    main()
