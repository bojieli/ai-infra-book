"""DeepSeek V3 base logical forward from pinned config and HF source.

The reference expands MLA keys/values before cache.update. The public HF
forward projects all output positions. Neither FP8 storage nor a compact cache
is inferred from config dtype fields. MTP is outside this base graph.
"""
from collections import Counter
from dataclasses import asdict
from math import exp, isfinite

from ..models.qwen3 import rmsnorm
from ..models.qwen3_moe import routing_counts
from ..schema import Operator, Scenario, Weight, linear
from ..sources import model_config, provenance, read_source

MODEL = 'deepseek-v3'


def validate(c: dict) -> None:
    """Refuse architectural changes that would invalidate the pinned graph."""
    required = dict(model_type='deepseek_v3', attention_bias=False, hidden_act='silu',
                    scoring_func='sigmoid', topk_method='noaux_tc', norm_topk_prob=True,
                    tie_word_embeddings=False, attention_dropout=0.0, moe_layer_freq=1,
                    ep_size=1)
    for key, expected in required.items():
        if c.get(key) != expected:
            raise ValueError(f'Unsupported V3 field {key}: {c.get(key)!r}')
    if c['q_lora_rank'] is None or c['n_shared_experts'] != 1 or c['rope_scaling']['type'] != 'yarn':
        raise ValueError('Requires low-rank Q, one shared expert and YaRN')
    if c['n_routed_experts'] % c['n_group'] or c['qk_rope_head_dim'] % 2:
        raise ValueError('Invalid grouped routing or rotary dimensions')


def weights(c: dict) -> list[Weight]:
    """Base logical tensors; {layer} records have explicitly stated repetition."""
    validate(c)
    h, l, v = c['hidden_size'], c['num_hidden_layers'], c['vocab_size']
    heads, qr, kr = c['num_attention_heads'], c['q_lora_rank'], c['kv_lora_rank']
    dn, dr, dv = c['qk_nope_head_dim'], c['qk_rope_head_dim'], c['v_head_dim']
    dense, f, e = c['first_k_dense_replace'], c['moe_intermediate_size'], c['n_routed_experts']
    result = [Weight('model.embed_tokens.weight', (v, h)), Weight('lm_head.weight', (v, h)),
              Weight('model.norm.weight', (h,))]
    attention = [('q_a_proj', (qr, h)), ('q_a_layernorm', (qr,)),
                 ('q_b_proj', (heads * (dn + dr), qr)), ('kv_a_proj_with_mqa', (kr + dr, h)),
                 ('kv_a_layernorm', (kr,)), ('kv_b_proj', (heads * (dn + dv), kr)),
                 ('o_proj', (h, heads * dv))]
    result += [Weight('model.layers.{layer}.self_attn.' + name + '.weight', shape, l)
               for name, shape in attention]
    result += [Weight('model.layers.{layer}.' + name + '.weight', (h,), l)
               for name in ('input_layernorm', 'post_attention_layernorm')]
    result += [Weight('moe_layers.{layer}.mlp.gate.weight', (e, h), l - dense),
               Weight('moe_layers.{layer}.mlp.gate.e_score_correction_bias', (e,), l - dense)]
    for prefix, copies, width in [('dense_layers.{layer}.mlp', dense, c['intermediate_size']),
                                   ('moe_layers.{layer}.mlp.shared_experts', l - dense, f)]:
        for name, shape in [('gate_proj', (width, h)), ('up_proj', (width, h)), ('down_proj', (h, width))]:
            result.append(Weight(prefix + '.' + name + '.weight', shape, copies))
    for expert in range(e):
        for name, shape in [('gate_proj', (f, h)), ('up_proj', (f, h)), ('down_proj', (h, f))]:
            result.append(Weight(f'moe_layers.{{layer}}.mlp.experts.{expert}.{name}.weight', shape, l - dense))
    return result


def grouped_route(logits: list[float], bias: list[float], c: dict) -> tuple[list[int], list[float]]:
    """Mathematical noaux_tc selection for tests/inspection, not a CUDA emulator.

    Ties use lowest index here; torch.topk does not promise that tie order.
    Correction bias changes selection only, not the gathered mixture weights.
    """
    e, groups, keep, k = (c[x] for x in ('n_routed_experts', 'n_group', 'topk_group', 'num_experts_per_tok'))
    if len(logits) != e or len(bias) != e or not all(isfinite(x) for x in logits + bias):
        raise ValueError('Finite logits/bias of the configured expert count required')
    scores = [1 / (1 + exp(-x)) if x >= 0 else exp(x) / (1 + exp(x)) for x in logits]
    choice = [s + b for s, b in zip(scores, bias)]
    width = e // groups
    group_score = [sum(sorted(choice[g * width:(g + 1) * width], reverse=True)[:2]) for g in range(groups)]
    chosen_groups = sorted(range(groups), key=lambda g: (-group_score[g], g))[:keep]
    candidates = [i for i in range(e) if i // width in chosen_groups]
    ids = sorted(candidates, key=lambda i: (-choice[i], i))[:k]
    denom = sum(scores[i] for i in ids) + 1e-20
    return ids, [scores[i] / denom * c['routed_scaling_factor'] for i in ids]


def calculate(batch: int = 1, tokens: int = 8192, history: int = 0,
              output_head: str = 'all', attention_work: str = 'valid',
              routing: str = 'balanced', counts: list[int] | None = None) -> dict:
    s = Scenario(batch=batch, tokens=tokens, history=history, output_head=output_head)
    c = model_config(MODEL)
    read_source('sources/deepseek-v3/modeling_deepseek.py')
    validate(c)
    if history + tokens > c['max_position_embeddings']:
        raise ValueError('Requested positions exceed pinned configuration context')
    if attention_work not in ('valid', 'eager'):
        raise ValueError('attention_work must be valid or eager')
    h, l, v, m = c['hidden_size'], c['num_hidden_layers'], c['vocab_size'], s.rows
    heads, qr, kr = c['num_attention_heads'], c['q_lora_rank'], c['kv_lora_rank']
    dn, dr, dv = c['qk_nope_head_dim'], c['qk_rope_head_dim'], c['v_head_dim']
    dense, f, e, k = (c[x] for x in ('first_k_dense_replace', 'moe_intermediate_size', 'n_routed_experts', 'num_experts_per_tok'))
    moe, end = l - dense, history + tokens
    hist = routing_counts(m, e, k, routing, counts)
    ops = [Operator('embedding_lookup', 'embedding', {'ids': [batch, tokens], 'output': [m, h]},
                    weight_read_bytes=m*h*2, activation_write_bytes=m*h*2)]
    ops += [rmsnorm('input_rmsnorm', m, h, s, l), rmsnorm('post_attention_rmsnorm', m, h, s, l)]
    for name, inputs, outputs in [('q_a_proj', h, qr), ('q_b_proj', qr, heads*(dn+dr)),
                                  ('kv_a_proj_with_mqa', h, kr+dr), ('kv_b_proj', kr, heads*(dn+dv)),
                                  ('o_proj', heads*dv, h)]:
        ops.append(linear(name, m, inputs, outputs, s, repeats=l))
    ops += [rmsnorm('q_a_layernorm', m, qr, s, l), rmsnorm('kv_a_layernorm', m, kr, s, l)]
    rotary_cells = m * (heads + 1) * dr
    ops.append(Operator('rotary_q_and_shared_k', 'position',
                        {'q_rotary': [batch, heads, tokens, dr], 'k_rotary': [batch, 1, tokens, dr]},
                        repeats=l, scalar_flops=3*rotary_cells, special_ops={'sign_negation': rotary_cells//2},
                        activation_read_bytes=rotary_cells*2 + 2*m*dr*2,
                        activation_write_bytes=rotary_cells*2,
                        notes='2 multiplies + 1 add per rotary cell; sign flips separate. Cos/sin table operands read once per token and broadcast over heads. YaRN tables assumed prepared.'))
    ops.append(Operator('expanded_kv_append', 'cache',
                        {'key': [batch, heads, tokens, dn+dr], 'value': [batch, heads, tokens, dv]},
                        repeats=l, activation_read_bytes=m*heads*(dn+dr+dv)*2,
                        activation_write_bytes=m*heads*(dn+dr+dv)*2,
                        notes='Logical newly expanded cache records only; shared rotary branch is repeated across key heads. DynamicCache concatenation/copies are not these bytes.'))
    pairs = s.pairs if attention_work == 'valid' else s.rectangular_pairs
    cells, query_rows = heads*pairs, heads*m
    ops.append(Operator('qk_scores', 'attention',
                        {'query': [batch, heads, tokens, dn+dr], 'keys': [batch, heads, end, dn+dr],
                         'scores_rectangle': [batch, heads, tokens, end]}, repeats=l,
                        matrix_flops=2*cells*(dn+dr), activation_read_bytes=2*heads*(m+batch*end)*(dn+dr),
                        activation_write_bytes=2*cells,
                        notes='Logical Q/K read once each; valid triangular cells versus eager rectangular work selected explicitly.'))
    ops.append(Operator('score_scale_softmax', 'attention', {'accounted_cells': cells, 'query_rows': query_rows},
                        repeats=l, scalar_flops=4*cells-query_rows + (cells if attention_work == 'eager' else 0),
                        special_ops={'exp': cells, 'compare_max': cells-query_rows},
                        activation_read_bytes=2*cells, activation_write_bytes=2*cells,
                        notes='Scale + stable subtract/exp/sum/divide; eager includes explicit mask addition. Softmax internally FP32; logical interface is activation dtype, internal casts separate.'))
    ops.append(Operator('pv_output', 'attention',
                        {'probability_rectangle': [batch, heads, tokens, end], 'values': [batch, heads, end, dv],
                         'output': [batch, heads, tokens, dv]}, repeats=l,
                        matrix_flops=2*cells*dv, activation_read_bytes=2*(cells+batch*heads*end*dv),
                        activation_write_bytes=2*m*heads*dv))
    router = linear('router_fp32', m, h, e, s, repeats=moe)
    router.weight_read_bytes, router.activation_read_bytes, router.activation_write_bytes = e*h*4, m*h*4, m*e*4
    router.notes = 'Source explicitly casts input and gate weights to FP32. Operands use FP32; conversion/source reads are not hidden in this GEMM.'
    ops.append(router)
    ops.append(Operator('router_sigmoid_and_correction', 'routing', {'scores': [m, e]}, repeats=moe,
                        scalar_flops=m*e, special_ops={'sigmoid': m*e}, weight_read_bytes=e*4,
                        activation_read_bytes=m*e*4, activation_write_bytes=2*m*e*4,
                        notes='One correction-bias add per expert; original sigmoid scores remain for weighting.'))
    ops.append(Operator('router_group_sum_and_weight_normalization', 'routing',
                        {'group_top2': [m, c['n_group'], 2], 'selected': [m, k]}, repeats=moe,
                        scalar_flops=m*(c['n_group']+3*k),
                        activation_read_bytes=m*(2*c['n_group']+k)*4, activation_write_bytes=m*(c['n_group']+k)*4,
                        notes='Each group sums top-2; selected original scores sum (k-1), epsilon add, k divisions and k scale multiplications. Selection operation counts are separate; topk comparisons are backend dependent.'))

    def mlp(prefix, rows, width, repeats):
        for name, inputs, outputs in [('gate', h, width), ('up', h, width), ('down', width, h)]:
            ops.append(linear(prefix+'_'+name, rows, inputs, outputs, s, repeats=repeats))
        ops.append(Operator(prefix+'_silu_and_product', 'activation', {'gate_and_up': [rows, width]},
                            repeats=repeats, scalar_flops=2*rows*width, special_ops={'sigmoid': rows*width},
                            activation_read_bytes=4*rows*width, activation_write_bytes=2*rows*width,
                            notes='SiLU multiply and gated product; sigmoid is a separate primitive, fused logical interface.'))
    mlp('dense', m, c['intermediate_size'], dense)
    mlp('shared', m, f, moe)
    for expert, n in enumerate(hist):
        if n:
            mlp(f'expert_{expert}', n, f, moe)
    ops.append(Operator('routed_weighted_reduce_and_shared_add', 'routing', {'expert_outputs': [m,k,h]}, repeats=moe,
                        scalar_flops=m*h*(k+k-1+1), activation_read_bytes=m*k*h*2+m*k*4+m*h*2,
                        activation_write_bytes=m*h*2,
                        notes='k weighted products, k-1 reductions, shared add per output cell. Source does weighted accumulation in FP32; operand interface uses BF16 expert outputs plus FP32 gate weights.'))
    ops.append(Operator('attention_and_ffn_residual_adds', 'residual', {'input': [m,h]}, repeats=2*l,
                        scalar_flops=m*h, activation_read_bytes=4*m*h, activation_write_bytes=2*m*h))
    ops.append(rmsnorm('final_rmsnorm', m, h, s))
    if s.head_rows:
        ops.append(linear('lm_head', s.head_rows, h, v, s))
        ops.append(Operator('logits_float32_cast', 'cast', {'logits': [s.head_rows,v]},
                            special_ops={'cast_elements': s.head_rows*v},
                            activation_read_bytes=2*s.head_rows*v, activation_write_bytes=4*s.head_rows*v))
    tensors = weights(c)
    total = {key: sum(getattr(op,key)*op.repeats for op in ops) for key in
             ('matrix_flops','scalar_flops','weight_read_bytes','activation_read_bytes','activation_write_bytes')}
    special = Counter()
    for op in ops:
        special.update({key:value*op.repeats for key,value in op.special_ops.items()})
    parameters = sum(w.parameters for w in tensors)
    cache_unit = l*heads*(dn+dr+dv)*2
    return dict(schema_version=1, calculation='deepseek-v3-base-forward', model=MODEL,
                scenario={**asdict(s), 'attention_work': attention_work, 'routing': routing if counts is None else 'explicit_histogram',
                          'tokens_per_expert_per_moe_layer': hist, 'mla_path': 'reference_expanded', 'training': False},
                sources=provenance(MODEL), weights=[w.record(2) for w in tensors],
                operators=[op.record() for op in ops],
                routing_selection=dict(groups=c['n_group'], experts_per_group=e//c['n_group'],
                                       groups_retained=c['topk_group'], selected_experts=k,
                                       group_top2_calls=moe*m*c['n_group'], group_topk_calls=moe*m,
                                       expert_topk_calls=moe*m, sort_comparisons=None),
                layer_ids=dict(dense=list(range(dense)), moe=list(range(dense,l)), attention=list(range(l))),
                summary={**total, 'special_ops':dict(special), 'logical_base_parameters':parameters,
                         'uniform_bf16_parameter_bytes':2*parameters,
                         'logical_base_tensor_count':sum(w.copies for w in tensors),
                         'dense_layers':dense, 'moe_layers':moe, 'expert_union_per_layer':sum(n>0 for n in hist),
                         'kv_bytes_per_token_per_request':cache_unit,
                         'kv_resident_after_bytes':batch*end*cache_unit,
                         'kv_new_write_bytes':m*cache_unit, 'history_unique_payload_bytes':batch*history*cache_unit,
                         'valid_attention_matrix_flops':2*l*heads*s.pairs*(dn+dr+dv),
                         'eager_attention_matrix_flops':2*l*heads*s.rectangular_pairs*(dn+dr+dv),
                         'rectangular_score_fp32_bytes_per_layer':batch*heads*tokens*end*4,
                         'complete_runtime_bytes':None, 'complete_hbm_bytes':None, 'predicted_latency_seconds':None},
                coverage=dict(base_logical_weight_and_operator_graph=True, checkpoint_header_validation=False,
                              missing=['FP8 checkpoint scales and runtime quantization/conversion allocations',
                                       'backend tile work, topk/sort internal comparisons and traffic, dispatch copies',
                                       'YaRN table construction/growth, DynamicCache concatenation, allocator/workspace lifetimes',
                                       'MTP, training/backward, compact MLA alternative, measured runtime/HBM']),
                assumptions=[
                    'Pinned base model with 61 attention layers, 3 dense FFNs and 58 MoE FFNs; 256 routed top-8 plus one shared expert. Weights enumerate logical model tensors, excluding MTP and checkpoint quantization scales. No checkpoint index/header evidence is claimed.',
                    'Official HF forward expands KV then cache.update, applies RoPE to Q and shared K extra branch, and projects all positions by default. last/none output heads are explicit workload alternatives, not a claim about this unmodified forward.',
                    'Valid attention counts useful causal cells; eager counts full score rectangle plus additive mask, matching the source mathematical path. FP32 internal softmax and source conversion traffic are not inferred as fused backend HBM. No attention dropout in inference.',
                    'YaRN cos/sin tables and softmax scale are prepared constants. Rotary application is counted; table preparation/growth is separate. Shared rotary K is expanded across heads in the reference cache.',
                    'Balanced/concentrated histograms are conditional routing inputs repeated across MoE layers, not measured choices. Explicit histograms pass assignment conservation but do not prove realizability under four-group selection. Grouped routing uses biased scores only for selection; mixture weights use original sigmoid scores, normalized then multiplied by 2.5.',
                    'Matrix FMA counts as two FLOPs. Scalar arithmetic and special functions stay separate. Weight and activation bytes are declared logical operator interfaces with one read per operand; expert weights read once per visited expert. They are not cache-aware HBM measurements or simultaneous allocation peaks.',
                    'Uniform two-byte weight capacity is a comparison format only. Router executes FP32 operands; official FP8 block quantization requires separate physical storage and conversion accounting. Global state, runtime copies, dispatch/reshape traffic and unsupported paths stay explicit in coverage.',
                ])
