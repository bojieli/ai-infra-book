"""Plot only validated observed counts. No mock data, traffic or capacity model."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ap=argparse.ArgumentParser()
ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args()
p=a.out/'route-analysis.json'
d=json.loads(p.read_text())
assert d['status']=='observed_routes_validated'
cases=[r['id'] for r in json.loads((a.out/'cases.json').read_text())['cases']]
assert len(cases)==4
plots=a.out/'plots';plots.mkdir(exist_ok=True)
manifest=dict(analysis_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),figures=[])
for phase in ['prefill','decode']:
    matrices=[]; denominators=[]
    for case in cases:
        rows=[r for r in d['counts'] if r['case_id']==case and r['phase']==phase]
        raw=np.zeros((43,256),dtype=np.int64)
        den=np.zeros(43,dtype=np.int64)
        for r in rows:
            raw[r['layer_id']]+=np.asarray(r['expert_counts'],dtype=np.int64)
            den[r['layer_id']]+=r['valid_tokens']
        assert (den>0).all() and (den==den[0]).all()
        assert np.array_equal(raw.sum(axis=1),6*den)
        matrices.append(raw/den[:,None] if phase=='prefill' else raw)
        denominators.append(int(den[0]))
    fig,axs=plt.subplots(2,2,figsize=(13.2,8.5),sharex=True,sharey=True)
    fig.subplots_adjust(left=.07,right=.875,bottom=.15,top=.90,wspace=.13,hspace=.25)
    vmax=max(float(m.max()) for m in matrices)
    for ax,case,m,n in zip(axs.flat,cases,matrices,denominators):
        im=ax.imshow(m,origin='upper',aspect='auto',interpolation='nearest',cmap='magma',vmin=0,vmax=vmax)
        ax.axhline(2.5,color='#67e8f9',linewidth=.75)
        suffix=' (includes 1 terminal EOS)' if phase=='decode' else ''
        ax.set_title(f"{case.replace('retrieval-','')} · {n} tokens{suffix}",fontsize=9)
        ax.set_xticks([0,64,128,192,255]);ax.set_yticks([0,2,10,20,30,42])
        ax.set_xlabel('Expert ID');ax.set_ylabel('Layer ID')
    unit='Assignments / consumed token' if phase=='prefill' else 'Observed assignment count'
    cax=fig.add_axes([.90,.22,.018,.60])
    fig.colorbar(im,cax=cax,label=unit)
    title='Actual V4 prefill routes — four frozen prompts' if phase=='prefill' else 'Actual V4 decode routes — small observed samples only'
    fig.suptitle(title,fontsize=15)
    fig.text(.5,.035,'Cyan boundary: layers 0–2 use hash routing; layers 3–42 use learned TopK. Six assignments per token.\nObserver adds copies and synchronization; these are route observations, not communication measurements.',ha='center',fontsize=9)
    for ext in ['png','svg']:
        f=plots/f'{phase}-routes.{ext}';fig.savefig(f,dpi=180,bbox_inches='tight',pad_inches=.15)
        manifest['figures'].append(dict(file=str(f.relative_to(a.out)),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),phase=phase,unit=unit,consumed_tokens_per_case=dict(zip(cases,denominators)),color_max=vmax))
    plt.close(fig)
(plots/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
