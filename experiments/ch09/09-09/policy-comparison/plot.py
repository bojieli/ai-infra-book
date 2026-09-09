import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
rows=json.loads((R/'summary.json').read_text())['groups']
fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for ax,key,title in zip(axes,['target_median_s','pair_median_s'],['Target completion','Both jobs complete']):
 for p,marker in [('cache_first','o'),('queue_first','s'),('predicted_completion','^')]:
  data=[r for r in rows if r['policy']==p]
  ax.plot([r['output_budget'] for r in data],[r[key] for r in data],marker=marker,label=p)
 ax.set(title=title,xlabel='Background output tokens',ylabel='Median seconds',xticks=[8,32,128]);ax.grid(alpha=.2)
axes[0].legend(fontsize=8)
fig.suptitle('Two trials per condition; two workers share one GPU')
fig.savefig(R/'comparison.png',dpi=170)
