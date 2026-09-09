import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).parent/'results';report=json.loads((r/'summary.json').read_text());data=report['summary']
fig,axes=plt.subplots(1,3,figsize=(13,4.3),layout='constrained')
labels=['JSON / worker','binary copy / worker','binary view / worker','binary view / inline']
for mode,label in enumerate(labels):
 rows=[x for x in data if x['mode']==mode];x=[a['size']/1024 for a in rows]
 for ax,key in zip(axes,['total_ms','client_cpu_ms','server_decode_ms']):ax.plot(x,[a['median'][key] for a in rows],marker='o',label=label)
 raw=[a for a in report['requests'] if a['mode']==mode and not a['warmup']]
 axes[0].scatter([a['size']/1024 for a in raw],[a['total_ms'] for a in raw],s=8,alpha=.2,color=f'C{mode}')
for ax,label in zip(axes,['Complete RPC wall time (ms)','Client process CPU time (ms)','Server decode/materialize time (ms)']):
 ax.set_xscale('log');ax.set_xticks([1,64,1024],labels=['1','64','1024']);ax.set_xlabel('Payload (KiB)');ax.set_ylabel(label);ax.grid(alpha=.2)
axes[0].legend(fontsize=8)
fig.suptitle('Mac to RTX host over SSH: measured RPC preparation and completion\n20 paired samples; lines: medians; faint dots: individual RPC times',fontsize=11)
for ext in ['svg','png']:fig.savefig(r/f'rpc-costs.{ext}',dpi=160)
