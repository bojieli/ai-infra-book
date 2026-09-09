import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
rows = [r for r in json.loads((ROOT / 'summary.json').read_text())['rows'] if not r['warmup']]
fig, ax = plt.subplots(figsize=(9, 4), constrained_layout=True)
labels = []
for i, r in enumerate(rows):
    a, b, c = [r[k] for k in ['ready_after_launch_s', 'first_complete_after_launch_s', 'drained_after_launch_s']]
    ax.plot([0, c], [i, i], color='#cccccc', linewidth=3)
    for t, marker, color, label in [(a, 'o', '#3b78a0', 'Ready'), (b, 's', '#e09a40', 'First response'), (c, 'D', '#429369', 'All 8 responses')]:
        ax.scatter(t, i, marker=marker, color=color, label=label if i == 0 else None)
    labels.append('Trial ' + r['trial'] + ': ' + r['policy'])
ax.set_yticks(range(len(rows)), labels)
ax.set_xlabel('Seconds after process launch (cache-directory preparation excluded)')
ax.set_title('Fixed client startup backlog; same 8 requests per fresh server')
ax.set_xlim(left=0)
ax.legend(loc='upper left')
fig.savefig(ROOT / 'startup.png', dpi=160)
fig.savefig(ROOT / 'startup.svg')
