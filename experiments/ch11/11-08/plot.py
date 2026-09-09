import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;rows=sorted(json.loads((R/'summary.json').read_text())['rows'],key=lambda r:(not r['thinking'],r['total_output_budget'],r['trial']))
fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
labels=[f"{'think' if r['thinking'] else 'no-think'}\ncap {r['total_output_budget']}, t{r['trial']}" for r in rows]
for ax,key,title in zip(axes,['output_tokens','attempt_s'],['Actual generated tokens','Model + validation elapsed']):
 ax.bar(range(6),[r[key] for r in rows],color=['tab:green' if r['passed'] else 'tab:red' for r in rows]);ax.set(title=title,xticks=range(6),xticklabels=labels,ylabel='Tokens' if key=='output_tokens' else 'Seconds');ax.tick_params(axis='x',labelsize=7);ax.grid(axis='y',alpha=.2)
fig.suptitle('One fixed repair task; green = passed checker, red = failed')
fig.savefig(R/'budget-results.png',dpi=160)
