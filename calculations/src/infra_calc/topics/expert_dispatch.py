"""Logical reference dispatch operands, with sorting internals left unknown.

Boundary: selected expert IDs and routing probabilities -> combined routed
output. Expert GEMMs and activations are accounted elsewhere. No EP collective.
"""


def calculate(model: str, g: dict, rows: int, histogram: list[int], activation_bytes: int) -> dict:
    if model not in ('deepseek-v4-flash', 'deepseek-v4-pro', 'kimi-k3'):
        return {}
    m, e, k, r, a = rows, g['experts'], g['top_k'], g['expert_hidden'], activation_bytes
    assignments, union = sum(histogram), sum(n > 0 for n in histogram)
    operations = []

    def add(name, layers, shapes, read=0, write=0, note='', kind='logical_operand'):
        operations.append(dict(name=name, layer_ids=layers, shapes=shapes, interface='device_memory_logical',
                               read_bytes_per_layer=read, write_bytes_per_layer=write,
                               read_bytes=read * len(layers), write_bytes=write * len(layers),
                               accounting_kind=kind, notes=note))

    layers = g['moe_layers']
    host_transfer = len(layers) * e * 8
    if model == 'kimi-k3':
        add('count_matrix_zero', layers, {'int64_counts': [m, e]}, write=m * e * 8)
        add('count_scatter', layers, {'int64_ids': [m, k]}, read=assignments * 8, write=assignments * 8,
            note='scatter stores one int64 constant per selected expert, without reading prior destination.')
        add('count_reduce', layers, {'input': [m, e], 'output': [e]}, read=m * e * 8, write=e * 8)
        add('argsort_endpoints', layers, {'int64_ids': [assignments], 'int64_permutation': [assignments]},
            read=assignments * 8, write=assignments * 8, kind='endpoint_minimum',
            note='Only one input read and output write. Sort passes, comparisons, scratch and synchronization are UNKNOWN, not zero.')
        add('permutation_to_token', layers, {'int64_permutation': [assignments]},
            read=assignments * 8, write=assignments * 8,
            note='Materialize idxs // top_k; integer division is not floating-point work.')
        add('input_gather', layers, {'gathered': [assignments, r]},
            read=assignments * (8 + r * a), write=assignments * r * a)
        add('expert_output_cat', layers, {'concatenated': [assignments, r]},
            read=assignments * r * a, write=assignments * r * a,
            note='Expert input slices are views; reference torch.cat materializes all expert outputs.')
        add('restore_assignment_order', layers, {'output': [assignments, r]},
            read=assignments * (8 + r * a), write=assignments * r * a,
            note='new_x[idxs] = outs; permutation is bijective, so no destination read.')
        if a != 4:
            add('outputs_cast_fp32', layers, {'output': [assignments, r]},
                read=assignments * r * a, write=assignments * r * 4)
        add('probability_multiply_fp32', layers, {'output': [assignments, r], 'probabilities': [assignments]},
            read=assignments * (r * 4 + 4), write=assignments * r * 4,
            note='One probability reused across each row. Arithmetic is already in non_matrix_operations.')
        add('topk_sum_fp32', layers, {'input': [m, k, r], 'output': [m, r]},
            read=assignments * r * 4, write=m * r * 4)
        if a != 4:
            add('combined_cast', layers, {'output': [m, r]}, read=m * r * 4, write=m * r * a)
    else:
        # Hash lookup returns int32 IDs; score top-k returns int64 IDs.
        for ids, index_bytes in [(g['hash_layers'], 4), (g['router_bias_layers'], 8)]:
            add('bincount_endpoints', ids, {'indices': [m, k], 'int64_counts': [e]},
                read=assignments * index_bytes, write=e * 8, kind='endpoint_minimum',
                note='Input/output endpoints only. Histogram initialization/atomic updates are backend-dependent.')
            add('expert_equality_masks', ids, {'bool_masks_total': [union, m, k]},
                read=union * assignments * index_bytes, write=union * assignments,
                note='Reference skips empty experts before comparing IDs, so only union masks are formed.')
        add('where_coordinates', layers, {'bool_masks_total': [union, m, k], 'two_int64_coordinates': [assignments, 2]},
            read=union * assignments, write=assignments * 16)
        add('input_gather', layers, {'gathered': [assignments, r]},
            read=assignments * (8 + r * a), write=assignments * r * a)
        add('probability_gather', layers, {'probabilities_fp32': [assignments]},
            read=assignments * (16 + 4), write=assignments * 4,
            note='Weights are passed into the expert; intermediate F-wide multiplication belongs to its activation graph.')
        add('routed_output_zero', layers, {'accumulator_fp32': [m, r]}, write=m * r * 4)
        add('accumulator_gather', layers, {'gathered_fp32': [assignments, r]},
            read=assignments * (8 + r * 4), write=assignments * r * 4)
        add('expert_output_add', layers, {'sum_fp32': [assignments, r]},
            read=assignments * r * (4 + a), write=assignments * r * 4)
        add('accumulator_scatter', layers, {'updated_fp32': [assignments, r]},
            read=assignments * (8 + r * 4), write=assignments * r * 4,
            note='Within each expert the selected token indices are distinct. Cross-expert additions follow reference order.')
    return dict(dispatch_operations=operations,
                dispatch_summary=dict(logical_operand_bytes=sum(op['read_bytes'] + op['write_bytes'] for op in operations
                                                                 if op['accounting_kind'] == 'logical_operand'),
                                      endpoint_minimum_bytes=sum(op['read_bytes'] + op['write_bytes'] for op in operations
                                                                 if op['accounting_kind'] == 'endpoint_minimum'),
                                      device_to_host_count_bytes=host_transfer,
                                      sorting_or_histogram_internal_bytes=None),
                dispatch_scope='Single-device pinned reference, unfused operand ledger. CPU counts transfer is a separate interface; sort/bincount internals remain unknown. Excludes GEMMs, expert activations, shared branch, latent norm/projections, allocator and communication. Not measured HBM, workspace peak, or optimized grouped-dispatch traffic.')
