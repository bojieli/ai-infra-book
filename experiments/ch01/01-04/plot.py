import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent;r=json.loads((ROOT/'results/analysis.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for kind,label,color in [('short','2048 tokens; no cache hit','#3388ae'),('prefix','8192 tokens; 6144 cached','#d57936')]:
    rows=[x for x in r['groups'] if x['kind']==kind];base=rows[0]['tpot_ms']
    axes[0].plot([x['batch'] for x in rows],[x['tpot_ms']/base for x in rows],'-o',label=label,color=color)
    axes[1].plot([x['batch'] for x in rows],[x['throughput'] for x in rows],'-o',label=label,color=color)
    for x in r['batches']:
        if x['kind']==kind:axes[1].scatter(x['batch'],x['throughput'],s=16,color=color,alpha=.5)
axes[0].axhline(1,color='gray',ls='--',label='Weight-only flat-step hypothesis')
axes[0].set(ylabel='Client TPOT / same-group batch1 TPOT',title='Retrospective hypothesis vs observation')
axes[1].set(ylabel='Output tokens/s including prefill',title='Throughput gain has a latency cost')
for ax in axes:ax.set_xscale('log',base=4);ax.set_xticks([1,4,16,64],[1,4,16,64]);ax.set_xlabel('Requested batch (occupancy verified)');ax.legend(fontsize=8);ax.grid(alpha=.2)
fig.suptitle('Same Qwen3-8B / vLLM path, forced 256 output tokens\nLength and APC differ across groups; not a causal length-only comparison')
fig.savefig(ROOT/'results/comparison.svg');fig.savefig(ROOT/'results/comparison.png',dpi=160)
