import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent;r=json.loads((ROOT/'results/followup-summary.json').read_text())
fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
for kind,color in [('short','#3388ae'),('long','#d57936')]:
    rows=[x for x in r['rows'] if x['kind']==kind]
    for ax,key,label in zip(axes,['ttft_ms','tpot_ms','throughput'],['TTFT (ms)','Client TPOT (ms)','Output tokens/s']):
        ax.plot([x['batch'] for x in rows],[x[key] for x in rows],'-o',color=color,label='2048 tokens' if kind=='short' else '8192 tokens')
        for x in r['batches']:
            if x['kind']==kind:ax.scatter(x['batch'],x[key],s=15,color=color,alpha=.5)
        ax.set(ylabel=label,xlabel='Requested concurrency');ax.set_xticks([1,16]);ax.grid(alpha=.2)
axes[0].legend()
fig.suptitle('APC off for both nested prompt lengths; same eager engine\n3 trials per case, 256 forced output tokens; no per-step scheduler logging')
fig.savefig(ROOT/'results/followup.svg');fig.savefig(ROOT/'results/followup.png',dpi=160)
