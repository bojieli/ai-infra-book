#!/usr/bin/env python3
"""实验 4-7：负载变化与芯片资源分配（进阶推演）。

选 Ampere→Hopper→Blackwell→Rubin 这条线：
  1. 先按“前代代表负载”提出资源分配（用当代能看到的负载算瓶颈）；
  2. 换成大 Transformer、长上下文与稀疏专家三类新负载，重新计算瓶颈；
  3. 选择一次硬件改动，与公开设计对照，说明动机依据、预期收益、代价与最需要的验证。

规格取自统一计算项目的官方硬件表；负载工作量由 calc.py 现场生成。
本实验不重算公式，只做推演与对照。只依赖 Python 3 标准库。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
HARDWARE = os.path.join(ROOT, 'calculations', 'configs', 'hardware.json')
RESULTS = os.path.join(HERE, 'results')
GB = 10 ** 9

GENERATIONS = ['a100-80gb-sxm', 'h100-sxm', 'b200-sxm', 'rubin-nvl72-product-profile']

WORKLOADS = [
    ('前代代表：BERT-large 级 prefill（短序列、密集）', 'qwen3-8b', 1, 512, 0),
    ('新负载 A：大 Transformer prefill（8K）', 'qwen3-8b', 1, 8192, 0),
    ('新负载 B：长上下文 decode（32K 历史、batch 64）', 'qwen3-8b', 64, 1, 32768),
    ('新负载 C：稀疏专家 decode（V4-Flash、batch 64）', 'deepseek-v4-flash', 64, 1, 8192),
]


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ['failed'])[-1]
    return json.load(open(path)), None


def load_generations():
    raw = json.load(open(HARDWARE))
    devs = raw['devices'] if isinstance(raw, dict) and 'devices' in raw else raw
    devs = devs if isinstance(devs, list) else list(devs.values())
    out = []
    for gid in GENERATIONS:
        d = next((x for x in devs if x.get('id') == gid), None)
        if d is None:
            continue
        peaks = d.get('peak_rates') or []
        bf16 = next((p for p in peaks if p['input_precision'] == 'BF16'
                     and p.get('sparsity') == 'dense'), None)
        out.append(dict(id=gid, name=d['name'],
                        capacity_GB=d['memory'].get('nominal_capacity'),
                        bandwidth=d['memory'].get('bandwidth_bytes_per_second'),
                        bf16_dense_tflops=bf16['tera_ops_per_second'] if bf16 else None,
                        power_watts=d.get('power_watts')))
    return out


def work_of(model, batch, tokens, history, tag):
    if model == 'qwen3-8b':
        doc, err = run(['forward', '--model', model, '--batch', str(batch),
                        '--tokens', str(tokens), '--history', str(history)], 'work-%s.json' % tag)
        if doc is None:
            return None, err
        s = doc['summary']
        return dict(matrix_flops=s['matrix_flops'],
                    traffic_bytes=(s['weight_read_once_per_operator_bytes'] +
                                   s['kv_attention_unique_payload_bytes'] + s['kv_new_write_bytes']),
                    scalar_flops=s['scalar_flops'],
                    special_ops=sum(s['special_ops'].values())), None
    doc, err = run(['v4-forward', '--model', model, '--batch', str(batch),
                    '--tokens', str(tokens), '--history', str(history)], 'work-%s.json' % tag)
    if doc is None:
        return None, err
    s = doc['summary']
    return dict(matrix_flops=s['matrix_flops_effective_attention'],
                traffic_bytes=s['uniform_bf16_parameter_bytes'] + s['state_resident_after_bytes'],
                scalar_flops=s['accounted_scalar_flops'],
                special_ops=sum(s['accounted_special_ops'].values())), None


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    gens = load_generations()
    works = []
    for i, (label, model, batch, tokens, history) in enumerate(WORKLOADS):
        wk, err = work_of(model, batch, tokens, history, 'w%d' % i)
        if wk is None:
            sys.exit('工作量调用失败：%s：%s' % (label, err))
        wk.update(label=label, model=model, batch=batch, tokens=tokens, history=history,
                  intensity=wk['matrix_flops'] / wk['traffic_bytes'],
                  scalar_per_matrix=wk['scalar_flops'] / wk['matrix_flops'])
        works.append(wk)

    grid = []
    for g in gens:
        if not g['bf16_dense_tflops'] or not g['bandwidth']:
            for wk in works:
                grid.append(dict(generation=g['id'], workload=wk['label'],
                                 note='官方未记录该代的 BF16 dense 峰值或带宽，跳过'))
            continue
        ridge = g['bf16_dense_tflops'] * 1e12 / g['bandwidth']
        for wk in works:
            c = wk['matrix_flops'] / (g['bf16_dense_tflops'] * 1e12)
            m = wk['traffic_bytes'] / g['bandwidth']
            grid.append(dict(generation=g['id'], generation_name=g['name'],
                             workload=wk['label'], intensity=wk['intensity'], ridge=ridge,
                             compute_seconds=c, memory_seconds=m,
                             lower_bound_seconds=max(c, m),
                             dominant='compute' if c >= m else 'memory'))

    deltas = []
    for a, b in zip(gens, gens[1:]):
        deltas.append(dict(
            frm=a['id'], to=b['id'],
            capacity_ratio=(b['capacity_GB'] / a['capacity_GB']) if a['capacity_GB'] and b['capacity_GB'] else None,
            bandwidth_ratio=(b['bandwidth'] / a['bandwidth']) if a['bandwidth'] and b['bandwidth'] else None,
            bf16_ratio=((b['bf16_dense_tflops'] / a['bf16_dense_tflops'])
                        if a['bf16_dense_tflops'] and b['bf16_dense_tflops'] else None)))

    proposal = dict(
        era_workload='前代代表负载是短序列密集 prefill：算术强度高、状态小，瓶颈在矩阵吞吐。',
        era_allocation='按这一负载提出的分配是：优先加矩阵单元与更高的矩阵峰值精度，'
                       '容量与带宽按比例小幅跟进即可。',
        new_bottlenecks=[
            '大 Transformer prefill 仍是计算受限，原分配继续有效。',
            '长上下文 decode 变成访存受限，且历史读取随 batch×长度线性增长，'
            '矩阵单元再多也不动下界。',
            '稀疏专家 decode 同样访存受限，但瓶颈来自批内专家并集的权重载荷，'
            '而不是历史；同时标量／特殊函数工作显著上升。',
        ],
        chosen_change='把一次硬件改动用在**显存带宽与容量**上（HBM 代际与堆叠数），'
                      '而不是继续按同样比例加矩阵单元。',
        expected_gain='长上下文 decode 与稀疏专家 decode 的资源下界按带宽比例直接下降；'
                      'prefill 不受损失（它不受带宽限制）。',
        cost='HBM 面积、功率与成本上升；封装与散热约束收紧；'
             '若负载重新变回计算受限，这部分投入无法转化为收益。',
        most_needed_validation='在目标负载分布上测出 prefill 与 decode 的实际时间占比：'
                               '若 decode 占比不高，带宽投入的收益会被 Amdahl 限制住。'
                               '其次要测批内专家并集的真实分布（均匀还是集中），'
                               '它决定稀疏专家一侧的载荷究竟有多大。',
        public_comparison='公开设计与这条推演一致的部分：H100→B200→Rubin 的显存带宽比矩阵峰值涨得更早也更快；'
                          'HBM 容量与堆叠数逐代提高；同时新增了更低精度的矩阵格式，'
                          '把“降位宽”作为减少载荷的第二条路径。'
                          '不一致或本推演未覆盖的部分：互联（NVLink 与机架级组织）'
                          '在公开设计里的权重远高于本单卡推演。',
    )

    result = dict(schema_version=1, experiment='4-7', title='负载变化与芯片资源分配',
                  generations=gens, generation_deltas=deltas, workloads=works, grid=grid,
                  proposal=proposal,
                  source_note='规格取自 calculations/configs/hardware.json 的官方记录；'
                              '工作量由 calc.py 现场生成。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'evolution.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 4-7 结果：负载变化与芯片资源分配', '',
             '## 这条演进线的官方规格', '',
             '| 代际 | 名义容量 | 显存带宽 | BF16 dense 峰值 | 官方功率 |',
             '| --- | ---: | ---: | ---: | ---: |']
    for g in gens:
        lines.append('| %s | %s | %s | %s | %s |' % (
            g['name'],
            '%.0f GB' % g['capacity_GB'] if g['capacity_GB'] else '未记录',
            '%.0f GB/s' % (g['bandwidth'] / GB) if g['bandwidth'] else '未记录',
            '%.0f T' % g['bf16_dense_tflops'] if g['bf16_dense_tflops'] else '未记录',
            '%s W' % g['power_watts'] if g['power_watts'] else '未记录'))
    lines += ['', '## 逐代增幅', '',
              '| 代际变化 | 容量 | 带宽 | BF16 dense |', '| --- | ---: | ---: | ---: |']
    for d in deltas:
        lines.append('| %s → %s | %s | %s | %s |' % (
            d['frm'], d['to'],
            '%.2f×' % d['capacity_ratio'] if d['capacity_ratio'] else '—',
            '%.2f×' % d['bandwidth_ratio'] if d['bandwidth_ratio'] else '—',
            '%.2f×' % d['bf16_ratio'] if d['bf16_ratio'] else '—'))
    lines += ['', '## 四类负载的瓶颈', '',
              '| 负载 | 算术强度 | 标量/矩阵 | ' + ' | '.join(
                  g['name'] for g in gens if g['bf16_dense_tflops']) + ' |',
              '| --- | ---: | ---: | ' + ' | '.join(
                  ['---'] * len([g for g in gens if g['bf16_dense_tflops']])) + ' |']
    for wk in works:
        cells = []
        for g in gens:
            if not g['bf16_dense_tflops']:
                continue
            row = next((x for x in grid if x.get('generation') == g['id']
                        and x.get('workload') == wk['label'] and 'lower_bound_seconds' in x), None)
            cells.append('%s %.2f ms' % ('计算' if row['dominant'] == 'compute' else '访存',
                                         row['lower_bound_seconds'] * 1e3) if row else '—')
        lines.append('| %s | %.1f | %.4f | %s |' % (
            wk['label'], wk['intensity'], wk['scalar_per_matrix'], ' | '.join(cells)))
    lines += ['', '## 推演', '',
              '**前代负载与当时的分配**：' + proposal['era_workload'] + proposal['era_allocation'], '',
              '**换成新负载后的瓶颈**：'] + ['- ' + x for x in proposal['new_bottlenecks']]
    lines += ['', '**选择的一次硬件改动**：' + proposal['chosen_change'], '',
              '**预期收益**：' + proposal['expected_gain'], '',
              '**代价**：' + proposal['cost'], '',
              '**最需要的验证**：' + proposal['most_needed_validation'], '',
              '**与公开设计对照**：' + proposal['public_comparison'], '']
    open(os.path.join(RESULTS, 'evolution.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
