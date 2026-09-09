import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
s=json.loads((ROOT/'results/summary.json').read_text());fig,axs=plt.subplots(1,2,figsize=(11,5),layout='constrained')
for j,key in enumerate(['window_s','training_s']):
 for i,m in enumerate(['none','sync','async']):
  rows=[r for r in s['runs'] if r['mode']==m]
  axs[j].scatter([i]*5,[1000*r[key] for r in rows],s=35,alpha=.7)
  axs[j].plot([i-.15,i+.15],[1000*s['medians'][m][key]]*2,color='black',lw=2)
 axs[j].set_xticks([0,1,2],['No save','Synchronous','Asynchronous']);axs[j].set(ylabel='Milliseconds',title='Training and save both complete' if j==0 else 'Actual 20-step training interval');axs[j].grid(axis='y',alpha=.2)
fig.suptitle('CPU DCP: identical final model, optimizer and RNG state\nFive fresh processes per mode; no injected storage delay; bars mark medians')
for ext in ['svg','png']:fig.savefig(ROOT/f'results/comparison.{ext}',dpi=150)
