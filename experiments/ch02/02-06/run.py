#!/usr/bin/env python3
"""实验 2-6：从 Qwen3.6 到 V4-Flash 的专家矩阵与负载。

三个模型的专家结构分别算，不互相套公式：
  - Qwen3.6-35B-A3B：256 选 8 ＋ 共享专家（逐专家 gate_up／down 矩阵）；
  - DeepSeek-V4-Flash／Pro：256 选 6 ＋ 共享专家（含 hash 层 router）；
  - Kimi K3：潜空间专家 ＋ 共享 ＋ dense 首层（进阶变体）。

同时改变 batch 与路由集中度，比较：同一专家被多个 token 使用时新增的计算，
与整批专家权重载荷的变化。

本实验不重算：全部由 `calculations/calc.py qwen36-forward|experts|forward`
现场生成。只依赖 Python 3 标准库。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
GiB = 2 ** 30
TFLOP = 10 ** 12


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (' '.join(args), proc.stderr[-800:]))
    return json.load(open(path))


def qwen36_expert_rows(doc):
    """从逐算子账里把 256 个专家和共享专家分开汇总。"""
    routed_flops = routed_weight = 0
    shared_flops = shared_weight = 0
    router_flops = router_weight = 0
    active = set()
    per_expert = {}
    for op in doc['operators']:
        name = op.get('name') or ''
        if not name.startswith('moe.'):
            continue
        r = op['repeats']
        f, w = op['matrix_flops'] * r, op['weight_read_bytes'] * r
        if name.startswith('moe.router'):
            router_flops += f
            router_weight += w
        elif name.startswith('moe.shared'):
            shared_flops += f
            shared_weight += w
        elif name.startswith('moe.expert'):
            idx = name.split('.')[1]
            routed_flops += f
            routed_weight += w
            row = per_expert.setdefault(idx, dict(expert=idx, matrix_flops=0, weight_read_bytes=0))
            row['matrix_flops'] += f
            row['weight_read_bytes'] += w
            if op['matrix_flops'] > 0:
                active.add(idx)
    return dict(routed_matrix_flops=routed_flops, routed_weight_read_bytes=routed_weight,
                shared_matrix_flops=shared_flops, shared_weight_read_bytes=shared_weight,
                router_matrix_flops=router_flops, router_weight_read_bytes=router_weight,
                experts_listed=len(per_expert), experts_with_work=len(active),
                per_expert=sorted(per_expert.values(),
                                  key=lambda r: -r['matrix_flops'])[:8])


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    qwen36 = []
    for label, batch, tokens in [('Qwen3.6 prefill 8192（batch=1）', 1, 8192),
                                 ('Qwen3.6 decode batch=1', 1, 1),
                                 ('Qwen3.6 decode batch=64', 64, 1)]:
        inputs = dict(batch=batch, tokens=tokens, history=0 if tokens > 1 else 8192,
                      output_head='last', chunk_size=64, record_past=False)
        ipath = os.path.join(RESULTS, 'qwen36-input-b%d-t%d.json' % (batch, tokens))
        json.dump(inputs, open(ipath, 'w'), indent=1)
        doc = run(['qwen36-forward', '--inputs', ipath],
                  'qwen36-b%d-t%d.json' % (batch, tokens))
        row = qwen36_expert_rows(doc)
        row.update(label=label, batch=batch, tokens=tokens,
                   total_matrix_flops=doc['summary']['matrix_flops'],
                   total_weight_read_bytes=doc['summary']['weight_read_bytes'],
                   base_text_parameters=doc['summary']['base_text_parameters'])
        qwen36.append(row)

    experts = []
    for model in ('deepseek-v4-flash', 'deepseek-v4-pro', 'kimi-k3'):
        for routing in ('balanced', 'concentrated'):
            for batch in (1, 64):
                doc = run(['experts', '--model', model, '--batch', str(batch),
                           '--routing', routing],
                          'experts-%s-b%d-%s.json' % (model, batch, routing))
                s = doc['summary']
                experts.append(dict(model=model, batch=batch, routing=routing,
                                    summary=s))

    result = dict(schema_version=1, experiment='2-6',
                  title='从 Qwen3.6 到 V4-Flash 的专家矩阵与负载',
                  source_note='由 calculations/calc.py 现场生成，本实验不另行实现公式。',
                  qwen36=qwen36, experts=experts, python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'experts.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 2-6 结果：专家矩阵与负载', '',
             '## Qwen3.6-35B-A3B（256 选 8 ＋ 共享专家，40 层）', '',
             '| 场景 | 有工作的专家 | routed TFLOPs | routed 权重读取 | 共享 TFLOPs | 共享权重 | 全模型 TFLOPs |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in qwen36:
        lines.append('| %s | %d／%d | %.4f | %.3f GiB | %.4f | %.3f GiB | %.3f |' % (
            r['label'], r['experts_with_work'], r['experts_listed'],
            r['routed_matrix_flops'] / TFLOP, r['routed_weight_read_bytes'] / GiB,
            r['shared_matrix_flops'] / TFLOP, r['shared_weight_read_bytes'] / GiB,
            r['total_matrix_flops'] / TFLOP))
    lines += ['', '## V4-Flash／V4-Pro／K3 的 FFN 矩阵台账', '',
              '| 模型 | batch | 路由 | FFN TFLOPs | routed | shared | latent | dense 首层 | 每层专家并集 | 批内权重载荷 |',
              '| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in experts:
        s = r['summary']
        lines.append('| %s | %d | %s | %.4f | %.4f | %.4f | %.4f | %.4f | %s | %.2f GiB |' % (
            r['model'], r['batch'], r['routing'],
            s.get('ffn_matrix_flops', 0) / TFLOP,
            s.get('routed_matrix_flops', 0) / TFLOP,
            s.get('shared_matrix_flops', 0) / TFLOP,
            s.get('latent_matrix_flops', 0) / TFLOP,
            s.get('dense_matrix_flops', 0) / TFLOP,
            s.get('expert_union_per_moe_layer', '—'),
            s.get('uniform_matrix_weight_payload_bytes', 0) / GiB))
    lines.append('')
    open(os.path.join(RESULTS, 'experts.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
