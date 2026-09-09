import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;s=json.loads((R/'summary.json').read_text());cases=sorted(s['cases'],key=lambda c:(c['world'],c['reshard']))
fig,axs=plt.subplots(1,2,figsize=(12,4.5),layout='constrained');labels=[]
for i,c in enumerate(cases):
 label=f"{c['world']} ranks / reshard {c['reshard']}";labels.append(label)
 snaps=[r for r in c['memory'][0]['snapshots'] if r['step']==2]
 axs[0].plot(range(len(snaps)),[r['unique_visible_storage_bytes']/2**20 for r in snaps],marker='o',label=label)
 peak=max(m['training_region_peak_bytes'] for m in c['memory'])/2**20
 visible=max(m['max_visible_storage'] for m in c['memory'])/2**20
 axs[1].bar(i-.16,visible,width=.32,color='#3679a8');axs[1].bar(i+.16,peak,width=.32,color='#d18b36')
axs[0].set_xticks(range(5),['before forward','inside forward','after forward','after backward','after step'],rotation=25);axs[0].set(ylabel='Unique visible state storage (MiB)',title='Third step, rank 0');axs[0].legend(fontsize=7)
axs[1].set_xticks(range(4),labels,rotation=25);axs[1].set(ylabel='MiB',title='Visible state vs profiled training allocation peak')
from matplotlib.patches import Patch
axs[1].legend(handles=[Patch(color='#3679a8',label='Visible state maximum'),Patch(color='#d18b36',label='CPU profiler training peak')],fontsize=8)
fig.suptitle('Actual CPU FSDP2: temporary allocations exceed visible parameter/gradient/Adam state')
fig.savefig(R/'state-memory.png',dpi=150);fig.savefig(R/'state-memory.svg')
