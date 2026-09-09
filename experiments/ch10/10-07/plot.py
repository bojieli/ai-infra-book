"""Actual second-checkpoint timing, normal versus injected interruption."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).parent/'results'
outcomes=json.loads((root/'outcomes.json').read_text())
fig,axes=plt.subplots(2,1,figsize=(9,5.8),layout='constrained')
colors=['#356aa0','#5a9e65','#d3983b']
for ax,case in zip(axes,['normal','fault']):
    events=[json.loads(x) for x in (root/case/'events.jsonl').read_text().splitlines()]
    t={e['event']:e['monotonic_s'] for e in events if e.get('checkpoint')=='checkpoint-2'}
    base=t['api_call'];ms=lambda v:1000*(v-base)
    for y,(start,end,label,color) in enumerate([
        ('stage_start','stage_complete','CPU staging',colors[0]),
        ('write_start','data_write_complete','Data write + fsync',colors[1]),
        ('api_return','training_complete','20 training steps',colors[2])]):
        ax.barh(y,ms(t[end])-ms(t[start]),left=ms(t[start]),height=.5,color=color)
    ax.axvline(ms(t['api_return']),ls='--',color='#333333',label='API returned')
    if case=='normal':
        ax.axvline(ms(t['metadata_commit_complete']),color='#3a843e',label='Metadata committed')
    else:
        end=ms(outcomes['fault']['sigkill_monotonic_s'])
        ax.barh(1,end-ms(t['metadata_commit_enter']),left=ms(t['metadata_commit_enter']),height=.5,
                facecolor='none',edgecolor='#bb4444',hatch='///',label='Injected gate; not I/O')
        ax.axvline(end,color='#aa3333',label='SIGKILL')
    ax.set_yticks([0,1,2],['CPU staging','Data write','Training'])
    ax.set_xlabel('ms from async_save call');ax.set_title(case.capitalize())
    ax.legend(fontsize=8,loc='upper right');ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
fig.suptitle('PyTorch DCP async save: API return and recoverability\nSingle CPU process; actual timestamps; controlled metadata-commit failure',fontsize=11)
for suffix in ['svg','png']:fig.savefig(root/f'async-timeline.{suffix}',dpi=160)
