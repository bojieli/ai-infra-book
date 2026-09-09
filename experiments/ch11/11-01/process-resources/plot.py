import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
fig,axes=plt.subplots(3,1,figsize=(9,7),sharex=True)
for ax,condition in zip(axes,['wait-burst','cpu-burst','cpu-stagger']):
 for p in (R/'results').glob('case*.json'):
  c=json.loads(p.read_text())
  if c['trial']==1 and c['mode']+'-'+c['arrival']==condition:break
 t=[x['at']-c['start'] for x in c['samples']];rss=[sum(p['rss'] for p in x['processes'])/1024**2 for x in c['samples']]
 ax.plot(t,rss,label='Sampled sum of child VmRSS');ax.set_ylabel('MiB');ax.set_title(condition+' (trial 1)',loc='left');ax.set_ylim(bottom=0);ax.grid(alpha=.2)
 for launch in c['launch']:ax.axvline(launch['at']-c['start'],color='orange',alpha=.5,ls=':')
axes[0].legend(loc='upper right');axes[-1].set_xlabel('Seconds since group start; dotted lines: actual process launches')
fig.suptitle('Real Linux tool processes: memory stays resident while waiting')
fig.tight_layout();fig.savefig(R/'resources.png',dpi=160);fig.savefig(R/'resources.svg')
