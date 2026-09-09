import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;s=json.loads((R/'summary.json').read_text())
fig,axs=plt.subplots(1,2,figsize=(10,4.5),layout='constrained')
for ax,c in zip(axs,[1,4]):
 rows=[r for r in s['conditions'] if r['concurrency']==c]
 labels=[r['protocol'].upper()+'\n'+('reuse' if r['reuse'] else 'new') for r in rows]
 ax.bar(labels,[r['median_attempt_ms'] for r in rows],color=['#4078ac','#79a5ce','#de893e','#e8b887'])
 for i,r in enumerate(rows):ax.scatter([i]*3,r['per_trial_attempt_median_ms'],c='black',s=16,zorder=3)
 ax.set(ylabel='Attempt through verified response (ms)',title=f'{c} concurrent lane(s); loopback stacks')
 ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.suptitle('Same 64 KiB echo; same asyncio loop; host not exclusive\nBars: all-request median; points: three trial medians',fontsize=10)
fig.savefig(R/'loopback.png',dpi=170)
