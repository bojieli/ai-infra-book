import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).parent/'results';data=json.loads((r/'summary.json').read_text())['configurations']
fig,axes=plt.subplots(1,3,figsize=(12,4.2),layout='constrained')
for index,c in enumerate(data):
 for mode,style in [('natural','-'),('fixed','--')]:
  rows=[x for x in c['summary'] if x['mode']==mode]
  label=f'{c["name"]}, {mode}';x=range(4)
  axes[0].plot(x,[a['median_latency_s'] for a in rows],style,marker='o',label=label,color=f'C{index}')
  axes[1].plot(x,[a['median_ttft_ms'] for a in rows],style,marker='o',label=label,color=f'C{index}')
  if mode=='natural':axes[2].plot(x,[a['correct'] for a in rows],marker='o',label=c['name'],color=f'C{index}')
for ax in axes:
 ax.set_xticks(range(4),labels=['128 / 1','128 / 4','512 / 1','512 / 4']);ax.set_xlabel('Document rows / concurrent requests');ax.grid(alpha=.2)
axes[0].set_ylabel('Median request completion (s)');axes[1].set_ylabel('Median first output (ms)')
axes[2].set_ylabel('Exact JSON answers / 8 executions');axes[2].set_ylim(-.3,8.5)
axes[0].legend(fontsize=8);axes[2].legend(fontsize=8)
fig.suptitle('Qwen3-8B: same BF16 weights and Triton attention, different KV formats\n8 distinct synthetic retrieval tasks; 2 passes; natural vs forced-length output',fontsize=11)
for ext in ['svg','png']:fig.savefig(r/f'kv-quality.{ext}',dpi=160)
