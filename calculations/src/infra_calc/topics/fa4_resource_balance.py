"""Reproduce FA4 Table 1 and independent supply changes, using exact cycles."""
from fractions import Fraction
import hashlib
import json
from ..paths import PROJECT

ROOT = PROJECT


def inputs():
    record = json.loads((ROOT / 'configs/fa4-resource-inputs.json').read_text())
    for source in record['sources']:
        if hashlib.sha256((ROOT / source['file']).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Pinned FA4/config input changed: ' + source['file'])
    config = json.loads((ROOT / record['sources'][2]['file']).read_text())
    if config['head_dim'] != 128 or config['model_type'] != 'qwen3':
        raise ValueError('This audited example requires the pinned Qwen3 head width')
    return record, config


def exact(number):
    return {'numerator': number.numerator, 'denominator': number.denominator}


def tile(m, n, d, matrix_multiplier=1, exp_multiplier=1, smem_multiplier=1):
    """Rectangular tiles only; never count a partially masked diagonal as dense."""
    for value in (m, n, d):
        if type(value) is not int or value <= 0 or value % 128:
            raise ValueError('Paper comparison requires positive multiples of 128')
    for value in (matrix_multiplier, exp_multiplier, smem_multiplier):
        if type(value) is not int or value <= 0:
            raise ValueError('Supply multipliers must be positive integers')
    record, config = inputs()
    if d != config['head_dim']:
        raise ValueError('Head width must match the selected real Qwen3 config')
    rates = record['rates']
    # QK: each 128x128 output tile consumes both Q and K from SMEM.
    qk_instructions = (m // 128) * (n // 128)
    qk_smem = qk_instructions * (128 * d + 128 * d) * 2
    # PV: P comes from TMEM; each 128x128 output tile reads N x128 V.
    pv_instructions = (m // 128) * (d // 128)
    pv_smem = pv_instructions * n * 128 * 2
    work = {'matrix_flops': 4 * m * n * d,
            'smem_read_bytes': qk_smem + pv_smem, 'exp_results': m * n}
    cycles = {'matrix': Fraction(work['matrix_flops'], rates['bf16_matrix_flops_per_sm_cycle'] * matrix_multiplier),
              'smem': Fraction(work['smem_read_bytes'], rates['smem_read_bytes_per_sm_cycle'] * smem_multiplier),
              'exp': Fraction(work['exp_results'], rates['exponential_results_per_sm_cycle'] * exp_multiplier)}
    bound = max(cycles.values())
    return dict(shape={'M':m, 'N':n, 'd':d}, multipliers={'matrix':matrix_multiplier,'exp':exp_multiplier,'smem':smem_multiplier},
                matrices=[{'name':'QK','left':[m,d],'right':[d,n],'output':[m,n],'flops':2*m*n*d},
                          {'name':'PV','left':[m,n],'right':[n,d],'output':[m,d],'flops':2*m*n*d}],
                mma_output_tiles={'QK':qk_instructions,'PV':pv_instructions},
                interface_bytes={'qk_smem_read':qk_smem,'pv_smem_read':pv_smem,
                                 'unique_qkv_input_payload':2*(m*d+2*n*d),
                                 'measured_hbm':None}, work=work,
                cycles={key:exact(value) for key,value in cycles.items()},
                accounted_steady_state_bound_cycles=exact(bound),
                tied_limiting_resources=[key for key,value in cycles.items() if value == bound],
                complete_softmax_cycles=None, measured_kernel_cycles=None)


def calculate():
    record, config = inputs()
    scenarios = []
    for m,n in ((128,128),(256,128),(128,256),(256,256)):
        baseline = tile(m,n,config['head_dim'])
        base = Fraction(**baseline['accounted_steady_state_bound_cycles'])
        for name, multipliers in [('paper-baseline',(1,1,1)),('matrix-double',(2,1,1)),
                                  ('matrix-exp-double',(2,2,1)),('all-three-double',(2,2,2))]:
            row = tile(m,n,config['head_dim'],*multipliers)
            row['id'] = f'm{m}-n{n}-{name}'
            row['accounted_bound_ratio_to_baseline'] = exact(Fraction(**row['accounted_steady_state_bound_cycles'])/base)
            scenarios.append(row)
    return dict(calculation='fa4-single-sm-resource-balance',sources=record,scenarios=scenarios,
                assumptions=['BF16 dense rectangular QK/PV tiles; no projections or causal masking/padding claim.',
                             'Matrix rate is a paper analytical input, not an independently selected whole-device precision peak.',
                             'SMEM reads count repeated MMA operands; unique Q/K/V bytes cannot replace them. P is consumed from TMEM.',
                             'max(resource work/rate) assumes ideal overlap for a steady-state resource bound; not the serial QK-softmax-PV latency.',
                             'Exp is only part of softmax. Reductions, scaling, TMEM traffic, correction, scheduling and synchronization are not assigned zero cost.',
                             'Multipliers are hypothetical supply changes, not other GPU specifications. No measured throughput or kernel speedup is inferred.'])


def markdown(result):
    lines = ["# FA4单SM注意力资源配比", "", "固定Qwen3-8B head_dim=128，采用论文B200分析输入。周期是三项稳态资源下界，不是完整kernel时延。", "",
             "| 场景 | 矩阵周期 | SMEM周期 | 指数周期 | 下界周期 | 限制资源 |",
             "|---|---:|---:|---:|---:|---|"]
    for row in result['scenarios']:
        values = [str(Fraction(**row['cycles'][k])) for k in ('matrix','smem','exp')]
        bound = str(Fraction(**row['accounted_steady_state_bound_cycles']))
        lines.append('| ' + ' | '.join([row['id'], *values, bound, ', '.join(row['tied_limiting_resources'])]) + ' |')
    lines += ["", "共享内存按MMA输出分块重复读取Q/K/V；PV的P由TMEM提供。唯一QKV输入载荷不能替代SMEM访问计数。", "", "## 口径与限制", ""]
    lines += ['- ' + item for item in result['assumptions']]
    lines += ["", "## 完整形状、字节与来源", "", "```json", json.dumps(result,ensure_ascii=False,indent=2), "```", ""]
    return '\n'.join(lines)
