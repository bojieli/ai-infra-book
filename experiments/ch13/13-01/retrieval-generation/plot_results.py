"""Figures from final observed retrieval→generation records; no simulated points."""
import argparse,hashlib,json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);a=p.parse_args();d=a.data
quality=json.loads((d/'quality.json').read_text());pipeline=json.loads((d/'pipeline-analysis.json').read_text());cells=quality['cells'];assert len(cells)==12
out=d/'plots';out.mkdir(exist_ok=True)
labels=[('Flat' if c['index']=='flat' else f'HNSW ef{c["efSearch"]}')+f'\nk={c["k"]}' for c in cells]
colors=['#168176' if c['eligible'] else '#a85f23' for c in cells];x=np.arange(12)
fig,axs=plt.subplots(2,1,figsize=(14,10));fig.subplots_adjust(left=.08,right=.98,bottom=.13,top=.92,hspace=.37)
cal=np.array([c['calibration_correct']/8 for c in cells]);ev=np.array([c['evaluation_correct']/16 for c in cells])
axs[0].bar(x-.18,cal,width=.34,color='#416ca8',label='Calibration (8 questions)');axs[0].bar(x+.18,ev,width=.34,color='#84b7d2',label='Held-out evaluation (16 questions)')
for i,c in enumerate(cells):
 axs[0].text(i-.18,cal[i]+.018,f'{c["calibration_correct"]}/8',ha='center',fontsize=8)
 axs[0].text(i+.18,ev[i]+.018,f'{c["evaluation_correct"]}/16',ha='center',fontsize=8)
axs[0].set_ylim(0,1.15);axs[0].set_ylabel('Strict exact-answer fraction');axs[0].set_xticks(x,labels,fontsize=8);axs[0].axhline(1,color='#555555',linestyle=':',linewidth=.8);axs[0].legend(loc='lower left');axs[0].set_title('Frozen cell quality — selected k=1 policies fail held-out validation')
for i,c in enumerate(cells):
 rows=[r for r in pipeline['records'] if r['config_id']==i and r['split']=='evaluation'];assert len(rows)==16
 vals=np.array([r['end_to_end_s']*1000 for r in rows]);jitter=np.linspace(-.15,.15,16)
 axs[1].scatter(i+jitter,vals,s=17,color=colors[i],alpha=.7)
 med=float(np.median(vals));axs[1].plot([i-.23,i+.23],[med,med],color='black',linewidth=2)
axs[1].set_yscale('log');axs[1].set_xticks(x,labels,fontsize=8);axs[1].set_ylabel('Observed full pipeline wall time (ms, log scale)');axs[1].set_title('Live CPU query encoder + Faiss + tokenizer + GPU generation: 16 held-out observations per cell')
axs[1].grid(axis='y',alpha=.2);fig.text(.5,.035,'Teal: fixed cell passes all 24 questions; brown: fails at least one split. Black: median.\nNo calibration-selected policy passed held-out validation. Single shared-host run with observers; no stable speed ranking.',ha='center',fontsize=10)
for ext in ['png','svg']:fig.savefig(out/f'quality-pipeline.{ext}',dpi=180,bbox_inches='tight',pad_inches=.15)
plt.close(fig)
fig,ax=plt.subplots(figsize=(10,6));fig.subplots_adjust(left=.1,right=.96,top=.87,bottom=.2)
for i,c in enumerate(cells):
 rows=[r for r in pipeline['records'] if r['config_id']==i and r['split']=='evaluation']
 if not c['eligible']:continue
 ax.scatter([r['input_tokens'] for r in rows],[r['assigned_kv_storage_bytes']/1024**2 for r in rows],s=45,alpha=.7,marker='o' if c['k']==4 else '^',label=labels[i].replace('\n',' '))
ax.set_xlabel('Actual prompt tokens');ax.set_ylabel('Observed peak request-assigned KV block storage (MiB)');ax.set_title('Actual KV assignment for six fixed cells passing all 24 questions\n16 held-out requests per cell; overlapping marks represent actual repeated sizes')
ax.grid(alpha=.2);ax.legend(fontsize=9,ncol=2)
fig.text(.5,.04,f'Actual worker pool: {pipeline["pool_blocks"]} blocks / {pipeline["reserved_pool_storage_bytes"]:,} bytes reserved.\nAssigned blocks come from native scheduler records; pool reservation stays fixed. No allocator-wide or GPU-total peak claim.',ha='center',fontsize=9)
for ext in ['png','svg']:fig.savefig(out/f'actual-kv.{ext}',dpi=180,bbox_inches='tight',pad_inches=.15)
plt.close(fig)
manifest=dict(sources={n:hashlib.sha256((d/n).read_bytes()).hexdigest() for n in ['quality.json','pipeline-analysis.json']},figures=[dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(out.iterdir()) if f.suffix in ['.png','.svg']])
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
