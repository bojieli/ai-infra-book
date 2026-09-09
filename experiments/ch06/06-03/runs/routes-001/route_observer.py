"""Private route observation; intentionally synchronized, not performance-neutral."""
import functools
import hashlib
import inspect
import json
import os
from pathlib import Path
import time


def install():
    import torch
    from sglang.srt.models.deepseek_v4 import DeepseekV4Model, DeepseekV4DecoderLayer
    from sglang.srt.layers.moe.topk import TopK
    from sglang.srt.layers.moe.hash_topk import HashTopK
    if getattr(DeepseekV4Model.forward, '_route_observer', False):
        return
    out = Path(os.environ['V4_ROUTE_OUT'])
    ctx = {'batch': None, 'layer': None, 'seq': 0}
    records = out / 'routes'
    records.mkdir(exist_ok=True)
    sources = {}
    for cls in (DeepseekV4Model, TopK, HashTopK):
        p = Path(inspect.getfile(cls))
        sources[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    (records / f'{os.getpid()}-installed.json').write_text(json.dumps(dict(pid=os.getpid(), sources=sources, observer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2))
    original_model = DeepseekV4Model.forward
    model_sig = inspect.signature(original_model)
    original_layer = DeepseekV4DecoderLayer.forward
    layer_sig = inspect.signature(original_layer)

    @functools.wraps(original_model)
    def model(self, *args, **kwargs):
        assert ctx['batch'] is None, 'nested model forward unsupported'
        phase = json.loads((out / 'phase.json').read_text())
        bound = model_sig.bind(self, *args, **kwargs)
        fb = bound.arguments['forward_batch']
        input_ids = bound.arguments['input_ids']
        positions = bound.arguments['positions']
        ctx['seq'] += 1
        batch = dict(pid=os.getpid(), sequence=ctx['seq'], request_phase=phase,
                     host_start=time.monotonic(), routes=[],
                     mode=getattr(fb.forward_mode, 'name', str(fb.forward_mode)),
                     is_decode=bool(fb.forward_mode.is_decode()),
                     is_extend=bool(fb.forward_mode.is_extend()),
                     batch_size=int(fb.batch_size),
                     num_token_non_padded_cpu=int(fb.num_token_non_padded_cpu),
                     input_shape=list(input_ids.shape), positions_shape=list(positions.shape),
                     _input_ids=input_ids.detach().clone(), _positions=positions.detach().clone(),
                     _num_non_padded=(fb.num_token_non_padded.detach().clone() if fb.num_token_non_padded is not None else None))
        ctx['batch'] = batch
        try:
            result = original_model(self, *args, **kwargs)
            batch['model_host_return'] = time.monotonic()
            torch.cuda.synchronize()
            batch['observer_sync_end'] = time.monotonic()
            batch['input_ids'] = batch.pop('_input_ids').cpu().tolist()
            batch['positions'] = batch.pop('_positions').cpu().tolist()
            non_padded = batch.pop('_num_non_padded')
            batch['num_token_non_padded_gpu'] = int(non_padded.cpu().item()) if non_padded is not None else None
            for row in batch['routes']:
                begin, end = row.pop('_events')
                row['route_cuda_observed_ms'] = begin.elapsed_time(end)
                row['ids'] = row.pop('_ids').cpu().tolist()
                row['weights'] = row.pop('_weights').cpu().tolist()
            batch['observer_copy_end'] = time.monotonic()
            with (records / f'{os.getpid()}-batches.jsonl').open('a') as f:
                f.write(json.dumps(batch, separators=(',', ':')) + '\n')
            return result
        finally:
            ctx['batch'] = None
            ctx['layer'] = None

    @functools.wraps(original_layer)
    def layer(self, *args, **kwargs):
        assert ctx['batch'] is not None
        bound = layer_sig.bind(self, *args, **kwargs)
        fb = bound.arguments['forward_batch']
        mode = fb.forward_mode
        ctx['layer'] = dict(layer_id=self.layer_id, mode=getattr(mode, 'name', str(mode)),
                            batch_size=int(fb.batch_size))
        try:
            return original_layer(self, *args, **kwargs)
        finally:
            ctx['layer'] = None

    def wrap_router(cls):
        original = cls.forward
        @functools.wraps(original)
        def router(self, hidden_states, *args, **kwargs):
            assert ctx['batch'] is not None and ctx['layer'] is not None
            begin = torch.cuda.Event(enable_timing=True)
            end = torch.cuda.Event(enable_timing=True)
            start = time.monotonic()
            begin.record()
            result = original(self, hidden_states, *args, **kwargs)
            end.record()
            host_end = time.monotonic()
            assert hasattr(result, 'topk_ids') and hasattr(result, 'topk_weights'), 'explicit standard routes required'
            row = dict(**ctx['layer'], router_class=cls.__name__, tokens=int(hidden_states.shape[0]),
                       host_start=start, host_return=host_end,
                       ids_dtype=str(result.topk_ids.dtype), weights_dtype=str(result.topk_weights.dtype),
                       _events=(begin, end), _ids=result.topk_ids.detach().clone(),
                       _weights=result.topk_weights.detach().clone())
            cfg = getattr(self, 'topk_config', None)
            row['expected_weight_sum'] = (float(cfg.routed_scaling_factor) if cfg is not None and cfg.apply_routed_scaling_factor_on_output else 1.0)
            ctx['batch']['routes'].append(row)
            return result
        cls.forward = router
    wrap_router(TopK)
    wrap_router(HashTopK)
    model._route_observer = True
    DeepseekV4Model.forward = model
    DeepseekV4DecoderLayer.forward = layer
