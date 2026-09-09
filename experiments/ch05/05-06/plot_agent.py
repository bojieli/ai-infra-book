import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
fig,axes=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
for version,color in [(1,'#2369a1'),(2,'#b95732')]:
    rows=[json.loads(p.read_text()) for p in sorted((ROOT/f'results/agent-search-v{version}').glob('round-*.json'))]
    x=[r['turn']+1 for r in rows]
    axes[1].plot(x,[r['charged_s'] for r in rows],'-o',color=color,label=f'Run {version}')
    if version==1:axes[0].plot(x,[r['tool_result']['score_us'] for r in rows],'-o',color=color,label='Run 1: same code each turn')
axes[0].set(xlabel='Tool turn',ylabel='Sum of two shape medians (µs)',title='Repeated code; timing variation only')
axes[0].text(.03,.93,'Run 2: all six duplicates rejected\nNo measured scores',transform=axes[0].transAxes,va='top',color='#b95732')
axes[0].set_ylim(346.65,347.6)
axes[1].axhline(60,color='gray',ls='--',label='Budget ceiling')
axes[1].set(xlabel='Tool turn',ylabel='Charged seconds (cumulative)',title='Inference wall + evaluation event windows')
for ax in axes:ax.grid(alpha=.2);ax.set_xticks(range(1,7));ax.legend(loc='lower right',fontsize=8)
fig.suptitle('Actual Qwen3-8B tool loop: no new candidate discovered')
fig.savefig(ROOT/'results/agent-search.svg');fig.savefig(ROOT/'results/agent-search.png',dpi=160)
