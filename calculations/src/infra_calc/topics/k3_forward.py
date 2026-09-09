"""Compose the K3 text forward with explicit logical KDA algorithm selection.

Matrix FMA=2 and scalar/special operations stay separate. No complete runtime
storage, traffic or latency is inferred from these mathematical subledgers.
"""
from collections import Counter
from ..schema import Scenario
from ..sources import model_config, provenance
from . import k3_mla, k3_kda, kda_chunk, attn_res, experts, state, k3_checkpoint


def calculate(batch: int = 1, tokens: int = 8192, history: int = 0,
              mla_path: str = 'expanded', kda_algorithm: str = 'auto',
              chunk_size: int = 64, output_head: str = 'last',
              routing: str = 'balanced', counts: list[int] | None = None) -> dict:
    s = Scenario(batch=batch, tokens=tokens, history=history, output_head=output_head)
    if output_head not in ('last', 'all'):
        raise ValueError('K3 reference vocabulary head supports last or all positions')
    if kda_algorithm not in ('auto', 'recurrent', 'chunk'):
        raise ValueError('KDA algorithm must be auto, recurrent or chunk')
    algorithm = ('recurrent' if tokens == 1 else 'chunk') if kda_algorithm == 'auto' else kda_algorithm
    c = model_config('kimi-k3')['text_config']
    h, layers, vocab, m = c['hidden_size'], c['num_hidden_layers'], c['vocab_size'], s.rows
    mla = k3_mla.calculate(batch, tokens, history, mla_path)
    kda = k3_kda.calculate(batch, tokens, history)
    residual = attn_res.calculate(batch, tokens)
    expert = experts.calculate('kimi-k3', batch, tokens, routing, counts)
    cache = state.calculate('kimi-k3', history + tokens, batch, mla_path=mla_path)
    a, k, r, e = mla['summary'], kda['summary'], residual['summary'], expert['summary']
    parameters = dict(mla_matrices=a['matrix_parameters'], mla_norms=a['norm_scale_parameters'],
                      kda_projections=k['projection_parameters'], kda_convolution=k['convolution_parameters'],
                      kda_output_norm=k['output_norm_parameters'], kda_decay=k['decay_parameters'],
                      expert_matrices=e['ffn_matrix_parameters'], router_bias=e['router_bias_elements'],
                      latent_norm=e['latent_norm_scale_elements'],
                      attn_res=r['allocated_norm_and_projection_parameters'],
                      external_norms=(2 * layers + 1) * h, embedding=vocab * h,
                      vocabulary_head=0 if c['tie_word_embeddings'] else vocab * h)
    head_rows = batch if output_head == 'last' else m
    head_flops = 2 * head_rows * h * vocab
    matrix_components = dict(mla=a['matrix_flops'], kda_projections=k['projection_matrix_flops'],
                             experts=e['ffn_matrix_flops'], attn_res=r['weighted_sum_matrix_flops'],
                             vocabulary_head=head_flops, kda_block_core=0)
    special = Counter()
    kda_scalar = 0
    for op in kda['non_matrix_operations']:
        if algorithm == 'chunk' and op['name'] == 'recurrent_state_update_and_query':
            continue
        kda_scalar += op['scalar_flops']
        special.update(op['special_ops'])
    components = dict(mla=mla, kda=kda, experts=expert, attn_res=residual, state=cache)
    if algorithm == 'chunk':
        chunk = kda_chunk.calculate(batch, tokens, chunk_size)
        components['kda_chunk'] = chunk
        matrix_components['kda_block_core'] = chunk['summary']['mathematical_block_matrix_flops']
        kda_scalar += chunk['summary']['mathematical_block_scalar_flops']
        # Block prefix/difference exponentials replace the recurrent decay exp.
        special.pop('exp_decay', None)
        linear = c['linear_attn_config']
        special['exp_block'] = (batch * linear['num_heads'] * len(linear['kda_layers'])
                                * chunk['mathematical_block_work']['exp_ops'])
    external_scalar = (2 * layers + 1) * m * (4 * h + 1)
    # Stable softmax on valid causal entries: scale, subtract, sum, divide.
    heads = c['num_attention_heads']
    mla_layers = len(c['linear_attn_config']['full_attn_layers'])
    score_cells, score_rows = mla_layers * heads * s.pairs, mla_layers * heads * m
    softmax_scalar = 4 * score_cells - score_rows
    scalar_components = dict(kda=kda_scalar, experts=expert['non_matrix_summary']['scalar_flops'],
                             mla_norm_and_gate=a['qk_norm_scalar_flops'] + a['output_gate_scalar_flops'],
                             mla_valid_score_scale_and_softmax=softmax_scalar,
                             attn_res=r['mixing_scalar_flops'] + r['prefix_accumulation_scalar_flops'],
                             external_norms=external_scalar)
    special.update(expert['non_matrix_summary']['special_ops'])
    special.update(dict(rsqrt=a['norm_rsqrt_ops'] + r['rsqrt_ops'] + (2 * layers + 1) * m,
                        sigmoid=a['output_gate_sigmoid_ops'], exp=r['exp_ops'] + score_cells,
                        compare_max=r['max_comparisons'] + score_cells - score_rows))
    checkpoint = k3_checkpoint.calculate()
    config_parameters = sum(parameters.values())
    if checkpoint['logical_parameters_by_component']['text'] - config_parameters != checkpoint['text_parameter_delta_from_config']:
        raise ValueError('K3 logical parameter difference is not explained by explicit shape discrepancies')
    return dict(schema_version=1, calculation='kimi-k3-text-forward-ledger', model='kimi-k3', checkpoint=checkpoint,
                scenario=dict(batch=batch, tokens=tokens, history=history, mla_path=mla_path,
                              kda_algorithm=algorithm, chunk_size=chunk_size if algorithm == 'chunk' else None,
                              output_head=output_head, generation_mode=output_head == 'last', routing=routing,
                              tokens_per_expert=expert['scenario']['tokens_per_expert']),
                sources=provenance('kimi-k3'), parameter_components=parameters, components=components,
                matrix_components=matrix_components, scalar_components=scalar_components,
                summary=dict(logical_text_parameters=sum(parameters.values()),
                             checkpoint_logical_text_parameters=checkpoint['logical_parameters_by_component']['text'],
                             checkpoint_text_parameter_delta=checkpoint['text_parameter_delta_from_config'],
                             text_checkpoint_payload_bytes=checkpoint['byte_groups']['text_total_bytes'],
                             config_checkpoint_shape_match=checkpoint['config_shape_match'],
                             uniform_bf16_parameter_bytes=2 * sum(parameters.values()),
                             matrix_flops=sum(matrix_components.values()),
                             accounted_scalar_flops=sum(scalar_components.values()),
                             accounted_special_ops=dict(special), vocabulary_head_matrix_flops=head_flops,
                             embedding_lookup_payload_bytes=m * h * 2,
                             state_resident_after_bytes=cache['summary']['resident_bytes'],
                             complete_actual_weight_bytes=None, complete_hbm_traffic_bytes=None,
                             predicted_latency_seconds=None),
                coverage=dict(text_logical_matrix_graph=True, checkpoint_index_validation=True,
                              config_checkpoint_shape_match=checkpoint['config_shape_match'],
                              non_matrix_arithmetic='declared logical algorithms; backend coverage partial',
                              missing=['resolve official config/source versus checkpoint A_log shape discrepancy',
                                       'runtime mixed-format conversions and resident copies',
                                       'quantization/casts, backend padding, compiled tile and instruction work',
                                       'complete allocation lifetimes, device placement and measured traffic/latency',
                                       'vision, multimodal wrapper and MTP forwards']),
                assumptions=[
                    'Pinned K3 text model only: embedding, 24 MLA and 69 KDA sublayers, 93 FFNs, AttnRes, external norms and vocabulary head. Logical parameters follow config/source. Every checkpoint header is independently audited; 69 A_log vectors have length 128 rather than the declared 96, adding 2208 checkpoint parameters. The discrepancy remains unresolved; config calculations are not a verified loadable checkpoint execution.',
                    'generation_mode=True selects last position before lm_head; otherwise all positions. Final model norm and output AttnRes still process all new tokens.',
                    'Expanded MLA follows the reference cache. Compact is an algebraic alternative. Attention uses valid causal entries and stable softmax including score scaling; rectangular/padded backend work is not this total.',
                    'Auto selects recurrent mathematics for T=1 and block mathematics for T>1. Chunk replaces the recurrent core and decay exponentials; it is not added to them. Explicit overrides are comparison algorithms, not runtime dispatch promises.',
                    'Selected FLA block algorithm uses valid triangular terms and forward substitution, not the fused kernel instruction count. Its compatibility with the pinned K3 dependency is not proven.',
                    'AttnRes includes prefix accumulation; no ordinary residual additions are added a second time. Its depth stack is not persistent decode state.',
                    'Uniform BF16 parameter/cache payload is a comparison convention. KDA persistent recurrent state is FP32. Complete actual bytes, traffic and latency remain null.',
                    'Special functions remain primitive counts; scalar arithmetic must not be divided by a Tensor Core peak.',
                ])
