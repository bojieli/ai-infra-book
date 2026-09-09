import json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
summary=json.loads((ROOT/'results/projection-summary.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(10,4.7),sharey=True)
for ax,device in zip(axes,['mps','cuda']):
    rows=json.loads((ROOT/f'results/projection-{device}/results.json').read_text())['rows']
    for mode,color,offset in [('reused','#3078b0',-.08),('rotating','#d47721',.08)]:
        med=[]
        for i,r in enumerate(rows):
            y=r['paths'][mode]['wall_us'];med.append(statistics.median(y));ax.scatter([i+offset]*len(y),y,s=14,alpha=.4,color=color)
        ax.plot([i+offset for i in range(2)],med,'o-',color=color,label=mode+' weights')
    predictions=[r for r in summary if r['device']==device and r['mode']=='rotating']
    y=[r['predicted_memory_service_us'] for r in predictions]
    ax.plot(range(2),y,'s--',color='#555555',label='Cold memory service bound' if device=='mps' else 'Cold Roofline bound')
    ax.set_xticks(range(2),['M=1','M=256']);ax.set_yscale('log');ax.grid(axis='y',alpha=.2)
    ax.set_title('M2 Max / MPS' if device=='mps' else 'RTX PRO 6000 / CUDA');ax.legend(fontsize=8)
axes[0].set_ylabel('Time (µs)')
fig.suptitle('BF16 4096×4096 projection: measured wall time and conditional bounds')
fig.text(.5,.035,'Solid: 11 × 16 eager calls, submit + sync. Rotation: 16 distinct 32 MiB buffers.',ha='center',fontsize=9)
fig.text(.5,.005,'Dashed: existing calculation records; cold traffic is not verified. MPS has no compute bound.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.065,1,.94))
for ext in ['png','svg']:fig.savefig(ROOT/f'results/projection.{ext}',dpi=160)
