import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'results/analysis.json').read_text())
fig,ax=plt.subplots(figsize=(11,6),layout='constrained');ax.set(xlim=(0,11),ylim=(0,6));ax.axis('off')
def box(x,y,w,h,title,body,color):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08',facecolor=color,edgecolor='#566675'))
    ax.text(x+w/2,y+h-.25,title,ha='center',va='top',fontsize=12,weight='bold')
    ax.text(x+w/2,y+h/2-.12,body,ha='center',va='center',fontsize=10)
def arrow(a,b,label,offset=(0,0),style='-'):
    ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color='#536773',lw=1.6,linestyle=style))
    ax.text((a[0]+b[0])/2+offset[0],(a[1]+b[1])/2+offset[1],label,ha='center',va='center',fontsize=9,bbox=dict(facecolor='white',edgecolor='none',alpha=.95))
box(.3,3.9,3.4,1.3,'CPU controller / RAM','Chat messages + token IDs\nJSON parsing; tool dispatch','#e1edf4')
box(7.1,3.9,3.5,1.3,'GPU / device memory','Resident Qwen3-8B\nGenerate candidate code','#e6eee0')
box(.3,.6,3.4,1.3,'Host files','Model cache; captured tensors\nCandidate .py; JSON; logs','#f3e8d9')
box(7.1,.6,3.5,1.3,'Evaluator CPU + same GPU','Load inputs; correctness checks\nKernel timing; result JSON','#e6eee0')
arrow((3.8,4.9),(7,4.9),'Prompt tokens',(0,.2))
arrow((7,4.2),(3.8,4.2),'Generated JSON/code',(0,-.2))
arrow((2,3.8),(2,2),'Write candidate\n(source file)',(-.15,0))
arrow((3.8,1.3),(7,1.3),'Source + tensors',(0,.2))
arrow((8.8,2),(3.8,3.9),'Feedback: correctness + timing',(0,-.15),'--')
ax.text(5.5,5.75,'Actual six-turn Agent loop on one RTX host',ha='center',fontsize=15,weight='bold')
ax.text(5.5,.05,'Solid arrows: data dependencies. Dashed: tool feedback. Controller waits for each stage.\nModel inference and evaluator kernels use the GPU sequentially. Archive transfer to Mac is outside loop timing.',ha='center',fontsize=10)
fig.savefig(ROOT/'results/resource-map.svg');fig.savefig(ROOT/'results/resource-map.png',dpi=160)
fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
rows=r['rows'];x=[q['turn'] for q in rows];model=[q['model_generation_wall_s'] for q in rows];tool=[q['tool_subprocess_wall_s'] for q in rows]
ax.bar(x,model,label='Model generation wall time',color='#4385a9');ax.bar(x,tool,bottom=model,label='Evaluator subprocess wall time',color='#d39449')
ax.set(xlabel='Tool turn',ylabel='Seconds',title='Measured sequential stage durations (not an absolute timeline)');ax.set_ylim(0,8);ax.legend();ax.grid(axis='y',alpha=.2)
fig.savefig(ROOT/'results/stages.svg');fig.savefig(ROOT/'results/stages.png',dpi=160)
