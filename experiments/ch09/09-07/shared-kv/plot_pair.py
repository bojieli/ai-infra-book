"""Plot actual per-request observations; no network model or estimated points."""
import argparse
import json
from pathlib import Path
import statistics
import matplotlib.pyplot as plt

p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();data=json.loads(a.analysis.read_text());assert not data['smoke']
paths=['baseline','producer','retrieve','resident','miss']
labels=['Recompute','Producer','Fetch candidate','Resident','Pool miss']
fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
for column,(limit,title) in enumerate([(4096,'~2K input tokens'),(12288,'~8K input tokens')]):
    selected=[r for r in data['rows'] if (r['input_tokens']<4096)==(column==0)
              and not (r['path']=='baseline' and r['case_id'].endswith('-miss'))]
    for row,(key,scale,ylabel) in enumerate([('observed_ttft_s',1000,'Observed TTFT (ms)'),('scheduled_tokens',1,'Actually scheduled tokens')]):
        ax=axes[row,column]
        for x,path in enumerate(paths):
            values=[r[key]*scale for r in selected if r['path']==path]
            assert len(values)==6
            offsets=[(i-(len(values)-1)/2)*.045 for i in range(len(values))]
            ax.scatter([x+offset for offset in offsets],values,s=24,alpha=.75,color=f'C{x}')
            ax.plot([x-.22,x+.22],[statistics.median(values)]*2,color='black',lw=2)
        ax.set_xticks(range(5),labels,rotation=18);ax.set_ylabel(ylabel)
        ax.grid(axis='y',alpha=.2);ax.set_title(title if row==0 else 'Scheduler work, including decode')
fig.suptitle('Two engines sharing one CPU KV pool on one GPU\nSix observations per condition; bars are medians, not confidence intervals',fontsize=12)
a.out.parent.mkdir(parents=True,exist_ok=True)
for ext in ['png','svg']:fig.savefig(a.out.with_suffix('.'+ext),dpi=160)
