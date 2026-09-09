"""Logical butterfly and V4 in-place quantize/dequantize arithmetic.

Butterfly counts are mathematical work, not CUDA shuffle/sign instructions.
Quantization counts follow pinned V4 kernels with power-of-two scale rounding.
"""
from ..units import positive_int


def hadamard(rows: int, width: int) -> dict:
    positive_int(rows, 'rows', allow_zero=True)
    positive_int(width, 'width')
    if width & (width - 1):
        raise ValueError('Butterfly accounting requires a power-of-two width')
    return dict(scalar_flops=rows * width * (width.bit_length() - 1 + 1),
                notes='N log2(N) butterfly add/subtract plus N output scale multiplies per row; CUDA sign/shuffle instructions not inferred.')


def simulated_quantization(elements: int, group_size: int, precision: str) -> dict:
    positive_int(elements, 'elements', allow_zero=True)
    positive_int(group_size, 'group_size')
    if precision not in ('FP4', 'FP8') or elements % group_size:
        raise ValueError('Quantization requires FP4/FP8 and complete scale groups')
    groups = elements // group_size
    return dict(scalar_flops=2 * elements + groups,
                special_ops={'abs': elements, 'amax_compare': groups * (group_size - 1),
                             'scale_floor_compare': groups, 'clamp_bound_compare': 2 * elements,
                             'power_of_two_scale_bit_round': groups,
                             precision.lower() + '_encode': elements,
                             precision.lower() + '_decode': elements},
                notes='FP32 divide, quantized encode/decode, rescale multiply; one amax scale multiply per group. Bitwise exponent rounding, comparisons and format conversions are separate.')
