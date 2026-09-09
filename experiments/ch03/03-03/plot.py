import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
s=json.loads((R/'summary.json').read_text());raw=[json.loads(x) for x in (R/'results/raw.jsonl').read_text().splitlines()];policies=['serial','parallel','adaptive'];colors=['#3478b5','#e79038','#579b68']
fig,axes=plt.subplots(1,3,figsize=(12,3.8))
axes[0].bar(policies,[s[p]['correct'] for p in policies],color=colors);axes[0].set_ylim(0,8.8);axes[0].set_ylabel('Correct task results / 8');axes[0].set_title('Fixed answer selection rule')
for i,p in enumerate(policies):axes[0].text(i,s[p]['correct']+.15,str(s[p]['correct'])+'/8',ha='center',color='firebrick')
axes[1].bar(policies,[s[p]['wall_s'] for p in policies],color=colors);axes[1].set_ylabel('Sum of task wall times (seconds)');axes[1].set_title('Generation + validation + selection')
for i,p in enumerate(policies):
 lengths=[len(c['output_ids']) for r in raw if r['policy']==p for c in r['candidates']]
 axes[2].scatter([i+(j%5-2)*.035 for j in range(len(lengths))],lengths,color=colors[i],alpha=.5)
axes[2].set_xticks(range(3),policies);axes[2].set_ylabel('Generated tokens per candidate');axes[2].axhline(1024,color='gray',ls='--');axes[2].set_title('Thinking + final output, total cap 1024')
for ax in axes:ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.tight_layout();fig.savefig(R/'comparison.png',dpi=160);fig.savefig(R/'comparison.svg')
