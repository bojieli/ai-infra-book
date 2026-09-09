"""Compose V4 base-forward ledgers without double-counting subcomponents.

This is an explicit accounting report, not a claim that every backend operation
or byte is known. Missing coverage is machine-readable and prevents a complete
traffic/latency total. MTP modules are not called by the reference base forward.
"""
from collections import Counter

from ..sources import model_config, provenance
from . import experts, hyper_connections, state, v4_attention, v4_checkpoint


def calculate(model: str, batch: int = 1, tokens: int = 8192, history: int = 0,
              routing: str = 'balanced', counts: list[int] | None = None) -> dict:
    attention = v4_attention.calculate(model, batch, tokens, history)
    expert = experts.calculate(model, batch, tokens, routing, counts)
    hc = hyper_connections.calculate(model, batch, tokens)
    cache = state.calculate(model, history + tokens, batch)
    c = model_config(model, reference=True)
    m, h, layers, vocab = batch * tokens, c['dim'], c['n_layers'], c['vocab_size']
    # These norm scales and APE/sink vectors are absent from matrix subledgers.
    parameters = {
        'attention_matrices': attention['summary']['matrix_parameters'],
        'expert_matrices_including_router_shared': expert['summary']['ffn_matrix_parameters'],
        'hyper_connections': hc['summary']['hc_parameters'],
        'embedding': vocab * h, 'vocabulary_head': vocab * h,
        'external_norms': (2 * layers + 1) * h,
        'attention_q_lowrank_and_kv_norm': layers * (c['q_lora_rank'] + c['head_dim']),
        'attention_sinks': layers * c['n_heads'],
        'compressor_norms': 0, 'compressor_ape': 0,
        'router_bias': expert['summary']['router_bias_elements'],
    }
    for ratio in c['compress_ratios'][:layers]:
        if ratio:
            widths = [c['head_dim']] + ([c['index_head_dim']] if ratio == 4 else [])
            for width in widths:
                parameters['compressor_norms'] += width
                parameters['compressor_ape'] += ratio * (2 if ratio == 4 else 1) * width
    external_norm_scalar = (2 * layers + 1) * m * (4 * h + 1)
    head_matrix = 2 * batch * h * vocab
    a, e, residual = attention['summary'], expert['summary'], hc['summary']
    effective = a['matrix_flops'] + e['ffn_matrix_flops'] + residual['matrix_flops'] + head_matrix
    # Replace, never add again, valid sparse attention and routed expert GEMMs.
    routed = expert['routed_expert_format']['summary']
    reference_tiles = (a['reference_with_sparse_tiles_matrix_flops'] + e['ffn_matrix_flops']
                       - routed['valid_matrix_flops'] + routed['padded_tile_matrix_flops']
                       + residual['matrix_flops'] + head_matrix)
    scalar = (a['accounted_scalar_flops'] + expert['non_matrix_summary']['scalar_flops']
              + residual['scalar_flops'] + external_norm_scalar
              + routed['logical_scale_accumulation_flops'] + routed['activation_quantization_scalar_flops'])
    special = Counter()
    for values in (attention['non_matrix_summary']['special_ops'], expert['non_matrix_summary']['special_ops'], residual['special_ops']):
        special.update(values)
    special.update({'rsqrt': (2 * layers + 1) * m,
                    'exp': attention['sparse_kernel_summary']['exp_ops'],
                    'compare_max': attention['sparse_kernel_summary']['max_comparisons']})
    checkpoint = v4_checkpoint.calculate(model)
    if checkpoint['base_logical_parameters_excluding_scales_and_hash'] != sum(parameters.values()):
        raise ValueError('Base logical parameter enumeration differs from official checkpoint headers')
    return dict(schema_version=1, calculation='v4-base-forward-ledger', model=model, checkpoint=checkpoint,
                scenario=dict(batch=batch, tokens=tokens, history=history, routing=routing,
                              tokens_per_expert=expert['scenario']['tokens_per_expert'], output_head='last'),
                sources=provenance(model), parameter_components=parameters,
                components=dict(attention=attention, experts=expert, hyper_connections=hc, state=cache),
                summary=dict(logical_parameters_excluding_mtp_and_quant_scales=sum(parameters.values()),
                             uniform_bf16_parameter_bytes=2 * sum(parameters.values()),
                             hash_routing_table_int32_bytes=e['hash_lookup_resident_int32_bytes'],
                             matrix_flops_effective_attention=effective,
                             matrix_flops_with_reference_sparse_and_expert_tiles=reference_tiles,
                             vocabulary_head_matrix_flops=head_matrix,
                             accounted_scalar_flops=scalar, accounted_special_ops=dict(special),
                             state_resident_after_bytes=cache['summary']['resident_bytes'],
                             embedding_lookup_payload_bytes=m * h * 2,
                             complete_actual_weight_bytes=None, complete_hbm_traffic_bytes=None,
                             base_checkpoint_payload_bytes=checkpoint['byte_groups']['base_total_bytes'],
                             predicted_latency_seconds=None),
                coverage=dict(base_matrix_graph=True, non_matrix_arithmetic='partial',
                              actual_weight_formats='all checkpoint header dtypes; runtime conversions remain separate', checkpoint_index_validation=True,
                              missing=['FP8 projection/shared-expert activation quantization and scale application',
                                       'runtime conversions/aliases and resident allocations beyond checkpoint storage',
                                       'all remaining source copies/casts, frequency precomputation and allocator/backend bookkeeping',
                                       'compiled tile work for projection GEMMs, device feasibility and measured traffic',
                                       'MTP separate forward and multi-token cached-prefix execution path']),
                assumptions=[
                    'Base reference forward: embedding -> all attention/FFN mHC blocks -> hc_head -> final RMSNorm -> last-position vocabulary head. MTP weights/forward excluded explicitly.',
                    'Parameter total is derived from all base logical matrices plus explicit vectors. It is checked against all official checkpoint headers; quantization scales and integer hash tables are excluded and identified separately. Checkpoint hash tables are I64, unlike runtime int32.',
                    'Effective matrix total uses selected attention pairs and unpadded expert rows, but reference rectangular Indexer work. The alternate total replaces sparse-attention/expert work with their known tiles; other projection padding is not yet included.',
                    'Scalar subtotal mixes declared logical algorithms; routed scale-application uses unpadded output cells. It is not a complete GPU instruction count or a quantity to divide by Tensor peak.',
                    'Uniform BF16 bytes are a comparison format, not actual V4 resident storage. Missing complete bytes/latency remain null.',
                ])
