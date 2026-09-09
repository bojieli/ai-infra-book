#!/usr/bin/env python3
"""Offline analysis: only accepts a fully completed run, never invents missing timing."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, default=ROOT / 'results')
    args = ap.parse_args()
    p = args.results
    read = lambda name: json.loads((p / name).read_text())
    done, env, rows, checks = [read(n) for n in ['execution.json', 'environment.json', 'measurements.json', 'checks.json']]
    assert done['status'] == 'completed'
    assert done['run_sha256'] == env['run_sha256'] == hashlib.sha256((ROOT / 'run.py').read_bytes()).hexdigest()
    assert env['decode_sha256'] == hashlib.sha256((ROOT / 'sources/flashinfer-decode.py').read_bytes()).hexdigest()
    assert env['qwen_config_sha256'] == hashlib.sha256((ROOT / 'sources/qwen3-config.json').read_bytes()).hexdigest()
    assert len(rows) == 4 * env['trials'] == done['groups']
    assert len({(r['case'], r['trial'], r['policy']) for r in rows}) == len(rows)
    assert all(r['passed'] and r['run_calls'] == 36 and r['plan_calls'] == (36 if r['policy'] == 'plan_per_layer' else 1) for r in rows)
    assert len(checks) == 4
    for c in checks:
        if c.get('phase') == 'independent_fp32':
            assert c['passed']
        else:
            assert not c['stale_vs_new']['passed'] and c['replanned_vs_new']['passed'] and c['restored_equals_old']
    groups = []
    for case in sorted({r['case'] for r in rows}):
        for policy in ['plan_per_layer', 'reuse_plan']:
            subset = [r for r in rows if r['case'] == case and r['policy'] == policy]
            assert sorted(r['trial'] for r in subset) == list(range(env['trials']))
            medians = {k: statistics.median(r[k] for r in subset) for k in
                       ['wall_s', 'stream_span_ms', 'plan_host_s', 'run_host_s']}
            groups.append({'case': case, 'policy': policy, 'medians': medians,
                           'exact_equal_initial_count': sum(r['exact_equal_initial'] for r in subset)})
    # Preserve CUPTI events as recorded. memcpy durations may overlap, so sums are not wall time.
    trace_report = []
    for f in sorted(p.glob('trace-*.json')):
        events = json.loads(f.read_text())['traceEvents']
        copies = [e for e in events if e.get('ph') == 'X' and 'memcpy' in e.get('cat', '').lower()]
        kernels = [e for e in events if e.get('ph') == 'X' and e.get('cat') == 'kernel']
        ranges = [e for e in events if e.get('ph') == 'X' and e.get('cat') == 'user_annotation'
                  and e.get('name', '').startswith(('plan/', 'run/'))]
        trace_report.append({'file': f.name, 'kernel_count': len(kernels), 'copies': copies,
                             'host_ranges': ranges, 'copy_duration_sum_us': sum(e['dur'] for e in copies),
                             'copy_payload_bytes': sum(e.get('args', {}).get('bytes', 0) for e in copies),
                             'copy_sum_is_not_critical_path': True})
    assert len(trace_report) == 4
    summary = {'groups': groups, 'checks': checks, 'traces': trace_report,
               'limitations': ['Random independent per-layer Q/K/V, not full model or sequential hidden-state chain.',
               'Stream span includes host gaps; host plan includes implicit copies and native planner.',
               'Explicit copy control is separate and must not be subtracted from plan.',
               'Graph-compatible fixed metadata buffers used, but no CUDA Graph captured.',
               'No hardware counter or physical bandwidth claim; profiled times are separate.']}
    (ROOT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'groups': groups, 'checks_passed': True}, indent=2))


if __name__ == '__main__':
    main()
