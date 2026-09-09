import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parent;s=json.loads((B/'formal/summary.json').read_text());results=s['results'];groups=[('sequence',32),('sequence',96),('extract',32),('extract',96)];colors=['#427A97','#C77A41','#528772'];strategies=['baseline','restart','preserve'];names=['Uninterrupted','Restart from prompt','Keep received prefix'];fig,axes=plt.subplots(1,2,figsize=(11.5,5.5))
for i,(strategy,color,name) in enumerate(zip(strategies,colors,names)):
 rows=[next(r for r in results if (r['task'],r['cut'],r['strategy'])==(task,k,strategy)) for task,k in groups];y=[j+(i-1)*.24 for j in range(4)]
 axes[0].barh(y,[r['sampled_tokens'] for r in rows],height=.21,color=color,label=name);axes[1].barh(y,[r['wall_s'] for r in rows],height=.21,color=color)
for ax in axes:
 ax.set_yticks(range(4),[f'{task} / K={k}' for task,k in groups]);ax.set_ylim(3.55,-.55);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);ax.spines[['top','right']].set_visible(False)
axes[0].set_title('Actual sampled output tokens, including EOS');axes[0].set_xlabel('All worker attempts summed');axes[1].set_title('Observed request completion window');axes[1].set_xlabel('Seconds from first worker start to last worker exit')
fig.suptitle('Real generation preemption and token-prefix recovery',fontsize=14);fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,.09),ncol=3,frameon=False);fig.text(.5,.035,'Keeping the prefix still rebuilds KV for K received tokens. Single local runner; per-token SQLite commits; no production speedup claim.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.18,1,.93]);fig.savefig(B/'recovery-work.png',dpi=170);fig.savefig(B/'recovery-work.svg');plt.close(fig)
