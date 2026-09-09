import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
rows = json.loads((ROOT / 'summary.json').read_text())['groups']
fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
conditions = [(e, n) for e in ['native', 'http_plain', 'http_logprob'] for n in [1, 8]]
labels = [e.replace('http_', 'HTTP\n') + '\n' + str(n) + ' request(s)' for e, n in conditions]
for ax, key, title in zip(axes, ['first_cached_tokens', 'get_count'],
                          ['First completed request: reported cached tokens', 'Successful file get calls in complete request wave']):
    for i, (entry, count) in enumerate(conditions):
        subset = sorted([r for r in rows if r['entry'] == entry and r['count'] == count], key=lambda r: r['trial'])
        for j, r in enumerate(subset):
            if r[key] is None:
                if j == 0: ax.text(i, 5, 'not observed', ha='center', va='bottom', fontsize=7)
                continue
            ax.bar(i + (j - .5) * .3, r[key], width=.28, color=['#3b78a0', '#e09a40'][j], label='Trial '+str(j) if i == 0 else None)
    ax.set_xticks(range(6), labels, fontsize=8)
    ax.set_ylim(bottom=0)
    ax.set_title(title, fontsize=10)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label='Trial '+str(i)) for i,c in enumerate(['#3b78a0','#e09a40'])])
fig.suptitle('Same complete file cache, wait_complete, and outputs; 12 fresh engines')
fig.savefig(ROOT / 'cache-behavior.png', dpi=160)
fig.savefig(ROOT / 'cache-behavior.svg')
