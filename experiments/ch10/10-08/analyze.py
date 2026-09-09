#!/usr/bin/env python3
"""Independent CPU/std-library audit of final main/control; never trains models."""
import argparse,collections,csv,json,math,pathlib,hashlib,struct
ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(pathlib.Path(__file__).resolve().parent));ap.add_argument('--main-dir',default='main');ap.add_argument('--control-dir',default='control');ap.add_argument('--output',default='analysis');a=ap.parse_args();root=pathlib.Path(a.root);out=root/a.output;out.mkdir(exist_ok=True)
def readj(p):return json.loads(p.read_text())
def values(t,key):return t[key]['values']
def flat(x):
 if isinstance(x,list):
  for y in x:yield from flat(y)
 else:yield x
runs={};traces=[]
initial=readj(root/'initial-weight-independent.json')['bf16_sha256']
for mode in ['main','control']:
 d=root/(a.main_dir if mode=='main' else a.control_dir);ex=readj(d/'exit.json');assert ex['returncode']==0 and not ex['remaining_pids']
 exported=readj(d/'tensor-export.json');tf=exported['tensor_files'];events=[]
 for path in sorted((d/'observations').glob('events-*.jsonl')):events.extend(json.loads(l) for l in path.read_text().splitlines())
 events.sort(key=lambda e:e['time_ns']);metrics={e['step']:e['metrics'] for e in events if e['kind']=='trainer_metrics'}
 batches=[]
 for step in [1,2]:
  name=f'advantage-batch-{step}.pt';t=tf[name];rows=exported['decoded_batches'][name];mask=values(t,'response_mask');rew=values(t,'token_level_rewards');adv=values(t,'advantages')
  sums=[sum(row) for row in rew]
  expected_rewards=[float(x['arithmetic_correct']) if mode=='main' else ({'2':1.,'15':-1.,'7':1.,'12':-1.}[x['ground_truth']] if x['response'].strip() else 0.) for x in rows]
  assert sums==expected_rewards,(mode,step,sums,expected_rewards)
  expected=[[0.]*len(row) for row in rew]
  if mode=='main':
   groups=collections.defaultdict(list)
   for i,row in enumerate(rows):groups[row['uid']].append(i)
   for ids in groups.values():
    rr=[sums[i] for i in ids];mean=sum(rr)/len(rr);std=math.sqrt(sum((v-mean)**2 for v in rr)/(len(rr)-1)) if len(rr)>1 else 1.
    for i in ids:expected[i]=[(sums[i]-mean)/(std+1e-6)*m for m in mask[i]]
  else:
   returns=[]
   for rewards,mm in zip(rew,mask):
    running=0.;rr=[0.]*len(rewards)
    for j in reversed(range(len(rewards))):
     new=rewards[j]+running;rr[j]=new*mm[j];running=new*mm[j]+running*(1-mm[j])
    returns.append(rr)
   valid=[v for row,mm in zip(returns,mask) for v,m in zip(row,mm) if m];mean=sum(valid)/len(valid);var=sum((v-mean)**2 for v in valid)/(len(valid)-1)
   expected=[[(v-mean)/math.sqrt(var+1e-8)*m for v,m in zip(row,mm)] for row,mm in zip(returns,mask)]
  error=max(abs(x-y) for x,y in zip(flat(expected),flat(adv)));assert error<2e-6,(mode,step,error)
  for k in ['rollout_log_probs','old_log_probs']:assert k in t and all(math.isfinite(v) for v in flat(values(t,k)))
  diffs=[abs(x-y) for a,b,mm in zip(values(t,'rollout_log_probs'),values(t,'old_log_probs'),mask) for x,y,m in zip(a,b,mm) if m]
  before=next(e for e in events if e['kind']=='optimizer_observation' and e['step']==step and e['phase']=='before');after=next(e for e in events if e['kind']=='optimizer_observation' and e['step']==step and e['phase']=='after')
  bt=tf[before['tensors']];at=tf[after['tensors']];g=values(bt,'gradient_at_indices');nonzero=any(v!=0 for v in g)
  assert int(values(at,'optimizer_step')[0])==step
  assert 'optimizer_exp_avg' in at and 'optimizer_exp_avg_sq' in at
  changed=before['sha256']!=after['sha256'];bf16_changed=before['bf16_sha256']!=after['bf16_sha256']
  sample_delta=max([abs(x-y) for x,y in zip(values(bt,'param_first4096'),values(at,'param_first4096'))]+[0.])
  update_error=0.;decay_only=False
  if mode=='main':
   f32=lambda x:struct.unpack('f',struct.pack('f',x))[0]
   predicted=[f32(v*f32(1-1e-5*.01)) for v in values(bt,'param_first4096')]
   update_error=max(abs(x-y) for x,y in zip(predicted,values(at,'param_first4096')))
   decay_only=not nonzero and update_error==0 and all(x==0 for x in values(at,'optimizer_exp_avg'))
   assert decay_only
  if mode=='control':
   m=values(at,'optimizer_exp_avg_at_indices');v=values(at,'optimizer_exp_avg_sq_at_indices')
   predicted=[old*(1-1e-5*.01)-1e-5*mi/(1-.9**step)/(math.sqrt(vi/(1-.999**step))+1e-8) for old,mi,vi in zip(values(bt,'param_at_indices'),m,v)]
   update_error=max(abs(x-y) for x,y in zip(predicted,values(at,'param_at_indices')))
   assert update_error<5e-8,(mode,step,update_error)
   assert nonzero and changed and bf16_changed
   assert any(v>0 for v in values(at,'optimizer_exp_avg_sq_at_indices'))
   assert values(bt,'indices')==values(at,'indices')
  batches.append(dict(update_equation_max_abs_error=update_error,observed_main_change_is_decay_only=decay_only,step=step,n=len(rows),rewards=sums,arithmetic_correct=sum(x['arithmetic_correct'] for x in rows),advantage_abs_max=max(abs(v) for v in flat(adv)),advantage_reference_max_error=error,gradient_norm=metrics[step]['actor/grad_norm'],nonzero_gradient_sample=nonzero,fp32_weight_changed=changed,bf16_weight_changed=bf16_changed,param_first4096_max_abs_delta=sample_delta,optimizer_state_step=int(values(at,'optimizer_step')[0]),rollout_vs_recomputed_logprob_max_abs_diff=max(diffs),optimizer_before=before['tensors'],optimizer_after=after['tensors']))
 matches=[]
 for version in [0,1,2]:
  sender=next(e for e in events if e['kind']=='sender_embedding' and e['step']==version)
  next_sender=min([e['time_ns'] for e in events if e['kind']=='sender_embedding' and e['time_ns']>sender['time_ns']]+[2**63])
  receiver=next(e for e in events if e['kind']=='receiver_loaded_embedding' and sender['time_ns']<=e['time_ns']<next_sender and e['bf16_sha256']==sender['bf16_sha256'])
  if version==0:assert sender['bf16_sha256']==initial
  else:
   after=next(e for e in events if e['kind']=='optimizer_observation' and e['step']==version and e['phase']=='after');assert sender['bf16_sha256']==after['bf16_sha256']
  consumption=next(e for e in events if e['kind']==('validation_batch' if version==2 else 'advantage_batch') and e['step']==(2 if version==2 else version+1))
  assert receiver['time_ns']<consumption['time_ns']
  matches.append(dict(version=version,bf16_sha256=sender['bf16_sha256'],sender_pid=sender['pid'],receiver_pid=receiver['pid'],sender_time_ns=sender['time_ns'],receiver_time_ns=receiver['time_ns'],subsequent_batch_time_ns=consumption['time_ns']))
 validation=exported['decoded_batches']['validation-batch-2.pt'];assert len(validation)==4
 vt=tf['validation-batch-2.pt'];assert 'rollout_log_probs' in vt
 validation_rewards=[sum(v) for v in values(vt,'rm_scores')]
 expected_validation=[float(x['arithmetic_correct']) if mode=='main' else ({'2':1.,'15':-1.,'7':1.,'12':-1.}[x['ground_truth']] if x['response'].strip() else 0.) for x in validation]
 assert validation_rewards==expected_validation
 samples=[json.loads(l) for l in (d/'resources.jsonl').read_text().splitlines()]
 peakgpu=max(s['gpu_mib'] for s in samples)/1024;peakrss=max(s['rss_bytes'] for s in samples)/2**30;minmem=min(s['mem_available_bytes'] for s in samples)/2**30
 assert peakgpu<=16 and peakrss<=24 and minmem>=16
 assert all(set(cpus)<=set([12,13,14,15]) for s in samples for cpus in s['affinity_by_pid'].values())
 for s in samples:traces.append(dict(run=mode,elapsed_s=s['elapsed_s'],gpu_gib=s['gpu_mib']/1024,rss_gib=s['rss_bytes']/2**30,mem_available_gib=s['mem_available_bytes']/2**30,pids=len(s['pids'])))
 obs_time=sum(e.get('observation_s',0) for e in events)
 runs[mode]=dict(exit=ex,batches=batches,weight_versions=matches,final_validation=validation,validation_rewards=validation_rewards,validation_arithmetic_correct=sum(x['arithmetic_correct'] for x in validation),peak_gpu_gib=peakgpu,peak_rss_gib=peakrss,min_mem_available_gib=minmem,metrics=metrics,total_observation_seconds=obs_time)
summary=dict(status='minimal_real_loop_verified',runs=runs,control_nonzero_updates=sum(b['nonzero_gradient_sample'] and b['fp32_weight_changed'] and b['bf16_weight_changed'] for b in runs['control']['batches']),quality_improvement_claim=False,limitations=['representative full embedding verified, not all model parameters','shared GPU and warm private JIT cache; no isolated performance claim','main zero policy gradient must not be called learning','control signed reward is not arithmetic correctness'])
assert summary['control_nonzero_updates']==2
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (out/'resources.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(traces[0]));w.writeheader();w.writerows(traces)
lines=['# 正式运行独立核验','','| 运行 | 步 | 正确回答 | 奖励 | 最大绝对advantage | 梯度范数 | FP32变化 | BF16变化 |','|---|---:|---:|---|---:|---:|---|---|']
for mode,r in runs.items():
 for b in r['batches']:lines.append(f"| {mode} | {b['step']} | {b['arithmetic_correct']}/{b['n']} | {b['rewards']} | {b['advantage_abs_max']:.6g} | {b['gradient_norm']:.6g} | {b['fp32_weight_changed']} | {b['bf16_weight_changed']} |")
lines+=['','已用独立标准库计算复核每个实际奖励和advantage；原始tensor、代表参数/梯度/optimizer状态、版本0/1/2接收及最后验证batch相互匹配。两个小更新步不构成质量改善证据。']
(out/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'status':summary['status'],'control_nonzero_updates':2,'runs':{m:{'peak_gpu_gib':r['peak_gpu_gib'],'peak_rss_gib':r['peak_rss_gib'],'batches':r['batches']} for m,r in runs.items()}},indent=2))
