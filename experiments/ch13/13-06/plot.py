import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
s=json.loads((ROOT/'results/summary.json').read_text());fig,axs=plt.subplots(1,2,figsize=(10,5),layout='constrained')
for i,r in enumerate(s['reports']):
 axs[0].scatter([i]*5,[v*1000 for v in r['client_s']],alpha=.7)
 axs[0].plot([i-.15,i+.15],[r['client_median_s']*1000]*2,color='black')
axs[0].set_xticks([0,1],['256 tokens','512 tokens']);axs[0].set(ylabel='Client completion latency (ms)',title='Five new requests per configuration')
axs[1].axhline(1,color='gray',ls=':',label='Equal latency');axs[1].axhline(1.1,color='#b65735',ls='--',label='Sealed prediction minimum')
axs[1].scatter([0],[s['measured_ratio256_over512']],s=70,label='Measured median ratio');axs[1].set(xlim=(-.5,.5),ylim=(0,max(1.4,s['measured_ratio256_over512']+.15)),ylabel='256 / 512 latency ratio',title='Prediction vs new evidence',xticks=[]);axs[1].legend(fontsize=8)
for ax in axs:ax.grid(axis='y',alpha=.2)
fig.suptitle('Qwen3-8B, same 8K prompt, eager / APC off\nInstrumented single-request experiment; fixed engine order')
for ext in ['svg','png']:fig.savefig(ROOT/f'results/prediction.{ext}',dpi=150)
