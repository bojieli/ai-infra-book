import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
s=json.loads((ROOT/'results/summary.json').read_text());cases=s['cases']
fig,axes=plt.subplots(2,1,figsize=(11,7),layout='constrained',sharex=True)
x=range(len(cases))
axes[0].bar(x,[c['cached_tokens'][0] for c in cases],color='#447ca1');axes[0].set(ylabel='Actual cached input tokens',ylim=(0,3400),title='Same 3,136-token prompt: cache identity changes reuse\nFive distinct leading-token trials; identical hit counts in all five')
for i,c in enumerate(cases):axes[1].scatter([i]*5,c['ttft_ms'],s=24,color='#b35d3c',alpha=.6)
axes[1].set(ylabel='Client first-token delay (ms)',xlabel='Sequential case within each trial')
axes[1].set_xticks(list(x),[c['case'] for c in cases],rotation=30,ha='right')
for ax in axes:ax.grid(axis='y',alpha=.2)
for ext in ['svg','png']:fig.savefig(ROOT/f'results/identity.{ext}',dpi=150)
