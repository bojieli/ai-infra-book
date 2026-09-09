"""Qwen3 MoE inference graph: exact weights and declared per-expert routing counts.

Attention is shared with Qwen3 Dense. Expert work is a sum of variable-M GEMMs,
never a dense model scaled by advertised active parameters. Routing histograms
are scenario inputs; neither balanced nor concentrated is an observed trace.
"""
from . import qwen3
from ..schema import Operator, Scenario, Weight, linear
from ..sources import model_config
from ..units import positive_int


def validate(config: dict) -> None:
    if config['model_type'] != 'qwen3_moe':
        raise ValueError('MoE adapter requires model_type=qwen3_moe')
    qwen3.validate_common(config)
    for key in ('num_experts', 'num_experts_per_tok', 'moe_intermediate_size'):
        positive_int(config[key], key)
    if config['num_experts_per_tok'] > config['num_experts']:
        raise ValueError('top-k exceeds the expert count')
    if config.get('mlp_only_layers') or config.get('decoder_sparse_step', 1) != 1:
        raise ValueError('This adapter requires MoE at every decoder layer')


def weights(config: dict) -> list[Weight]:
    validate(config)
    h, f, layers, experts = (config[k] for k in (
        'hidden_size', 'moe_intermediate_size', 'num_hidden_layers', 'num_experts'))
    result = qwen3.base_weights(config)
    result.append(Weight('model.layers.{layer}.mlp.gate.weight', (experts, h), layers))
    for expert in range(experts):
        for name, shape in [('gate_proj', (f, h)), ('up_proj', (f, h)), ('down_proj', (h, f))]:
            result.append(Weight(f'model.layers.{{layer}}.mlp.experts.{expert}.{name}.weight', shape, layers))
    return result


def routing_counts(rows: int, experts: int, top_k: int, policy: str,
                   counts: list[int] | None = None) -> list[int]:
    """A common per-layer histogram. Every token chooses top_k distinct experts."""
    if counts is None:
        if policy == 'balanced':
            # token i uses (i*top_k + j) % experts, j=0..top_k-1.
            quotient, remainder = divmod(rows * top_k, experts)
            counts = [quotient + (e < remainder) for e in range(experts)]
        elif policy == 'concentrated':
            counts = [rows if e < top_k else 0 for e in range(experts)]
        else:
            raise ValueError('Routing must be balanced, concentrated, or an explicit histogram')
    if not isinstance(counts, list):
        raise ValueError('Expert counts must be a JSON array of integers')
    if len(counts) != experts:
        raise ValueError(f'Expected {experts} expert counts')
    for count in counts:
        positive_int(count, 'expert count', allow_zero=True)
        if count > rows:
            raise ValueError('An expert cannot receive a token twice within top-k')
    if sum(counts) != rows * top_k:
        raise ValueError('Expert histogram must sum to tokens × top-k')
    return list(counts)


def expert_operators(config: dict, scenario: Scenario, counts: list[int]) -> list[Operator]:
    h, f, e, top, layers = (config[k] for k in (
        'hidden_size', 'moe_intermediate_size', 'num_experts', 'num_experts_per_tok', 'num_hidden_layers'))
    m, a, w = scenario.rows, scenario.activation_bytes, scenario.weight_bytes
    assignments, union = sum(counts), sum(count > 0 for count in counts)
    ops = [linear('router', m, h, e, scenario, repeats=layers)]
    ops.append(Operator('router_softmax', 'routing', {'input': [m, e], 'probabilities_fp32': [m, e]},
                        repeats=layers, scalar_flops=m * (3 * e - 1),
                        special_ops={'exp': m * e, 'compare_max': m * (e - 1)},
                        activation_read_bytes=m * e * a, activation_write_bytes=m * e * 4,
                        notes='FP32 softmax: subtract max, exp, reduction, divide; casts are not FLOPs.'))
    ops.append(Operator('router_topk', 'routing', {'input_fp32': [m, e], 'values_fp32': [m, top], 'indices_int64': [m, top]},
                        repeats=layers, special_ops={'topk_rows': m, 'topk_candidates': m * e},
                        activation_read_bytes=m * e * 4, activation_write_bytes=assignments * 12,
                        notes='Top-k is an explicit selection primitive; candidate counts are not comparisons or FLOPs. Backend selection algorithm is unspecified.'))
    ops.append(Operator('router_renormalize_cast', 'routing', {'selected_probabilities': [m, top]},
                        repeats=layers, scalar_flops=m * (2 * top - 1) if config['norm_topk_prob'] else 0,
                        activation_read_bytes=assignments * 4, activation_write_bytes=assignments * a,
                        notes='Selected probabilities are renormalized if norm_topk_prob, then cast to activation dtype; row reduction assumed on-chip.'))
    mask_elements = m * top * e
    ops.append(Operator('routing_one_hot', 'routing_metadata', {'selected_int64': [m, top], 'mask_int64': [m, top, e]},
                        repeats=layers, special_ops={'one_hot_entries': mask_elements},
                        activation_read_bytes=assignments * 8, activation_write_bytes=mask_elements * 8,
                        notes='Pinned HF reference materializes one_hot int64; this large routing mask is not assumed in optimized dispatch.'))
    ops.append(Operator('routing_where', 'routing_metadata', {'mask_int64': [e, top, m], 'top_x_and_slot_each': [assignments]},
                        repeats=layers, special_ops={'integer_nonzero_tests': mask_elements},
                        activation_read_bytes=mask_elements * 8, activation_write_bytes=assignments * 16,
                        notes='Scan each expert mask; two int64 coordinates per assignment. Permute is a view.'))
    ops.append(Operator('expert_gather', 'routing', {'source': [m, h], 'gathered_rows': [assignments, h]},
                        repeats=layers, activation_read_bytes=assignments * (h * a + 8),
                        activation_write_bytes=assignments * h * a,
                        notes='Logical gathers summed over experts; n_e and each concrete GEMM shape are in expert_matrices.'))
    for name, inputs, outputs in [('expert_gate_proj', h, f), ('expert_up_proj', h, f)]:
        ops.append(Operator(name, 'linear', {'input_per_expert': ['n_e', inputs], 'weight_storage_each': [outputs, inputs],
                                            'output_per_expert': ['n_e', outputs], 'nonempty_experts': union, 'tokens_per_expert': counts},
                            repeats=layers, matrix_flops=2 * assignments * inputs * outputs,
                            weight_read_bytes=union * inputs * outputs * w,
                            activation_read_bytes=assignments * inputs * a, activation_write_bytes=assignments * outputs * a,
                            notes='Sum of unpadded per-expert GEMMs; each visited expert weight read once per layer, not once per token.'))
    ops.append(Operator('expert_silu_mul', 'activation', {'gate_and_up_each': [assignments, f]},
                        repeats=layers, scalar_flops=4 * assignments * f,
                        special_ops={'exp': assignments * f, 'negate': assignments * f},
                        activation_read_bytes=2 * assignments * f * a, activation_write_bytes=assignments * f * a))
    ops.append(Operator('expert_down_proj', 'linear', {'input_per_expert': ['n_e', f], 'weight_storage_each': [h, f],
                                                     'output_per_expert': ['n_e', h], 'nonempty_experts': union, 'tokens_per_expert': counts},
                        repeats=layers, matrix_flops=2 * assignments * f * h,
                        weight_read_bytes=union * f * h * w, activation_read_bytes=assignments * f * a,
                        activation_write_bytes=assignments * h * a,
                        notes='Unpadded per-expert GEMMs; empty experts have zero arithmetic and no weight payload.'))
    ops.append(Operator('expert_probability_multiply', 'routing', {'expert_outputs': [assignments, h], 'routing_weights': [assignments]},
                        repeats=layers, scalar_flops=assignments * h,
                        activation_read_bytes=assignments * (h * a + a + 16), activation_write_bytes=assignments * h * a,
                        notes='Probability broadcast reuses one value per assignment; int64 token/slot indices included.'))
    ops.append(Operator('expert_output_zero', 'routing', {'output': [m, h]}, repeats=layers,
                        activation_write_bytes=m * h * a, notes='Reference initializes final_hidden_states to zero.'))
    ops.append(Operator('expert_index_add', 'routing', {'weighted_outputs': [assignments, h], 'combined_output': [m, h]},
                        repeats=layers, scalar_flops=assignments * h,
                        activation_read_bytes=2 * assignments * h * a + assignments * 8,
                        activation_write_bytes=assignments * h * a,
                        notes='Reference index_add includes the first add into zero; destination read/update per assignment is logical payload, not measured HBM.'))
    return ops


def calculate(model: str, scenario: Scenario, routing: str = 'balanced', counts: list[int] | None = None) -> dict:
    config = model_config(model)
    validate(config)
    hist = routing_counts(scenario.rows, config['num_experts'], config['num_experts_per_tok'], routing, counts)
    mlp = expert_operators(config, scenario, hist)
    result = qwen3.summarize(model, config, scenario, qwen3.build_operators(config, scenario, mlp), weights(config))
    result['calculation'] = 'qwen3-moe-forward'
    result['scenario']['routing'] = 'explicit_histogram' if counts is not None else routing
    result['scenario']['tokens_per_expert_per_layer'] = hist
    result['dimensions'].update({key: config[key] for key in ('num_experts', 'num_experts_per_tok', 'moe_intermediate_size', 'norm_topk_prob')})
    h, f, layers, top = (config[k] for k in ('hidden_size', 'moe_intermediate_size', 'num_hidden_layers', 'num_experts_per_tok'))
    union = sum(n > 0 for n in hist)
    result['expert_matrices'] = [
        {'expert': expert, 'tokens': n, 'gate_and_up_each': {'A': [n, h], 'W_math': [h, f], 'Y': [n, f]},
         'down': {'A': [n, f], 'W_math': [f, h], 'Y': [n, h]}}
        for expert, n in enumerate(hist)]
    result['summary'].update({
        'expert_assignments_per_layer': sum(hist), 'expert_union_per_layer': union,
        'max_tokens_per_expert': max(hist), 'min_tokens_per_expert': min(hist),
        'routed_expert_total_parameters': 3 * layers * config['num_experts'] * h * f,
        'routed_expert_active_parameters_per_token': 3 * layers * top * h * f,
        'routed_expert_matrix_flops': 6 * layers * scenario.rows * top * h * f,
        'routed_expert_unique_weight_payload_bytes': 3 * layers * union * h * f * scenario.weight_bytes,
        'router_matrix_flops': 2 * layers * scenario.rows * h * config['num_experts'],
    })
    result['assumptions'] += [
        'Each layer uses the explicitly reported same histogram. Balanced/concentrated are scenarios, not measured routing or inferred probabilities.',
        'Top-k choices per token are distinct; no token drop, capacity padding, shared experts, auxiliary training loss or expert parallel communication.',
        'Expert matrices list every expert including empty ones. Operator rows sum variable-M GEMMs without padding; actual grouped kernels and execution order may differ.',
        'Routing includes reference FP32 softmax, selection, renormalization/cast, int64 one_hot/where, gather, probability weighting and zero/index_add combination.',
        'Top-k is counted as a selection primitive with candidates/rows, not a fabricated comparison FLOP count. Runtime bookkeeping and conversion instruction counts remain backend-dependent.',
    ]
    return result
