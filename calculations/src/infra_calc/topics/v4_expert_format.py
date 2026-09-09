"""Actual routed-expert format and compute route in pinned V4 fp4_gemm.

FP4 storage is expanded to FP8 before T.gemm. This is NOT native FP4 MMA.
Tile work counts the declared 32x128x32 kernel, not achieved performance.
"""


def calculate(model: str, geometry: dict, histogram: list[int]) -> dict:
    if model not in ('deepseek-v4-flash', 'deepseek-v4-pro'):
        return {}
    g = geometry
    h, f, e, layers = g['expert_hidden'], g['intermediate'], g['experts'], len(g['moe_layers'])
    union = sum(n > 0 for n in histogram)
    records = []
    for name, inputs, outputs in [('gate', h, f), ('up', h, f), ('down', f, h)]:
        if inputs % 128 or outputs % 128:
            raise ValueError('Current V4 expert shape must align to pinned activation and output groups')
        packed = outputs * inputs // 2
        scales = outputs * inputs // 32
        rows = sum(histogram)
        padded_rows = sum(((n + 31) // 32) * 32 for n in histogram if n)
        records.append(dict(name=name, logical_weight_shape=[outputs, inputs],
                            packed_fp4_shape=[outputs, inputs // 2], e8m0_scale_shape=[outputs, inputs // 32],
                            resident_packed_bytes=layers * e * packed,
                            resident_scale_bytes=layers * e * scales,
                            visited_weight_and_scale_payload_bytes=layers * union * (packed + scales),
                            activation_fp8_output_bytes=layers * rows * inputs,
                            activation_e8m0_scale_bytes=layers * rows * (inputs // 128),
                            valid_matrix_flops=layers * 2 * rows * inputs * outputs,
                            padded_tile_matrix_flops=layers * 2 * padded_rows * inputs * outputs,
                            logical_scale_accumulation_flops=layers * 3 * rows * outputs * (inputs // 32),
                            padded_scale_accumulation_flops=layers * 3 * padded_rows * outputs * (inputs // 32),
                            activation_quantization_scalar_flops=layers * (rows * inputs + rows * inputs // 128)))
    summary = {key: sum(row[key] for row in records) for key in (
        'resident_packed_bytes', 'resident_scale_bytes', 'visited_weight_and_scale_payload_bytes',
        'activation_fp8_output_bytes', 'activation_e8m0_scale_bytes', 'valid_matrix_flops',
        'padded_tile_matrix_flops', 'logical_scale_accumulation_flops', 'padded_scale_accumulation_flops',
        'activation_quantization_scalar_flops')}
    summary['resident_weight_and_scale_bytes'] = summary['resident_packed_bytes'] + summary['resident_scale_bytes']
    return dict(routed_expert_format=dict(
        weight_storage='FP4 E2M1 packed, E8M0 scale per output row per 32 K elements',
        activation_storage='FP8 E4M3, E8M0 scale per activation row per 128 K elements',
        mma_input_a='FP8 E4M3', mma_input_b='FP8 E4M3 after FP4 -> FP32 -> FP8 conversion',
        accumulator='FP32', sparsity='dense', tile_mnk=[32, 128, 32],
        native_fp4_peak_eligible=False, matrices=records, summary=summary,
        assumptions=[
            'Routed experts only. Shared experts, routers, other model weights and checkpoint metadata are outside these totals.',
            'E8M0 scales use one byte. Per-weight scale overhead is 1/32 byte, so total is 17/32 byte per routed weight, not 1/2.',
            'Actual FP4 GEMM converts weight subtiles to FP8 before multiplication. Use FP8/FP32 dense evidence for that multiply, never a native FP4 peak.',
            'Each nonempty expert independently rounds M up to 32. N and K of these official models already align to 128 and 32. Tile counts are reference work, not measured instructions or latency.',
            'After every K=32 subtile, reference multiplies by activation scale and weight scale and adds to FP32 accumulator: three scalar operations per output cell per K subtile.',
            'Input activation quantization counts one scale multiply per group and one divide per element; abs/max, clamps, casts and bitwise power-of-two scale rounding are separate primitives, not included in its scalar count.',
            'Activation byte fields are summed generated quantization buffers, not simultaneously resident memory. Gate/up reference calls quantize independently; no fusion reuse assumed.',
            'Weight payload assumes each visited expert weight/scale read once; tiling may reload weights. Not a whole-kernel HBM claim.',
        ]))
