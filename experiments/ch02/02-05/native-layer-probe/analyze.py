"""Offline verification of the final successful four-layer probe only."""
from pathlib import Path
import hashlib
import json

B = Path(__file__).resolve().parent
P = B / 'attempt-05'
def read(name):
    return json.loads((P / 'results' / name).read_text())
sup, cfg, requests = read('supervisor.json'), read('config.json'), read('requests.json')
completion, ready, final = read('completion.json'), read('ready.json'), read('finally.json')
checks = {
    'exit_zero': sup['exit_code'] == 0,
    'no_monitor_termination': sup['reason'] is None,
    'no_residual_processes_signalled': sup['residual_pids_signalled'] == [],
    'four_layers': json.loads(cfg['json_model_override_args']) == dict(num_hidden_layers=4, compress_ratios=[0, 0, 4, 128]),
    'final_parameters': all(cfg[k] == v for k, v in dict(cpu_offload_gb=8, context_length=1024, max_total_tokens=2048, max_running_requests=1, chunked_prefill_size=256, mem_fraction_static=.9, swa_full_tokens_ratio=1.0, disable_cuda_graph=True, disable_radix_cache=True).items()),
    'two_completed_requests': len(requests) == 2 and completion['requests'] == 2 and completion['status'] == 'native_truncated_forward_returned',
    'lifecycle': sup['start'] <= ready['time'] <= completion['time'] <= final['time'] <= sup['end'] and final['engine_created'],
    'sampled_gpu_within_limit': sup['peak_gpu_mib'] <= 24 * 1024,
    'sampled_rss_within_limit': sup['peak_rss_bytes'] <= 50 * 1024**3,
    'sampled_memory_available': bool(sup['samples']) and min(s['available_bytes'] for s in sup['samples']) >= 24 * 1024**3,
}
for i, (q, length) in enumerate(zip(requests, (256, 512))):
    response = q['response']; meta = response['meta_info']; ids = response['output_ids']
    checks[f'request_{i}_input'] = q['input_ids'] == ([1000, 1001, 1002, 1003] * 128)[:length]
    checks[f'request_{i}_output'] = len(ids) == 4 and all(isinstance(x, int) and x >= 0 for x in ids) and meta['completion_tokens'] == 4 and meta['prompt_tokens'] == length and meta['finish_reason']['type'] == 'length' and meta['cached_tokens'] == 0
    checks[f'request_{i}_lifecycle'] = ready['time'] <= q['sent'] <= q['end'] <= completion['time']
for name, status in [('jit-preflight', 'original_compress_plan_compiled_only_no_inference'), ('jit-mhc-preflight', 'original_mhc_compiled_only_no_model_or_numerical_check')]:
    result = json.loads((B / name / 'result.json').read_text())
    checks[name] = result['status'] == status and all(hashlib.sha256((B / name / r['path']).read_bytes()).hexdigest() == r['sha256'] for r in result['files'])
for manifest, key in [('source-hashes.json', 'file'), ('raw-transfer-manifest.json', 'path')]:
    rows = json.loads((B / manifest).read_text())
    checks[manifest] = all(hashlib.sha256((B / r[key]).read_bytes()).hexdigest() == r['sha256'] for r in rows)
report = dict(scope='four-layer native loading and synthetic forward only', attempt='attempt-05', exit_code=sup['exit_code'], requests_completed=len(requests), ready_elapsed_s=ready['elapsed'], request_wall_seconds=[q['end']-q['sent'] for q in requests], peak_gpu_mib=sup['peak_gpu_mib'], peak_rss_bytes=sup['peak_rss_bytes'], truncated_runtime_probe_complete=all(checks.values()), full_model_or_quality_pass=False, checks=checks)
text = json.dumps(report, indent=2) + '\n'
(B / 'analysis.json').write_text(text)
print(text, end='')
raise SystemExit(0 if all(checks.values()) else 1)
