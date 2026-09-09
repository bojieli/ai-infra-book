import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).absolute().parent
x=json.loads((B/'analysis.json').read_text())
fig,axs=plt.subplots(1,3,figsize=(12,3.9))
for stack,color in [('baseline','#666666'),('queqiao','#0072B2')]:
 for flows,style in [(1,'-'),(4,'--')]:
  rows=[r for r in x['bulk_cells'] if r['stack']==stack and r['flows']==flows]
  axs[0].plot([r['round'] for r in rows],[r['seconds']*1000 for r in rows],style,marker='o',color=color,label=f'{stack}, {flows} flow(s)')
 rows=[r for r in x['latency_cells'] if r['stack']==stack]
 for ax,key in [(axs[1],'cold_ms'),(axs[2],'warm_ms')]:
  ax.plot([r['round'] for r in rows],[r[key] for r in rows],'-o',color=color,label=stack)
for ax,title in zip(axs,['Bulk completion (355000 B / flow)','Cold 1024 B request','Warm 1024 B request']):
 ax.set_title(title,fontsize=10);ax.set_ylabel('Elapsed time (ms)');ax.set_xticks(range(4),['0: on','1: off','2: off','3: on']);ax.set_xlabel('Round: Queqiao pool');ax.grid(alpha=.2);ax.set_ylim(bottom=0);ax.legend(fontsize=7)
fig.suptitle('Native Queqiao / QUIC baseline, loopback + emulated 40 ms RTT',fontsize=12)
fig.tight_layout();fig.savefig(B/'pool-comparison.svg');fig.savefig(B/'pool-comparison.png',dpi=150)
