import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;raw=[json.loads(l) for l in (R/'results/raw.jsonl').read_text().splitlines()]
fig,axes=plt.subplots(3,1,figsize=(9,6),sharex=True,layout='constrained')
for ax,policy in zip(axes,['fixed_quota','fifo','batch_A_first']):
 r=next(r for r in raw if r['trial']==1 and r['policy']==policy);available=[0,0]
 for j in sorted(r['tasks'],key=lambda j:j['dispatch_s']):
  slot=next(i for i,t in enumerate(available) if t<=j['dispatch_s']);available[slot]=j['release_s']
  start=j['dispatch_s']-r['start_s'];duration=j['release_s']-j['dispatch_s']
  ax.broken_barh([(start,duration)],(slot-.3,.6),facecolors='tab:blue' if j['batch']=='A' else 'tab:orange')
  ax.text(start+duration/2,slot,j['id'],ha='center',va='center',fontsize=8,color='white')
 ax.set(title=policy,yticks=[0,1],yticklabels=['Slot 0','Slot 1'],ylim=(-.6,1.6));ax.grid(axis='x',alpha=.2)
axes[-1].set_xlabel('Seconds from batch B availability')
fig.suptitle('Actual process occupancy: dispatch to reap (trial 1)')
fig.savefig(R/'timeline.png',dpi=170)
