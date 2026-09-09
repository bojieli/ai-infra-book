import json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
rows=json.loads((ROOT/'results/first/results.json').read_text())['rows']
fig,axes=plt.subplots(1,2,figsize=(10,4.5),sharey=True)
for ax,row in zip(axes,rows):
 for mode,key,color,offset in [('Eager','eager_us','#3078b0',-.08),('CUDA Graph','graph_us','#d47721',.08)]:
  med=[]
  for i,name in enumerate(['source_chain','two_kernel','one_kernel']):
   y=row['paths'][name][key];med.append(statistics.median(y));ax.scatter([i+offset]*11,y,s=12,color=color,alpha=.4)
  ax.plot([i+offset for i in range(3)],med,'o-',color=color,label=mode)
 ax.set_xticks(range(3),['Source chain','Two kernels','One kernel']);ax.set_yscale('log');ax.grid(axis='y',alpha=.2);ax.set_title(f"T={row['t']}, D=2048")
axes[0].set_ylabel('CUDA event time / chain (µs)');axes[0].legend()
fig.suptitle('V4 expert activation subchain: preserve clipping and route-weight order')
fig.text(.5,.025,'11 × 20 calls; shared GPU, warm buffers. Graph construction excluded; small BF16 rounding differences remain.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.05,1,.94))
for ext in ['png','svg']:fig.savefig(ROOT/f'results/comparison.{ext}',dpi=160)
