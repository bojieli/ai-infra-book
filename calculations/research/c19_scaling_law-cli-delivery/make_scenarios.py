"""Generate explicitly synthetic controlled records, no downloaded experiments."""
import json
from pathlib import Path
from copy import deepcopy
s=dict(model_family='dense',data_kind='synthetic_teaching',control_id='fixed-teaching-v1',
       control_description='Identical hypothetical data distribution, tokenizer, optimizer and validation protocol; no models trained.',
       N0=1e9,D0=1e10,training_flops_per_parameter_token=6,
       exponent_grid=[[a,b] for a in (.4,.5,.6) for b in (.4,.5,.6)],
       budgets_flops=[6e19,6e20,6e21,6e22],candidate_sizes=[1e9,2e9,4e9,8e9,16e9],target_loss=1.8,
       demand=dict(calls_per_day=1000000,lifetime_days=365,input_tokens=512,output_tokens=128),
       costs=dict(train_per_flop=1e-18,prefill_per_flop=2e-18,decode_per_flop=5e-18,setup_cost=0,
                  prefill_flops_per_parameter_token=2,decode_flops_per_parameter_token=2),
       call_counts=[0,1000000,10000000,100000000,365000000,1000000000],
       extrapolation_points=[dict(N=1e10,D=1e12),dict(N=1e12,D=1e14)],
       sources=json.loads(Path('sources/manifest.json').read_text()),
       generator=dict(E=1,A=1,B=1,alpha=.5,beta=.5,noise='none; exact recovery control'))
s['allocation_policies']=[dict(id='Kaplan-inspired',N_compute_exponent=.73,source='https://arxiv.org/html/2001.08361v1#S6.SS1'),dict(id='Chinchilla-equal-scaling',N_compute_exponent=.5,source='https://arxiv.org/abs/2203.15556v1')]
records=[]
for N in (1e9,2e9,4e9):
 for D in (1e10,2e10,4e10):
  records.append(dict(id=f'fit-{len(records)}',N=N,D=D,loss=1+(N/1e9)**-.5+(D/1e10)**-.5,C_flops=6*N*D,split='fit',control_id=s['control_id'],origin='synthetic equation'))
for N,D in ((3e9,3e10),(8e9,8e10),(16e9,16e10)):
 records.append(dict(id=f'holdout-{len(records)}',N=N,D=D,loss=1+(N/1e9)**-.5+(D/1e10)**-.5,C_flops=6*N*D,split='holdout',control_id=s['control_id'],origin='synthetic equation'))
s['records']=records
Path('scenarios/teaching.json').write_text(json.dumps(s,indent=2)+'\n')
noisy=deepcopy(s); noisy['generator']['noise']='deterministic residual pattern, no statistical uncertainty claim'
for i,r in enumerate(noisy['records']): r['loss']+=(-1,0,1)[i%3]*.002
Path('scenarios/perturbed.json').write_text(json.dumps(noisy,indent=2)+'\n')
zero=deepcopy(s); zero['demand']['calls_per_day']=0
Path('scenarios/zero-demand.json').write_text(json.dumps(zero,indent=2)+'\n')
