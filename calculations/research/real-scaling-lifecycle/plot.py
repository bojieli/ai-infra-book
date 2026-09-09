"""Standalone research figure from the frozen real fit and cost scenario."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
result = json.loads((HERE/'result.json').read_text())
fit = json.loads((HERE.parents[2]/result['fit_source']['file']).read_text())['primary']['result']
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout='constrained')
for split, color, marker in [('fit','#276FBF','o'),('holdout','#D45A28','s')]:
    rows = [r for r in fit['predictions'] if r['split']==split]
    axes[0].scatter([r['loss'] for r in rows], [r['predicted_loss'] for r in rows], color=color, marker=marker, label=f'{split}: {len(rows)} real points')
values = [r['loss'] for r in fit['predictions']]+[r['predicted_loss'] for r in fit['predictions']]
axes[0].plot([min(values),max(values)],[min(values),max(values)], color='gray', linestyle='--', linewidth=1)
axes[0].set(xlabel='Observed C4 loss (nats/token)', ylabel='Predicted loss (nats/token)', title=f"Finite-grid fit; holdout RMSE {fit['holdout_rmse']:.5f}")
axes[0].legend()
calls = np.geomspace(1,1e9,160)
for row in result['variants'][0]['lifecycle']['rows']:
    if not row['feasible']: continue
    outside = row['outside_fit_box']
    axes[1].plot(calls,row['upfront_cost']+calls*row['cost_per_call'], linestyle='--' if outside else '-',label=f"N={row['N']/1e9:g}B" + ('; outside fit box' if outside else ''))
axes[1].set(xscale='log',yscale='log',xlabel='Lifetime calls (512 input; 128 returned tokens)',ylabel='Declared abstract cost units',title='Target loss 2.9; training + inference proxy')
axes[1].legend(fontsize=8)
for ax in axes: ax.grid(alpha=.2)
fig.suptitle('Real-data fit and conditional lifecycle — no hardware price or task-quality claim',fontsize=11)
fig.savefig(HERE/'real-scaling-lifecycle.png',dpi=160)
fig.savefig(HERE/'real-scaling-lifecycle.svg')
