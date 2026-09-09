import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent;d=json.loads((root/'summary.json').read_text())
fig,ax=plt.subplots(figsize=(7,3.4),layout='constrained')
for i,c in enumerate(d['cases']):
 ax.bar([i*4+j for j in range(3)],[r['cached_tokens'] for r in c['requests']],color=['#d78a32','#3676a5','#3676a5'])
 for j,r in enumerate(c['requests']):ax.text(i*4+j,r['cached_tokens']+20,str(r['cached_tokens']),ha='center')
ax.set_xticks([0,1,2,4,5,6],['First','Repeat 1','Repeat 2']*2);ax.set_ylim(0,1200);ax.set_ylabel('Reused prompt tokens / 1024');ax.set_title('Missing page 0                      Missing page 32');ax.text(.5,.95,'Orange: first request; blue: device-cache repeats',ha='center',transform=ax.transAxes,fontsize=9)
fig.savefig(root/'missing-pages.png',dpi=170)
