import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
rows=json.loads((R/'results/summary.json').read_text())['rows'];fig,axes=plt.subplots(1,2,figsize=(11,4))
for name,label in [('int8_direct_e2e','INT8 direct, full path'),('int8_dequant_bf16_e2e','Dequantize to BF16, full path')]:
 axes[0].plot([r['m'] for r in rows],[1000*r['stages'][name]['device_ms']['median'] for r in rows],'o-',label=label)
for name,label in [('int8_matmul_only','INT8 matmul only'),('bf16_matmul_only','BF16 matmul only')]:
 axes[1].plot([r['m'] for r in rows],[1000*r['stages'][name]['device_ms']['median'] for r in rows],'o-',label=label)
for ax in axes:ax.set_xscale('log');ax.set_xlabel('Batch M; INT8 pads M < 32 to 32');ax.set_ylabel('CUDA event stream span (microseconds)');ax.set_ylim(bottom=0);ax.legend();ax.grid(alpha=.2)
fig.suptitle('RTX PRO 6000: same INT8 weights and activation quantization')
fig.tight_layout();fig.savefig(R/'results/paths.png',dpi=160);fig.savefig(R/'results/paths.svg')
