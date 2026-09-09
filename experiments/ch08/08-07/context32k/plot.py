import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent/'results';s=json.loads((P/'summary.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(10,4))
for trial in [0,1]:
 cs=sorted([c for c in s['cases'] if c['trial']==trial],key=lambda c:c['slots'])
 axes[0].plot([c['slots'] for c in cs],[c['max_ready_kv_bytes']/1024**3 for c in cs],marker='o',label=f'KV trial {trial}')
 axes[0].plot([c['slots'] for c in cs],[c['max_ready_active_bytes']/1024**3 for c in cs],marker='x',linestyle='--',label=f'MLX active trial {trial}')
 axes[1].plot([c['slots'] for c in cs],[c['elapsed_s'] for c in cs],marker='o',label=f'Trial {trial}')
axes[0].set(xlabel='Maximum resident slots',ylabel='GiB',title='Actual 32K KV residency');axes[0].legend(fontsize=8)
axes[1].set(xlabel='Maximum resident slots',ylabel='Seconds',title='Same two tasks: serial prefill and decode');axes[1].legend()
for ax in axes:ax.set_xticks([1,2]);ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(P/'context32k.png',dpi=160);fig.savefig(P/'context32k.svg')
