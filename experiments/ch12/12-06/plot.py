#!/usr/bin/env python3
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[k]='1'
import json, pathlib
os.environ['MPLCONFIGDIR']=str(pathlib.Path(__file__).resolve().parent/'mpl-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parent
rows=json.loads((ROOT/'results-summary.json').read_text())['rows']
fig,axes=plt.subplots(1,3,figsize=(12,4.2),layout='constrained')
colors={'replicate':'#2166ac','switch':'#c65b16'}
for mi,mode in enumerate(colors):
    for fi,fault in enumerate(('none','primary','endpoint')):
        r=[x for x in rows if x['mode']==mode and x['fault']==fault]; x=fi+(mi-.5)*.22
        axes[0].bar(x,sum(v['completed'] for v in r),width=.2,color=colors[mode],label=mode if fi==0 else None)
        axes[1].scatter([x]*len(r),[v['duplicate_audio_bytes']/1024 for v in r],color=colors[mode],alpha=.65)
        axes[2].scatter([x+(j-2)*.018 for j in range(len(r))],[v['application_ms'] for v in r],color=colors[mode],s=24)
for ax in axes:
    ax.set_xticks(range(3),['No fault','Primary close','Endpoint close']); ax.grid(axis='y',alpha=.2); ax.set_axisbelow(True)
axes[0].set(title='Application completion',ylabel='Completed / 5 attempts',ylim=(0,5.8)); axes[0].legend()
axes[1].set(title='Received duplicate PCM',ylabel='KiB per attempt',ylim=(-.2,5.6))
axes[2].set(title='Implementation observation only',ylabel='Connect A to completion / failure (ms)')
fig.suptitle('12-6 | Real loopback TCP, two processes, two connections\nEndpoint failure is an expected negative; no WAN or energy inference',fontsize=12)
fig.savefig(ROOT/'dualpath.png',dpi=170); fig.savefig(ROOT/'dualpath.svg'); plt.close(fig)
