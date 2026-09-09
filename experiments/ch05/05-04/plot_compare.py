import json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
rows=json.loads((ROOT/'results/compare/results.json').read_text())['rows']
fig,axes=plt.subplots(1,2,figsize=(10,4.5),sharey=True)
for ax,row in zip(axes,rows):
 for mode,key,color,offset in [('Eager','samples_us','#3078b0',-.08),('CUDA Graph','graph_samples_us','#d47721',.08)]:
  med=[]
  for i,name in enumerate(['opaque_custom','compiler_visible','explicit_fusion']):
   y=row['paths'][name][key];med.append(statistics.median(y));ax.scatter([i+offset]*11,y,s=12,color=color,alpha=.4)
  ax.plot([i+offset for i in range(3)],med,'o-',color=color,label=mode)
 ax.set_xticks(range(3),['Native cast\nopaque','RNE bits\ncompiled','Explicit\nfusion']);ax.set_yscale('log');ax.grid(axis='y',alpha=.2);ax.set_title(f"T={row['t']}, D=12288")
axes[0].set_ylabel('CUDA event time / chain (µs)');axes[0].legend()
fig.suptitle('SwiGLU → BF16 boundary → FP8: same-session comparison')
fig.text(.5,.025,'11 × 20 calls; shared GPU, warm buffers. Graph construction excluded; small FP8 bit differences remain.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.05,1,.94))
for ext in ['png','svg']:fig.savefig(ROOT/f'results/compare.{ext}',dpi=160)
