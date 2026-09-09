"""Independent teaching arithmetic; never import or execute archived source."""
from pathlib import Path
import hashlib
import json
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[4]
D = Path(__file__).resolve().parent
config = ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json'
c = json.loads(config.read_text())
h, q, kv, d, f, layers = [c[k] for k in ['hidden_size', 'num_attention_heads', 'num_key_value_heads', 'head_dim', 'intermediate_size', 'num_hidden_layers']]
assert (h, q, kv, d, f, layers) == (4096, 32, 8, 128, 12288, 36)
linear_elements = h * (q + 2 * kv) * d + q * d * h + 3 * h * f
cases = []
for lengths in ([4096, 4096], [7168, 1024], [8192]):
    tokens = sum(lengths)
    pairs = sum(s * (s + 1) // 2 for s in lengths)
    cases.append(dict(lengths=lengths, tokens=tokens, squared_lengths=sum(s*s for s in lengths),
                      causal_pairs=pairs,
                      per_layer_linear_forward_flops=2 * tokens * linear_elements,
                      per_layer_attention_forward_flops=4 * q * d * pairs))
assert cases[0]['tokens'] == cases[1]['tokens'] == 8192
ratio = Fraction(cases[1]['causal_pairs'], cases[0]['causal_pairs'])
assert Fraction(cases[1]['squared_lengths'], cases[0]['squared_lengths']) == Fraction(25, 16)
assert cases[0]['per_layer_linear_forward_flops'] == cases[1]['per_layer_linear_forward_flops']
degree, local_tokens, dtype_bytes = 8, 1024, 2
kv_bytes = 2 * kv * d * dtype_bytes
q_bytes = q * d * dtype_bytes
expanded_qkv = 3 * q_bytes
native_qkv = q_bytes + kv_bytes
wire = lambda payload: Fraction(local_tokens * payload * (degree-1), degree)
comm = dict(degree=degree, local_tokens=local_tokens, original_kv_bytes_per_token=kv_bytes,
            expanded_kv_bytes_per_token=2*q_bytes,
            original_qkv_bytes_per_token=native_qkv,
            expanded_qkv_bytes_per_token=expanded_qkv,
            context_bytes_per_token=q_bytes,
            expanded_forward_send_bytes_per_rank=int(wire(expanded_qkv+q_bytes)),
            hypothetical_native_gqa_forward_send_bytes_per_rank=int(wire(native_qkv+q_bytes)))
assert comm['expanded_forward_send_bytes_per_rank'] == 28*1024**2
assert comm['hypothetical_native_gqa_forward_send_bytes_per_rank'] == 17.5*1024**2
grad = dict(token_counts=[1024, 7168], per_token_gradient=[1, 3],
            token_mean=float(Fraction(1024+7168*3,8192)), unweighted_group_mean=2.0)
assert grad['token_mean'] == 2.75
chunks = [dict(prompt_tokens=513, chunk_size=n, chunks=(513+n-1)//n,
               padded_linear_tokens=((513+n-1)//n)*n,
               extra_linear_tokens=((513+n-1)//n)*n-513) for n in [256,128]]
assert [x['extra_linear_tokens'] for x in chunks] == [255,127]
mobile = json.loads((D/'mllm-qwen3-config.json').read_text())
mobile_kv = 2*mobile['num_hidden_layers']*mobile['num_key_value_heads']*mobile['head_dim']*mobile['max_cache_length']
assert mobile_kv == 112*1024**2
end_to_end = [dict(prefill_ms=900, decode_ms=x, prefill_speedup_assumed=3,
                      overall_speedup=(900+x)/(300+x)) for x in [100,2700]]
assert end_to_end[0]['overall_speedup'] == 2.5
assert end_to_end[1]['overall_speedup'] == 1.2
out = dict(scope='Independent mathematical budgets, not paper reproduction or hardware measurements.',
           config_file=str(config.relative_to(ROOT)), config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
           token_partitions=cases, causal_attention_ratio=float(ratio),
           exclusions='Forward main-layer linear projections and effective causal QK/AV pairs only; excludes softmax, backward, recompute, padding execution, embedding, head, collectives and optimizer.',
           ulysses_payload=comm, loss_normalization=grad, fixed_chunk_examples=chunks,
           mobile_kv=dict(config_file=str((D/'mllm-qwen3-config.json').relative_to(ROOT)),
                          config_sha256=hashlib.sha256((D/'mllm-qwen3-config.json').read_bytes()).hexdigest(),
                          cache_tokens=mobile['max_cache_length'], logical_int8_bytes=mobile_kv,
                          logical_bf16_bytes=2*mobile_kv,
                          exclusions='One sequence, no replicas, padding, scales, temporary buffers or graph-specific layout.'),
           end_to_end=end_to_end)
(D/'arithmetic.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Independent sequence, communication, loss weighting, chunk and KV budgets passed.')
