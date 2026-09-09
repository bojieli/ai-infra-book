import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent/'results';s=json.loads((P/'summary.json').read_text());q=json.loads((P/'quality.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(11,4.3))
for op,label in [('direct','Packed 4-bit direct'),('decode_matmul','Dequantize + matmul'),('cached_expanded_matmul','Resident expanded matmul')]:
 g=[r for r in s if r['operation']==op];axes[0].plot([r['batch'] for r in g],[r['median_ms'] for r in g],marker='o',label=label)
axes[0].set(xscale='log',xlabel='Batch (log scale)',ylabel='Synchronized wall time median (ms)',title='Same quantized weights and FP16 activations');axes[0].legend();axes[0].grid(alpha=.2)
g=[r for r in q['outputs'] if r['operation']=='direct']
for ref,label in [('same_quant_reference','Same quantized reference'),('original_fp32_reference','Original FP32 reference')]:
 axes[1].plot([r['batch'] for r in g],[r[ref]['relative_l2'] for r in g],marker='o',label=label)
axes[1].set(xscale='log',yscale='log',xlabel='Batch (log scale)',ylabel='Relative L2 output error',title='Kernel consistency and quantization differ');axes[1].legend();axes[1].grid(alpha=.2)
fig.tight_layout();fig.savefig(P/'lowbit.png',dpi=160);fig.savefig(P/'lowbit.svg')
