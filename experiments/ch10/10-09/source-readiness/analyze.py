"""Offline analysis of author-exported W&B histories; stdlib only, no model calls."""
import argparse,hashlib,json,math,statistics
from pathlib import Path
B=Path(__file__).resolve().parent
METRICS=['train/token_mult_prob_error','train/js_divergence_error','train/reward','train/loss','timing/train/generation','timing/train/policy_and_reference_logprobs','timing/train/policy_training','timing/train/total_step_time']
LABELS={1:'BF16 / 2048 / cache off',2:'FP8 rollout / 2048 / cache off',6:'BF16 / 2048 / cache + chunk on',7:'BF16 / 8192 / cache off'}
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def finite(x):return type(x) in (int,float) and math.isfinite(x)
def flatten(x,p=''):
 if not isinstance(x,dict):return {p:x}
 out={}
 for k,v in x.items():out.update(flatten(v,p+'.'+k if p else k))
 return out
def quantile(x,p):
 x=sorted(x);f=(len(x)-1)*p;i=int(f);return x[i]+(x[min(i+1,len(x)-1)]-x[i])*(f-i)
def stats(values):return dict(n=len(values),mean=statistics.mean(values),median=statistics.median(values),min=min(values),max=max(values),q25=quantile(values,.25),q75=quantile(values,.75),first=values[0],last=values[-1],last10_mean=statistics.mean(values[-10:]))
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=B/'analysis');a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 nodes={e['node']['name']:e['node'] for e in load(B/'wandb/runs.json')['data']['project']['runs']['edges']};pairs=[];sources={};total_raw=0
 for v in [1,2,6,7]:
  pair=dict(id=f'gate3-v{v}',label=LABELS[v],runs={})
  configs={}
  for mode in ['off','on']:
   name=next(n for n in nodes if n.startswith(f'gate3-v{v}-r3{mode}-'));path=B/'wandb/histories'/(name+'.json');response=load(path);assert not response.get('errors');run=response['data']['project']['run'];assert run['state']=='finished'
   history=[json.loads(s) for s in run['history']];assert [x['_step'] for x in history]==list(range(101));total_raw+=len(history)
   assert all(history[0].get(k) is None for k in METRICS),'setup row must not become zero-valued training point'
   train=history[1:];assert all(finite(x.get(k)) for x in train for k in METRICS)
   config={k:v['value'] for k,v in json.loads(nodes[name]['config']).items()};configs[mode]=config
   assert config['grpo']['seed']==42 and config['policy']['router_replay']['enabled']==(mode=='on')
   assert config['cluster']['num_nodes']==8 and config['cluster']['gpus_per_node']==8
   assert 'ad44e777bcd18fa416d9da3bd8f70d33ebb85d39' in config['policy']['model_name']
   gen=config['policy']['generation'];assert gen['max_new_tokens']==(8192 if v==7 else 2048)
   assert gen['vllm_cfg']['precision']==('fp8' if v==2 else 'bfloat16')
   assert gen['vllm_cfg']['enable_prefix_caching']==(v==6) and gen['vllm_kwargs']['enable_chunked_prefill']==(v==6)
   assert config['policy']['sequence_packing']['enabled'] is True
   pair['runs'][mode]=dict(run_id=name,public_url=f'https://wandb.ai/nvidia-nemo-fw-public/R3-Effectiveness-0609/runs/{name}',state=run['state'],history_rows=101,training_steps=100,seed=42,series={k:[x[k] for x in train] for k in METRICS},steps=[x['_step'] for x in train],statistics={k:stats([x[k] for x in train]) for k in METRICS},setup={k:x for k,x in history[0].items() if x is not None and k.startswith('timing/setup/')},raw_route_trace_files=[e['node']['name'] for e in run['files']['edges'] if 'r3_trace' in e['node']['name'] or 'routed_experts' in e['node']['name']])
   sources[str(path.relative_to(B))]=sha(path)
  x=flatten(configs['off']);y=flatten(configs['on']);diff=[k for k in sorted(x.keys()|y.keys()) if x.get(k)!=y.get(k)];assert set(diff)=={'checkpointing.checkpoint_dir','logger.log_dir','logger.wandb.name','policy.router_replay.enabled'}
  pair['config_differences']=diff;pair['median_on_minus_off']={k:pair['runs']['on']['statistics'][k]['median']-pair['runs']['off']['statistics'][k]['median'] for k in METRICS};pairs.append(pair)
 assert total_raw==808
 for relative in ['wandb/runs.json','wandb/report-spec.json','github/observed-run-commit.json','github/commit.json','historical/nemo_rl/algorithms/loss/loss_functions.py','historical/nemo_rl/algorithms/utils.py','historical/nemo_rl/algorithms/grpo.py','historical/nemo_rl/utils/logger.py','historical/nemo_rl/utils/timer.py']:
  sources[relative]=sha(B/relative)
 report=dict(scope='Author historical NeMo RL Qwen3-30B-A3B R3 comparison; not a local reproduction or raw token-route audit',raw_history_rows=808,setup_rows=8,finite_training_rows=800,pairs=pairs,all_runs_seed=42,independent_seeds=1,source_sha256=sources,analysis_sha256=sha(Path(__file__)),historical_commit=load(B/'github/observed-run-commit.json')['sha'],current_readiness_commit=load(B/'github/commit.json')['sha'],metrics_scope='Logged reduced sampled-token error metrics; no original per-token logprobs or expert tensors available to recompute them; JS error label is not exact full-vocabulary Jensen-Shannon divergence.',timing_scope='Author controller stage timers; medians/IQR describe 100 changing-policy steps, not independent repetitions or confidence intervals; separate stage medians are not additive.')
 (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
 table=['| Setting | R3 | Median token multiplier | Median logged JS error | Mean reward (steps 91–100) | Median total step s |','|---|---|---:|---:|---:|---:|']
 for pair in pairs:
  for mode in ['off','on']:
   s=pair['runs'][mode]['statistics'];table.append(f"| {pair['label']} | {mode} | {s['train/token_mult_prob_error']['median']:.6f} | {s['train/js_divergence_error']['median']:.8f} | {s['train/reward']['last10_mean']:.6f} | {s['timing/train/total_step_time']['median']:.3f} |")
 (a.output/'TABLE.md').write_text('\n'.join(table)+'\n');print('\n'.join(table));print('808 raw rows = 8 setup + 800 training rows; four pairs share seed42')
if __name__=='__main__':main()
