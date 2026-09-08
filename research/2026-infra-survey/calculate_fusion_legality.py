#!/usr/bin/env python3
"""Independent teaching arithmetic; does not import or execute RedFuser/GPU code."""
from fractions import Fraction as F
from pathlib import Path
import json
import math
import random
import struct
import hashlib
import sympy as sp


def summarize(scores, values):
    valid = [(s, v) for s, v in zip(scores, values) if s != -math.inf]
    if not valid:
        return None  # Empty/masked segment is neutral, not exp(-inf - -inf).
    maximum = max(s for s, _ in valid)
    weights = [math.exp(s - maximum) for s, _ in valid]
    return (maximum, math.fsum(weights),
            [math.fsum(w * v[j] for w, (_, v) in zip(weights, valid))
             for j in range(len(valid[0][1]))])


def merge(a, b):
    if a is None:
        return b
    if b is None:
        return a
    maximum = max(a[0], b[0])
    ra, rb = math.exp(a[0] - maximum), math.exp(b[0] - maximum)
    return maximum, ra * a[1] + rb * b[1], [ra * x + rb * y for x, y in zip(a[2], b[2])]


def e4m3fn_grid():
    """Positive finite encodings, including zero; exact ONNX E4M3FN values."""
    values = []
    for code in range(127):  # 0x7f is NaN.
        exponent, fraction = divmod(code, 8)
        value = F(fraction, 512) if exponent == 0 else F(2) ** (exponent - 7) * (1 + F(fraction, 8))
        values.append((code, value))
    return values


def quantize(x):
    """Finite saturation and round-to-nearest, ties-to-even. No NaN policy claim."""
    sign = -1 if x < 0 else 1
    x = abs(F(x))
    _, value = min(e4m3fn_grid(), key=lambda cv: (abs(cv[1] - x), cv[0] % 2))
    return sign * value


def quantized_dot(values, weights, block):
    """Prefix-amax online scheme with exact arithmetic outside the FP8 cast."""
    maximum, partial = F(0), F(0)
    for offset in range(0, len(values), block):
        a = values[offset:offset + block]
        w = weights[offset:offset + block]
        updated = max(maximum, max(abs(v) for v in a))
        if updated == 0:
            continue  # Teaching policy, not a claim about the source's zero guard.
        partial *= maximum / updated
        partial += sum(quantize(F(448) * x / updated) * y for x, y in zip(a, w))
        maximum = updated
    return partial * maximum / 448


def calculate():
    x, m, z = sp.symbols('x m z', real=True)
    f = sp.exp(x - m) / z
    identity = sp.simplify(f - f.subs({m: 0, z: 1}) * f.subs(x, 0))
    assert identity == 0  # For finite inputs and nonzero z; real arithmetic.
    rng = random.Random(20260908)
    checked = 0
    for size in [1, 3, 17, 65]:
        scores = [rng.uniform(-50, 50) for _ in range(size)]
        values = [[rng.uniform(-4, 4) for _ in range(3)] for _ in scores]
        for block in [1, 2, 8, 32]:
            states = [summarize(scores[i:i + block], values[i:i + block]) for i in range(0, size, block)]
            for reverse in [False, True]:
                state = None
                for part in states[::-1] if reverse else states:
                    state = merge(state, part)
                reference = summarize(scores, values)
                assert all(math.isclose(a / state[1], b / reference[1], rel_tol=1e-12, abs_tol=1e-12)
                           for a, b in zip(state[2], reference[2]))
                checked += 1
    left = summarize([0, math.log(2)], [[1], [3]])
    right = summarize([math.log(4)], [[-2]])
    result = merge(left, right)
    assert math.isclose(result[2][0] / result[1], -1 / 7, abs_tol=1e-15)
    assert merge(left, summarize([-math.inf], [[999]])) == left

    # H(local)=0 has already erased the unscaled sum. Replacing its inverse cannot restore it.
    xs, ys = [1, -1, 1], [1, 1, 1]
    local_m = [sum(xs[:2]), sum(xs[2:])]
    local_outputs = [local_m[0] * sum(ys[:2]), local_m[1] * sum(ys[2:])]
    global_m = sum(xs)
    patched = sum(F(o) / (m if m else 1) * (global_m if global_m else 1)
                  for o, m in zip(local_outputs, local_m))
    expected = global_m * sum(ys)
    assert patched == 1 and expected == 3

    grid = e4m3fn_grid()
    assert len(grid) == 127 and grid[-1][1] == 448 and grid[1][1] == F(1, 512)
    assert all(quantize(value) == value and quantize(-value) == -value for _, value in grid)
    assert quantize(F(224, 5)) == 44 and quantize(46) == 48 and quantize(42) == 40
    # Two 128-wide K tiles; only the first weight is nonzero.
    a = [F(0)] * 256; a[0] = F(1); a[128] = F(10)
    w = [F(0)] * 256; w[0] = F(1)
    global_quant = quantized_dot(a, w, 256)
    prefix_quant = quantized_dot(a, w, 128)
    assert global_quant == F(55, 56) and prefix_quant == 1
    assert quantized_dot(a[128:] + a[:128], w[128:] + w[:128], 128) == global_quant
    rounded_outputs = [struct.unpack('e', struct.pack('e', float(v)))[0] for v in [global_quant, prefix_quant]]
    assert rounded_outputs[0] != rounded_outputs[1]

    # Qwen3-235B expert single projection, teaching M=4096; explicit 128x128 output tiles.
    config_path = Path(__file__).resolve().parents[2] / 'references/outline-checks/2026-09-07/scaling-history/qwen3-235b-config.json'
    config = json.loads(config_path.read_text())
    M, N, K, bm, bn = 4096, config['moe_intermediate_size'], config['hidden_size'], 128, 128
    assert (N, K) == (1536, 4096)
    a_bytes, aq_bytes, w_bytes, o_bytes = 2 * M * K, M * K, N * K, 2 * M * N
    mt, nt = M // bm, N // bn
    materialized = a_bytes + aq_bytes + aq_bytes * nt + w_bytes * mt + o_bytes
    fused_same_scale = a_bytes + a_bytes * nt + w_bytes * mt + o_bytes
    fused_prefix_scale = a_bytes * nt + w_bytes * mt + o_bytes
    assert [v // 2**20 for v in [materialized, fused_same_scale, fused_prefix_scale]] == [444, 620, 588]
    return dict(
        scope='Independent real/FP64 and finite E4M3FN teaching calculations, not a framework or GPU reproduction.',
        softmax=dict(symbolic_identity=True, finite_nonzero_denominator_required=True, checked_cases=checked,
                     two_segment_result='-1/7', masked_segment_neutral=True),
        noninvertible=dict(xs=xs, ys=ys, local_m=local_m, local_outputs=local_outputs,
                           original=expected, replace_zero_by_identity_merge=int(patched)),
        fp8=dict(format='E4M3FN', rounding='nearest ties-even, finite saturation',
                 input_nonzero={'0':1,'128':10}, weights_nonzero={'0':1}, K=256,
                 global_scale_result=str(global_quant), prefix_scale_result=str(prefix_quant),
                 difference=str(prefix_quant-global_quant), fp16_outputs=rounded_outputs,
                 reversed_tiles_match_global=True, positive_finite_encodings_checked=len(grid)),
        traffic=dict(config_file=str(config_path.relative_to(Path(__file__).resolve().parents[2])),
                     config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),
                     M=M,N=N,K=K,bm=bm,bn=bn,m_tiles=mt,n_tiles=nt,matrix_flops=2*M*N*K,
                     activation_bytes=a_bytes,quantized_activation_bytes=aq_bytes,
                     weight_bytes=w_bytes,output_bytes=o_bytes,
                     materialized_bytes=materialized,fused_same_scale_bytes=fused_same_scale,
                     fused_prefix_scale_bytes=fused_prefix_scale,
                     limits='Main tensor payload at an interface without cross-output-tile reuse; scale/metadata traffic and hardware caches excluded. Quantizer retains one complete input row. Prefix scale changes rounding semantics.'))


if __name__ == '__main__':
    report = calculate()
    Path(__file__).with_name('fusion-legality-arithmetic.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
