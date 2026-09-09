import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent;summary=json.loads((ROOT/'results/schedule-summary.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(11,4.5))
for ax,t in zip(axes,[1,7239]):
 labels=[]
 for i,r in enumerate(summary['rows']):
  d=json.loads((ROOT/f"results/schedule-search-v2/{r['index']}-{r['kind']}.json").read_text());row=next(x for x in d['rows'] if x['t']==t)
  color='#d47721' if r['index']==summary['selected_schedule']['index'] else '#3078b0'
  ax.scatter([i]*11,row['samples_us'],s=12,color=color,alpha=.45);ax.scatter(i,r['median_us'][str(t)],s=42,color=color)
  labels.append('Native' if r['kind']=='native' else 'Compile' if r['kind']=='compiled' else str(r['block']))
 ax.set_xticks(range(len(labels)),labels,rotation=35);ax.set_title(f'T={t}, D=12288');ax.set_ylabel('Graph time / call (µs)');ax.grid(axis='y',alpha=.2)
fig.suptitle('Real Qwen activations: baseline and six schedule candidates')
fig.text(.5,.025,'Orange: selected on search shapes. Sequential shared-GPU runs; not an exclusive-window speed claim.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.05,1,.94))
for ext in ['svg','png']:fig.savefig(ROOT/f'results/schedule-search.{ext}',dpi=160)
