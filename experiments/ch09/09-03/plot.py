import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
root=Path(__file__).resolve().parent;d=json.loads((root/'records.json').read_text());metrics=['HumanEval','MBPP','GSM8K','StrategyQA']
fig,ax=plt.subplots(figsize=(8,3.8),layout='constrained')
for i,(r,color) in enumerate(zip(d['quality_changes'],['#3477a5','#cf8531','#57854b'])):
 x=np.arange(4)+(i-1)*.24;y=[r['delta_percentage_points'][m] for m in metrics]
 ax.bar(x,y,width=.23,label=r['model'],color=color)
 for xx,yy in zip(x,y):ax.text(xx,yy+(.06 if yy>=0 else -.06),f'{yy:+.1f}',ha='center',va='bottom' if yy>=0 else 'top',fontsize=9)
ax.axhline(0,color='black',linewidth=.8);ax.set_xticks(range(4),metrics);ax.set_ylim(-1.8,2.65);ax.set_ylabel('Score change (percentage points)');ax.set_title('Published Table 2: Expert Deferral minus baseline');ax.legend(ncol=3,loc='upper right',frameon=False);fig.savefig(root/'quality-deltas.png',dpi=170)
