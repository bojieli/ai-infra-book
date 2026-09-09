import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).parent/'results'
data=json.loads((r/'summary.json').read_text())['summary']
fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
for kind,label in [('short','2K input, no shared prefix'),('prefix','8K input, 6K cached prefix')]:
 rows=[x for x in data if x['kind']==kind]
 x=[a['batch'] for a in rows];y=[a['output_tokens_per_s'] for a in rows]
 axes[0].errorbar(x,y,yerr=[[a['output_tokens_per_s']-a['throughput_min'] for a in rows],[a['throughput_max']-a['output_tokens_per_s'] for a in rows]],marker='o',capsize=3,label=label)
 axes[1].plot(x,[a['median_ttft_ms'] for a in rows],marker='o',label=label)
 axes[2].plot(x,[a['median_time_per_output_ms'] for a in rows],marker='o',label=label)
for ax,ylabel in zip(axes,['Output tokens / second','First output delivery (ms)','Request-average output interval (ms)']):
 ax.set_xscale('log',base=4);ax.set_xticks([1,4,16,64],labels=['1','4','16','64']);ax.set_xlabel('Submitted batch');ax.set_ylabel(ylabel);ax.grid(alpha=.2)
axes[0].legend(fontsize=8)
fig.suptitle('Qwen3-8B BF16 / RTX PRO 6000: fixed 256-token output\n3 shuffled measured passes; matched warmups; prefix seeding excluded',fontsize=11)
for ext in ['svg','png']:fig.savefig(r/f'batch-sweep.{ext}',dpi=160)
