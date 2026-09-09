import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
reports=json.loads((ROOT/'profiles/analysis.json').read_text())['reports']
fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
for r,color in zip(reports,['#3388ae','#d57936']):
    label=r['mode'];steps=r['steps']
    axes[0].bar(label,steps[0]['swiglu_sum_ms'],color=color)
    axes[1].plot([s['step'] for s in steps[1:32]],[s['swiglu_sum_ms']*1000 for s in steps[1:32]],'-',label=label,color=color)
    axes[2].bar(label,r['range_ms'],color='#d9dfe3')
    axes[2].bar(label,r['swiglu_sum_ms'],color=color)
    axes[2].text(label,r['range_ms']+8,f"{r['swiglu_fraction_of_range']*100:.2f}% hotspot",ha='center',fontsize=9)
axes[0].set(title='Prefill: 36 SwiGLU kernels',ylabel='Kernel sum (ms)')
axes[1].set(title='Decode: 36 SwiGLU kernels / step',xlabel='Decode step',ylabel='Kernel sum (µs)');axes[1].legend()
axes[2].set(title='Whole capture vs hotspot',ylabel='Milliseconds');axes[2].set_ylim(0,950)
for ax in axes:ax.grid(axis='y',alpha=.2)
fig.suptitle('Matched 7239 / 32-token Nsight captures\nInstrumented single requests; timing comparison uses the separate paired run')
fig.savefig(ROOT/'profiles/comparison.svg');fig.savefig(ROOT/'profiles/comparison.png',dpi=160)
