"""Closed-form full-history cache accounting across prompt and decode calls.

A record is counted once per call, assuming ideal query-head reuse. This is
logical payload, not a hardware traffic measurement or cache hierarchy model.
"""
from ..sources import model_config, provenance
from ..units import positive_int
from . import state


def calculate(model: str = 'qwen3-8b', batch: int = 1, prompt: int = 8192,
              steps: int = 1024, prefix_hit: int = 6144,
              element_bytes: int = 2, recurrent_bytes: int = 4) -> dict:
    for name, value in (('batch', batch), ('prompt', prompt), ('element_bytes', element_bytes), ('recurrent_bytes', recurrent_bytes)):
        positive_int(value, name)
    for name, value in (('steps', steps), ('prefix_hit', prefix_hit)):
        positive_int(value, name, allow_zero=True)
    if prefix_hit > prompt:
        raise ValueError('Prefix hit cannot exceed prompt length')
    config = model_config(model)
    c = config['text_config'] if model == 'kimi-k3' else config
    if prompt + steps > c['max_position_embeddings']:
        raise ValueError('Sequence exceeds pinned config context limit')
    variants = []
    if config['model_type'] in ('qwen3', 'qwen3_moe'):
        if c.get('use_sliding_window'):
            raise ValueError('Full-history accounting does not support sliding-window Qwen')
        heads, d, layers = c['num_attention_heads'], c['head_dim'], c['num_hidden_layers']
        for name, kv_heads in (('native_gqa', c['num_key_value_heads']), ('counterfactual_mha', heads), ('counterfactual_mqa', 1)):
            variants.append(dict(name=name, reference=name == 'native_gqa', kv_heads=kv_heads,
                                 history_bytes_per_token=2 * layers * kv_heads * d * element_bytes,
                                 attention_flops_per_pair=4 * layers * heads * d,
                                 kv_projection_parameters=2 * layers * c['hidden_size'] * kv_heads * d,
                                 recurrent_bytes=0, convolution_bytes=0))
    elif model == 'kimi-k3':
        for path in ('expanded', 'compact'):
            cache = state.calculate(model, prompt, batch, element_bytes, recurrent_bytes, path)
            layers, heads = len(c['linear_attn_config']['full_attn_layers']), c['num_attention_heads']
            qk_pv_width = (c['qk_nope_head_dim'] + c['qk_rope_head_dim'] + c['v_head_dim'] if path == 'expanded'
                           else 2 * c['kv_lora_rank'] + c['qk_rope_head_dim'])
            variants.append(dict(name=path, reference=path == 'expanded', kv_heads=None,
                                 history_bytes_per_token=cache['summary']['next_token_mla_append_bytes'] // batch,
                                 attention_flops_per_pair=2 * layers * heads * qk_pv_width,
                                 kv_projection_parameters=None,
                                 recurrent_bytes=cache['components']['kda_recurrent_bytes'],
                                 convolution_bytes=cache['components']['short_conv_slots_bytes']))
    else:
        raise ValueError('Cache sequence adapter supports Qwen3 Dense/MoE and Kimi K3')
    # Before each append: P, P+1, ..., P+G-1. The current token is separate.
    history_records = steps * prompt + steps * (steps - 1) // 2
    visible_pairs = history_records + steps
    # Recompute the full prefix at every call: sum_n n(n+1)/2.
    def triangular_sum(n):
        return n * (n + 1) * (n + 2) // 6
    uncached_pairs = triangular_sum(prompt + steps) - triangular_sum(prompt)
    suffix = prompt - prefix_hit
    full_pairs = prompt * (prompt + 1) // 2
    suffix_pairs = suffix * prefix_hit + suffix * (suffix + 1) // 2
    rows = []
    for variant in variants:
        unit = batch * variant['history_bytes_per_token']
        persistent = variant['recurrent_bytes'] + variant['convolution_bytes']
        row = dict(variant)
        row.update(initial_history_bytes=prompt * unit,
                   final_history_bytes=(prompt + steps) * unit,
                   final_persistent_state_bytes=(prompt + steps) * unit + persistent,
                   decode_prior_history_read_payload_bytes=history_records * unit,
                   decode_current_record_operand_bytes=steps * unit,
                   decode_visible_kv_operand_bytes=visible_pairs * unit,
                   decode_append_write_bytes=steps * unit,
                   decode_recurrent_read_plus_write_bytes=2 * steps * variant['recurrent_bytes'],
                   decode_convolution_slot_read_plus_write_bytes=2 * steps * variant['convolution_bytes'],
                   decode_attention_matrix_flops=batch * visible_pairs * variant['attention_flops_per_pair'],
                   uncached_recompute_attention_matrix_flops=batch * uncached_pairs * variant['attention_flops_per_pair'],
                   full_prefill_attention_matrix_flops=batch * full_pairs * variant['attention_flops_per_pair'],
                   prefix_suffix_attention_matrix_flops=batch * suffix_pairs * variant['attention_flops_per_pair'],
                   full_prefill_history_write_bytes=prompt * unit,
                   prefix_suffix_history_write_bytes=suffix * unit,
                   prefix_checkpoint_payload_bytes=prefix_hit * unit + (persistent if prefix_hit else 0),
                   final_capacity_saved_by_prefix_hit_bytes=0)
        rows.append(row)
    native = next(row for row in rows if row['reference'])
    return dict(schema_version=1, calculation='cache-sequence', model=model,
                scenario=dict(batch=batch, prompt=prompt, steps=steps, prefix_hit=prefix_hit,
                              element_bytes=element_bytes, recurrent_bytes=recurrent_bytes),
                sources=provenance(model), cache_variants=rows,
                summary=dict(reference_variant=native['name'],
                             decode_prior_history_records_per_request=history_records,
                             decode_visible_pairs_per_request=visible_pairs,
                             uncached_recompute_pairs_per_request=uncached_pairs,
                             cached_decode_projection_rows=batch * steps,
                             uncached_recompute_projection_rows=batch * visible_pairs,
                             prefill_full_pairs_per_request=full_pairs,
                             prefill_suffix_pairs_per_request=suffix_pairs,
                             saved_prefill_pairs_per_request=full_pairs - suffix_pairs,
                             saved_new_token_projection_rows=batch * prefix_hit,
                             decode_prior_history_read_payload_bytes=native['decode_prior_history_read_payload_bytes'],
                             decode_append_write_bytes=native['decode_append_write_bytes'],
                             final_persistent_state_bytes=native['final_persistent_state_bytes'],
                             actual_hbm_traffic_bytes=None),
                assumptions=[
                    'P prompt tokens are already processed before G subsequent one-token calls. Call i starts with P+i history and appends one token; total prior records = GP+G(G-1)/2. This is G model calls, not an unqualified API output-token count.',
                    'Prior-history read excludes the current record; visible attention operands include it; append writes are separate. Query heads ideally reuse every K/V record once per call. These are logical payloads, not summed HBM traffic.',
                    'MHA/MQA are architecture counterfactuals with unchanged Q heads and head width; they are not alternative execution modes of the downloaded GQA weights or evidence of equal quality. KV projections/cache change; QK/PV matrix work does not.',
                    'K3 compact is an algebraic alternative to reference expanded MLA. Only MLA QK/PV is in attention FLOPs; KDA, projection, FFN, normalization and output-head work are outside this ledger.',
                    'Prefix reuse skips C token rows and C(C+1)/2 causal pairs; suffix queries still attend to cached prefix. Final unshared per-request cache capacity is unchanged. Prefix lookup, transfer, reference counting and physical sharing are not modeled.',
                    'K3 prefix checkpoint must include recurrent and convolution state at the exact prefix boundary, not merely MLA history. Per-decode read/write of those state objects is a declared payload, not an allocator or HBM trace. K3 config/checkpoint A_log shape discrepancy remains documented separately.',
                    'Full prompt hit has zero new prompt attention work; producing first logits still requires cached boundary output or recomputation, which this state/attention-only calculation does not include.',
                    'Without cache, every call recomputes all P+i+1 positions. Projection rows and causal attention pairs are reported separately; this does not eliminate temporary KV tensors or imply zero peak memory.',
                    'No workspace, weights, padding, parallel replication, quantization metadata or cache-offloading costs are included. Explicit bytes describe uniform teaching state formats.',
                ])
