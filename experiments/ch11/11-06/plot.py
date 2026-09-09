import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent/'results';s=json.loads((P/'summary.json').read_text())
fig,axes=plt.subplots(1,3,figsize=(12,4))
labels=['Resident','Demand','Predict 50ms','Predict full gap']
for ax,key,title in zip(axes,['call_wait_s','sampled_gib_seconds','unused_ready_residency_s'],['Summed tool call latency (s)','Sampled worker residency (GiB s)','Unused preparation residency (s)']):
 ax.bar(range(4),[x[key] for x in s],color=['#3575ae','#dd9851','#6e9d63','#806699'])
 ax.set_xticks(range(4),labels,rotation=25,ha='right');ax.set_title(title);ax.grid(axis='y',alpha=.2)
fig.suptitle('Actual replay of 12 tool actions; median of 3 runs');fig.tight_layout();fig.savefig(P/'prewarm.png',dpi=160);fig.savefig(P/'prewarm.svg')
fig,axes=plt.subplots(2,1,figsize=(10,6),sharex=True)
for ax,policy in zip(axes,['predict-50ms','predict-fullgap']):
 r=json.loads((P/f'0-{policy}'/'raw.json').read_text());origin=r['origin_ns']; launch={e['pid']:e for e in r['events'] if e['event']=='launch'}
 ready={e['pid']:e for e in r['events'] if e['event']=='ready'}
 destroy={e['pid']:e for e in r['events'] if e['event']=='destroy'}
 for row in r['rows'][:3]:
  y=row['turn'];a=(row['gap_start_ns']-origin)/1e9;b=(row['call_ns']-origin)/1e9
  ax.barh(y,b-a,left=a,height=.2,color='#999999',label='Recorded model gap replay' if y==0 else None)
  ax.barh(y,(row['received_ns']-row['call_ns'])/1e9,left=b,height=.2,color='#3575ae',label='Actual call to reply' if y==0 else None)
  for pid,e in launch.items():
   if row['gap_start_ns']<=e['t_ns']<=row['received_ns']:
    start=(e['t_ns']-origin)/1e9;end=(destroy[pid]['end_ns']-origin)/1e9
    ax.barh(y+.25,end-start,left=start,height=.15,color='#6e9d63',label='Worker launch to reaped' if y==0 else None)
 ax.set(title=f'{policy}: actual first three rounds, trial 0',yticks=[0,1,2],ylabel='Round');ax.grid(axis='x',alpha=.2)
fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',ncol=3);axes[-1].set_xlabel('Elapsed time (s)');fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(P/'timeline.png',dpi=160);fig.savefig(P/'timeline.svg')
