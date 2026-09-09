import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--name',required=True);a=p.parse_args();s=json.loads((B/a.name/'summary.json').read_text());rows=s['timing'];labels=['New reference: 43 updates','Restore step 3: 40 updates','Restore step 23: 20 updates'];fig,axes=plt.subplots(1,2,figsize=(10,5.4))
for i,r in enumerate(rows):
 axes[0].barh(i-.16,r['actual_update_s']*1000,height=.3,color='#267E92',label='Actual math steps' if i==0 else None);axes[0].barh(i+.16,r['observed_window_s']*1000,height=.3,color='#DDBB76',label='Window including observation' if i==0 else None)
 if r['load_s'] is not None:axes[1].barh(i,r['load_s']*1000,color='#467196');axes[1].text(r['load_s']*1000+.3,i,f"{r['load_s']*1000:.2f}",va='center')
 else:axes[1].text(2,i,'No checkpoint loaded',va='center')
for ax in axes:ax.set_yticks(range(3),labels);ax.set_ylim(2.6,-.6);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);ax.spines[['top','right']].set_visible(False)
axes[0].set_xlabel('Elapsed milliseconds');axes[0].set_title('Real CPU update work');axes[0].legend(loc='upper center',bbox_to_anchor=(.5,-.18),fontsize=8);axes[1].set_xlabel('DCP load call milliseconds');axes[1].set_title('Actual checkpoint load');axes[1].margins(x=.3)
fig.suptitle('Checkpoint recovery and actual catch-up');fig.text(.5,.02,'One run per path; different update counts. Historical full states exist at steps 3 and 23; step 43 is a new reference.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.12,1,.94]);fig.savefig(B/'catch-up.png',dpi=170);fig.savefig(B/'catch-up.svg')
