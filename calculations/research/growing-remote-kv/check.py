"""Independent explicit-position/epoch audit of the C36 candidate."""
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('growing_candidate',HERE/'calculate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
EXPECTED={'qwen3-8b':(147456,0,36*4*32*128),
          'qwen3.6-35b-a3b':(20480,64880640,10*4*16*256)}
traces=[]
count=0
for model,(single_unit,fixed,pair_flops) in EXPECTED.items():
 for placement in ('remote_all','remote_prefix_local_tail'):
  for copies in (1,2,3):
   for batch,steps in ((1,0),(1,1),(1,4),(2,0),(2,1),(2,4)):
    prompt=3;bw=17000000000;startup=7000;unit=batch*single_unit
    result=m.calculate(model=model,batch=batch,prompt=prompt,steps=steps,copies=copies,
                       placement=placement,bandwidth_bytes_per_second=bw,startup_ns=startup)
    g=result['geometry'];s=result['summary']
    assert g['kv_bytes_per_position']==single_unit
    assert g['local_recurrent_bytes_per_request']+g['local_convolution_bytes_per_request']==fixed
    assert g['qk_pv_flops_per_position_pair']==pair_flops
    assert len(result['steps'])==steps
    origin={(b,p) for b in range(batch) for p in range(prompt)}
    remote=[set() for _ in range(copies)]
    local=set();cursor=F(0);initial_network=0;remote_read=0;local_read=0;append=0
    epoch_trace=[]
    def transfer(size):
      return F(startup,10**9)+F(size,bw) if size else F(0)
    for i,message in enumerate(result['initial_copy_messages']):
      assert message=={'replica':i,'bytes':len(origin)*single_unit}
      remote[i]|=origin
      initial_network+=len(origin)*single_unit
      cursor+=transfer(message['bytes'])
    assert len(remote)==len(result['initial_copy_messages'])==copies
    assert F(s['initial_copy_seconds_exact'])==cursor
    initial_time=cursor
    for index,row in enumerate(result['steps']):
      prior=prompt+index
      old={(b,p) for b in range(batch) for p in range(prior)}
      current={(b,prior) for b in range(batch)}
      expected_remote=old if placement=='remote_all' else origin
      expected_local=old-expected_remote
      # All replicas have the committed epoch before any is selected to read.
      assert all(replica==expected_remote for replica in remote)
      assert local==expected_local
      assert row['required_remote_epoch']==(prior if placement=='remote_all' else prompt)
      assert row['selected_read_replica']==0
      assert current.isdisjoint(remote[row['selected_read_replica']])
      assert row['remote_prior_read_bytes']==len(expected_remote)*single_unit
      assert row['local_prior_read_bytes']==len(local)*single_unit
      assert row['current_kv_operand_bytes']==len(current)*single_unit
      assert row['full_attention_qk_pv_flops']==batch*(prior+1)*pair_flops
      assert F(row['read_start_seconds_exact'])==cursor
      cursor+=transfer(len(expected_remote)*single_unit)
      assert F(row['read_finish_seconds_exact'])==cursor
      remote_read+=len(expected_remote)*single_unit;local_read+=len(local)*single_unit
      if placement=='remote_all':
       assert len(row['replica_writes'])==copies
       for i,write in enumerate(row['replica_writes']):
        assert write['replica']==i and write['position']==prior
        assert write['bytes']==len(current)*single_unit
        assert F(write['start_seconds_exact'])==cursor
        assert not current & remote[i]
        cursor+=transfer(write['bytes']);remote[i]|=current;append+=write['bytes']
        assert F(write['commit_seconds_exact'])==cursor
      else:
       assert row['replica_writes']==[]
       local|=current
      assert F(row['all_replica_commit_seconds_exact'])==cursor
      assert row['remote_lengths_after']==[len(r)//batch for r in remote]
      assert row['local_tail_bytes_after']==len(local)*single_unit
      assert row['logical_full_history_bytes_after']==len(old|current)*single_unit
      union=set().union(*remote,local)
      assert union==old|current
      epoch_trace.append(dict(step=index,replicas=[sorted([list(i) for i in r]) for r in remote],
                              local_tail=sorted([list(i) for i in local]),barrier=str(cursor)))
    final=set().union(*remote,local)
    assert len(final)==batch*(prompt+steps)
    assert s['initial_copy_network_bytes']==initial_network
    assert s['remote_prior_read_bytes']==remote_read
    assert s['local_prior_read_bytes']==local_read
    assert s['prior_history_logical_read_bytes']==remote_read+local_read
    assert s['current_kv_operand_bytes']==steps*unit
    assert s['append_replica_network_bytes']==append
    assert s['total_network_bytes']==initial_network+remote_read+append
    assert s['remote_final_bytes_per_replica']==len(remote[0])*single_unit
    assert s['remote_physical_final_bytes']==sum(len(r) for r in remote)*single_unit
    assert s['local_tail_final_bytes']==len(local)*single_unit
    assert s['local_fixed_state_bytes']==batch*fixed
    assert s['local_current_append_buffer_bytes']==(unit if steps else 0)
    assert s['final_unique_history_bytes']==len(final)*single_unit
    assert F(s['communication_skeleton_seconds_exact'])==cursor
    assert F(s['token_communication_seconds_exact'])==cursor-initial_time
    assert s['actual_decode_seconds'] is None and s['actual_task_feasible'] is None
    traces.append(dict(model=model,placement=placement,copies=copies,batch=batch,steps=steps,
                       initial_identities=sorted([list(i) for i in origin]),epochs=epoch_trace,
                       network_bytes=s['total_network_bytes'],communication_seconds=str(cursor)))
    count+=1
# Budget is specifically the final newly-created local attention tail; fixed
# states/current-buffer/source ownership are separate, not silently covered.
boundary_checks=0
for model,(unit,fixed,_) in EXPECTED.items():
 for copies in (1,3):
  need=2*unit*4
  for budget in (need-1,need,need+1):
   r=m.calculate(model=model,batch=2,prompt=3,steps=4,copies=copies,
                 placement='remote_prefix_local_tail',local_tail_budget_bytes=budget)
   assert r['summary']['local_tail_budget_fits']==(budget>=need)
   assert r['summary']['local_fixed_state_bytes']==2*fixed
   boundary_checks+=1
  r=m.calculate(model=model,prompt=1,steps=0,copies=copies,
                placement='remote_prefix_local_tail',local_tail_budget_bytes=0)
  assert r['summary']['local_tail_budget_fits'] and r['summary']['token_communication_seconds_exact']=='0'
  boundary_checks+=1
invalid=[{'steps':-1},{'steps':True},{'prompt':0},{'copies':0},{'copies':4},
         {'bandwidth_bytes_per_second':0},{'startup_ns':-1},{'local_tail_budget_bytes':-1},
         {'placement':'random'},{'model':'qwen3.6-unknown'}]
for args in invalid:
 try:m.calculate(**args)
 except ValueError:pass
 else:raise AssertionError(args)
for model in EXPECTED:
 maximum=m.geometry(model)['max_positions']
 try:m.calculate(model=model,prompt=maximum,steps=1)
 except ValueError:pass
 else:raise AssertionError('Context overflow accepted')
 # Boundary accepted without enumerating a large position set.
 r=m.calculate(model=model,prompt=maximum,steps=0,startup_ns=0)
 assert r['summary']['final_unique_history_bytes']==maximum*EXPECTED[model][0]
(HERE/'check-result.json').write_text(json.dumps(dict(status='passed',position_scenarios=count,
    tail_boundary_checks=boundary_checks,invalid_cases=len(invalid)+2,traces=traces),indent=2)+'\n')
print(f'PASS: {count} explicit position/epoch cases; {boundary_checks} tail boundaries;12 invalid cases;2 max-context zero-step cases.')
