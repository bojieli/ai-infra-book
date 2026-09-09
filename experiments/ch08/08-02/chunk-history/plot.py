import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
s=json.loads((ROOT/'results/summary.json').read_text());b=s['blocks']
fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
x=[r['history_tokens'] for r in b];y=[r['median_ms'] for r in b]
for r in b:ax.scatter([r['history_tokens']]*11,r['samples_ms'],s=12,alpha=.4,color='#447ca1')
ax.plot(x,y,'o-',color='#b45435',label='Median of 11 actual requests')
ax.set(xlabel='Previously scheduled tokens before this 512-token chunk',ylabel='execute_model CUDA event interval (ms)',title='Qwen3-8B: same new-token budget at different history positions\nBF16, eager, APC off, one request; interval includes host launch gaps')
ax.legend();ax.grid(alpha=.2)
for ext in ['svg','png']:fig.savefig(ROOT/f'results/history.{ext}',dpi=150)
