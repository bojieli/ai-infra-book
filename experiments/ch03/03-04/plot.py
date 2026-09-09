"""Render actual serial model/tool timing and measured cache hits."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).parent/'results'
rows=[json.loads(x) for x in (root/'rounds.jsonl').read_text().splitlines()]
fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
for i,r in enumerate(rows):
    axes[0].barh(i,r['model_end_s']-r['model_start_s'],left=r['model_start_s'],color='#487eab',label='Model wall time' if i==0 else None)
    axes[0].barh(i,r['tool_end_s']-r['tool_start_s'],left=r['tool_start_s'],color='#d08b3c',label='CPU tool wall time' if i==0 else None)
    axes[1].barh(i,r['cached_tokens'],color='#60a16d',label='Engine cache hit' if i==0 else None)
    axes[1].barh(i,len(r['prompt_token_ids'])-r['cached_tokens'],left=r['cached_tokens'],color='#b6c9de',label='Uncached input' if i==0 else None)
for ax in axes:
    ax.set_yticks(range(len(rows)),[f"{r['turn']}: {r['action']['tool']}" for r in rows]);ax.invert_yaxis()
    ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);ax.legend(fontsize=8)
axes[0].set_xlabel('Seconds from task start');axes[0].set_title('Actual model → tool loop')
axes[1].set_xlabel('Prompt tokens per round');axes[1].set_title('Measured prefix reuse')
fig.suptitle('Qwen3-8B / vLLM 0.23.0: task failed at the 12-round limit\nControlled local task; thinking disabled; shared RTX PRO 6000',fontsize=11)
for ext in ['svg','png']:fig.savefig(root/f'agent-trace.{ext}',dpi=160)
