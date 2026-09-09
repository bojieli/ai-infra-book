from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).absolute().parent
j=json.loads((B/'results/analysis.json').read_text());counts=np.load(B/'results/counts.npy',allow_pickle=False)
for stage,index in [('prompt',0),('continuation',1)]:
    fig,axes=plt.subplots(2,2,figsize=(10,6),layout='constrained')
    vmax=max(float(counts[i*2+index].max()/j['cases'][i]['stages'][index]['tokens']) for i in range(4))
    for i,ax in enumerate(axes.flat):
        c=j['cases'][i];tokens=c['stages'][index]['tokens']
        im=ax.imshow(counts[i*2+index]/tokens,origin='lower',aspect='auto',vmin=0,vmax=vmax,cmap='magma')
        ax.set(title=f"{c['id']}: {tokens} consumed tokens",xlabel='Logical expert ID',ylabel='Layer')
    fig.colorbar(im,ax=axes,label='Assignments / token (sum across experts = 8)')
    fig.suptitle('Qwen3-VL MoE native routes: '+stage+'; four fixed retrieval tasks')
    for ext in ['png','svg']:fig.savefig(B/'results'/(stage+'-routes.'+ext),dpi=150)
