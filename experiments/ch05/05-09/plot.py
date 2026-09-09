import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
raw=json.loads((ROOT/'results/paired-eager-v1/raw.json').read_text())
summary=json.loads((ROOT/'results/summary.json').read_text())
fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
for ax,key,title in zip(axes[:2],['ttft_s','latency_s'],['Time to first token','Complete request']):
    for trial in range(11):
        rows={r['mode']:r for r in raw['requests'] if r['phase']=='measure' and r['trial']==trial}
        ax.plot([0,1],[rows[m][key]*1000 for m in ['native','schedule']],'-o',alpha=.65,lw=1,ms=3)
    ax.set_xticks([0,1],['native','schedule']);ax.set(title=title,ylabel='Client latency (ms)')
for key,label,color in [('ttft_saving_ms','TTFT','#3388ae'),('latency_saving_ms','Complete','#d57936')]:
    axes[2].plot(range(1,12),[p[key] for p in summary['pairs']],'-o',label=label,color=color,ms=4)
axes[2].axhline(0,color='gray',lw=1);axes[2].set(title='Paired savings: native − schedule',xlabel='Trial',ylabel='Milliseconds; positive favors schedule');axes[2].legend()
for ax in axes:ax.grid(alpha=.2)
fig.suptitle('Actual 36-layer replacement: one prompt, 7239 input / 32 forced output tokens\nSame eager engine, concurrency 1, APC off; 11 paired trials')
fig.savefig(ROOT/'results/comparison.svg');fig.savefig(ROOT/'results/comparison.png',dpi=160)
