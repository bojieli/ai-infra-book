import json
from pathlib import Path
import matplotlib.pyplot as plt
r=Path(__file__).absolute().parent;a=json.loads((r/'analysis.json').read_text())
fig,axes=plt.subplots(2,1,figsize=(11,6),layout='constrained')
pts=a['saved_reference_curve'];axes[0].step([p[0] for p in pts],[p[1]/1024 for p in pts],where='post',label='Live saved nonparameter storages (deduplicated)')
for mb in a['host_forward_intervals']:axes[0].axvspan(mb['start_ms'],mb['end_ms'],color='C1',alpha=.15)
axes[0].set(xlabel='Host callback time since first event (ms)',ylabel='Saved-reference storage (KiB)',title='Eight microbatches; shaded intervals are host forward calls')
axes[0].legend(fontsize=8);axes[0].grid(axis='y',alpha=.2)
bins=list(range(0,int(a['cuda_kernel_span_ms'])+2,2))
values=[sum(max(0,min(start+dur,b+2)-max(start,b)) for start,dur in a['cuda_kernel_intervals_ms']) for b in bins]
axes[1].bar(bins,values,width=2,align='edge',color='C2')
axes[1].set(xlabel='GPU trace time since first kernel (ms)',ylabel='Summed kernel time per 2 ms bin (ms)',title=f"{a['cuda_kernel_count']} actual GPU kernels; profiler and host overhead retained")
fig.suptitle('Megatron Core 0.16.0: official no-pipeline GPU baseline\nSingle rank; no four-stage speedup claim; host and GPU clocks have separate origins',fontsize=11)
for ext in ['png','svg']:fig.savefig(r/('baseline-lifetime.'+ext),dpi=160)
