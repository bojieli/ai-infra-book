import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;curves=json.loads((R/'curves.json').read_text())
fig,ax=plt.subplots(figsize=(8,4.5),layout='constrained')
for name,curve in curves.items():
 trial,delay=name.split('-');ax.step([r['t_s'] for r in curve],[r['outstanding'] for r in curve],where='post',label=f'{delay} service delay, trial {trial}',color='tab:blue' if delay=='10ms' else 'tab:orange',linestyle='-' if trial=='0' else '--',alpha=.85)
ax.axvline(2,color='black',linestyle=':',label='Backend available after 2 s')
ax.set(xlabel='Seconds from first scheduled event',ylabel='Dispatched but not committed events',title='Real Collector file queue; new arrivals continue during recovery',ylim=(0,None));ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.savefig(R/'backlog.png',dpi=170)
