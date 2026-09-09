"""Pinned V4 non-routed FP8 Linear calls: interfaces and declared tile work.

One device (world_size=1), contiguous BF16 activations, default E8M0 scales.
Repeated quantization calls stay repeated: shared w1 and w3 each call linear.
"""
from ..sources import model_config, provenance, read_source
from ..units import positive_int
from . import v4_attention, experts


def account(rows: int, inputs: int, outputs: int) -> dict:
    """Account one aligned Linear invocation; bytes are logical API operands."""
    for name, value in [('rows', rows), ('inputs', inputs), ('outputs', outputs)]:
        positive_int(value, name)
    if inputs % 128 or outputs % 128:
        raise ValueError('This ledger requires aligned K and N; partial output tiles need separate handling')
    m, k, n = rows, inputs, outputs
    padded_m = ((m + 31) // 32) * 32
    kb, nb = k // 128, n // 128
    # Scale_C[i] is shared across all 128 output columns, not recomputed per cell.
    scale_multiply = m * nb * kb
    corrected_accumulate = 2 * m * n * kb
    quant_interface = 2 * m * k + m * k + m * kb
    gemm_interface = m * k + n * k + m * kb + nb * kb + 2 * m * n
    return dict(rows=m, input_width=k, output_width=n,
                weight_shape=[n, k], activation_scale_shape=[m, kb], weight_scale_shape=[nb, kb],
                valid_matrix_flops=2 * m * n * k,
                padded_tile_matrix_flops=2 * padded_m * n * k,
                activation_quantization_scalar_flops=m * k + m * kb,
                activation_abs_ops=m * k, activation_max_comparisons=m * k,
                activation_clamp_comparisons=2 * m * k,
                activation_round_scale_calls=m * kb,
                activation_fp8_cast_elements=m * k, activation_e8m0_cast_elements=m * kb,
                scale_product_flops=scale_multiply,
                scale_corrected_accumulation_flops=corrected_accumulate,
                logical_scale_flops=scale_multiply + corrected_accumulate,
                padded_scale_flops=padded_m * nb * kb + 2 * padded_m * n * kb,
                quantization_interface_bytes=quant_interface, gemm_interface_bytes=gemm_interface,
                total_interface_bytes=quant_interface + gemm_interface,
                resident_weight_bytes=n * k, resident_weight_scale_bytes=nb * kb,
                activation_fp8_bytes=m * k, activation_scale_bytes=m * kb,
                output_bf16_bytes=2 * m * n)


def calculate(model: str = 'deepseek-v4-flash', batch: int = 1,
              tokens: int = 8192, history: int = 0) -> dict:
    if model not in ('deepseek-v4-flash', 'deepseek-v4-pro'):
        raise ValueError('Only pinned V4 Flash/Pro are covered')
    # Verify implementation bytes as well as config before depending on its defaults.
    for name in ('model.py', 'kernel.py'):
        read_source(f'sources/{model}/inference/{name}')
    c = model_config(model, reference=True)
    if c['dtype'] != 'fp8' or c.get('scale_dtype', 'fp8') != 'fp8':
        raise ValueError('This path requires reference FP8 weights and E8M0 scales')
    attention = v4_attention.calculate(model, batch, tokens, history)
    expert = experts.calculate(model, batch, tokens)
    names = {'wq_a', 'wq_b', 'wkv_shared', 'wo_b', 'index_wq_b'}
    selected = [r for r in attention['matrices'] if r['name'] in names]
    selected += [r for r in expert['matrices'] if r['category'] == 'shared']
    rows = []
    for source in selected:
        if source['stored_copies_per_layer'] != 1:
            raise ValueError('Only independent single-copy Linear matrices are covered')
        work = account(source['rows_summed_per_layer'], source['input_width'], source['output_width'])
        repeat = len(source['layer_ids'])
        totals = {key: value * repeat for key, value in work.items()
                  if isinstance(value, int) and key not in ('rows', 'input_width', 'output_width')}
        if totals['valid_matrix_flops'] != source['matrix_flops']:
            raise ValueError('Selected Linear work does not match existing matrix ledger')
        rows.append(dict(name=source['name'], layer_ids=source['layer_ids'], invocation_count=repeat,
                         per_invocation=work, totals=totals))
    summary = {key: sum(row['totals'][key] for row in rows) for key in rows[0]['totals']}
    summary['linear_invocations'] = sum(row['invocation_count'] for row in rows)
    return dict(schema_version=1, calculation='v4-fp8-linear', model=model,
                scenario=dict(batch=batch, tokens=tokens, history=history, world_size=1,
                              input_dtype='BF16', weight_dtype='FP8 E4M3', scale_dtype='E8M0',
                              accumulator_dtype='FP32', sparsity='dense'),
                sources=provenance(model), v4_fp8_linear_rows=rows, summary=summary,
                assumptions=[
                    'Pinned model.py Linear dispatch, default dtype FP8 and ModelArgs.scale_dtype=fp8. Explicit FP32 compressors/router/head and BF16 grouped output/index weights projection are excluded; routed FP4 experts have their own ledger. MTP is excluded.',
                    'Each shared gate/up/down and each selected attention projection calls act_quant separately. No cross-call input quantization reuse is assumed, even where w1 and w3 receive the same input.',
                    'Valid matrix work already belongs to v4_forward: replace it with padded work for a tile comparison, never add both. Kernel tiles are 32 by 128 by 128, with FP8 inputs and FP32 accumulation; no structured sparsity.',
                    'Scale_A times Scale_B costs one multiply per row/output-block/K-block; scale-corrected C uses multiply plus add per output cell/K-block. This is not three FLOPs per cell because Scale_C is shared over 128 columns.',
                    'Quantization counts valid cells: absmax reduction K/128 groups of 128, clamp-min once per group, scale multiply and division, clamp and casts. Power-of-two bit manipulation is counted as fast_round_scale calls, not floating log/exp FLOPs. Padded quantization instructions and compiler effects are not claimed.',
                    'API operand bytes sum act_quant BF16 read, FP8/scales write, then GEMM FP8/scales/weight read and BF16 output write. Intermediates appear once per interface. These are not physical HBM bytes; cache reuse, repeated tile loads, contiguous copies, workspace and tensor lifetimes remain separate.',
                    'Resident weights/scales describe these reference Linear objects only, not complete checkpoint/runtime allocations. Contiguous BF16 input and single-device execution are explicit assumptions; no hardware time or executable model claim.',
                ])
