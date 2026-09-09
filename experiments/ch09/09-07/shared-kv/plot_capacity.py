import json
from pathlib import Path
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent
data=json.loads((root/'capacity-comparison.json').read_text())
fig,axes=plt.subplots(2,1,figsize=(10,7),layout='constrained')
for group in data['comparison']:
    candidates=group['candidates']
    axes[0].plot(range(1,13),[x['matched_tokens']/x['aligned_prefix_tokens'] for x in candidates],
                 marker='o',label=f"{group['pool_gib']} GiB CPU pool")
    axes[1].plot(range(1,49),[x['evicted_chunks'] for x in group['metrics_trajectory']],
                 label=f"{group['pool_gib']} GiB CPU pool")
axes[0].set(ylabel='Matched / chunk-aligned prefix',xlabel='Consumer fetch candidate in frozen order',
            title='Complete prefix hits: 4 GiB 5/12; 8 GiB 12/12',ylim=(-.05,1.08),xticks=range(1,13))
axes[1].set(ylabel='Cumulative evicted chunks',xlabel='Shared-path request in frozen order',
            title='Both pools evict chunks; unexported counters remain blank',xlim=(1,48))
for ax in axes:ax.grid(alpha=.2);ax.legend()
fig.suptitle('Same requests and order, two independent engines on one GPU',fontsize=13)
for ext in ['png','svg']:fig.savefig(root/('capacity-control.'+ext),dpi=160)
