import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent;P=ROOT/'results/replay-v1'
stats=[json.loads(l) for l in (P/'scheduler.jsonl').read_text().splitlines()]
fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
for i,mode in enumerate(['original','permuted']):
 rows=[json.loads(l) for l in (P/f'{mode}-requests.jsonl').read_text().splitlines()];samples=[s for s in stats if s['case']==mode]
 for key,label in [('actual_dispatch_s','Dispatched'),('end_s','Completed')]:
  ts=sorted(r[key] for r in rows);axes[i,0].step(ts,range(1,len(ts)+1),where='post',label=label)
 for key in ['waiting','running']:axes[i,1].plot([s['t_s'] for s in samples],[s[key] for s in samples],label=key)
 axes[i,2].plot([s['t_s'] for s in samples],[100*s['kv_usage'] for s in samples],label='KV occupancy')
 for j,unit in enumerate(['Cumulative requests','Sampled requests','Sampled KV pool %']):
  ax=axes[i,j];ax.axvline(120,color='gray',ls=':');ax.set(title=mode,ylabel=unit,xlabel='Seconds since arrival-window start');ax.grid(alpha=.2);ax.legend(fontsize=8)
for i in range(2):
 axes[i,1].set_ylim(-.2,7.5);axes[i,2].set_ylim(-.05,2.2)
fig.suptitle('ServeGen arrivals and length pairs: original vs temporal permutation\nSynthetic tokens, forced output; one run per case, same 480 tasks and timestamps')
for ext in ['svg','png']:fig.savefig(ROOT/f'results/timeline.{ext}',dpi=150)
