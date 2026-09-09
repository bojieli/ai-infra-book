import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).parent/'profiles';data=json.loads((r/'analysis.json').read_text())['configurations']
fig,ax=plt.subplots(figsize=(8,4.4),layout='constrained')
for i,c in enumerate(data):
    q=sum(v['count'] for k,v in c['kernel_groups'].items() if 'scaled_fp8_quant' in k)
    values=[c['cache_write_count'],q,c['attention_count'],c['kernel_count']-c['cache_write_count']-c['attention_count']-q]
    bars=ax.bar([x+i*.36 for x in range(4)],values,width=.36,label=c['name'])
    ax.bar_label(bars,padding=3)
ax.set_xticks([x+.18 for x in range(4)],labels=['KV write','Q quantize','Attention','Other'])
ax.set_ylabel('Actual kernel launches');ax.set_ylim(0,900);ax.legend()
fig.suptitle('vLLM/Triton: 7239-token prefill + one decode step\nFP8 configuration also changes the Q execution path',fontsize=11)
for ext in ['svg','png']:fig.savefig(r/f'kernel-paths.{ext}',dpi=160)
