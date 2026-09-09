#!/usr/bin/env python3
"""Actual FlashInfer plan reuse benchmark; importing this file does not touch CUDA."""
import argparse
import contextlib
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import time

ROOT = Path(__file__).resolve().parent
LAYERS, QH, KH, HD, PAGE = 36, 32, 8, 128, 16


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=ROOT / 'results')
    ap.add_argument('--trials', type=int, default=7)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    import torch
    import flashinfer
    import flashinfer.decode
    from torch.profiler import profile, ProfilerActivity, record_function
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.manual_seed(508)
    assert args.trials > 0
    source = Path(flashinfer.decode.__file__)
    expected = sha(ROOT / 'sources/flashinfer-decode.py')
    assert sha(source) == expected, 'Installed source differs from reviewed source'
    config = json.loads((ROOT / 'sources/qwen3-config.json').read_text())
    assert [config[k] for k in ['num_hidden_layers', 'num_attention_heads', 'num_key_value_heads', 'head_dim']] == [LAYERS, QH, KH, HD]
    dump(args.output / 'environment.json', {
        'python': platform.python_version(), 'torch': torch.__version__,
        'flashinfer': flashinfer.__version__, 'cuda': torch.version.cuda,
        'device': torch.cuda.get_device_name(), 'capability': torch.cuda.get_device_capability(),
        'run_sha256': sha(__file__), 'decode_sha256': sha(source),
        'qwen_config_sha256': sha(ROOT / 'sources/qwen3-config.json'),
        'trials': args.trials, 'layers': LAYERS, 'q_heads': QH, 'kv_heads': KH,
        'head_dim': HD, 'page_size': PAGE, 'seed': 508,
        'backend': 'CUDA-core decode (use_tensor_cores=False)',
        'fixed_metadata_buffers': True, 'graph_capture': False,
    })

    def metadata(lengths):
        pages = [(n + PAGE - 1) // PAGE for n in lengths]
        indptr = [0]
        for n in pages:
            indptr.append(indptr[-1] + n)
        values = [indptr, list(range(sum(pages))), [(n - 1) % PAGE + 1 for n in lengths]]
        return [torch.tensor(v, dtype=torch.int32).pin_memory() for v in values]

    def wrapper(meta):
        workspace = torch.zeros(128 * 1024 * 1024, dtype=torch.uint8, device='cuda')
        return flashinfer.BatchDecodeWithPagedKVCacheWrapper(
            workspace, 'NHD', use_cuda_graph=True, use_tensor_cores=False,
            paged_kv_indptr_buffer=torch.empty_like(meta[0], device='cuda'),
            paged_kv_indices_buffer=torch.empty_like(meta[1], device='cuda'),
            paged_kv_last_page_len_buffer=torch.empty_like(meta[2], device='cuda'))

    def plan(w, meta):
        w.plan(*meta, QH, KH, HD, PAGE, pos_encoding_mode='NONE',
               q_data_type=torch.bfloat16, kv_data_type=torch.bfloat16, non_blocking=True)

    def reference(q, kv, meta):
        # Independent explicit GQA attention, no FlashInfer or SDPA calls.
        outputs = []
        for b in range(q.shape[0]):
            ids = meta[1][int(meta[0][b]):int(meta[0][b + 1])].to('cuda', dtype=torch.long)
            n = (len(ids) - 1) * PAGE + int(meta[2][b])
            k = kv[ids, 0].reshape(-1, KH, HD)[:n].float().repeat_interleave(QH // KH, 1)
            v = kv[ids, 1].reshape(-1, KH, HD)[:n].float().repeat_interleave(QH // KH, 1)
            scores = torch.einsum('hd,shd->hs', q[b].float(), k) / math.sqrt(HD)
            outputs.append(torch.einsum('hs,shd->hd', scores.softmax(-1), v))
        return torch.stack(outputs)

    def check(actual, expected):
        delta = (actual.float() - expected.float()).abs()
        ok = bool(torch.allclose(actual.float(), expected.float(), atol=0.005, rtol=0.02))
        return {'passed': ok, 'max_abs': float(delta.max()), 'rmse': float(delta.square().mean().sqrt())}

    rows, checks = [], []
    rng = random.Random(508)
    for lengths in ([128, 256], [1024, 2048]):
        label = '-'.join(map(str, lengths))
        meta = metadata(lengths)
        npages = len(meta[1])
        qs = torch.randn(LAYERS, len(lengths), QH, HD, device='cuda', dtype=torch.bfloat16)
        kvs = torch.randn(LAYERS, npages, 2, PAGE, KH, HD, device='cuda', dtype=torch.bfloat16)
        outs = torch.empty_like(qs)
        w = wrapper(meta)
        t0 = time.perf_counter()
        plan(w, meta)
        for i in range(LAYERS):
            w.run(qs[i], kvs[i], out=outs[i], enable_pdl=False)
        torch.cuda.synchronize()
        dump(args.output / ('startup-' + label + '.json'), {'first_plan_and_36_runs_s': time.perf_counter() - t0,
             'includes_possible_jit': True, 'kv_tensor_bytes': kvs.numel() * kvs.element_size(),
             'metadata_input_bytes': sum(t.numel() * t.element_size() for t in meta)})
        refs = torch.stack([reference(qs[i], kvs[i], meta) for i in range(LAYERS)])
        initial = check(outs, refs)
        checks.append({'case': label, 'phase': 'independent_fp32', **initial})
        dump(args.output / 'checks.json', checks)
        assert initial['passed'], initial
        golden = outs.clone()
        torch.save({'queries': qs.cpu(), 'kv': kvs.cpu(), 'metadata': [x.cpu() for x in meta],
                    'reference_fp32': refs.cpu(), 'flashinfer_initial': golden.cpu()},
                   args.output / ('inputs-' + label + '.pt'))

        def workload(policy, traced=False):
            # No per-layer synchronize: measure actual enqueue/overlap critical path.
            calls = 0
            plan_host = run_host = 0.0
            for i in range(LAYERS):
                if policy == 'plan_per_layer' or i == 0:
                    ctx = record_function('plan/' + str(i)) if traced else contextlib.nullcontext()
                    with ctx:
                        a = time.perf_counter()
                        plan(w, meta)
                        plan_host += time.perf_counter() - a
                    calls += 1
                ctx = record_function('run/' + str(i)) if traced else contextlib.nullcontext()
                with ctx:
                    a = time.perf_counter()
                    w.run(qs[i], kvs[i], out=outs[i], enable_pdl=False)
                    run_host += time.perf_counter() - a
            return calls, plan_host, run_host

        for policy in ['plan_per_layer', 'reuse_plan']:
            for _ in range(2):
                workload(policy)
        torch.cuda.synchronize()
        for trial in range(args.trials):
            order = ['plan_per_layer', 'reuse_plan']
            rng.shuffle(order)
            for order_index, policy in enumerate(order):
                torch.cuda.synchronize()
                start, end = [torch.cuda.Event(enable_timing=True) for _ in range(2)]
                a = time.perf_counter()
                start.record()
                calls, plan_host, run_host = workload(policy)
                end.record()
                end.synchronize()
                wall = time.perf_counter() - a
                verdict = check(outs, refs)
                rows.append({'case': label, 'trial': trial, 'order_index': order_index,
                             'policy': policy, 'plan_calls': calls, 'run_calls': LAYERS,
                             'plan_host_s': plan_host, 'run_host_s': run_host,
                             'wall_s': wall, 'stream_span_ms': start.elapsed_time(end),
                             'exact_equal_initial': bool(torch.equal(outs, golden)), **verdict})
                dump(args.output / 'measurements.json', rows)
                assert verdict['passed'], verdict
                print(json.dumps(rows[-1]), flush=True)

        # Separate profiled runs: never merge their times with formal samples.
        for policy in ['plan_per_layer', 'reuse_plan']:
            torch.cuda.synchronize()
            with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA], record_shapes=True) as prof:
                with record_function('formal_workload/' + policy):
                    workload(policy, traced=True)
                torch.cuda.synchronize()
            prof.export_chrome_trace(str(args.output / ('trace-' + label + '-' + policy + '.json')))

        # Explicit H2D copy control is a separate operation, not subtraction from plan.
        dst = [torch.empty_like(t, device='cuda') for t in meta]
        copy_rows = []
        for trial in range(args.trials):
            torch.cuda.synchronize()
            ev0, ev1 = [torch.cuda.Event(enable_timing=True) for _ in range(2)]
            a = time.perf_counter()
            ev0.record()
            for _ in range(36):
                for target, source_tensor in zip(dst, meta):
                    target.copy_(source_tensor, non_blocking=True)
            ev1.record()
            ev1.synchronize()
            copy_rows.append({'trial': trial, 'wall_s': time.perf_counter() - a,
                              'stream_span_ms': ev0.elapsed_time(ev1), 'copies': 108,
                              'payload_bytes': 36 * sum(t.numel() * t.element_size() for t in meta)})
            assert all(torch.equal(x.cpu(), y) for x, y in zip(dst, meta))
        dump(args.output / ('copy-control-' + label + '.json'), copy_rows)

        # Fresh metadata objects do not mutate wrapper-owned buffers. Keep page count fixed.
        changed = [x.clone().pin_memory() for x in meta]
        changed[2].fill_(1)
        sentinel_q = torch.zeros_like(qs[0])
        sentinel_kv = torch.zeros_like(kvs[0])
        for b in range(len(lengths)):
            last_id = int(meta[1][int(meta[0][b + 1]) - 1])
            sentinel_kv[last_id, 1, 1:].fill_(8)
        plan(w, meta)
        stale = w.run(sentinel_q, sentinel_kv, enable_pdl=False).clone()
        expected_new = reference(sentinel_q, sentinel_kv, changed)
        stale_check = check(stale, expected_new)
        plan(w, changed)
        updated = w.run(sentinel_q, sentinel_kv, enable_pdl=False).clone()
        updated_check = check(updated, expected_new)
        plan(w, meta)
        restored = w.run(sentinel_q, sentinel_kv, enable_pdl=False).clone()
        torch.cuda.synchronize()
        change_record = {'case': label, 'stale_vs_new': stale_check, 'replanned_vs_new': updated_check,
                         'restored_equals_old': bool(torch.equal(stale, restored)),
                         'old_lengths': lengths, 'new_lengths': [n - 15 for n in lengths]}
        checks.append(change_record)
        dump(args.output / 'checks.json', checks)
        torch.save({'q': sentinel_q.cpu(), 'kv': sentinel_kv.cpu(), 'old_metadata': [x.cpu() for x in meta],
                    'new_metadata': [x.cpu() for x in changed], 'stale': stale.cpu(),
                    'replanned': updated.cpu(), 'expected_new': expected_new.cpu(), 'restored': restored.cpu()},
                   args.output / ('metadata-change-' + label + '.pt'))
        assert not stale_check['passed'] and updated_check['passed'] and change_record['restored_equals_old']
        del w, qs, kvs, outs, refs, golden, sentinel_q, sentinel_kv
        torch.cuda.empty_cache()
    dump(args.output / 'execution.json', {'status': 'completed', 'groups': len(rows),
         'elapsed_end_unix_s': time.time(), 'run_sha256': sha(__file__)})


if __name__ == '__main__':
    main()
