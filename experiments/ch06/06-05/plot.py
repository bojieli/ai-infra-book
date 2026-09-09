from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parent;rows=[r for r in json.loads((B/'groups.json').read_text()) if r['dataset']=='formal' and not r['warmup']]
labels=['4 KiB','4 MiB','64 MiB'];sizes=sorted({r['bytes'] for r in rows})
fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for ax,field,baseline,title in zip(axs,['comm_visible_ms','compute_ms'],['comm','compute'],['Communication: submit to completion callback','Computation: actual CPU GEMM interval']):
 for i,n in enumerate(sizes):
  for trial in range(5):
   d={r['mode']:r for r in rows if r['bytes']==n and r['trial']==trial}
   ax.plot([i-.15,i+.15],[d[baseline][field],d['shared'][field]],color='.65',lw=.8,zorder=1)
  for offset,mode,color,label in [(-.15,baseline,'#3465a4','Alone'),(.15,'shared','#d86b39','Shared')]:
   vals=[r[field] for r in rows if r['bytes']==n and r['mode']==mode]
   ax.scatter([i+offset]*5,vals,color=color,s=24,label=label if i==0 else None,zorder=2)
 ax.set_xticks(range(3),labels);ax.set_ylabel('Maximum rank interval (ms)');ax.set_title(title,fontsize=11);ax.grid(axis='y',alpha=.25);ax.legend(frameon=False)
axs[0].set_yscale('log');axs[0].set_ylabel('Maximum rank interval (ms, log scale)')
fig.suptitle('Four CPU ranks: Gloo loopback and 16×4096×4096 GEMM\nFive paired blocks; shared OS/memory, no GPU or isolated-core claim',fontsize=13)
fig.savefig(B/'intervals.png',dpi=180);fig.savefig(B/'intervals.svg');plt.close(fig)
g=next(r for r in rows if r['bytes']==67108864 and r['trial']==0 and r['mode']=='shared');origin=g['start_ns']
fig,ax=plt.subplots(figsize=(12,4.7),layout='constrained')
for r in g['ranks']:
 m=r['marks'];rank=r['rank']
 for lo,hi,off,color in [('comm_submit_ns','comm_callback_ns',.06,'#3465a4'),('compute_start_ns','compute_end_ns',-.28,'#d86b39')]:
  ax.broken_barh([((m[lo]-origin)/1e6,(m[hi]-m[lo])/1e6)],(rank+off,.23),facecolors=color)
ax.set_yticks([i-.02 for i in range(4)],[f'Rank {i}' for i in range(4)]);ax.set_xlabel('Milliseconds from earliest rank start (same-host monotonic clock)');ax.set_title('64 MiB shared run, first trial (trial 0)\nBlue: communication outstanding until callback; orange: CPU GEMM',fontsize=12);ax.grid(axis='x',alpha=.25)
fig.savefig(B/'timeline.png',dpi=180);fig.savefig(B/'timeline.svg')
