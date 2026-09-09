"""Plot preserved generated requests and released record metadata."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
cases=json.loads((ROOT/'results/summary.json').read_text())['cases']
rows=json.loads((ROOT/'results/conversation-rows.json').read_text())
pairs=json.loads((ROOT/'results/conversation-pairs.json').read_text())
fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for c in cases:
    if c['seed']!=302:continue
    r=json.loads((ROOT/'results'/c['file']).read_text())
    axs[0,0].scatter([x['data']['input_tokens'] for x in r],[x['data']['output_tokens'] for x in r],s=9,alpha=.4,label=str(c['source_window_start']))
axs[0,0].set(xlabel='Generated input length (tokens)',ylabel='Generated output length (tokens)',title='Original generator, seed 302')
axs[0,0].legend(title='Source window start',fontsize=8)
axs[0,1].plot(range(15),[c['input_output_spearman'] for c in cases],'o',label='Original pairing')
axs[0,1].plot(range(15),[c['shuffled_output_spearman'] for c in cases],'x',label='Permuted output control')
axs[0,1].axhline(0,color='gray',lw=.7)
axs[0,1].set(xlabel='Window / seed case index',ylabel='Spearman correlation',title='Generated pairing, not production joint data',ylim=(-.15,1.05))
axs[0,1].legend()
for key,label in [('input_count','Input'),('output_count','Output')]:
    x=sorted(r[key] for r in rows)
    axs[1,0].plot(x,[(i+1)/len(x) for i in range(len(x))],label=label)
axs[1,0].set(xscale='symlog',xlabel='Declared token count (symlog)',ylabel='Empirical CDF',title='Released subset: 5,720 requests')
axs[1,0].legend()
x=sorted(p['start_timestamp_gap_s'] for p in pairs)
axs[1,1].plot(x,[(i+1)/len(x) for i in range(len(x))])
axs[1,1].set(xscale='symlog',xlabel='Adjacent request start gap (seconds, symlog)',ylabel='Empirical CDF',title='4,104 gaps; completion timestamps unavailable')
for ax in axs.flat:ax.grid(alpha=.2)
for ext in ['svg','png']:fig.savefig(ROOT/f'results/audit.{ext}',dpi=150)
