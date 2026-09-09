import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent;P=ROOT/'results/arrival-v1'
stats=[json.loads(l) for l in (P/'scheduler.jsonl').read_text().splitlines()]
fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
for i,mode in enumerate(['uniform','phased']):
    rows=[json.loads(l) for l in (P/f'{mode}-requests.jsonl').read_text().splitlines()]
    samples=[s for s in stats if s['case']==mode]
    for kind,color in [('A','#3388ae'),('B','#d57936')]:
        arrivals=sorted(r['actual_dispatch_s'] for r in rows if r['kind']==kind)
        ends=sorted(r['end_s'] for r in rows if r['kind']==kind)
        axes[i,0].step(arrivals,range(1,len(arrivals)+1),where='post',color=color,label=f'{kind} dispatched')
        axes[i,0].step(ends,range(1,len(ends)+1),where='post',color=color,ls='--',label=f'{kind} completed')
    axes[i,1].plot([s['t_s'] for s in samples],[s['waiting'] for s in samples],label='waiting',color='#a84c36')
    axes[i,1].plot([s['t_s'] for s in samples],[s['running'] for s in samples],label='running',color='#3388ae')
    axes[i,2].plot([s['t_s'] for s in samples],[100*s['kv_usage'] for s in samples],color='#558759',label='KV occupancy')
    axes[i,2].set_ylim(0,105)
    for j,unit in enumerate(['Cumulative requests','Sampled requests','Sampled KV pool %']):
        ax=axes[i,j];ax.axvline(60,color='gray',ls=':',lw=1);ax.axvline(120,color='black',ls=':',lw=1)
        ax.set(title=mode,ylabel=unit,xlabel='Seconds since arrival-window start');ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.suptitle('Same 480 requests and 4 rps arrival target; different temporal mixtures\n120-second arrival window followed by real drain; sampled occupancy is not a continuous peak guarantee')
fig.savefig(ROOT/'results/timeline.svg');fig.savefig(ROOT/'results/timeline.png',dpi=160)
