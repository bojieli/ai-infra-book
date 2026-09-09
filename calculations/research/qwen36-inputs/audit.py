"""Offline metadata/expected text tensor audit; never opens tensor payloads."""
import json,hashlib,math,collections,struct
from pathlib import Path
P=Path(__file__).resolve().parent
for record in json.loads((P/'source-lock.patch.json').read_text())['sources']:
 raw=(P.parents[1]/record['file']).read_bytes()
 assert len(raw)==record['bytes'] and hashlib.sha256(raw).hexdigest()==record['sha256']
http=json.loads((P/'http-evidence.json').read_text())
index=json.loads((P/'model/model.safetensors.index.json').read_text())
c=json.loads((P/'model/config.json').read_text());t=c['text_config'];seen={};totals=collections.Counter();dtypes=collections.Counter()
for shard in sorted(set(index['weight_map'].values())):
 raw_header=(P/'headers'/f'{shard}.json').read_bytes()
 assert struct.unpack('<Q',(P/'prefixes'/f'{shard}.length').read_bytes())[0]==len(raw_header)
 h=json.loads(raw_header);offsets=[]
 for name,v in h.items():
  if name=='__metadata__':continue
  assert name not in seen and index['weight_map'][name]==shard
  size=v['data_offsets'][1]-v['data_offsets'][0]
  assert size==math.prod(v['shape'])*{'BF16':2,'F32':4}[v['dtype']]
  offsets.append(v['data_offsets']);seen[name]=v;dtypes[v['dtype']]+=1
  owner='mtp' if name.startswith('mtp.') else 'vision' if name.startswith('model.visual.') else 'text'
  totals[owner+'_bytes']+=size;totals[owner+'_parameters']+=math.prod(v['shape'])
 end=0
 for start,stop in sorted(offsets):assert start==end;end=stop
 evidence=next(r for r in http if r['file']==f'headers/{shard}.json')
 assert end+8+len(raw_header)==int(evidence['content_range'].split('/')[-1])
assert set(seen)==set(index['weight_map'])
assert sum(v for k,v in totals.items() if k.endswith('_bytes'))==index['metadata']['total_size']
H=t['hidden_size'];V=t['vocab_size'];E=t['num_experts'];F=t['moe_intermediate_size'];S=t['shared_expert_intermediate_size'];expected={}
def add(n,shape):expected[n]=shape
add('model.language_model.embed_tokens.weight',[V,H]);add('model.language_model.norm.weight',[H]);add('lm_head.weight',[V,H])
for i,kind in enumerate(t['layer_types']):
 p=f'model.language_model.layers.{i}.'
 for n in ['input_layernorm','post_attention_layernorm']:add(p+n+'.weight',[H])
 add(p+'mlp.gate.weight',[E,H]);add(p+'mlp.experts.gate_up_proj',[E,2*F,H]);add(p+'mlp.experts.down_proj',[E,H,F])
 for n,sh in [('gate_proj',[S,H]),('up_proj',[S,H]),('down_proj',[H,S])]:add(p+'mlp.shared_expert.'+n+'.weight',sh)
 add(p+'mlp.shared_expert_gate.weight',[1,H])
 if kind=='linear_attention':
  K=t['linear_num_key_heads']*t['linear_key_head_dim'];W=t['linear_num_value_heads']*t['linear_value_head_dim'];heads=t['linear_num_value_heads']
  for n,sh in [('in_proj_qkv.weight',[2*K+W,H]),('in_proj_z.weight',[W,H]),('in_proj_b.weight',[heads,H]),('in_proj_a.weight',[heads,H]),('out_proj.weight',[H,W]),('conv1d.weight',[2*K+W,1,t['linear_conv_kernel_dim']]),('A_log',[heads]),('dt_bias',[heads]),('norm.weight',[t['linear_value_head_dim']])]:add(p+'linear_attn.'+n,sh)
 else:
  D=t['head_dim'];Q=t['num_attention_heads'];KV=t['num_key_value_heads']
  for n,sh in [('q_proj.weight',[2*Q*D,H]),('k_proj.weight',[KV*D,H]),('v_proj.weight',[KV*D,H]),('o_proj.weight',[H,Q*D]),('q_norm.weight',[D]),('k_norm.weight',[D])]:add(p+'self_attn.'+n,sh)
missing=[n for n in expected if n not in seen];conflicts=[dict(tensor=n,expected=sh,checkpoint=seen[n]['shape']) for n,sh in expected.items() if n in seen and sh!=seen[n]['shape']]
unexpected=[n for n in seen if (n.startswith('model.language_model.') or n=='lm_head.weight') and n not in expected]
result=dict(verified_shards=len(set(index['weight_map'].values())),verified_tensors=len(seen),total_payload_bytes=int(index['metadata']['total_size']),groups=dict(totals),storage_dtypes=dict(dtypes),expected_base_text_tensors=len(expected),missing_expected=missing,shape_conflicts=conflicts,unexpected_base_text=unexpected,base_text_shape_match=not(missing or conflicts or unexpected),layer_counts=dict(collections.Counter(t['layer_types'])),scope='All storage shapes/dtype/offset/index checked; expected config shapes only base text, not vision or MTP; no runtime load or numerical test.')
(P/'header-audit.json').write_text(json.dumps(result,indent=2)+'\n')
(P/'tensor-inventory.json').write_text(json.dumps(seen,indent=2)+'\n')
print(json.dumps(result,indent=2))
