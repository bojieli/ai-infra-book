import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).absolute().parent
j=json.loads((B/'results/analysis.json').read_text());t=max(j['traces'],key=lambda t:t['kernel_count'])
top=sorted(t['kernels'].items(),key=lambda kv:-kv[1]['sum_duration_us'])[:10]
labels=[f'K{i+1}: '+(name if len(name)<66 else name[:63]+'…') for i,(name,v) in enumerate(top)]
fig,ax=plt.subplots(figsize=(12,5.5),layout='constrained')
ax.barh(labels,[v['sum_duration_us']/1000 for name,v in top]);ax.invert_yaxis()
ax.set(xlabel='Sum of recorded CUDA kernel durations (ms)',title='Four profiled Qwen3-VL MoE requests: top kernel names\nSums are not elapsed time or disjoint dispatch/GEMM/combine phases')
ax.grid(axis='x',alpha=.2)
for ext in ['png','svg']:fig.savefig(B/'results'/('kernel-durations.'+ext),dpi=150)
(B/'results/kernel-labels.json').write_text(json.dumps([dict(label=f'K{i+1}',name=n,**v) for i,(n,v) in enumerate(top)],indent=2)+'\n')
