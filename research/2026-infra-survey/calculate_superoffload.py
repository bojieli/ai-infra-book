#!/usr/bin/env python3
"""Teaching calculation only: one Qwen3 gate gradient, no hardware benchmark."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json'


def calculate():
    q = json.loads(CONFIG.read_text())
    n = q['hidden_size'] * q['intermediate_size']
    low, high = 2*n, 4*n
    cpu_bw, gpu_bw = 100*10**9, 1500*10**9
    cpu_cast, gpu_cast = F(low+high, cpu_bw), F(low+high, gpu_bw)
    rows = []
    for bw in [32*10**9, 300*10**9]:
        a = F(low, bw) + cpu_cast
        b = gpu_cast + F(high, bw)
        rows.append(dict(effective_link_Bps=bw,
                         transfer_low_ms=float(F(low, bw)*1000),
                         transfer_high_ms=float(F(high, bw)*1000),
                         cpu_cast_path_ms=float(a*1000),
                         gpu_cast_path_ms=float(b*1000),
                         faster='cpu_cast' if a < b else 'gpu_cast'))
    return dict(kind='teaching_assumptions_not_measured',
                config_file=str(CONFIG.relative_to(ROOT)),
                config_sha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
                matrix=[q['intermediate_size'], q['hidden_size']], elements=n,
                low_bytes=low, high_bytes=high, cast_read_write_bytes=low+high,
                effective_cpu_cast_Bps=cpu_bw, effective_gpu_cast_Bps=gpu_bw,
                cpu_cast_ms=float(cpu_cast*1000), gpu_cast_ms=float(gpu_cast*1000),
                link_crossover_Bps=float(F(high-low, 1)/(cpu_cast-gpu_cast)),
                cases=rows,
                incremental_capacity=dict(cpu_cast_host_bytes=low+high,
                                          gpu_cast_host_bytes=high,
                                          cpu_cast_gpu_bytes=0,
                                          gpu_cast_gpu_bytes=high),
                limitations=['Single dependent conversion/transfer chain; no overlap assumed.',
                             'Both host paths use preallocated pinned buffers.',
                             'Common GPU low-precision gradient, optimizer states and return path excluded.',
                             'No launch, allocation, NUMA, contention or whole-step performance prediction.'])


if __name__ == '__main__':
    result = calculate()
    Path(__file__).with_name('superoffload-arithmetic.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
