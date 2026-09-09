import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;s=json.loads((R/'results-summary.json').read_text());raw=[json.loads(l) for l in (R/'results/requests.jsonl').read_text().splitlines()];groups=json.loads((R/'results/groups.json').read_text());names=['one_serial','one_parallel','four_parallel'];labels=['1 conn / serial','1 conn / 8 streams','4 conns / 2 streams each']
fig,axs=plt.subplots(2,2,figsize=(13,8),layout='constrained');ax=axs.flat[0]
for warm,shift,color in [(False,-.18,'#4179ad'),(True,.18,'#e39a4b')]:
 rr=[next(g for g in s['aggregate'] if g['topology']==n and g['warm']==warm) for n in names]
 ax.bar([i+shift for i in range(3)],[g['median_group_ms'] for g in rr],width=.36,color=color,label='warm connection' if warm else 'cold group incl. connect')
ax.set_xticks(range(3),labels,rotation=10);ax.set(ylabel='All 8 images verified (ms)',title='Three-trial group median');ax.legend(fontsize=8)
for ax,name,label in zip(list(axs.flat)[1:],names,labels):
 g=next(g for g in groups if g['trial']==0 and g['topology']==name and g['warm']);base=g['dispatch_start'];rr=sorted([r for r in raw if not r['prewarm'] and r['trial']==0 and r['topology']==name and r['warm']],key=lambda r:r['index'])
 for r in rr:
  i=r['index'];ax.broken_barh([((r['send']-base)*1000,(r['end']-r['send'])*1000)],(i-.3,.6),facecolors='#4179ad');ax.broken_barh([((r['decode_start']-base)*1000,(r['decode_end']-r['decode_start'])*1000)],(i-.3,.6),facecolors='#e39a4b');ax.scatter([(r['first_data']-base)*1000],[i],s=12,color='black',zorder=3)
 ax.set(xlabel='Milliseconds since dispatch',ylabel='Request index',title=f'Trial 0 warm: {label}',yticks=range(8));ax.grid(axis='x',alpha=.2)
fig.suptitle('Actual PNG upload + echo + decode, loopback H3 (shared asyncio loop)\nBlue: send to HTTP body completion; orange: actual RGBA decode; dot: first data',fontsize=11)
fig.savefig(R/'multistream.png',dpi=170)

fig.savefig(R/'multistream.svg')
