"""Declared Qwen8 non-matrix training reference; preserves original GEMM ledger."""
import math
from collections import Counter

from infra_calc.sources import model_config
from infra_calc.units import positive_int, positive_number
from infra_calc.topics import training_matrix

MODEL = 'qwen3-8b'


def rms_vjp(x, gamma, dy, epsilon=1e-6):
    """FP64 reference for y=gamma*x/rms(x), with shared gamma across rows."""
    width = len(gamma)
    y, dx = [], []
    dgamma = [0.0] * width
    for row, upstream in zip(x, dy):
        r = 1 / math.sqrt(sum(v * v for v in row) / width + epsilon)
        z = [v * r for v in row]
        g = [a * b for a, b in zip(upstream, gamma)]
        a = sum(u * v for u, v in zip(g, z)) / width
        y.append([u * v for u, v in zip(z, gamma)])
        dx.append([r * (u - v * a) for u, v in zip(g, z)])
        for j in range(width):
            dgamma[j] += upstream[j] * z[j]
    return y, dx, dgamma


def swiglu_vjp(gate, up, dy):
    sigmoid = [1 / (1 + math.exp(-x)) for x in gate]
    silu = [x * s for x, s in zip(gate, sigmoid)]
    out = [a * u for a, u in zip(silu, up)]
    dg = [v * u * (s + a * (1 - s)) for v, u, s, a in zip(dy, up, sigmoid, silu)]
    du = [v * a for v, a in zip(dy, silu)]
    return out, dg, du


def softmax_vjp(logits, dy, scale=1):
    scaled = [v * scale for v in logits]
    peak = max(scaled)
    e = [math.exp(v - peak) for v in scaled]
    p = [v / sum(e) for v in e]
    dot = sum(a * b for a, b in zip(dy, p))
    return p, [scale * p[i] * (dy[i] - dot) for i in range(len(p))]


def mean_cross_entropy(logits, targets):
    """Targets describe selected valid rows; excluded rows never enter this call."""
    losses, gradients = [], []
    count = len(targets)
    for row, target in zip(logits, targets):
        peak = max(row)
        e = [math.exp(v - peak) for v in row]
        total = sum(e)
        losses.append(math.log(total) + peak - row[target])
        gradients.append([(v / total - int(i == target)) / count for i, v in enumerate(e)])
    return sum(losses) / count, gradients


def adamw_update(weights, gradients, first_moment, second_moment, step,
                 learning_rate, beta1, beta2, epsilon, weight_decay):
    """Unfused declared AdamW scalar reference, not a GPU implementation."""
    next_weights, next_first, next_second = [], [], []
    correction1, correction2 = 1 - beta1**step, 1 - beta2**step
    complement1, complement2 = 1 - beta1, 1 - beta2
    decay_coefficient = 1 - learning_rate * weight_decay
    for weight, gradient, first, second in zip(weights, gradients, first_moment, second_moment):
        first = beta1 * first + complement1 * gradient
        second = beta2 * second + complement2 * gradient * gradient
        mhat, vhat = first / correction1, second / correction2
        weight = weight * decay_coefficient - learning_rate * mhat / (math.sqrt(vhat) + epsilon)
        next_weights.append(weight)
        next_first.append(first)
        next_second.append(second)
    return next_weights, next_first, next_second


def calculate(batch=1, tokens=128, supervised_tokens=None, head_strategy='dense',
              activation_policy='save_nonlinear', adam_step=1, learning_rate=0.001,
              beta1=0.9, beta2=0.999, epsilon=1e-8, weight_decay=0.01):
    if activation_policy not in ('save_nonlinear', 'recompute_silu'):
        raise ValueError('Only declared nonlinear save/recompute_silu policies are supported')
    for name, value in (('adam step', adam_step), ('batch', batch), ('tokens', tokens)):
        positive_int(value, name)
    for name, value in (('learning rate', learning_rate), ('epsilon', epsilon), ('weight decay', weight_decay)):
        if not (name != 'epsilon' and type(value) in (int, float) and value == 0):
            positive_number(value, name)
    for name, value in (('beta1', beta1), ('beta2', beta2)):
        if not (type(value) in (int, float) and value == 0):
            positive_number(value, name)
        if value >= 1:
            raise ValueError('Adam beta must be below one')
    # Original matrix/states record is untouched and included for review.
    matrices = training_matrix.calculate(MODEL, batch=batch, tokens=tokens,
                                         supervised_tokens=supervised_tokens, head_strategy=head_strategy,
                                         gradient_bytes=4, master_weight_bytes=4)
    c = model_config(MODEL)
    h, f, d, q, k, layers, vocab = (c[key] for key in ('hidden_size', 'intermediate_size', 'head_dim',
                                                       'num_attention_heads', 'num_key_value_heads', 'num_hidden_layers', 'vocab_size'))
    rows = batch * tokens
    supervised = matrices['summary']['loss_tokens']
    head_rows = matrices['summary']['executed_head_rows']
    ops = []

    def op(name, forward, backward, shape, special_forward=None, special_backward=None, note=''):
        ops.append(dict(name=name, shape=shape, forward_scalar_flops=forward, backward_scalar_flops=backward,
                        forward_special_ops=special_forward or {}, backward_special_ops=special_backward or {}, notes=note))

    def norm(name, count, width, copies):
        op(name, copies * count * (4 * width + 1),
           copies * (6 * count * width + (2 * count - 1) * width),
           [copies, count, width], {'rsqrt': copies * count},
           note='dx=6RD; shared dgamma=(2R-1)D per parameter copy. FP32 saved z/r; no cross-layer gamma merge.')

    norm('input_rmsnorm', rows, h, layers)
    norm('post_attention_rmsnorm', rows, h, layers)
    norm('query_rmsnorm', rows * q, d, layers)
    norm('key_rmsnorm', rows * k, d, layers)
    norm('final_rmsnorm', rows, h, 1)
    elements = layers * rows * f
    recompute = activation_policy == 'recompute_silu'
    op('swiglu', 2 * elements, (6 + int(recompute)) * elements,
       [layers, rows, f], {'sigmoid': elements}, {'sigmoid': elements} if recompute else {},
       'Save a/s/u; or save g/u and recompute sigmoid plus a=g*s immediately before backward.')
    attention_rows = layers * batch * q * tokens
    attention_cells = layers * batch * q * tokens * (tokens + 1) // 2
    op('attention_scale_softmax', 4 * attention_cells - attention_rows,
       5 * attention_cells - attention_rows, [layers, batch, q, tokens, 'causal_row_width=1..T'],
       {'exp': attention_cells, 'max_compare': attention_cells - attention_rows},
       note='Backward softmax=4K-1; backward score scale adds K. No gradient through stabilizing max selection.')
    rope_elements = layers * rows * (q + k) * d
    op('rotary_apply', 3 * rope_elements, 3 * rope_elements, [layers, rows, q + k, d],
       note='Fixed rotation and transpose; no learned position parameter.')
    op('rotary_table_per_step', tokens * d // 2, 0, [tokens, d],
       {'sin': tokens * d, 'cos': tokens * d}, note='Shared across batch and layers; fixed inv_freq initialization excluded.')
    op('residual_and_branch_gradient_merges', 2 * layers * rows * h, 5 * layers * rows * h,
       [layers, rows, h], note='Backward: two residual joins, one gate/up input join, two Q/K/V input joins; fork/alias itself is no arithmetic.')
    op('gqa_head_gradient_reduce', 0, 2 * layers * rows * k * d * (q // k - 1),
       [layers, rows, k, q // k, d],
       note='Declared independent per-query-head dK/dV outputs are summed into each KV group; fused grouped contraction may absorb this reduction into its own matrix convention.')
    op('embedding_scatter_add', 0, rows * h, [rows, h],
       note='One additive contribution per token component into a zeroed dense embedding gradient; IDs/collisions/atomics unknown.')
    op('mean_cross_entropy', supervised * (3 * vocab + 2), supervised * (vocab + 1),
       [supervised, vocab], {'exp': supervised * vocab, 'log': supervised, 'max_compare': supervised * (vocab - 1)},
       note='Stable logsumexp plus saved probabilities; mean reduction S operations. Backward only target subtract then V scales per row.')

    # Ordered graph of declared saved nonlinear objects only, not all activations.
    saved = []

    def save(name, elements, layer=None):
        saved.append(dict(name=name, layer=layer, elements=elements, dtype='fp32', bytes=4 * elements))

    for layer in range(layers):
        save('input_norm_z_r', rows * (h + 1), layer)
        save('query_norm_z_r', rows * q * (d + 1), layer)
        save('key_norm_z_r', rows * k * (d + 1), layer)
        save('attention_probabilities', batch * q * tokens * (tokens + 1) // 2, layer)
        save('post_norm_z_r', rows * (h + 1), layer)
        save('swiglu_g_u' if recompute else 'swiglu_a_s_u', (2 if recompute else 3) * rows * f, layer)
    save('final_norm_z_r', rows * (h + 1))
    save('loss_probabilities', supervised * vocab)
    events, live, peak = [], 0, 0

    def event(kind, name, amount):
        nonlocal live, peak
        live += amount
        peak = max(peak, live)
        events.append(dict(event=len(events), kind=kind, object=name, delta_bytes=amount, declared_subset_live_bytes=live))

    for saved_index, item in enumerate(saved):
        item['id'] = f'saved-{saved_index}'
        event('save', item['id'], item['bytes'])
    end_forward_saved = live
    for item in reversed(saved):
        if recompute and item['name'] == 'swiglu_g_u':
            temporary = 2 * rows * f * 4
            event('backward_recompute_allocate', item['id'] + '-s-a', temporary)
            event('backward_recompute_release', item['id'] + '-s-a', -temporary)
        event('backward_last_use_release', item['id'], -item['bytes'])
    if live != 0:
        raise AssertionError('Declared saved lifetime ledger did not drain')

    parameters = matrices['summary']['parameters']
    # Hyperparameter expressions evaluated once per optimizer step, not per weight.
    optimizer = dict(algorithm='unfused dense AdamW declared scalar formula', parameters=parameters,
                     parameter_scalar_flops=14 * parameters, shared_coefficient_scalar_flops=6,
                     special_ops=dict(sqrt=parameters, pow=2), integer_ops=dict(step_index_increment=1),
                     typed_conversions=dict(fp32_master_to_bf16_weights=parameters),
                     interfaces=dict(fp32_gradient_master_m_v_read_bytes=16 * parameters,
                                     fp32_master_m_v_write_bytes=12 * parameters,
                                     bf16_parameter_write_bytes=2 * parameters),
                     constants=dict(step=adam_step, learning_rate=learning_rate, beta1=beta1, beta2=beta2,
                                    epsilon=epsilon, weight_decay=weight_decay))
    norm_elements = layers * rows * (2 * h + (q + k) * d) + rows * h
    data_ops = dict(embedding_gradient_zero_fp32_bytes=vocab * h * 4,
                    embedding_index_reads_int64_bytes=rows * 8,
                    loss_gradient_zero_fp32_bytes=head_rows * vocab * 4,
                    loss_label_reads_int64_bytes=supervised * 8,
                    loss_selected_logits_bf16_read_bytes=supervised * vocab * 2,
                    loss_gradient_scatter_fp32_write_bytes=supervised * vocab * 4,
                    bf16_to_fp32_nonlinear_input_elements=norm_elements + 2 * elements + supervised * vocab,
                    fp32_to_bf16_norm_swiglu_output_elements=norm_elements + elements,
                    compact_hidden_gather_bf16_read_write_bytes=4 * supervised * h if head_strategy == 'compact' else 0,
                    compact_hidden_gradient_zero_fp32_bytes=4 * rows * h if head_strategy == 'compact' else 0,
                    compact_hidden_gradient_scatter_fp32_read_write_bytes=8 * supervised * h if head_strategy == 'compact' else 0)
    forward = sum(x['forward_scalar_flops'] for x in ops)
    backward = sum(x['backward_scalar_flops'] for x in ops)
    update = optimizer['parameter_scalar_flops'] + optimizer['shared_coefficient_scalar_flops']
    special = Counter(optimizer['special_ops'])
    for row in ops:
        special.update(row['forward_special_ops'])
        special.update(row['backward_special_ops'])
    return dict(schema_version=1, calculation='qwen8-training-nonmatrix-reference', model=MODEL,
                scenario=dict(batch=batch, tokens=tokens, supervised_tokens=supervised_tokens,
                              head_strategy=head_strategy, activation_policy=activation_policy, adam_step=adam_step,
                              learning_rate=learning_rate, beta1=beta1, beta2=beta2, epsilon=epsilon, weight_decay=weight_decay),
                sources=matrices['sources'], training_matrix_original=matrices,
                nonmatrix_operations=ops, optimizer=optimizer, data_operations=data_ops,
                saved_objects=saved, lifetime_events=events,
                summary=dict(original_training_matrix_flops=matrices['summary']['training_matrix_flops'],
                             forward_scalar_flops=forward, backward_scalar_flops=backward,
                             optimizer_scalar_flops=update, accounted_special_ops=dict(special),
                             accounted_matrix_plus_scalar_flops=matrices['summary']['training_matrix_flops'] + forward + backward + update,
                             nonlinear_saved_at_forward_end_bytes=end_forward_saved,
                             declared_saved_and_recomputed_subset_peak_bytes=peak,
                             original_parameter_state_bytes=matrices['summary']['unsharded_parameter_state_bytes'],
                             complete_training_step_flops=None, complete_activation_peak_bytes=None,
                             complete_hbm_traffic_bytes=None, predicted_step_seconds=None),
                assumptions=[
                    'Official Qwen3-8B dimensions with declared mathematical backward algorithms; not an assertion about a specific autograd saved-tensor choice, fused optimizer, or kernel instruction sequence.',
                    'Original training_matrix record and parameter-state budget are preserved unchanged. New ordinary scalar operations never multiply or recount its GEMM gradients.',
                    'Nonlinear reference arithmetic and saved tensors are FP32; numerical derivative checks use FP64. BF16 interfaces/master copy are typed operations, not proof of identical BF16 backend rounding or Tensor hardware feasibility.',
                    'Attention counts valid causal cells and a ragged saved-probability reference. Dense masked buffers or FlashAttention recomputation would require a different explicitly expanded execution policy.',
                    'Compact head gradient scatters S selected rows into a newly zeroed full B*T by H FP32 buffer before final-norm backward. Its full-buffer zero write and selected read/write payload are separate; no existing initialized buffer is assumed.',
                    'S valid shifted/masked labels are caller input. Their identities are not fabricated; loss selects S rows, while dense vocabulary head still executes all B*T rows. Gather/scatter are logical contribution counts, not coalescing/atomic traces.',
                    'Every listed saved nonlinear object remains until its explicit backward event. This subset omits GEMM saved inputs/outputs, live gradients, full temporary buffers and allocator workspace; its peak is not model peak or a measured lower bound for every other algorithm.',
                    'Recompute_silu changes only this declared nonlinear subgraph: save g/u, recompute sigmoid and a, retain its two temporaries through that local backward and then release. No full-layer checkpoint is implied.',
                    'Unfused AdamW uses dense FP32 gradient/master/m/v for all parameters, including zero-gradient embedding rows. Bias correction two pow calls and six shared arithmetic operations execute once per step; no foreach/fused backend equivalence claimed.',
                    'Residual/backbone branch merges are declared additive accumulation into already available gradients. Embedding scatter explicitly accumulates into zeroed dense storage; collisions and exact zero-gating behavior require token identities.',
                    'Not included: V4 training, loss-specific branches beyond mean CE, clipping/loss-scaling, gradient accumulation, distributed communication, all casts/copies, scheduler/allocator and complete optimizer initialization. Chapter3 experiment3-6 remains partial.',
                ])


def markdown(result):
    import json

    def cell(x):
        if x is None:
            return 'unknown'
        if isinstance(x, (dict, list)):
            x = json.dumps(x, ensure_ascii=False, sort_keys=True)
        return str(x).replace('|', '\\|')

    def table(headers, rows):
        return ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |',
                *('| ' + ' | '.join(cell(x) for x in row) + ' |' for row in rows)]

    lines = ['# Qwen3-8B 训练非矩阵参考账', '', '## 输入', '']
    lines += table(['字段', '值'], result['scenario'].items())
    lines += ['', '## 汇总', '', '普通算术与矩阵FLOPs可加为已计子账；special、cast、integer和bytes分别列出。完整训练与峰值保留unknown。', '']
    lines += table(['字段', '值'], result['summary'].items())
    lines += ['', '## 非矩阵前向与反向', '']
    lines += table(['算子', '形状', '前向scalar', '反向scalar', '前向special', '反向special', '算法说明'],
                   [[r[k] for k in ('name', 'shape', 'forward_scalar_flops', 'backward_scalar_flops', 'forward_special_ops', 'backward_special_ops', 'notes')] for r in result['nonmatrix_operations']])
    lines += ['', '## AdamW', '']
    lines += table(['字段', '值'], result['optimizer'].items())
    lines += ['', '## Typed与数据操作', '']
    lines += table(['字段（名称标单位）', '值'], result['data_operations'].items())
    lines += ['', '## 声明保存对象', '', '只列本非线性反向算法对象；不包含全部矩阵保存输入、梯度或allocator。', '']
    lines += table(['ID', '对象', '层', '元素', 'dtype', 'bytes'],
                   [[r[k] for k in ('id', 'name', 'layer', 'elements', 'dtype', 'bytes')] for r in result['saved_objects']])
    lines += ['', '## 保存与重算事件', '']
    lines += table(['事件', '动作', '对象', '变化bytes', '子集合存活bytes'],
                   [[r[k] for k in ('event', 'kind', 'object', 'delta_bytes', 'declared_subset_live_bytes')] for r in result['lifetime_events']])
    lines += ['', '## 原矩阵与参数状态（不变）', '']
    old = result['training_matrix_original']
    lines += table(['原summary', '值'], old['summary'].items())
    lines += ['']
    lines += table(['矩阵', '形状', 'repeats', 'forward', 'gradient_each', 'training_total'],
                   [[r[k] for k in ('name', 'shapes', 'repeats', 'forward_flops', 'gradient_each_flops', 'training_matrix_flops')] for r in old['training_matrix_rows']])
    lines += ['', '## 假设与原题剩余', '', *('- ' + x for x in result['assumptions']), '', '## 固定来源', '']
    lines += table(['记录', '值'], enumerate(result['sources']))
    return '\n'.join(lines) + '\n'
