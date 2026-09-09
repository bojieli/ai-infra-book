"""Plot measured request TTFT and scheduler waiting; matplotlib required."""
import json
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).parent/'results'
names=['measured-chunk512','measured-chunk8192','measured-nochunk8192','measured-graph512']
labels=['chunk 512 / eager','chunk 8192 / eager','no chunk / eager','chunk 512 / decode graph']
fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
for i,(name,label) in enumerate(zip(names,labels)):
    rows=json.loads((root/name/'summary.json').read_text())['requests']
    for ax,key,title in zip(axes,['delivered_ttft_ms','engine_queue_ms'],['First output delivery','Engine queue waiting']):
        x=[r+(i-1.5)*.19 for r in range(6)]
        data=[[v[key] for v in rows if v['id']==f'r{r}'] for r in range(6)]
        means=[statistics.median(v) for v in data]
        ax.bar(x,means,width=.18,label=label)
        ax.errorbar(x,means,yerr=[[m-min(v) for m,v in zip(means,data)],[max(v)-m for m,v in zip(means,data)]],fmt='none',ecolor='black',capsize=2,lw=.7)
        ax.set_title(title); ax.set_ylabel('ms'); ax.set_xticks(range(6),['r0\n128','r1\n2048','r2\n256','r3\n4096','r4\n512','r5\n1024'])
        ax.set_xlabel('Request / prompt tokens');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
axes[0].legend(fontsize=8)
fig.suptitle('Qwen3-8B BF16 / RTX PRO 6000 / vLLM 0.23.0\n3 trials: median and min–max; shared GPU; fixed synthetic arrivals',fontsize=11)
for suffix in ['png','svg']:
    fig.savefig(root/f'replay.{suffix}',dpi=160)

fig2,ax=plt.subplots(figsize=(7.2,4.3),layout='constrained')
for name,label in zip(names,labels):
    engine=json.loads((root/name/'summary.json').read_text())['engine']
    values=sorted(v*1000 for v in engine['inter_token_intervals_s'])
    ax.step(values,[(i+1)/len(values) for i in range(len(values))],where='post',label=label)
ax.set_xscale('log');ax.set_xlabel('Engine token interval (ms, log scale)')
ax.set_ylabel('Empirical cumulative fraction');ax.set_ylim(.8,1.002)
ax.set_title('Decode interval tail: larger prefill budget exposes long stalls\n1,998 intervals per configuration; three trials pooled',fontsize=11)
ax.legend(fontsize=8,loc='lower right');ax.grid(alpha=.2)
for suffix in ['png','svg']:
    fig2.savefig(root/f'itl-tail.{suffix}',dpi=160)
