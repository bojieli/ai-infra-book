"""Plot actual author histories only; no interpolation or digitized source figures."""
import argparse,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parent
COLORS={'off':'#b95c39','on':'#247797'}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--analysis',type=Path,default=B/'analysis/summary.json');parser.add_argument('--output',type=Path,default=B/'plots');a=parser.parse_args();s=json.loads(a.analysis.read_text());a.output.mkdir(parents=True,exist_ok=True)
 for name,expected in s['source_sha256'].items():assert hashlib.sha256((B/name).read_bytes()).hexdigest()==expected
 plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
 def save(fig,name):
  for ext in ['png','svg']:fig.savefig(a.output/(name+'.'+ext),dpi=170,bbox_inches='tight')
  plt.close(fig)
 fig,axes=plt.subplots(4,2,figsize=(12,12),sharex=True,layout='constrained')
 for row,pair in enumerate(s['pairs']):
  for col,(metric,label) in enumerate([('train/token_mult_prob_error','Token multiplier − 1 (log scale)'),('train/js_divergence_error','Logged token-based JS error')]):
   ax=axes[row,col]
   for mode,r in pair['runs'].items():
    values=[value-1 for value in r['series'][metric]] if col==0 else r['series'][metric]
    assert all(value>0 for value in values)
    ax.plot(r['steps'],values,lw=1,color=COLORS[mode],label='R3 '+mode,alpha=.9)
   ax.set_title(pair['label']);ax.set_ylabel(label);ax.grid(alpha=.2)
   ax.set_yscale('log')
   if row==3:ax.set_xlabel('Author training step (1–100)')
 axes[0,0].legend();fig.suptitle('Author Qwen3-30B-A3B R3 histories: logprob mismatch\nFour settings, one shared seed (42); original logged points, no smoothing',fontsize=13)
 save(fig,'logprob-mismatch')
 fig,axes=plt.subplots(2,2,figsize=(12,7),sharex=True,sharey=True,layout='constrained')
 for ax,pair in zip(axes.flat,s['pairs']):
  for mode,r in pair['runs'].items():ax.plot(r['steps'],r['series']['train/reward'],lw=1,color=COLORS[mode],label='R3 '+mode,alpha=.85)
  ax.set_title(pair['label']);ax.set_xlabel('Author training step (1–100)');ax.set_ylabel('Logged mean training reward');ax.grid(alpha=.2)
 axes[0,0].legend();fig.suptitle('Author training-reward curves: no consistent reward improvement claimed\nFour paired settings share seed 42; these are not independent seed repeats',fontsize=13)
 save(fig,'training-reward')
 fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
 stage=[('timing/train/generation','Rollout generation'),('timing/train/policy_and_reference_logprobs','Policy + reference logprobs'),('timing/train/policy_training','Policy training'),('timing/train/total_step_time','Total training step')]
 labels=['BF16\n2048','FP8 rollout\n2048','BF16 cache+chunk\n2048','BF16\n8192']
 for ax,(key,label) in zip(axes.flat,stage):
  for mode,shift in [('off',-.18),('on',.18)]:
   stats=[p['runs'][mode]['statistics'][key] for p in s['pairs']];x=[i+shift for i in range(4)];y=[r['median'] for r in stats]
   ax.errorbar(x,y,yerr=[[r['median']-r['q25'] for r in stats],[r['q75']-r['median'] for r in stats]],fmt='o',capsize=4,color=COLORS[mode],label='R3 '+mode)
  ax.set_xticks(range(4),labels);ax.set_ylabel('Seconds: median and interquartile range');ax.set_title(label);ax.grid(axis='y',alpha=.2)
 axes[0,0].legend();fig.suptitle('Author stage timers across 100 training steps\nIQR is step-to-step dispersion, not a confidence interval; stage medians are not additive',fontsize=13)
 save(fig,'stage-timing')
 files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.output.iterdir() if p.suffix in ['.svg','.png']}
 (a.output/'provenance.json').write_text(json.dumps(dict(analysis_sha256=hashlib.sha256(a.analysis.read_bytes()).hexdigest(),plotter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),files=files,source='Actual author-exported history JSON; no digitization or invented data'),indent=2)+'\n')
if __name__=='__main__':main()
