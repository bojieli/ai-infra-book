import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).absolute().parent
j=json.loads((B/'results/analysis.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
for i,ax in enumerate(axes):
    for row in j['cases']:
        s=row['stages'][i]
        ax.plot(range(48),[100*v/s['aligned_tokens'] for v in s['expert_sets_different_by_layer']],label=row['id'],lw=1.2)
    ax.set(xlabel='Layer (zero-based)',ylabel='Positions with different top-8 sets (%)',ylim=(0,100),
           title=('Prompt: 7,235 positions/task' if i==0 else 'Continuation: 45 positions/task'))
    ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.suptitle('Same four answers and output IDs; different MoE routes\nTRITON W8A8 vs MARLIN W8A16, Qwen3-VL MoE')
for ext in ['png','svg']:fig.savefig(B/'results'/('route-differences.'+ext),dpi=160)
