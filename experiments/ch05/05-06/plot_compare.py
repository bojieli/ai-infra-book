import json
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
raw=json.loads((ROOT/'results/interleaved-v1/raw.json').read_text())
fig,axs=plt.subplots(2,2,figsize=(10,7),layout='constrained')
names=['native','compiled','schedule'];colors=['#627580','#3388ae','#d57936']
for i,t in enumerate([1,7239]):
    for j,mode in enumerate(['eager','graph']):
        ax=axs[i,j]
        for k,(name,color) in enumerate(zip(names,colors)):
            values=[r['event_us'] for r in raw['samples'] if (r['t'],r['mode'],r['name'])==(t,mode,name)]
            median=statistics.median(values)
            ax.scatter([k+(q-5)*.02 for q in range(11)],values,color=color,s=15,alpha=.7)
            ax.plot([k-.25,k+.25],[median]*2,color=color,lw=3,label=f'{name}: {median:.3f}')
        ax.set_xticks(range(3),names);ax.set(title=f'T={t}, {mode}',ylabel='CUDA event µs / call');ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8)
fig.suptitle('Post-selection interleaved measurements: 11 trials per path\nShared GPU; eager events include host submission gaps')
fig.savefig(ROOT/'results/interleaved.svg');fig.savefig(ROOT/'results/interleaved.png',dpi=160)
