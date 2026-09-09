import json
from pathlib import Path
import statistics
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent
data=json.loads((root/'analysis.json').read_text());conditions=['recompute','local-apc','shared-apc']
labels=['Recompute*','Local APC','Shared CPU + APC']
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for index,condition in enumerate(conditions):
    points=[r for r in data['rows'] if r['condition']==condition]
    for row,key,scale,label in [(0,'observed_ttft_s',1000,'Observed TTFT (ms)'),(1,'skipped_scheduled_tokens',1,'Tokens skipped by native scheduler')]:
        ax=axes[row,0]
        medians=[statistics.median(r[key] for r in points if r['turn']==turn)*scale for turn in range(12)]
        ax.plot(range(1,13),medians,marker='o',label=labels[index],color=f'C{index}')
        if row==0:
            ax.scatter([r['turn']+1 for r in points],[r[key]*scale for r in points],s=12,alpha=.3,color=f'C{index}')
        ax.set(xlabel='Frozen Agent request',ylabel=label,xticks=range(1,13))
        ax.legend(fontsize=9)
axes[0,0].set_title('Same input snapshots; all three repetitions shown')
axes[1,0].set_title('Actual schedule counts, including decode accounting')
for rep in range(3):
    subset={r['condition']:r for r in data['summary'] if r['rep']==rep}
    axes[0,1].plot(range(3),[subset[c]['replay_wall_s'] for c in conditions],marker='o',label=f'repeat {rep}')
axes[0,1].set(xticks=range(3),xticklabels=labels,ylabel='12-request replay wall time (s)',
              title='*Recompute differs in output on request 3')
axes[0,1].legend();axes[0,1].tick_params(axis='x',rotation=15)
sample=[r for r in data['rows'] if r['rep']==0 and r['condition']=='shared-apc']
axes[1,1].bar(range(1,13),[r['stored_decode_tokens'] for r in sample],label='Generated KV written to pool')
following=[r for r in sample if r['next_history_common_tokens'] is not None]
axes[1,1].scatter([r['turn']+1 for r in following],
                 [max(0,min(r['stored_decode_tokens'],r['next_history_common_tokens']-r['input_tokens'])) for r in following],
                 marker='x',color='C3',label='Reusable by next snapshot prefix identity')
axes[1,1].set(xlabel='Frozen Agent request',ylabel='Generated token positions',xticks=range(1,13),
              title='Next snapshot removes the 4-token empty-thinking tail',ylim=(-5,110))
axes[1,1].legend(fontsize=8)
for ax in axes.flat:ax.grid(axis='y',alpha=.2)
fig.suptitle('Two alternating engines: full generation for a frozen failed Agent history\nNo live tool execution; complete-output equivalence fails against recompute',fontsize=12)
for ext in ['png','svg']:fig.savefig(root/('agent-history.'+ext),dpi=160)
