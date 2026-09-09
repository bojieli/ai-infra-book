import json,statistics,math
from pathlib import Path
import matplotlib.pyplot as plt
root=Path(__file__).absolute().parent;data=json.loads((root/'analysis.json').read_text());conditions=[('serial',r) for r in [1,4,16]]+[('continuous',r) for r in [1,4,16]]+[('offline',None)];labels=['Serial\n1/s','Serial\n4/s','Serial\n16/s','Continuous\n1/s','Continuous\n4/s','Continuous\n16/s','Offline\nburst']
fig,axes=plt.subplots(2,2,figsize=(13,8),layout='constrained')
for ax,key,title,unit in [(axes[0,0],'slo_goodput_per_s','Correct and completed within 3 s','Qualified requests/s'),(axes[0,1],'p95_latency_s','Per-window p95 (16 requests: nearest-rank maximum)','Intended arrival to completion (s)'),(axes[1,0],'component_gross_j_per_qualified','Gross GPU + CPU-package energy / qualified result','Component joules / qualified request'),(axes[1,1],'correct','Task quality, independent of latency SLO','Strictly correct / 16 requests')]:
 for rep in range(3):
  rows=[next(g for g in data['groups'] if g['rep']==rep and (g['service'],g['rate'])==c) for c in conditions]
  ax.plot(range(7),[r[key] if r[key] is not None else math.nan for r in rows],marker='o',label=f'repeat {rep}',alpha=.75)
 ax.set(xticks=range(7),xticklabels=labels,title=title,ylabel=unit);ax.tick_params(axis='x',labelsize=8);ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8)
axes[1,1].set_ylim(0,17)
fig.suptitle('Qwen3-8B: same eight tasks, 336 formal requests\nShared host; component energy is not whole-machine energy; finite windows, not steady-state capacity',fontsize=12)
for ext in ['png','svg']:fig.savefig(root/('service-energy.'+ext),dpi=160)
