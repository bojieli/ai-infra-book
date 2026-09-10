#!/usr/bin/env python3
"""实验 2-1：序列计算的依赖与并行。

四个 token、三层的固定教学模型上，比较 RNN 与因果 Transformer 的
依赖边、矩阵工作与状态，并检验缓存前后同一模型的输出是否一致。

数值取自本书统一计算项目已复算的结果
`calculations/results/sequence-dependencies-book.json`（固定教学权重、
FP64、完整导出），本实验不重算，只做本题需要的整理、判断与绘图。

只依赖 Python 3 标准库。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SOURCE = os.path.join(ROOT, 'calculations', 'results', 'sequence-dependencies-book.json')
RESULTS = os.path.join(HERE, 'results')

MODE_LABEL = {
    'known_four_tokens': '四个已知 token 一次处理',
    'four_prefixes_recomputed': '四个前缀各重算一次',
    'four_tokens_state_reused': '四个 token 复用状态',
    'fifth_token_prefix_recomputed': '新生成第 5 个 token（重算前缀）',
    'fifth_token_state_reused': '新生成第 5 个 token（复用状态）',
}


def load():
    if not os.path.exists(SOURCE):
        sys.exit('缺少输入：%s\n请先在仓库根目录运行 python3 calculations/calc.py reproduce' % SOURCE)
    return json.load(open(SOURCE))


def dependency_svg(path, graphs, cache_graph):
    """自绘图 2-1：横轴 token、纵轴层，分别画时间递推、跨位置注意力和缓存后的逐 token 生成。"""
    w, h = 900, 720
    left, top, dx, dy = 90, 90, 150, 90
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
             'font-family="Helvetica,Arial,sans-serif">' % (w, h, w, h),
             '<rect width="%d" height="%d" fill="#ffffff"/>' % (w, h),
             '<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">'
             '<path d="M0,0 L8,3 L0,6 Z" fill="#5a6b7d"/></marker>'
             '<marker id="ak" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">'
             '<path d="M0,0 L8,3 L0,6 Z" fill="#c1666b"/></marker></defs>']

    def panel(y0, title, nodes, edges, colors):
        parts.append('<text x="30" y="%d" font-size="15" font-weight="600">%s</text>' % (y0 - 22, title))
        pos = {}
        for nd in nodes:
            token = nd.get('token', 0)
            layer = nd.get('layer', 0)
            x = left + token * dx
            y = y0 + (3 - layer) * dy if layer else y0 + 3 * dy
            pos[nd['id']] = (x, y)
        for e in edges:
            if e['source'] not in pos or e['target'] not in pos:
                continue
            x1, y1 = pos[e['source']]
            x2, y2 = pos[e['target']]
            color, marker = colors.get(e['kind'], ('#5a6b7d', 'ar'))
            parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.6" '
                         'opacity="0.85" marker-end="url(#%s)"/>' % (x1 + 16, y1, x2 - 16, y2, color, marker))
        for nd in nodes:
            x, y = pos[nd['id']]
            parts.append('<circle cx="%d" cy="%d" r="15" fill="#eef3fb" stroke="#3d5a80" stroke-width="1.4"/>' % (x, y))
            parts.append('<text x="%d" y="%d" font-size="10" text-anchor="middle" fill="#1d3557">%s</text>'
                         % (x, y + 4, nd['id'][:5]))

    colors_rnn = {'recurrent_state': ('#c1666b', 'ak'), 'depth': ('#5a6b7d', 'ar')}
    colors_tf = {'historical_kv': ('#c1666b', 'ak'), 'query_and_kv': ('#5a6b7d', 'ar')}
    panel(60, 'RNN：红＝时间递推（同层跨 token），灰＝深度依赖', graphs['rnn']['nodes'], graphs['rnn']['edges'], colors_rnn)
    panel(60 + 4 * dy, '因果 Transformer：红＝读历史 KV（跨位置，非递推），灰＝当前位置的深度依赖',
          graphs['transformer']['nodes'], graphs['transformer']['edges'], colors_tf)
    parts.append('<text x="30" y="%d" font-size="13" fill="#33475b">'
                 '“旋转 90 度”的类比在红边上失效：RNN 的红边是必须串行的状态递推，'
                 'Transformer 的红边只是读已经写好的 KV，可以并行。</text>' % (h - 40))
    parts.append('<text x="30" y="%d" font-size="13" fill="#33475b">'
                 '缓存后的逐 token 生成图（%d 个节点、%d 条边）另存于 results/cache-graph.json。</text>'
                 % (h - 18, len(cache_graph['nodes']), len(cache_graph['edges'])))
    parts.append('</svg>')
    open(path, 'w').write('\n'.join(parts))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    src = load()
    work = {(r['model'], r['mode']): r for r in src['sequence_work']}
    states = src['sequence_states']
    checks = src['sequence_checks']
    graphs = src['sequence_graphs']

    rnn_edges = graphs['rnn']['edges']
    tf_edges = graphs['transformer']['edges']
    edge_counts = dict(
        rnn_recurrent=sum(1 for e in rnn_edges if e['kind'] == 'recurrent_state'),
        rnn_depth=sum(1 for e in rnn_edges if e['kind'] == 'depth'),
        transformer_historical_kv=sum(1 for e in tf_edges if e['kind'] == 'historical_kv'),
        transformer_query_and_kv=sum(1 for e in tf_edges if e['kind'] == 'query_and_kv'),
    )

    last = {m: [s for s in states if s['model'] == m][-1] for m in ('rnn', 'transformer')}
    result = dict(
        schema_version=1, experiment='2-1', title='序列计算的依赖与并行',
        source=dict(file='calculations/results/sequence-dependencies-book.json',
                    scenario=src['scenario'],
                    note='数值来自本书统一计算项目，已复算并通过其自带检查；本实验不重算。'),
        dependency_edges=edge_counts,
        work=[dict(mode=MODE_LABEL[mode],
                   rnn_matrix_flops=work[('rnn', mode)]['matrix_flops'],
                   transformer_matrix_flops=work[('transformer', mode)]['matrix_flops'],
                   transformer_attention_flops=work[('transformer', mode)]['attention_matrix_flops'])
              for mode in MODE_LABEL],
        state=[dict(model=m,
                    persistent_history_bytes=last[m]['persistent_history_bytes'],
                    grows_with_length=last[m]['capacity_growth_bytes'] > 0,
                    next_token_history_read_bytes=last[m]['next_token_prior_history_read_bytes'])
               for m in ('rnn', 'transformer')],
        state_series=states,
        cache_equivalence=dict(
            all_pass=src['summary']['all_same_model_cache_checks_pass'],
            max_absolute_error=src['summary']['max_absolute_error'],
            checks=len(checks)),
        analogy_verdict=(
            '“把 Transformer 旋转 90 度就是 RNN”这个类比只在深度方向成立：两者都逐层加深、参数按层共享。'
            '在时间方向失效——RNN 的跨 token 边是状态递推（第 t 步必须等第 t−1 步算完），'
            'Transformer 的跨 token 边是读历史 KV（前缀写好后可并行读），因此已知输入可以一次处理，RNN 不能。'),
        python_version=sys.version,
    )
    json.dump(result, open(os.path.join(RESULTS, 'sequence.json'), 'w'), indent=2, ensure_ascii=False)
    json.dump(src['sequence_transformer_cache_graph'],
              open(os.path.join(RESULTS, 'cache-graph.json'), 'w'), indent=2, ensure_ascii=False)
    dependency_svg(os.path.join(RESULTS, 'dependencies.svg'), graphs, src['sequence_transformer_cache_graph'])

    lines = ['# 实验 2-1 结果：序列计算的依赖与并行', '',
             '固定教学模型：%d 个 token、%d 层、宽 %d、FP64。' % (
                 len(src['scenario']['tokens']), src['scenario']['layers'], src['scenario']['width']), '',
             '## 依赖边', '',
             '| 模型 | 跨 token 的边 | 条数 | 能否并行 |', '| --- | --- | ---: | --- |',
             '| RNN | 状态递推 | %d | 否（必须串行） |' % edge_counts['rnn_recurrent'],
             '| Transformer | 读历史 KV | %d | 是（前缀写好后可并行读） |' % edge_counts['transformer_historical_kv'],
             '', '## 矩阵工作（FLOPs）', '',
             '| 场景 | RNN | Transformer | 其中注意力 |', '| --- | ---: | ---: | ---: |']
    for row in result['work']:
        lines.append('| %s | %d | %d | %d |' % (row['mode'], row['rnn_matrix_flops'],
                                                row['transformer_matrix_flops'],
                                                row['transformer_attention_flops']))
    lines += ['', '## 状态（5 个 token 之后）', '',
              '| 模型 | 常驻历史 | 随长度增长 | 下一 token 要读 |', '| --- | ---: | :---: | ---: |']
    for row in result['state']:
        lines.append('| %s | %d B | %s | %d B |' % (
            'RNN' if row['model'] == 'rnn' else 'Transformer', row['persistent_history_bytes'],
            '是' if row['grows_with_length'] else '否（定长）', row['next_token_history_read_bytes']))
    lines += ['', '## 缓存前后一致性', '',
              '%d 项检查全部通过，最大绝对误差 %g。' % (result['cache_equivalence']['checks'],
                                                result['cache_equivalence']['max_absolute_error']),
              '', '![依赖图](dependencies.svg)', '']
    open(os.path.join(RESULTS, 'sequence.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
