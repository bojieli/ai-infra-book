import json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
fig,axes=plt.subplots(1,2,figsize=(11,4.5),sharey=True)
for ax,device in zip(axes,['mps','cuda']):
    rows=json.loads((ROOT/f'results/attention-{device}/results.json').read_text())['rows']
    for name,label,color,offset in [('explicit_fp32_intermediates','Explicit FP32 intermediates','#3078b0',-.08),('sdpa_default','Default SDPA','#d47721',.08)]:
        med=[]
        for i,r in enumerate(rows):
            y=r['paths'][name]['samples_wall_us'];med.append(statistics.median(y));ax.scatter([i+offset]*11,y,s=12,color=color,alpha=.4)
        ax.plot([i+offset for i in range(5)],med,'o-',label=label,color=color)
    ax.set_xticks(range(5),['P128','P257','P512','P2048','D2048']);ax.set_title('M2 Max / MPS' if device=='mps' else 'RTX / CUDA')
    ax.set_yscale('log');ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Wall time / eager call (µs)');axes[0].legend(fontsize=8)
fig.suptitle('FP16 attention: identical inputs, different backend paths')
fig.text(.5,.015,'P: causal prefill; D: final query over all KV. 11 samples × 10 calls, submit + synchronize.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.045,1,.94))
for ext in ['svg','png','pdf']:fig.savefig(ROOT/f'results/attention.{ext}',dpi=160)
