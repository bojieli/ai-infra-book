"""Display actual training completion times and observed phase drift."""
import json
from pathlib import Path
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent
data=json.loads((root/'analysis.json').read_text())
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for pair in data['pairs']:
    axes[0,0].plot([0,1],[pair['aligned_ms'],pair['offset_ms']],marker='o',label=f"repeat {pair['rep']}")
axes[0,0].set(xticks=[0,1],xticklabels=['Aligned start','B delayed 50 ms'],
              ylabel='Both jobs completed from release (ms)',title='Completion includes the initial delay')
axes[0,0].legend()
for entry in data['results']:
    if len(entry['jobs'])!=2:continue
    offset=entry['condition']=='offset-50ms'
    axes[0,1].plot(range(100),entry['same_step_comm_phase_delta_ms'],
                  color=f'C{entry["rep"]}',linestyle='-' if offset else '--',
                  label=f"r{entry['rep']} {'+50ms' if offset else 'aligned'}")
axes[0,1].set(xlabel='Training step',ylabel='B minus A first collective entry (ms)',
              title='One start offset; no periodic resynchronization')
axes[0,1].legend(ncol=2,fontsize=8)
groups=[('solo-a',0),('solo-b',1),('aligned',0),('aligned',1),('offset-50ms',0),('offset-50ms',1)]
values=[]
for condition,job in groups:
    values.append([v for e in data['results'] if e['condition']==condition for j in e['jobs']
                   if j['job']==job for v in j['rank0_step_period_ms']])
axes[1,0].boxplot(values,tick_labels=['Solo A','Solo B','Aligned A','Aligned B','Offset A','Offset B'],whis=(0,100))
axes[1,0].tick_params(axis='x',rotation=25)
axes[1,0].set(ylabel='Rank-0 step start interval (ms)',title='All periods; whiskers show min/max, not CI')
labels=[]
for entry in [e for e in data['results'] if e['rep']==0 and len(e['jobs'])==2]:
    for j in entry['jobs']:
        lane=len(labels);labels.append(f"{entry['condition']} {'AB'[j['job']]}")
        p=root/'formal'/f"r0-{entry['condition']}"/f"job{j['job']}-rank0/collectives.json"
        records=[x for x in json.loads(p.read_text()) if x['step']<20]
        axes[1,1].broken_barh([((e['begin_ns']-entry['release_ns'])/1e6,
                                (e['future_done_ns']-e['begin_ns'])/1e6) for e in records],
                              (lane-.3,.6),facecolors=f'C{j["job"]}')
axes[1,1].set(yticks=range(len(labels)),yticklabels=labels,xlabel='Time from each run release (ms)',
              title='First 20 steps: rank-0 collective future intervals')
for ax in axes.flat:ax.grid(alpha=.2)
fig.suptitle('Actual two-rank CPU DDP jobs on one Mac\nHost callback intervals are not NIC traffic or queue measurements',fontsize=13)
for ext in ['png','svg']:fig.savefig(root/('training-phase.'+ext),dpi=160)
