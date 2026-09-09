import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent;d=json.loads((root/'summary.json').read_text())
fig,ax=plt.subplots(figsize=(7,3.5),layout='constrained')
for j,(p,label,color) in enumerate([('cache_first','Cache first','#b27d35'),('queue_first','Queue first','#347da9')]):
 rows=sorted([r for r in d['rows'] if r['policy']==p],key=lambda r:r['trial'])
 x=[r['trial']+(j-.5)*.3 for r in rows];y=[r['elapsed_s']*1000 for r in rows]
 ax.bar(x,y,width=.28,label=label,color=color)
 for xx,yy in zip(x,y):ax.text(xx,yy+20,f'{yy:.0f}',ha='center',fontsize=9)
ax.set_xticks([0,1,2],['Trial 1','Trial 2','Trial 3']);ax.set_ylabel('Target request completion (ms)');ax.set_title('Cached worker busy; one running request per worker');ax.legend(frameon=False,loc="upper right",ncol=2);ax.set_ylim(0,max(r['elapsed_s']*1000 for r in d['rows'])*1.2);fig.savefig(root/'queue-pressure.png',dpi=170)
