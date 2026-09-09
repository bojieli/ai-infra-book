import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).parent/'results';data=json.loads((r/'summary.json').read_text())['configurations']
fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
for ax,c in zip(axes,data):
 t=c['timeline'];epoch=t[0]['time_s']
 ax.step([x['time_s']-epoch for x in t],[x['allocated_blocks'] for x in t],where='post',label='Request-owned blocks')
 ax.axhline(c['total_blocks']-c['reserved_blocks'],color='gray',ls='--',label='Usable pool')
 for p in c['preemptions']:ax.axvline(p['time_s']-epoch,color='red',ls=':',label='Preemption')
 for p in c['actions']:ax.axvline(p['start_s']-epoch,color='green',ls=':',label='Client abort')
 ax.set_title(c['name']);ax.set_xlabel('Seconds since scheduler init');ax.set_ylabel('Physical KV blocks (16 tokens each)');ax.grid(alpha=.2);ax.legend(fontsize=8)
 ax.set_ylim(-20,960)
fig.suptitle('Qwen3-8B / vLLM: actual block allocation, preemption and release\nFour 1536-token prompts; APC off; instrumented scheduler',fontsize=11)
for ext in ['svg','png']:fig.savefig(r/f'kv-lifecycle.{ext}',dpi=160)
