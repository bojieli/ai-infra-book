import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent/'results'
s=json.loads((P/'summary.json').read_text()); groups=json.loads((P/'groups.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(11,4.4))
for n,label in [(4096,'4 KiB'),(262144,'256 KiB'),(4194304,'4 MiB')]:
    g=[r for r in s if r['bytes']==n]
    axes[0].plot([r['delay_s']*1000 for r in g],[r['completion_ms']['median'] for r in g],marker='o',label=label)
axes[0].set(xlabel='Requested rank-3 sleep (ms)',ylabel='Whole-group completion median (ms)',title='Four CPU processes, Gloo SUM')
axes[0].legend(); axes[0].grid(alpha=.25)
g=[r for r in groups if not r['warmup'] and r['bytes']==4096 and r['delay_s']==.02]
median=next(r for r in s if r['bytes']==4096 and r['delay_s']==.02)['completion_ms']['median']
r=min(g,key=lambda r:abs(r['completion_ms']-median))
for rank in r['ranks']:
    y=rank['rank']
    axes[1].barh(y,rank['ready_ms']-rank['start_ms'],left=rank['start_ms'],color='#999999',label='Pre-call wait' if y==0 else None)
    axes[1].barh(y,rank['done_ms']-rank['ready_ms'],left=rank['ready_ms'],color='#3575ae',label='Blocking all_reduce' if y==0 else None)
axes[1].set(xlabel='Time from earliest barrier return (ms)',ylabel='Rank',yticks=range(4),title=f'4 KiB / requested 20 ms / trial {r["trial"]}')
axes[1].legend(); axes[1].grid(axis='x',alpha=.25)
fig.tight_layout(); fig.savefig(P/'readiness.png',dpi=160); fig.savefig(P/'readiness.svg')
