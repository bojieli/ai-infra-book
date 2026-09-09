import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
d=json.loads((ROOT/'summary.json').read_text())
fig,ax=plt.subplots(figsize=(8,3.6),layout='constrained')
rows=d['requests'];device=[(r['details'] or {}).get('device',0) for r in rows];storage=[(r['details'] or {}).get('storage',0) for r in rows]
ax.bar(range(6),device,label='Device cache',color='#3576a8');ax.bar(range(6),storage,bottom=device,label='File storage',color='#dc8d31')
ax.set_xticks(range(6),['Writer 1','Writer 2','Writer 3','Restart 1','Restart 2','Restart 3']);ax.set_ylim(0,1250);ax.set_ylabel('Reused prompt tokens / 1024');ax.set_title('HiCache normal restart: reported cache source');ax.axvline(2.5,color='gray',linestyle='--',linewidth=1);ax.legend(loc='upper left',ncol=2,frameon=False)
for i,r in enumerate(rows):ax.text(i,r['cached_tokens']+22,str(r['cached_tokens']),ha='center')
fig.savefig(ROOT/'cache-source.png',dpi=170)
