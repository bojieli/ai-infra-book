"""Plot measured CPU results after independent analysis has passed."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser();p.add_argument('directory',type=Path);root=p.parse_args().directory
s=json.loads((root/'summary.json').read_text());assert s['status']=='passed'
rows=sorted(s['results'],key=lambda r:r['name']);labels=[r['name'] for r in rows]
fig,axes=plt.subplots(1,3,figsize=(15,4.6))
axes[0].bar(labels,[r['median_ms'] for r in rows]);axes[0].set_ylabel('Blocking call median (ms)')
axes[0].set_title('One Mac CPU implementation')
axes[1].bar(labels,[r['relative_l2'] for r in rows]);axes[1].set_ylabel('Relative L2 error');axes[1].set_title('Against independent FP64 FFN')
axes[2].bar(labels,[r['activation_bytes_per_rank']/1024 for r in rows]);axes[2].set_ylabel('Output allocation per rank (KiB)');axes[2].set_title('Replicated TP / token-sharded SP')
for ax in axes:ax.tick_params(axis='x',rotation=65);ax.grid(axis='y',alpha=.2)
fig.suptitle('Actual XLA CPU logical devices; random Qwen-shaped FFN; no GPU scaling claim')
fig.tight_layout();fig.savefig(root/'comparison.png',dpi=140);fig.savefig(root/'comparison.svg');plt.close(fig)
