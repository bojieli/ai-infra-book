import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).parent/'results'
rows=json.loads((root/'summary.json').read_text())['configurations']
fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
for r in rows:
    axes[0].plot(range(12),r['cached_by_round'],marker='.',label=r['name'])
    axes[1].plot(range(12),r['ttft_ms_by_round'],marker='.',label=r['name'])
axes[0].set_ylabel('Actual cached input tokens');axes[1].set_ylabel('First output delivery (ms)')
for ax in axes:
    ax.set_xlabel('Frozen Agent round');ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.suptitle('Qwen3-8B / vLLM APC: real Agent inputs, controlled cache pressure\nOne-token replay; shared GPU; one pass per configuration',fontsize=11)
for ext in ['svg','png']:fig.savefig(root/f'cache-replay.{ext}',dpi=160)
