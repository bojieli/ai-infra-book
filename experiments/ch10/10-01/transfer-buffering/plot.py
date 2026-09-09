import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
fig,axs=plt.subplots(3,1,figsize=(12,7),layout='constrained')
for ax,policy in zip(axs,['serial','one_device','double']):
 events=json.loads((R/'results'/f'{policy}-trace.json').read_text())['traceEvents']
 prepares=[e for e in events if e.get('ph')=='X' and e.get('name','').startswith('cpu_prepare_')]
 copies=[e for e in events if e.get('name')=='Memcpy HtoD (Pinned -> Device)']
 kernels=[e for e in events if e.get('cat')=='kernel'];base=min(e['ts'] for e in prepares)
 for lane,es,color in [(2,prepares,'#427aa5'),(1,copies,'#df973e'),(0,kernels,'#438565')]:
  ax.broken_barh([((e['ts']-base)/1000,e['dur']/1000) for e in es],(lane-.3,.6),facecolors=color)
 ax.set(yticks=[0,1,2],yticklabels=['GPU kernels','Pinned H2D','CPU preparation'],title=policy,xlabel='Milliseconds from first preparation (profiler aligned clock)');ax.grid(axis='x',alpha=.2)
fig.suptitle('Actual 8 x 64 MiB pipeline traces: preparation overlaps H2D; H2D/kernel overlap is absent')
fig.savefig(R/'buffering.png',dpi=150);fig.savefig(R/'buffering.svg')
