import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze import ROOT,analyze
summary=analyze()
fig,axes=plt.subplots(1,2,figsize=(10,4.4))
for device,color,offset in [('mac','#3078b0',-.08),('rtx','#d47721',.08)]:
    raw=json.loads((ROOT/f'results/{device}/results.json').read_text())
    for ax,kind in zip(axes,['matmul','copy']):
        rows=[r for r in raw if r['kind']==kind]
        for x,r in enumerate(rows):
            y=[s['gpu_s']*1e6 for s in r['samples']]
            ax.scatter([x+offset]*len(y),y,s=14,alpha=.45,color=color)
        med=[r['gpu_median_us'] for r in summary if r['device']==device and r['kind']==kind]
        ax.plot([x+offset for x in range(3)],med,'o-',color=color,label=device.upper())
        ax.set_yscale('log');ax.set_ylabel('GPU batch time / operation (µs)');ax.grid(axis='y',alpha=.2)
axes[0].set_xticks(range(3),['M=1','M=32','M=256']);axes[0].set_title('FP32 GEMM: K=N=512')
axes[1].set_xticks(range(3),['16 MiB','64 MiB','256 MiB']);axes[1].set_title('Copy: payload size, warm reused buffers')
axes[0].legend();fig.suptitle('M2 Max / RTX PRO 6000: different runtime paths')
fig.text(.5,.015,'11 batch samples each; MPS command buffers vs CUDA Graph. No DRAM counters.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.04,1,.95))
for ext in ['png','svg']:fig.savefig(ROOT/f'results/comparison.{ext}',dpi=160)
