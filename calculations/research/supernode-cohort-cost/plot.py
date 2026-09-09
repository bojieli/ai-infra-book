"""Figure6-9 candidate: exact deadline staircases from complete request traces."""
from pathlib import Path
import json
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['svg.hashsalt']='ai-infra-book-supernode-cohort-v1'
from fractions import Fraction

root=Path(__file__).resolve().parent
results=json.loads((root/'result.json').read_text())
fig,axes=plt.subplots(2,3,figsize=(15,8),sharex=True)
colors={8:'#2166ac',4:'#e08214',2:'#198b5b'}
curve_data=[]
for row,model in enumerate(('qwen3-8b','qwen3-32b')):
    for col,count in enumerate((1,4,8)):
        ax=axes[row,col]
        for tag,style in [('healthy','-'),('long','--')]:
            result=results[f'{model}-n{count}-d600-{tag}']
            required=result['selection']['required_valid_requests']
            for candidate in result['candidates']:
                if not candidate['capacity_fits']:
                    continue
                cost=Fraction(candidate['cost']['full_declared_cost_exact'])
                deadline=np.arange(1,1001)
                values=[];records=[]
                for limit in deadline:
                    valid=sum(r['latency_ms']<=int(limit) for r in candidate['schedule']['requests'])
                    exact=str(cost/valid) if valid>=required else None
                    values.append(float(Fraction(exact)) if exact is not None else np.nan)
                    records.append(dict(deadline_ms=int(limit),valid=valid,cost_per_valid_exact=exact))
                ax.step(deadline,values,where='post',color=colors[candidate['tp']],linestyle=style,
                        label=f"TP{candidate['tp']} x {candidate['replicas']} replicas / {tag}")
                curve_data.append(dict(model=model,requests=count,profile=tag,candidate=candidate['id'],points=records))
        ax.set_title(f'{model} | {count} simultaneous requests')
        ax.grid(alpha=.2);ax.set_xlim(0,1000)
        ax.set_xlabel('Completion deadline (ms)')
        if col==0:ax.set_ylabel('Declared credit / SLO-valid request')
handles,labels=axes[0,0].get_legend_handles_labels()
fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=9,bbox_to_anchor=(.5,.025))
fig.suptitle('Figure 6-9: same eight cards, capacity + failure + SLO + cost',fontsize=15)
fig.text(.5,.005,'Only >=75% valid completion is shown. Gaps mean ineligible. Solid: healthy; dashed: failure at50ms, recovery200ms +1 external credit. Teaching inputs.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.12,1,.95))
for ext in ('png','svg'):
    fig.savefig(root/f'figure-6-9.{ext}',dpi=150,**({'metadata':{'Date':None}} if ext=='svg' else {}))
(root/'curve-data.json').write_text(json.dumps(curve_data,indent=2)+'\n')
files=['calculate.py','result.json','plot.py','curve-data.json','figure-6-9.png','figure-6-9.svg']
(root/'figure-manifest.json').write_text(json.dumps({'scope':'candidate declared cohort scenarios; no actual device performance/price claim','sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}},indent=2)+'\n')
