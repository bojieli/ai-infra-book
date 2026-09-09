from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parent;rows=json.loads((B/'evaluations.json').read_text());fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for width,color in zip([64,128,256],['#3667a4','#ce7338','#49865e']):
 for seed,style in [(308,'-'),(309,'--')]:
  rr=sorted([r for r in rows if r['width']==width and r['seed']==seed],key=lambda r:r['D']);label=f'{rr[0]["N"]:,} parameters' if seed==308 else None
  axes[0].plot([r['D']/1024 for r in rr],[r['val_mean_nll'] for r in rr],style,marker='o',color=color,label=label)
  axes[1].plot(rr[-1]['N'],rr[-1]['val_mean_nll'],'o' if seed==308 else '^',color=color)
axes[0].set(xlabel='Actual training targets (KiB of next-byte labels)',ylabel='Held-out mean NLL (nats per byte)',title='Identical data prefixes; two initialization seeds');axes[0].legend(fontsize=8)
axes[1].set(xlabel='Actual unique parameter count',ylabel='Held-out mean NLL (nats per byte)',title='After 524,288 training targets');axes[1].set_xscale('log')
from matplotlib.lines import Line2D
axes[1].legend(handles=[Line2D([],[],color='gray',marker='o',linestyle='None',label='Seed 308'),Line2D([],[],color='gray',marker='^',linestyle='None',label='Seed 309')],fontsize=8)
for ax in axes:ax.grid(alpha=.2)
fig.suptitle('Two-layer CPU language models, fixed optimizer and one held-out text segment\nLocal observations only; no scaling-law fit or large-model extrapolation',fontsize=11)
for ext in ['png','svg']:fig.savefig(B/f'learning-curves.{ext}',dpi=180)
