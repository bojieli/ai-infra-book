import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;rows=json.loads((R/'summary.json').read_text())['groups']
fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
policies=['round_robin','cache_aware','power_of_two']
for trial in [0,1]:
 values=[next(r['token_hit_rate']*100 for r in rows if r['trial']==trial and r['policy']==p) for p in policies]
 ax.bar([i+(trial-.5)*.34 for i in range(3)],values,width=.32,label=f'Trial {trial}')
ax.set(xticks=range(3),xticklabels=policies,ylabel='Token-weighted cache hit (%)',ylim=(0,100),title='Four-turn controlled Chat; two workers on one GPU');ax.legend();ax.grid(axis='y',alpha=.2)
fig.savefig(R/'cache-hits.png',dpi=160)
