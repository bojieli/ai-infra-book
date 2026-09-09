"""Plot author samples, keeping stage/device changes explicit."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).absolute().parent
fig, axes=plt.subplots(2, 1, figsize=(9, 6), constrained_layout=True)
for filename,label in [('history-28jt9vhg.json','stage 1: 384 configured ranks'),
                       ('history-uliytlp7.json','stage 2: 384 configured ranks'),
                       ('history-8ey7uow0.json','decay: 288 configured ranks'),
                       ('final-history-sampled10000.json','final decay: 192 configured ranks')]:
    h=json.loads((B/'wandb'/filename).read_text())['data']['project']['run']['sampledHistory'][0]
    axes[0].scatter([x['iteration_step']/1e6 for x in h], [x['time_per_iteration_ms'] for x in h],s=3,label=label,alpha=.5)
h=json.loads((B/'wandb/final-history-sampled10000.json').read_text())['data']['project']['run']['sampledHistory'][0]
axes[0].set(yscale='log',xlabel='Global resumed step (millions)',ylabel='Logged iteration time (ms)',title='Public SmolLM3 samples; stages are not a matched scaling experiment')
axes[0].legend(fontsize=8,markerscale=3)
axes[1].plot([x['iteration_step']-4706000 for x in h],[x['_timestamp']-h[0]['_timestamp'] for x in h],lw=1)
axes[1].set(xlabel='Step since final resume (sampled: 10,000 of 14,000)',ylabel='Timestamp elapsed (s)',title='Final segment: global counters include earlier training')
for ax in axes: ax.grid(alpha=.2)
for ext in ['png','svg']:fig.savefig(B/'results'/('public-training.'+ext),dpi=160)
