import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
B=Path(__file__).resolve().parent;s=json.loads((B/'formal/summary.json').read_text());rows=s['observations'];labels=[f"seed {r['seed']} / step {r['cut']}" for r in rows]
fig,axes=plt.subplots(1,2,figsize=(11.5,5.8),gridspec_kw={'width_ratios':[1,1.7]});ys=list(range(len(rows)))
axes[0].barh(ys,[r['save_s']*1000 for r in rows],color='#347A93');axes[0].set_yticks(ys,labels);axes[0].set_xlabel('Checkpoint write + fsync + commit (ms)');axes[0].set_title('Actual checkpoint persistence calls')
for i,r in enumerate(rows):
 wait=r['first_resume_update_start']-r['terminate_time'];update=r['first_resume_update_end']-r['first_resume_update_start'];axes[1].barh(i,wait,color='#BCC7D0');axes[1].barh(i,update,left=wait,color='#D77B32')
 workers=[json.loads(line) for p in (B/'formal'/f"seed{r['seed']}-cut{r['cut']}-resume").glob('worker-*.jsonl') for line in p.read_text().splitlines()];first=min(v['time'] for v in workers)-r['terminate_time'];axes[1].plot(first,i,'|',color='#153E49',markersize=16,markeredgewidth=2)
 axes[1].text(r['resume_delay_s']+.025,i,f"{r['resume_delay_s']:.3f} s",va='center',fontsize=9)
axes[1].set_yticks(ys,labels);axes[1].set_xlim(0,max(r['resume_delay_s'] for r in rows)+.25);axes[1].set_xlabel('Seconds since SIGTERM of the old process group');axes[1].set_title('New process to first correct resumed update');axes[1].legend(handles=[Patch(color='#BCC7D0',label='Restart to first update'),Patch(color='#D77B32',label='First resumed update'),plt.Line2D([0],[0],marker='|',color='#153E49',linestyle='',markersize=12,label='First worker read completes')],loc='upper center',bbox_to_anchor=(.5,-.2),ncol=1,fontsize=8)
for ax in axes:ax.invert_yaxis();ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Real text input recovery: six independent CPU restarts',fontsize=14);fig.text(.5,.015,'Every restart matched all final model / Adam tensors and every consumed byte position. Local CPU and filesystem; no throughput extrapolation.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.1,1,.95]);fig.savefig(B/'recovery.png',dpi=170);fig.savefig(B/'recovery.svg');plt.close(fig)
