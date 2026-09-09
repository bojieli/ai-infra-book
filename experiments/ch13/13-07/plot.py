import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',default='prediction-current');a=p.parse_args();assert not (a.output=='prediction-at-freeze' and (B/'prediction-at-freeze.png').exists()),'Frozen view is immutable';f=json.loads((B/'prediction.json').read_text());obs=sorted((B/'observations').glob('*.json'));o=json.loads(obs[-1].read_text()) if obs else None
fig,axes=plt.subplots(1,2,figsize=(10.5,5.1),gridspec_kw={'width_ratios':[1,1.5]});counter=f['strongest_known_counterexample'];axes[0].scatter([counter['ratio']],[0],color='#A75039',s=70);axes[0].annotate(f"{counter['ratio']:.3f}: prefix preservation was slower",(counter['ratio'],0),xytext=(.65,.35),fontsize=10);axes[0].set_yticks([0],['Known K96\nsequence task']);axes[0].set_ylim(-.5,.65);axes[0].set_title('Already known before the forecast')
lo,hi=f['interval'];axes[1].plot([lo,hi],[1,1],color='#33798A',linewidth=9,solid_capstyle='butt');axes[1].text((lo+hi)/2,1.15,f'Frozen interval [{lo:.2f}, {hi:.2f}]',ha='center',fontsize=10)
if o:
 axes[1].scatter([o['metric']],[0],s=70,color='#447C58' if o['verdict']=='supported_in_scope' else '#A75039');axes[1].text(o['metric']+.025,0,f"Observed {o['metric']:.3f}",va='center',fontsize=10)
else:axes[1].text(.77,0,'Unobserved (null)',va='center',fontsize=11,color='#777777')
axes[1].set_yticks([1,0],['Initial prediction','New K192 result']);axes[1].set_ylim(-.45,1.55);axes[1].set_title('K192: actual paired-trial review' if o else 'Five future paired trials per task')
for ax in axes:ax.set_xlim(.55,1.3);ax.axvline(1,color='#888888',linestyle='--',linewidth=1);ax.set_xlabel('Preserve / restart completion-window ratio');ax.grid(axis='x',alpha=.18);ax.spines[['top','right']].set_visible(False)
fig.suptitle('A dated, falsifiable prediction: larger retained token prefix',fontsize=14);fig.text(.5,.06,f"Frozen: {f['created_utc'][:19]} UTC   |   Deadline: 2026-09-16 23:59:59 Singapore",ha='center',fontsize=9);fig.text(.5,.015,'65% subjective judgment, not a confidence interval. Exact quality and token equality are a separate joint gate.',ha='center',fontsize=9);
if o:fig.text(.5,.105,f"Verdict: {o['verdict']}   |   Quality / token gate: {o['restored_tokens_equal']}/20 exact",ha='center',fontsize=10,color='#A75039' if o['verdict']=='refuted_in_scope' else '#447C58')
fig.tight_layout(rect=[0,.18,1,.92]);fig.savefig(B/f'{a.output}.png',dpi=170);fig.savefig(B/f'{a.output}.svg');plt.close(fig)
