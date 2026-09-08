#!/usr/bin/env python3
"""Book arithmetic and small FP64 checks; no GPU or upstream code execution."""
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json'


def online(scores, values, block):
    """One row, unnormalized output accumulator; -inf entries are masked."""
    m, total = -math.inf, 0.0
    output = [0.0] * len(values[0])
    for start in range(0, len(scores), block):
        end = min(start + block, len(scores))
        new_m = max(m, max(scores[start:end]))
        if new_m == -math.inf:
            continue
        scale = math.exp(m - new_m)
        probs = [math.exp(s - new_m) for s in scores[start:end]]
        output = [scale * old + sum(p * values[start + j][k] for j, p in enumerate(probs))
                  for k, old in enumerate(output)]
        total = scale * total + sum(probs)
        m = new_m
    if not total:
        raise ValueError('At least one unmasked entry is required')
    return [v / total for v in output]


def calculate():
    config = json.loads(CONFIG.read_text())
    d, n, capacity = config['head_dim'], 8192, 128 * 2**10
    rows = []
    for b in [1, 64, 128]:
        # Q and K/V: 2 bytes; S/P, O accumulator and three row vectors: 4 bytes.
        a = min(n, (capacity - 2*b*d) // (6*d + 4*b + 12))
        qblocks, kvblocks = math.ceil(n/a), math.ceil(n/b)
        rows.append(dict(kv_rows=b, query_rows=a, query_blocks=qblocks, kv_blocks=kvblocks,
                         live_bytes=a*(6*d+4*b+12)+2*b*d,
                         interface_bytes=4*n*d*(1+qblocks),
                         block_pair_updates=qblocks*kvblocks,
                         output_rescale_multiplies=n*d*(kvblocks-1)))
    trials = []
    for scores in [[0.0, math.log(2.0)], [-1000.0, 0.0, 1000.0],
                   [1000.0, 1001.0, 1002.0, 998.0, 1003.0],
                   [-math.inf, -math.inf, 3.0, -2.0, 7.0],
                   [2.0, -1.0, -math.inf, -math.inf, -math.inf]]:
        values = [[float(i+1), (-1.0)**i, float(i*i)] for i in range(len(scores))]
        exps = [math.exp(s-max(scores)) for s in scores]
        reference = [sum(p*v[k] for p,v in zip(exps, values))/sum(exps) for k in range(3)]
        for block in [1, 2, 3, len(scores)]:
            got = online(scores, values, block)
            error = max(abs(a-b) for a,b in zip(reference, got))
            assert error < 1e-12
            trials.append(dict(length=len(scores), block=block, max_abs_error=error))
    good = online([0.0, math.log(2.0)], [[1.0], [3.0]], 1)[0]
    printed_inverse = (2.0*1.0+3.0)/(0.5+1.0)
    assert math.isclose(good, 7/3) and math.isclose(printed_inverse, 10/3)
    return dict(config_file=str(CONFIG.relative_to(ROOT)),
                config_sha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
                scope='One query head and its K/V head; full unmasked forward attention; abstract two-level sequential schedule.',
                n=n, d=d, fast_capacity_bytes=capacity, matrix_flops=4*n*n*d,
                compulsory_input_output_bytes=8*n*d, full_score_fp32_bytes=4*n*n,
                separate_score_probability_read_write_bytes=16*n*n,
                rows=rows, fp64_checks=trials,
                rescale_counterexample=dict(correct=good, literal_inverse=printed_inverse),
                upstream_code_executed=False, hardware_experiments_run=False)


if __name__ == '__main__':
    result = calculate()
    Path(__file__).with_name('attention-tiles-arithmetic.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(rows=result['rows'], fp64_checks=len(result['fp64_checks']),
                          rescale_counterexample=result['rescale_counterexample']), indent=2))
