"""Verify final frozen deltas: cache alias/copy, conv slots, eager mask/attention."""
import hashlib,json,sys,types,importlib.util
from pathlib import Path
O=Path(__file__).resolve().parent
helper=types.ModuleType('reference_steps');exec(compile((O/'reference_steps.final.py').read_text(),'reference_steps.final.py','exec'),helper.__dict__);sys.modules['reference_steps']=helper
spec=importlib.util.spec_from_file_location('qwen35_final',O/'qwen35_forward.final.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
results=[]
for B,T,S,R in [(1,1,0,True),(2,2,0,True),(1,8,0,True),(1,1,0,False),(1,2,0,False),(1,8,0,False),(2,1,1,False),(1,3,7,False),(1,65,0,False),(1,1,7,True)]:
 r=mod.calculate(batch=B,tokens=T,history=S,output_head='none',record_past=R);ops=r['operators'];steps={x['name']:x for x in r['reference_execution_steps']['steps']}
 mat=lambda pred:sum(x['matrix_flops']*x['repeats'] for x in ops if pred(x['name']))
 # Full eager rectangle equals valid subtotal plus explicit masked slots.
 full=mat(lambda n:n in ('full.QK','full.PV','reference.full.eager_masked_matrix_slots'))
 assert full==15*4*32*256*B*T*(S+T)
 base=next(x for x in ops if x['name']=='full.softmax');supp=steps['full.eager_additional_softmax_and_mask']
 assert base['scalar_flops']+supp['scalar_flops']==5*32*B*T*(S+T)-32*B*T
 assert base['special_ops']['exp']+supp['special_ops']['exp']==32*B*T*(S+T)
 # Mask: one causal plane before batch expand, bool->BF16 across full B plane.
 assert steps['mask.causal_compare_before_batch_expand']['integer_operations']==T*(S+T)
 assert steps['mask.bool_to_BF16_where']['tensor_output_bytes']==2*B*T*(S+T)
 update=S>0 and T==1 and not R
 if not (R and S):
  L=T if R else (4+T if S else max(4,T));outputs=L-3 if update else L+3;kept=T if update else L
  conv=mat(lambda n:n in ('linear.causal_conv_valid','reference.conv.additional_padded_and_discarded_products'))
  assert conv==45*2*B*12288*outputs*4
  silu=sum(x['special_ops'].get('sigmoid',0)*x['repeats'] for x in ops if x['name'] in ('linear.conv_silu','reference.conv.extra_silu_before_final_crop'))
  assert silu==45*B*12288*kept
  if R:
   assert 'conv.cache_copy_last4' not in steps
   assert steps['conv.cache_concat_or_initial_pad']['tensor_input_bytes']==0
   assert steps['conv.cache_concat_or_initial_pad']['tensor_output_bytes']==0
   assert steps['conv.cache_initial_zero']['tensor_output_bytes']==2*B*12288*4
   assert r['state']['record_past_retained_conv_bytes']==45*2*B*12288*T
  else:assert steps['conv.cache_copy_last4']['tensor_output_bytes']==2*B*12288*4
 else:
  assert r['reference_execution_steps']['conv']['record_past_shape_known'] is False
  assert r['state']['record_past_retained_conv_bytes'] is None
 assert r['execution']['linear_path']['kind']==('reference_recurrent' if S>0 and T==1 else 'reference_chunk_nonexport')
 assert r['summary']['full_forward_exact'] is False
 results.append({'batch':B,'tokens':T,'history':S,'record_past':R,'eager_rectangle_and_mask':'passed','conv_slots_and_silu':'bounded_unknown_existing_recorded_length' if R and S else 'passed','record_past_copy_fix':'passed' if R and not S else 'not_applicable'})
# New source lock must be same fixed model commit, actual hash/length match.
lock=json.loads((O/'reference_sources/sources.lock.json').read_text())
for row in lock:
 data=(O/'reference_sources'/row['file']).read_bytes();assert len(data)==row['bytes'];assert hashlib.sha256(data).hexdigest()==row['sha256'];assert row['revision']=='cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55'
# Actual code branch confirmation: eager cannot skip causal mask; reference cache record branch aliases full input.
mask=(O/'reference_sources/masking_utils.py').read_text();assert 'allow_is_causal_skip=False' in mask[mask.index('def eager_mask'):mask.index('def flash_attention_mask')]
report={'cases':results,'case_count':len(results),'new_source_hash_bytes_revision':'passed','f01_last4_copy_fixed':True,'f02_fresh_recorded_input_false_pad_copy_fixed':True,'final_snapshot_hashes':{n:hashlib.sha256((O/n).read_bytes()).hexdigest() for n in ['qwen35_forward.final.py','reference_steps.final.py','reference_sources/masking_utils.py']},'scope':'Final delta verification only; earlier36 numeric core cases remain separately recorded. No measured HBM or full backend instruction count.'}
(O/'final-results.json').write_text(json.dumps(report,indent=2)+'\n');print('final cases',len(results),'source SHA/revision passed; both record_past fixes verified')
