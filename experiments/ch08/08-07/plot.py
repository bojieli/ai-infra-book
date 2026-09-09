import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent/'results';s=json.loads((P/'summary.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(10,4))
for trial in [0,1]:
 cs=sorted([c for c in s['cases'] if c['trial']==trial],key=lambda c:c['slots'])
 axes[0].plot([c['slots'] for c in cs],[c['kv_bytes']/1024**3 for c in cs],marker='o',label=f'KV arrays trial {trial}')
 axes[0].plot([c['slots'] for c in cs],[c['memory']['active']/1024**3 for c in cs],marker='x',linestyle='--',label=f'MLX active trial {trial}')
 axes[1].plot([c['slots'] for c in cs],[c['ready_prefill_s'] for c in cs],marker='o',label=f'Trial {trial}')
axes[0].set(xlabel='Independent resident slots',ylabel='GiB',title='Actual KV allocation and process allocator');axes[0].legend(fontsize=8)
axes[1].set(xlabel='Independent resident slots',ylabel='Seconds',title='Serial prefill of 8191 tokens per slot');axes[1].legend()
for ax in axes:ax.set_xticks([1,4]);ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(P/'mac-kv.png',dpi=160);fig.savefig(P/'mac-kv.svg')
