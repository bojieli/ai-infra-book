import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).absolute().parent;x=json.loads((B/'analysis.json').read_text());rows=x['results'][:4]
fig,axs=plt.subplots(1,2,figsize=(11,4))
colors=['#0072B2','#D55E00','#CC79A7','#009E73']
for r,color in zip(rows,colors):
 frames=r['frames'];axs[0].step([v['available_ns']/1e6 for v in frames],[(v['frame']+1)*.02 for v in frames],where='post',label=r['name'],color=color)
axs[0].set(xlabel='Time since request started (ms)',ylabel='Complete PCM frames available (audio seconds)',title='Client read-completion boundaries');axs[0].legend(fontsize=8);axs[0].grid(alpha=.2)
for i,r in enumerate(rows):
 axs[1].bar(i-.16,r['headers_ms'],.3,color='#999999',label='HTTP headers' if i==0 else None)
 axs[1].bar(i+.16,r['first_20ms_frame_ms'],.3,color='#0072B2',label='First complete 20 ms PCM' if i==0 else None)
axs[1].set_xticks(range(4),['0 stream','1 whole','2 whole','3 stream']);axs[1].set(ylabel='Time since request started (ms)',title='Headers are not audio');axs[1].legend(fontsize=8);axs[1].grid(axis='y',alpha=.2)
fig.suptitle('Fish Speech 1.5, RTX loopback; distinct sampled audio, no DAC playback')
fig.tight_layout();fig.savefig(B/'audio-arrivals.png',dpi=150);fig.savefig(B/'audio-arrivals.svg')
