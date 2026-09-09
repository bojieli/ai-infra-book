from pathlib import Path
from fractions import Fraction
import json
D=Path(__file__).resolve().parent;ROOT=Path(__file__).resolve().parents[3];C=ROOT/'references/outline-checks/2026-09-07/scaling-history'
q=json.loads((C/'qwen3-8b-config.json').read_text());m=json.loads((C/'qwen3-235b-config.json').read_text())
h=q['hidden_size'];L=q['num_hidden_layers'];a=q['num_attention_heads'];v=q['num_key_value_heads'];d=q['head_dim'];f=q['intermediate_size'];V=q['vocab_size']
mat=2*h*a*d+2*h*v*d+3*h*f
params=L*(mat+2*h+2*d)+h+2*V*h
kv=2*L*v*d*2
mh=m['hidden_size'];ml=m['num_hidden_layers'];md=m['head_dim'];ma=m['num_attention_heads'];mv=m['num_key_value_heads'];mf=m['moe_intermediate_size'];me=m['num_experts']
mparam=ml*(2*mh*ma*md+2*mh*mv*md+3*mh*mf*me+mh*me+2*mh+2*md)+mh+2*m['vocab_size']*mh
assert params==8190735360 and mparam==235093634560
rows=[]
for prefix,input_tokens,output_tokens in [(0,8192,1),(0,8192,129),(0,16,1),(6144,2048,129)]:
 H=prefix+input_tokens;Dcalls=output_tokens-1
 correct=kv*(Dcalls*H+Dcalls*(Dcalls-1)//2);wrong=kv*(output_tokens*H+output_tokens*(output_tokens-1)//2)
 rows.append(dict(existing_prefix=prefix,new_input=input_tokens,requested_outputs=output_tokens,prefill_end_kv_tokens=H,post_prefill_calls=Dcalls,correct_old_history_bytes=correct,if_output_count_used_as_call_count_old_history_bytes=wrong,correct_final_kv_bytes=kv*(H+Dcalls),if_output_count_used_as_call_count_final_kv_bytes=kv*(H+output_tokens),correct_final_pages=(H+Dcalls+15)//16,wrong_final_pages=(H+output_tokens+15)//16))
P=8192;pairs=P*(P+1)//2
checks=dict(qwen8_parameters=params,qwen235_parameters=mparam,qwen8_layer_projection_ffn_parameters=mat,qwen8_layer_projection_ffn_flops_per_input=2*mat,qwen8_bf16_full_weight_bytes=2*params,qwen8_bf16_backbone_matrix_bytes=2*L*mat,qwen8_kv_bytes_per_token=kv,qwen235_kv_bytes_per_token=2*ml*mv*md*2,qwen8_prefill_backbone_linear_flops=2*mat*P*L,qwen8_prefill_attention_causal_flops=4*a*d*pairs*L,qwen8_pp_hidden_bytes_per_token=2*h,qwen8_pp_hidden_and_residual_bytes_per_token=4*h,qwen8_half_model_kv_at8192_bytes=kv//2*8192,qwen8_training_state16_bytes=16*params,qwen8_training_state18_bytes=18*params,qwen8_checkpoint14_bytes=14*params,qwen235_expert_bf16_bytes=3*mh*mf*2,qwen235_all_experts_bf16_bytes=3*mh*mf*2*me*ml)
assert checks['qwen8_kv_bytes_per_token']==147456
assert checks['qwen235_kv_bytes_per_token']==192512
assert checks['qwen235_all_experts_bf16_bytes']==423*1024**3
out=dict(scope='Independent arithmetic from archived official config only; no downloaded code executed; ordinary causal generation with first output sampled from prefill and last output not forwarded again.',checks=checks,generation_boundaries=rows,pd_transfer=dict(legacy_32_layer_bytes=1024**3,qwen8_36_layer_bytes=kv*8192,assumed_bytes_per_second=25*10**9,legacy_ms=1024**3/(25*10**9)*1000,qwen8_ms=kv*8192/(25*10**9)*1000))
(D/'arithmetic.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('Qwen configuration, request boundary and PD arithmetic passed.')
