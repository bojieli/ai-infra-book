"""Readable single-head KDA recurrence and block triangular formulation.

Inputs are already normalized q/k, log decay g and sigmoid beta. Small numeric
examples use Python floats; this is not a replacement for a GPU implementation.
"""
import math
from ..units import positive_int


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def recurrent(q, k, v, g, beta, initial):
    state = [row[:] for row in initial]
    outputs = []
    d, dv = len(k[0]), len(v[0])
    for qt, kt, vt, gt, bt in zip(q, k, v, g, beta):
        for i in range(d):
            for j in range(dv):
                state[i][j] *= math.exp(gt[i])
        delta = [bt * (vt[j] - sum(kt[i] * state[i][j] for i in range(d))) for j in range(dv)]
        for i in range(d):
            for j in range(dv):
                state[i][j] += kt[i] * delta[j]
        outputs.append([sum(qt[i] * state[i][j] for i in range(d)) / math.sqrt(d) for j in range(dv)])
    return outputs, state


def chunked(q, k, v, g, beta, initial, chunk_size):
    positive_int(chunk_size, 'chunk_size')
    state, outputs = [row[:] for row in initial], []
    d, dv = len(k[0]), len(v[0])
    for start in range(0, len(q), chunk_size):
        qs, ks, vs, gs, bs = (x[start:start + chunk_size] for x in (q, k, v, g, beta))
        n = len(qs)
        prefix = [[sum(gs[t][a] for t in range(i + 1)) for a in range(d)] for i in range(n)]
        decay = [[math.exp(x) for x in row] for row in prefix]
        w, u = [], []
        # Forward substitution for the unit-lower triangular system (I+L).
        for i in range(n):
            lower = [bs[i] * sum(ks[i][a] * math.exp(prefix[i][a] - prefix[j][a]) * ks[j][a]
                                for a in range(d)) for j in range(i)]
            w.append([bs[i] * decay[i][a] * ks[i][a] - sum(lower[j] * w[j][a] for j in range(i)) for a in range(d)])
            u.append([bs[i] * vs[i][a] - sum(lower[j] * u[j][a] for j in range(i)) for a in range(dv)])
        delta = [[u[i][a] - sum(w[i][b] * state[b][a] for b in range(d)) for a in range(dv)] for i in range(n)]
        for i in range(n):
            aqk = [sum(qs[i][a] / math.sqrt(d) * math.exp(prefix[i][a] - prefix[j][a]) * ks[j][a]
                       for a in range(d)) for j in range(i + 1)]
            outputs.append([sum(qs[i][b] / math.sqrt(d) * decay[i][b] * state[b][a] for b in range(d))
                            + sum(aqk[j] * delta[j][a] for j in range(i + 1)) for a in range(dv)])
        state = [[state[a][b] * decay[-1][a]
                  + sum(math.exp(prefix[-1][a] - prefix[i][a]) * ks[i][a] * delta[i][b] for i in range(n))
                  for b in range(dv)] for a in range(d)]
    return outputs, state


def work(tokens: int, chunk_size: int, key_dim: int, value_dim: int) -> dict:
    """Logical block algorithm, triangular zero terms skipped; FMA=2.

Counts use prefix scan, once-per-row Q scaling and reused exp(prefix). The small
Python validator prioritizes readability and can recompute these expressions.
"""
    for name, value in [('tokens', tokens), ('chunk_size', chunk_size), ('key_dim', key_dim), ('value_dim', value_dim)]:
        positive_int(value, name)
    full, tail = divmod(tokens, chunk_size)
    sizes = [(chunk_size, full)] + ([(tail, 1)] if tail else [])
    rows = []
    for c, count in sizes:
        if not count:
            continue
        lower, causal, d, v = c * (c - 1) // 2, c * (c + 1) // 2, key_dim, value_dim
        stages = dict(lower_kk=2 * lower * d, solve_w_u=2 * lower * (d + v),
                      state_prediction=2 * c * d * v, state_query=2 * c * d * v,
                      causal_qk=2 * causal * d, causal_pv=2 * causal * v, state_update=2 * c * d * v)
        scalar_stages = dict(gate_prefix_scan=(c - 1) * d, query_scale=c * d,
                             prepare_w_u_rhs=2 * c * d + c * v,
                             lower_decay_and_beta=2 * lower * d + lower,
                             causal_query_decay=2 * causal * d, query_prefix_decay=c * d,
                             delta_subtract=c * v, output_add=c * v,
                             state_decay_and_add=2 * d * v, state_update_keys=2 * c * d)
        rows.append(dict(valid_tokens=c, chunks=count, matrix_stages_per_chunk=stages,
                         scalar_stages_per_chunk=scalar_stages,
                         matrix_flops=count * sum(stages.values()),
                         scalar_flops=count * sum(scalar_stages.values()),
                         exp_ops=count * (2 * c + lower + causal + 1) * d))
    return dict(blocks=rows, matrix_flops=sum(row['matrix_flops'] for row in rows),
                scalar_flops=sum(row['scalar_flops'] for row in rows), exp_ops=sum(row['exp_ops'] for row in rows),
                scope='Mathematical unit-lower forward-substitution block algorithm with valid triangular terms. Not the FLOPs of selected FLA fused 16x16 inverse/solve kernels or their padded GEMMs; no numeric-code instruction count claim.')
