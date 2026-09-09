import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import statistics

ROOT = Path(__file__).resolve().parent
rows = json.loads((ROOT / 'results/measurements.json').read_text())
fig, axes = plt.subplots(1, 3, figsize=(12, 4), constrained_layout=True)
for ax, key, title, scale in zip(axes, ['wall_s', 'plan_host_s', 'stream_span_ms'],
                               ['Complete 36-layer call', 'Sum of host plan calls', 'CUDA stream span (includes gaps)'],
                               [1000, 1000, 1]):
    labels = []
    for x, (case, policy) in enumerate((c, p) for c in ['128-256', '1024-2048'] for p in ['plan_per_layer', 'reuse_plan']):
        vals = [r[key] * scale for r in rows if r['case'] == case and r['policy'] == policy]
        ax.bar(x, statistics.median(vals), color='#3b78a0' if policy == 'plan_per_layer' else '#e09a40', alpha=.7)
        ax.scatter([x] * len(vals), vals, c='black', s=12, zorder=3)
        labels.append(case + '\n' + ('36 plans' if policy == 'plan_per_layer' else '1 plan'))
    ax.set_xticks(range(4), labels, fontsize=8)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel('milliseconds')
    ax.set_ylim(bottom=0)
fig.suptitle('Fixed 36 attention layers, 2 requests; every measured trial shown')
fig.savefig(ROOT / 'timings.png', dpi=160)
fig.savefig(ROOT / 'timings.svg')
