import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).parent
r=json.loads((root/'reasoning-comparison.json').read_text())['runs']
fig,axes=plt.subplots(1,3,figsize=(11,4.5),layout='constrained')
x=[0,1];labels=['Thinking off','Thinking on']
axes[0].bar(x,[a['total_model_s'] for a in r],label='Model wall time',color='#487eab')
axes[0].bar(x,[a['total_tool_s'] for a in r],bottom=[a['total_model_s'] for a in r],label='Tool wall time',color='#d08b3c')
axes[0].set_ylabel('Seconds');axes[0].set_title('Total observed work');axes[0].legend(fontsize=8)
axes[1].bar(x,[a['reasoning_tokens'] for a in r],label='Before reasoning end',color='#487eab')
axes[1].bar(x,[a['post_reasoning_tokens']+a['reasoning_end_delimiters'] for a in r],
            bottom=[a['reasoning_tokens'] for a in r],label='Delimiter + remaining',color='#d08b3c')
axes[1].set_ylabel('Generated tokens');axes[1].set_title('Includes truncated output');axes[1].legend(fontsize=8)
axes[2].bar([v-.18 for v in x],[a['value_and_input_passed'] for a in r],width=.35,label='Value + input unchanged',color='#60a16d')
axes[2].bar([v+.18 for v in x],[a['independent_passed'] for a in r],width=.35,label='+ no first-result alias',color='#487eab')
axes[2].set_ylabel('Passed cases / 1,013');axes[2].set_title('Two distinct test criteria');axes[2].legend(fontsize=7,loc='upper left')
axes[2].set_ylim(0,1300)
for ax in axes:
    ax.set_xticks(x,labels);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.suptitle('Same Qwen3-8B task and token limits: reasoning changes the outcome\nOne run per mode; shared GPU; task checks are not population success rates',fontsize=11)
for ext in ['svg','png']:fig.savefig(root/f'reasoning-comparison.{ext}',dpi=160)
