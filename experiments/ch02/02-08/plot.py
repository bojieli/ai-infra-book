import json
from fractions import Fraction
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
x=json.loads((R/'summary.json').read_text());names=['chat_capture','agent_thinking_off','agent_thinking_on'];labels=['Chat capture','Agent thinking off','Agent thinking on']
fig,axs=plt.subplots(1,3,figsize=(14,4.3),layout='constrained')
for name,label in zip(names,labels):
 rows=[r for r in x['requests'] if r['group']==name]
 axs[0].plot([r['request']+1 for r in rows],[r['input_tokens'] for r in rows],marker='o',label=label)
axs[0].set(xlabel='Request in recorded trajectory',ylabel='Input token IDs',title='Observed growing histories');axs[0].legend(fontsize=8)
base=[0]*3
for key in ['reasoning','nonreasoning','delimiter','termination']:
 values=[next(g for g in x['groups'] if g['group']==n)['output_parts'][key] for n in names]
 axs[1].bar(labels,values,bottom=base,label=key);base=[a+b for a,b in zip(base,values)]
axs[1].set(ylabel='Returned output token IDs',title='Syntactic phase partition');axs[1].tick_params(axis='x',labelrotation=15);axs[1].legend(fontsize=8)
eq=x['equal_mean_offline'];xx=range(4)
for shift,d in zip([-.18,.18],eq['distributions']):
 axs[2].bar([i+shift for i in xx],[float(Fraction(w)) for w in d['weights']],width=.36,label=d['label'].replace('_',' '))
axs[2].set_xticks(list(xx),eq['observed_lengths']);axs[2].set(xlabel='Input + returned output token IDs',ylabel='Offline probability weight',title='Both means = 208; no new requests');axs[2].legend(fontsize=7)
fig.savefig(R/'profiles.png',dpi=170)
