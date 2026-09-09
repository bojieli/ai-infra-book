import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=Path(__file__).parent
s=json.loads((p/'results/summary.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for policy,color in [('cpu_cast','#2171b5'),('gpu_cast','#d95f0e')]:
    rr=[r for r in s['formal'] if r['policy']==policy]
    axes[0].plot([r['step'] for r in rr],[r['wall_ms_median'] for r in rr],'-o',label=policy,color=color)
axes[0].set(xlabel='Update step (state initialization in step 1)',ylabel='Complete offload wall time (ms)',xticks=[1,2,3])
axes[0].legend()
stages=['gpu_cast','D2H','cpu_cast','CPUAdam','weight_cpu_cast','weight_H2D']
for i,policy in enumerate(['cpu_cast','gpu_cast']):
    r=next(r for r in s['formal'] if r['policy']==policy and r['step']==3)
    left=0
    for k,c in zip(stages,['#807dba','#9ecae1','#74c476','#fd8d3c','#bdbdbd','#3182bd']):
        v=r['stage_ms_median'][k]
        axes[1].barh(i,v,left=left,color=c,label=k if i==0 else None)
        left+=v
axes[1].set(xlabel='Step 3 stage medians (ms; sum is not median total)',yticks=[0,1],yticklabels=['cpu_cast','gpu_cast'])
handles,labels=axes[1].get_legend_handles_labels()
fig.legend(handles,labels,fontsize=9,ncol=6,loc='outside lower center')
fig.suptitle('Actual BF16 gradient offload + DeepSpeed CPUAdam | RTX / shared GPU')
fig.savefig(p/'offload.png',dpi=160);fig.savefig(p/'offload.svg');plt.close(fig)
