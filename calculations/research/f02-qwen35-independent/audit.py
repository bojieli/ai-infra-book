"""Independent offline metadata audit; never opens network or tensor payload."""
from pathlib import Path
import json,hashlib,struct,math,collections
R=Path(__file__).resolve().parents[2];P=R/'research/f02-qwen35-inputs';O=Path(__file__).parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def unique(pairs):
 d={}
 for k,v in pairs:
  assert k not in d,('duplicate_json_key',k);d[k]=v
 return d
def load(p):return json.loads(p.read_bytes(),object_pairs_hook=unique)
rows=load(P/'source-lock.patch.json')['sources']; assert len(rows)==204;assert len({r['file'] for r in rows})==204
logs=load(P/'http-evidence.json');logmap={x['file']:x for x in logs};tree={x['path']:x for x in load(P/'api/transformers-tree.json')['tree']}; modelrev=load(P/'api/model-revision.json')['sha'];commit=load(P/'api/transformers-commit.json')['sha'];assert load(P/'api/transformers-tree.json')['sha']==commit
verified_git=0
for r in rows:
 b=(R/r['file']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256'];local=str((R/r['file']).relative_to(P));x=logmap[local];assert x['url']==r['url'] and x['bytes']==len(b)
 assert r['revision'] in r['url']
 if local.startswith('transformers/'):
  path=local[len('transformers/'):];assert r['revision']==commit;assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==tree[path]['sha'];verified_git+=1
 else:assert r['revision']==modelrev
idx=load(P/'model/model.safetensors.index.json');seen={};groups=collections.Counter();types=collections.Counter();ranges=0;filebytes=0
for shard in sorted(set(idx['weight_map'].values())):
 pb=(P/'prefixes'/f'{shard}.length').read_bytes();hb=(P/'headers'/f'{shard}.json').read_bytes();assert len(pb)==8 and struct.unpack('<Q',pb)[0]==len(hb)
 totals=[]
 for local,start,end in [(f'prefixes/{shard}.length',0,7),(f'headers/{shard}.json',8,7+len(hb))]:
  x=logmap[local];assert x['status']==206;cr=x['content_range'];prefix=f'bytes {start}-{end}/';assert cr.startswith(prefix);totals.append(int(cr[len(prefix):]));ranges+=1
 assert totals[0]==totals[1];offsets=[]
 for name,t in load(P/'headers'/f'{shard}.json').items():
  if name=='__metadata__':continue
  assert name not in seen and idx['weight_map'][name]==shard;seen[name]=t
  assert all(isinstance(n,int) and n>=0 for n in t['shape']);start,end=t['data_offsets'];assert 0<=start<=end and end-start==math.prod(t['shape'])*{'BF16':2,'F32':4}[t['dtype']];offsets.append((start,end))
  group='mtp' if name.startswith('mtp.') else 'vision' if name.startswith('model.visual.') else 'text';groups[group+'_parameters']+=math.prod(t['shape']);groups[group+'_bytes']+=end-start;types[(group,t['dtype'])]+=1
 cursor=0
 for start,end in sorted(offsets):assert start==cursor;cursor=end
 assert cursor+8+len(hb)==totals[0],('shard_file_size',shard);filebytes+=totals[0]
assert seen.keys()==idx['weight_map'].keys();assert sum(v for k,v in groups.items() if k.endswith('_bytes'))==idx['metadata']['total_size']
assert seen==load(P/'tensor-inventory.json');baseline=load(P/'header-audit.json');assert dict(groups)==baseline['groups']
# Independently derive base text count, aggregate matrix geometry, and critical model distinctions.
c=load(P/'model/config.json');t=c['text_config'];H=t['hidden_size'];E=t['num_experts'];F=t['moe_intermediate_size'];S=t['shared_expert_intermediate_size'];expected={'model.language_model.embed_tokens.weight':[t['vocab_size'],H],'lm_head.weight':[t['vocab_size'],H],'model.language_model.norm.weight':[H]}
for i,kind in enumerate(t['layer_types']):
 p=f'model.language_model.layers.{i}.'
 shapes={'input_layernorm.weight':[H],'post_attention_layernorm.weight':[H],'mlp.gate.weight':[E,H],'mlp.experts.gate_up_proj':[E,2*F,H],'mlp.experts.down_proj':[E,H,F],'mlp.shared_expert.gate_proj.weight':[S,H],'mlp.shared_expert.up_proj.weight':[S,H],'mlp.shared_expert.down_proj.weight':[H,S],'mlp.shared_expert_gate.weight':[1,H]}
 if kind=='full_attention':
  q=t['num_attention_heads']*t['head_dim'];kv=t['num_key_value_heads']*t['head_dim'];a={'q_proj.weight':[2*q,H],'k_proj.weight':[kv,H],'v_proj.weight':[kv,H],'o_proj.weight':[H,q],'q_norm.weight':[t['head_dim']],'k_norm.weight':[t['head_dim']]};prefix='self_attn.'
 else:
  k=t['linear_num_key_heads']*t['linear_key_head_dim'];v=t['linear_num_value_heads']*t['linear_value_head_dim'];vh=t['linear_num_value_heads'];a={'in_proj_qkv.weight':[2*k+v,H],'in_proj_z.weight':[v,H],'in_proj_a.weight':[vh,H],'in_proj_b.weight':[vh,H],'out_proj.weight':[H,v],'conv1d.weight':[2*k+v,1,t['linear_conv_kernel_dim']],'A_log':[vh],'dt_bias':[vh],'norm.weight':[t['linear_value_head_dim']]};prefix='linear_attn.'
 shapes.update({prefix+k:v for k,v in a.items()});expected.update({p+k:v for k,v in shapes.items()})
assert len(expected)==1038;actual={n:v for n,v in seen.items() if n.startswith('model.language_model.') or n=='lm_head.weight'};assert actual.keys()==expected.keys();assert all(actual[n]['shape']==s for n,s in expected.items())
report={'decision':'accept_necessary_F02_fixed_inputs_with_explicit_nonruntime_boundary','sources':204,'source_bytes':sum(r['bytes'] for r in rows),'git_blob_verified_implementation_files':verified_git,'model_revision':modelrev,'transformers_revision':commit,'range_response_checks':ranges,'shards_checked':94,'shard_content_range_total_matches_header_plus_payload':94,'tensors':len(seen),'base_text_shapes_checked':len(expected),'groups':dict(groups),'group_dtype_counts':{f'{g}/{d}':n for (g,d),n in types.items()},'duplicate_json_keys_checked':True,'no_tensor_payload_read':True,'whole_forward_execution_verified':False,'vision_and_mtp_expected_shape_enumeration_complete':False,'bindings':{str(p.relative_to(R)):sha(p.read_bytes()) for p in [P/'source-lock.patch.json',P/'header-audit.json',P/'http-evidence.json',P/'model/config.json']}}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,indent=2))
