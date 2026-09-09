import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent;d=json.loads((root/'summary.json').read_text())['policies']
fig,axes=plt.subplots(1,2,figsize=(10,3.5),layout='constrained')
colors=['#7d8791','#337fac','#c38a35'];labels=['Round robin','Cache aware','Power of two']
for i,r in enumerate(d):
 axes[0].bar(i,100*r['token_weighted_hit_rate'],color=colors[i]);axes[0].text(i,100*r['token_weighted_hit_rate']+2,f"{100*r['token_weighted_hit_rate']:.1f}%",ha='center')
 axes[1].plot(range(12),r['worker_sequence'],marker=['o','s','^'][i],label=labels[i],color=colors[i],alpha=.8)
axes[0].set_xticks(range(3),labels);axes[0].set_ylim(0,100);axes[0].set_ylabel('Actual cached prompt tokens (%)');axes[0].set_title('Same 12-round Agent input trace')
axes[1].set_yticks([0,1]);axes[1].set_ylim(-.25,1.45);axes[1].set_xlabel('Request index');axes[1].set_ylabel('Worker from native request log');axes[1].legend(ncol=1,loc='upper right',fontsize=8);axes[1].set_title('Observed routing decisions')
fig.savefig(root/'routing.png',dpi=170)
