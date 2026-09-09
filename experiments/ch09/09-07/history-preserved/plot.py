import json,statistics
from pathlib import Path
import matplotlib.pyplot as plt
r=Path(__file__).absolute().parent;a=json.loads((r/'analysis.json').read_text());v=json.loads((r/'review.json').read_text())
conditions=['recompute','local-apc','shared-apc'];labels=['Recompute','Local APC','Shared CPU + APC']
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for c,label in zip(conditions,labels):
 rows=[x for x in a['rows'] if x['condition']==c]
 axes[0,0].plot(range(1,13),[statistics.median(x['observed_ttft_s'] for x in rows if x['turn']==t)*1000 for t in range(12)],marker='o',label=label)
 axes[1,0].plot(range(1,13),[statistics.median(x['skipped_scheduled_tokens'] for x in rows if x['turn']==t) for t in range(12)],marker='o',label=label)
for rep in range(3):
 rows={x['condition']:x for x in a['summary'] if x['rep']==rep}
 axes[0,1].plot(range(3),[rows[c]['replay_wall_s'] for c in conditions],marker='o',label=f'repeat {rep}')
 rows=[x for x in v['transitions'] if x['condition']=='shared-apc' and x['rep']==rep]
 axes[1,1].plot([x['from_turn']+1 for x in rows],[x['next_retrieve_generated_tokens'] for x in rows],marker='o',label=f'repeat {rep}')
axes[0,0].set(title='Per-request medians across 3 repetitions',xlabel='Frozen request',ylabel='Observed TTFT (ms)')
axes[0,1].set(title='Includes output generation and publication waits',xticks=range(3),xticklabels=labels,ylabel='Full replay wall (s)')
axes[1,0].set(title='Native schedule accounting',xlabel='Frozen request',ylabel='Skipped scheduled tokens')
axes[1,1].set(title='Actual next-copy intersection with matching generated prefix',xlabel='Previous request',ylabel='Generated token positions retrieved')
for ax in axes.flat:ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2)
gate=all(v[k]==36 for k in ['local_shared_exact','local_recompute_exact','shared_recompute_exact'])
fig.suptitle('Preserved thinking prefixes: frozen failed Agent history\nFull-output equivalence '+('passed' if gate else 'FAILED')+'; no live tool execution',fontsize=12)
for ext in ['png','svg']:fig.savefig(r/('preserved-history.'+ext),dpi=160)
