#!/usr/bin/env python3
"""实验 7-2：超节点之间的扩展效率。

扩大一个超节点和连接多个超节点，哪种方案先受到限制？
复用第 6 章的拓扑口径与同一层模型，分别计算：
  - 固定任务（strong scaling）：总工作量不变，设备增多；
  - 随设备扩大的任务（weak scaling）：每设备工作量不变。
按跨超节点字节、同步轮次与割集求步时下界，再判断哪些并行维度应留在超节点内部。

工作量由 `calculations/calc.py forward` 现场生成；割集与轮次沿用第 6 章的
声明模型（环形 all-reduce 每 rank 收发 2(P−1)/P×S）。
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

SUPERNODE_SIZES = [8, 16, 32, 64]        # 单个超节点内的设备数
SUPERNODE_COUNTS = [1, 2, 4, 8]          # 超节点数量
INTRA_BW, INTRA_ALPHA = 450e9, 3e-6      # 超节点内
INTER_BW, INTER_ALPHA = 50e9, 8e-6       # 超节点之间
CUT_LINKS = 4                            # 每个超节点到外部的上行链路数（声明输入）
PEAK = 989.4e12
BANDWIDTH = 3.35e12
LAYERS = 36
HIDDEN = 4096
ACT_BYTES = 2


def work(tokens):
    path = os.path.join(RESULTS, 'work-t%d.json' % tokens)
    proc = subprocess.run([sys.executable, CALC, 'forward', '--model', 'qwen3-8b',
                           '--batch', '1', '--tokens', str(tokens), '--history', '0',
                           '--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：\n' + proc.stderr[-600:])
    s = json.load(open(path))['summary']
    return s['matrix_flops'], (s['weight_read_once_per_operator_bytes'] +
                               s['kv_new_write_bytes'])


def step_bound(flops, traffic, tokens, devices, supernodes, per_node):
    """每层一次 all-reduce；跨超节点部分受割集限制。"""
    compute = flops / devices / PEAK
    memory = traffic / devices / BANDWIDTH
    payload = tokens * HIDDEN * ACT_BYTES
    intra_bytes = 2 * (per_node - 1) / per_node * payload if per_node > 1 else 0
    intra = LAYERS * (INTRA_ALPHA + intra_bytes / INTRA_BW) if per_node > 1 else 0.0
    if supernodes > 1:
        inter_bytes = 2 * (supernodes - 1) / supernodes * payload
        cut_bw = CUT_LINKS * INTER_BW
        inter = LAYERS * (INTER_ALPHA + inter_bytes / cut_bw)
    else:
        inter = 0.0
    return dict(devices=devices, supernodes=supernodes, per_node=per_node,
                compute_seconds=compute, memory_seconds=memory,
                intra_seconds=intra, inter_seconds=inter,
                lower_bound_seconds=max(compute, memory, intra + inter),
                dominant=max((('计算', compute), ('访存', memory),
                              ('超节点内通信', intra), ('跨超节点通信', inter)),
                             key=lambda kv: kv[1])[0])


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    fixed_flops, fixed_traffic = work(8192)
    rows_strong, rows_weak = [], []
    for per_node in SUPERNODE_SIZES:
        for count in SUPERNODE_COUNTS:
            devices = per_node * count
            rows_strong.append(dict(mode='固定任务', tokens=8192,
                                    **step_bound(fixed_flops, fixed_traffic, 8192,
                                                 devices, count, per_node)))
            tokens = 1024 * devices
            wf, wt = work(min(tokens, 32768))
            scale = tokens / min(tokens, 32768)
            rows_weak.append(dict(mode='随设备扩大', tokens=tokens,
                                  **step_bound(wf * scale, wt * scale, tokens,
                                               devices, count, per_node)))

    result = dict(schema_version=1, experiment='7-2', title='超节点之间的扩展效率',
                  intra=dict(bandwidth=INTRA_BW, alpha=INTRA_ALPHA),
                  inter=dict(bandwidth=INTER_BW, alpha=INTER_ALPHA, cut_links=CUT_LINKS),
                  strong=rows_strong, weak=rows_weak,
                  source_note='工作量由 calculations/calc.py forward 现场生成；'
                              '互联与割集是声明输入。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'scaling.json'), 'w'), indent=2, ensure_ascii=False)

    def table(rows, title):
        out = ['', '## ' + title, '',
               '| 每超节点设备 | 超节点数 | 总设备 | 计算 | 访存 | 节点内通信 | 跨节点通信 | 步时下界 | 主导 |',
               '| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
        for r in rows:
            out.append('| %d | %d | %d | %.2f ms | %.2f ms | %.2f ms | %.2f ms | %.2f ms | **%s** |' % (
                r['per_node'], r['supernodes'], r['devices'],
                r['compute_seconds'] * 1e3, r['memory_seconds'] * 1e3,
                r['intra_seconds'] * 1e3, r['inter_seconds'] * 1e3,
                r['lower_bound_seconds'] * 1e3, r['dominant']))
        return out

    lines = ['# 实验 7-2 结果：超节点之间的扩展效率', '',
             '超节点内 %.0f GB/s／α=%.0f μs；跨超节点 %.0f GB/s×%d 条上行／α=%.0f μs。' % (
                 INTRA_BW / 1e9, INTRA_ALPHA * 1e6, INTER_BW / 1e9, CUT_LINKS,
                 INTER_ALPHA * 1e6)]
    lines += table(rows_strong, '固定任务（8192-token prefill）')
    lines += table(rows_weak, '随设备扩大的任务（每设备 1024 token）')
    lines.append('')
    open(os.path.join(RESULTS, 'scaling.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
