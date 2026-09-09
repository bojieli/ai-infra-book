import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;data=json.loads((R/'results/resource-samples.json').read_text())['samples'];rounds=[json.loads(l) for l in (R/'results/rounds.jsonl').read_text().splitlines()]
fig,axes=plt.subplots(2,1,figsize=(9,5.5),sharex=True,layout='constrained')
x=[s['t_s'] for s in data];cpu0=data[0]['cpu_user_s']+data[0]['cpu_system_s']
axes[0].plot(x,[s['rss_kib']/1024 for s in data]);axes[0].set_ylabel('Controller RSS (MiB)')
axes[1].plot(x,[s['cpu_user_s']+s['cpu_system_s']-cpu0 for s in data]);axes[1].set_ylabel('Controller CPU seconds');axes[1].set_xlabel('Seconds from repair-loop start')
for ax in axes:
 for i,r in enumerate(rounds):
  ax.axvspan(r['model_start_s'],r['model_end_s'],color='tab:blue',alpha=.08,label='Model request interval' if i==0 else None)
  ax.axvline(r['tool_start_s'],color='tab:orange',alpha=.7,linewidth=.7,label='Tool dispatch' if i==0 else None)
 ax.grid(alpha=.2)
axes[0].legend(fontsize=8)
fig.suptitle('Real repair Agent controller; GPU worker and child RSS excluded')
fig.savefig(R/'resources.png',dpi=170)
