#!/usr/bin/env python3
"""实验 6-6：拓扑与割集带宽。

增加交换层还是增加直连链路？给定端口数与流量矩阵，构造两种可行拓扑，
比较任意二分割集带宽、最坏跳数与所需链路数。

两种拓扑（8 个设备、每设备 P 个端口）：
  A. 单层交换：每设备用 1 个端口连到交换机（其余端口空闲）；
  B. 直连网格：设备之间两两直连，端口全部用于直连（P≥7 时为全互连，
     否则按环形加弦构造一个 P-正则图）。

割集带宽用**穷举所有二分**求最小割，不用近似。统一计算项目未覆盖这一
拓扑构造问题，因此本实验独立实现；每一步都可手算核对。

只依赖 Python 3 标准库；同时自绘 SVG。
"""
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results')

DEVICES = 8
PORT_COUNTS = [1, 2, 3, 4, 7]
LINK_BPS = 50e9              # 每条链路单向有效带宽（声明输入）
SWITCH_RADIX = 16            # 交换机端口数
HOP_NS = {'switch': 700, 'direct': 300}   # 声明输入


def ring_with_chords(n, degree):
    """构造一个 degree-正则无向图：环 ＋ 逐步加弦。degree 必须为偶数或 n 为偶数。"""
    edges = set()
    offsets = []
    d = degree
    k = 1
    while d >= 2:
        offsets.append(k)
        d -= 2
        k += 1
    for off in offsets:
        for i in range(n):
            j = (i + off) % n
            if i != j:
                edges.add(tuple(sorted((i, j))))
    if degree % 2 == 1:
        if n % 2:
            raise ValueError('奇数度要求偶数个设备')
        for i in range(n // 2):
            edges.add(tuple(sorted((i, i + n // 2))))
    return sorted(edges)


def min_cut(n, edges, link_bps):
    """穷举所有非平凡二分，返回最小割带宽与该割。"""
    best = None
    for size in range(1, n // 2 + 1):
        for group in itertools.combinations(range(n), size):
            s = set(group)
            crossing = sum(1 for a, b in edges if (a in s) != (b in s))
            bw = crossing * link_bps
            if best is None or bw < best[0]:
                best = (bw, crossing, tuple(sorted(s)))
    return best


def hops(n, edges):
    """最坏情况跳数（BFS 直径）。"""
    adj = {i: set() for i in range(n)}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    worst = 0
    for src in range(n):
        seen = {src: 0}
        queue = [src]
        while queue:
            cur = queue.pop(0)
            for nxt in adj[cur]:
                if nxt not in seen:
                    seen[nxt] = seen[cur] + 1
                    queue.append(nxt)
        if len(seen) < n:
            return None
        worst = max(worst, max(seen.values()))
    return worst


def switch_topology(n, ports):
    """单层交换：每设备 1 条上行链路。割集受上行链路数限制。"""
    uplinks = min(ports, 1) * n
    # 任意二分的割 = 较小一侧的上行链路数（流量必须过交换机）
    min_cross = min(n // 2, n - n // 2)
    return dict(name='单层交换（每设备 1 条上行）', links=n, ports_used_per_device=1,
                switch_ports_used=n, switch_radix=SWITCH_RADIX,
                min_cut_bytes_per_second=min_cross * LINK_BPS,
                min_cut_links=min_cross,
                worst_hops=2, hop_ns=HOP_NS['switch'] * 2,
                note='割集由较小一侧的上行链路数决定；交换机内部按无阻塞假设。')


def direct_topology(n, ports):
    if ports >= n - 1:
        edges = [tuple(sorted((i, j))) for i in range(n) for j in range(i + 1, n)]
        name = '全互连直连（%d 端口）' % ports
    else:
        edges = ring_with_chords(n, ports)
        name = '直连网格（每设备 %d 端口）' % ports
    bw, cross, group = min_cut(n, edges, LINK_BPS)
    d = hops(n, edges)
    return dict(name=name, links=len(edges), ports_used_per_device=ports,
                switch_ports_used=0, switch_radix=None,
                min_cut_bytes_per_second=bw, min_cut_links=cross,
                min_cut_group=list(group),
                worst_hops=d, hop_ns=(HOP_NS['direct'] * d) if d else None,
                note='割集由穷举全部二分求得。')


def svg(path, rows):
    w, h = 880, 420
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
             'font-family="Helvetica,Arial,sans-serif">' % (w, h, w, h),
             '<rect width="%d" height="%d" fill="#ffffff"/>' % (w, h),
             '<text x="30" y="34" font-size="16" font-weight="600">'
             '割集带宽随端口数的变化（8 设备，每链路 50 GB/s）</text>']
    maxbw = max(r['min_cut_bytes_per_second'] for r in rows)
    x0, y0, bw, gap = 90, 90, 46, 26
    for i, r in enumerate(rows):
        y = y0 + i * (bw + gap) // 2
        length = int(r['min_cut_bytes_per_second'] / maxbw * 560)
        color = '#3d5a80' if '交换' in r['name'] else '#c1666b'
        parts.append('<rect x="%d" y="%d" width="%d" height="22" fill="%s" opacity="0.85"/>'
                     % (x0 + 180, y, max(2, length), color))
        parts.append('<text x="%d" y="%d" font-size="12" text-anchor="end" fill="#1d3557">%s</text>'
                     % (x0 + 172, y + 16, r['name']))
        parts.append('<text x="%d" y="%d" font-size="12" fill="#33475b">%.0f GB/s（%d 条链路，最坏 %s 跳）</text>'
                     % (x0 + 190 + max(2, length), y + 16,
                        r['min_cut_bytes_per_second'] / 1e9, r['min_cut_links'],
                        r['worst_hops'] if r['worst_hops'] else '—'))
    parts.append('<text x="30" y="%d" font-size="13" fill="#33475b">'
                 '增加交换层只把割集抬到较小一侧的上行链路数；增加直连链路直接抬高割集，'
                 '但端口数是硬约束。</text>' % (h - 30))
    parts.append('</svg>')
    open(path, 'w').write('\n'.join(parts))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = [switch_topology(DEVICES, 1)]
    for ports in PORT_COUNTS:
        if ports < 2:
            continue
        rows.append(direct_topology(DEVICES, ports))

    # 流量矩阵：全对全（每对设备等量），检查割集是否够用
    per_pair_bps = 16e9
    demand_across_min_cut = (DEVICES // 2) * (DEVICES - DEVICES // 2) * per_pair_bps
    for r in rows:
        r['all_to_all_demand_across_cut_bytes_per_second'] = demand_across_min_cut
        r['cut_sufficient_for_all_to_all'] = r['min_cut_bytes_per_second'] >= demand_across_min_cut
        r['oversubscription'] = demand_across_min_cut / r['min_cut_bytes_per_second']

    result = dict(schema_version=1, experiment='6-6', title='拓扑与割集带宽',
                  devices=DEVICES, link_bytes_per_second=LINK_BPS,
                  switch_radix=SWITCH_RADIX, hop_ns=HOP_NS,
                  traffic=dict(pattern='全对全等量', per_pair_bytes_per_second=per_pair_bps,
                               demand_across_balanced_cut=demand_across_min_cut),
                  topologies=rows,
                  method='割集带宽由穷举全部非平凡二分求最小值；跳数由 BFS 直径求得。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'topology.json'), 'w'), indent=2, ensure_ascii=False)
    svg(os.path.join(RESULTS, 'topology.svg'), rows)

    lines = ['# 实验 6-6 结果：拓扑与割集带宽', '',
             '%d 个设备、每条链路 %.0f GB/s；流量为全对全等量，每对 %.0f GB/s。' % (
                 DEVICES, LINK_BPS / 1e9, per_pair_bps / 1e9), '',
             '| 拓扑 | 每设备端口 | 链路数 | 最小割 | 割上链路 | 最坏跳数 | 单向跳时延 | 够用 | 收敛比 |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | ---: |']
    for r in rows:
        lines.append('| %s | %d | %d | %.0f GB/s | %d | %s | %s | %s | %.2f |' % (
            r['name'], r['ports_used_per_device'], r['links'],
            r['min_cut_bytes_per_second'] / 1e9, r['min_cut_links'],
            r['worst_hops'] if r['worst_hops'] else '—',
            '%.1f μs' % (r['hop_ns'] / 1000) if r['hop_ns'] else '—',
            '是' if r['cut_sufficient_for_all_to_all'] else '否',
            r['oversubscription']))
    lines += ['', '![割集带宽](topology.svg)', '']
    open(os.path.join(RESULTS, 'topology.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
