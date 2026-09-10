#!/usr/bin/env python3
"""实验 1-7：多卡容量与互联限制（第 1 章配套延伸）。

给定一个形状明确的教学模型和两种互联，回答三个问题：
  1. 逐卡驻留：把权重和历史状态切到 P 张卡上，每张卡占多少、放不放得下？
  2. 每步协作：一次 decode 需要在卡之间搬多少字节、搬几次？
  3. 增加卡数和更换互联各能解除什么限制？

第 1 章只做资源收支，不讨论 TP／PP 的实际切法（第 6 章展开）。

只依赖 Python 3 标准库；同时写出一张自绘 SVG 表示每步协作。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results')

GB = 10 ** 9

# 教学模型形状（显式声明；按 12·L·H² 计参数，与 1-2／1-3 的名义 70B 同量级但不是同一个数）
LAYERS = 80
HIDDEN = 8192
PARAMETERS = 12 * LAYERS * HIDDEN ** 2
WEIGHT_BYTES_PER_PARAM = 1          # 8 bit 存储
ACT_BYTES = 2                       # BF16 激活
KV_BYTES_PER_TOKEN = 2 * LAYERS * 8 * 128 * 2   # 8 个 KV 头、head_dim 128、K 和 V、BF16

# 单卡资源卡（H100 SXM 标称）
CARD_CAPACITY = 80 * GB
CARD_BANDWIDTH = 3.35e12
CARD_FLOPS = 989.4e12

LINKS = [
    dict(name='scale-out 400 Gb/s', bytes_per_second=50e9, latency_seconds=5e-6),
    dict(name='scale-up 900 GB/s', bytes_per_second=900e9, latency_seconds=0.6e-6),
]

CARD_COUNTS = [1, 2, 4, 8, 16, 32]
BATCH = 32
HISTORY_TOKENS = 8192


def residency(cards):
    """逐卡驻留：权重按卡均分，KV 也按卡均分（第 6 章再讨论真实切法）。"""
    weights = PARAMETERS * WEIGHT_BYTES_PER_PARAM
    kv = BATCH * HISTORY_TOKENS * KV_BYTES_PER_TOKEN
    per_card = weights / cards + kv / cards
    return dict(cards=cards, total_weight_bytes=weights, total_kv_bytes=kv,
                per_card_weight_bytes=weights / cards, per_card_kv_bytes=kv / cards,
                per_card_bytes=per_card, per_card_GB=per_card / GB,
                capacity_bytes=CARD_CAPACITY, fits=per_card <= CARD_CAPACITY,
                headroom_GB=(CARD_CAPACITY - per_card) / GB)


def collaboration(cards):
    """每步协作：每层一次 all-reduce，环形算法每卡收发 2(P-1)/P × S 字节。"""
    if cards == 1:
        return dict(cards=1, exchanges_per_step=0, bytes_per_card_per_step=0,
                    payload_per_exchange_bytes=0)
    payload = BATCH * HIDDEN * ACT_BYTES        # 一次交换的张量大小
    per_exchange = 2 * (cards - 1) / cards * payload
    return dict(cards=cards, exchanges_per_step=LAYERS,
                payload_per_exchange_bytes=payload,
                bytes_per_card_per_exchange=per_exchange,
                bytes_per_card_per_step=LAYERS * per_exchange)


def step_time(cards, link):
    """一步 decode 的三项时间：本卡读取、本卡计算、卡间协作。"""
    res = residency(cards)
    col = collaboration(cards)
    read_seconds = (res['per_card_weight_bytes'] + res['per_card_kv_bytes']) / CARD_BANDWIDTH
    compute_seconds = 2 * PARAMETERS * BATCH / cards / CARD_FLOPS
    if cards == 1:
        comm_seconds = 0.0
    else:
        comm_seconds = LAYERS * (link['latency_seconds'] +
                                 col['bytes_per_card_per_exchange'] / link['bytes_per_second'])
    return dict(cards=cards, link=link['name'],
                read_seconds=read_seconds, compute_seconds=compute_seconds,
                comm_seconds=comm_seconds,
                overlapped_lower_bound_seconds=max(read_seconds, compute_seconds, comm_seconds),
                serial_comm_seconds=max(read_seconds, compute_seconds) + comm_seconds,
                dominant=max((('读取', read_seconds), ('计算', compute_seconds),
                              ('协作', comm_seconds)), key=lambda kv: kv[1])[0],
                fits=residency(cards)['fits'])


def write_svg(path, rows):
    """自绘每步协作示意：P 张卡、每层一次交换、标出必要数据量。"""
    cards = 4
    w, h = 860, 330
    x0, gap, bw, bh = 60, 190, 140, 76
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Helvetica,Arial,sans-serif">' % (w, h, w, h),
             '<rect width="%d" height="%d" fill="#ffffff"/>' % (w, h),
             '<text x="30" y="34" font-size="17" font-weight="600">一步 decode 的卡间协作（P=4，每层一次 all-reduce）</text>']
    for i in range(cards):
        x = x0 + i * gap
        parts.append('<rect x="%d" y="70" width="%d" height="%d" rx="8" fill="#eef3fb" stroke="#3d5a80" stroke-width="1.5"/>' % (x, bw, bh))
        parts.append('<text x="%d" y="98" font-size="14" text-anchor="middle" font-weight="600">卡 %d</text>' % (x + bw // 2, i))
        parts.append('<text x="%d" y="120" font-size="12" text-anchor="middle" fill="#33475b">权重 %.1f GB</text>' % (x + bw // 2, rows['residency'][2]['per_card_weight_bytes'] / GB))
        parts.append('<text x="%d" y="137" font-size="12" text-anchor="middle" fill="#33475b">KV %.1f GB</text>' % (x + bw // 2, rows['residency'][2]['per_card_kv_bytes'] / GB))
    for i in range(cards - 1):
        x = x0 + i * gap + bw
        parts.append('<line x1="%d" y1="108" x2="%d" y2="108" stroke="#c1666b" stroke-width="2" marker-end="url(#a)"/>' % (x + 4, x + gap - bw - 4))
        parts.append('<line x1="%d" y1="118" x2="%d" y2="118" stroke="#c1666b" stroke-width="2" marker-start="url(#b)"/>' % (x + 4, x + gap - bw - 4))
    parts.append('<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#c1666b"/></marker>'
                 '<marker id="b" markerWidth="8" markerHeight="8" refX="1" refY="3" orient="auto"><path d="M7,0 L0,3 L7,6 Z" fill="#c1666b"/></marker></defs>')
    col = rows['collaboration'][2]
    parts.append('<text x="30" y="185" font-size="13" fill="#33475b">每次交换的张量：batch %d × hidden %d × BF16 = %.2f MB</text>' % (BATCH, HIDDEN, col['payload_per_exchange_bytes'] / 1e6))
    parts.append('<text x="30" y="207" font-size="13" fill="#33475b">环形 all-reduce 每卡收发 2(P−1)/P × S = %.2f MB；一步共 %d 层 → 每卡 %.1f MB</text>' % (
        col['bytes_per_card_per_exchange'] / 1e6, col['exchanges_per_step'], col['bytes_per_card_per_step'] / 1e6))
    y = 245
    for row in rows['step_time']:
        if row['cards'] != 4:
            continue
        parts.append('<text x="30" y="%d" font-size="13" fill="#1d3557">%s：读取 %.2f ms ／ 计算 %.2f ms ／ 协作 %.2f ms → 主导 %s</text>' % (
            y, row['link'], row['read_seconds'] * 1e3, row['compute_seconds'] * 1e3,
            row['comm_seconds'] * 1e3, row['dominant']))
        y += 24
    parts.append('</svg>')
    with open(path, 'w') as fh:
        fh.write('\n'.join(parts))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    res_rows = [residency(p) for p in CARD_COUNTS]
    col_rows = [collaboration(p) for p in CARD_COUNTS]
    time_rows = [step_time(p, link) for p in CARD_COUNTS for link in LINKS]
    result = dict(
        schema_version=1, experiment='1-7', title='多卡容量与互联限制',
        model=dict(layers=LAYERS, hidden=HIDDEN, parameters=PARAMETERS,
                   parameter_formula='12·L·H²',
                   weight_bytes_per_parameter=WEIGHT_BYTES_PER_PARAM,
                   kv_bytes_per_token=KV_BYTES_PER_TOKEN,
                   batch=BATCH, history_tokens=HISTORY_TOKENS,
                   note='形状是显式教学输入，与 1-2／1-3 的名义 70B 同量级但不是同一个数。'),
        card=dict(capacity_bytes=CARD_CAPACITY, bandwidth_bytes_per_second=CARD_BANDWIDTH,
                  peak_flops=CARD_FLOPS, basis='H100 SXM 标称'),
        links=LINKS,
        residency=res_rows, collaboration=col_rows, step_time=time_rows,
        findings=[],
        assumptions=[
            '权重与 KV 按卡数均分是容量收支的记账假设，不是可行的切法。真实 TP／PP 的切分粒度、复制份数与不可整除层在第 6 章处理。',
            '每层一次 all-reduce、环形算法每卡收发 2(P−1)/P×S 是声明的通信模型，不是某个集合通信库的实测。',
            '互联速率是单向有效值输入；协议开销、拥塞和拓扑竞争没有计入。',
            '“重叠下界”取三项最大值，“串行协作”取协作不与计算重叠。真实执行介于两者之间，取决于调度。',
            '没有计入工作区、分配器保留、启动与调度等待。这是资源下界，不是延迟预测。',
        ],
        python_version=sys.version,
    )
    write_svg(os.path.join(RESULTS, 'collaboration.svg'), result)
    with open(os.path.join(RESULTS, 'multi-card.json'), 'w') as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
        fh.write('\n')

    lines = ['# 实验 1-7 结果：多卡容量与互联', '',
             '教学模型：%d 层、隐藏维 %d，按 12·L·H² 计 %.1f B 参数；8 bit 权重，batch=%d，历史 %d token。' % (
                 LAYERS, HIDDEN, PARAMETERS / 1e9, BATCH, HISTORY_TOKENS), '',
             '## 逐卡驻留', '',
             '| 卡数 | 每卡权重 | 每卡 KV | 每卡合计 | 80 GB 放得下 | 余量 |',
             '| ---: | ---: | ---: | ---: | :---: | ---: |']
    for row in res_rows:
        lines.append('| %d | %.1f GB | %.1f GB | %.1f GB | %s | %+.1f GB |' % (
            row['cards'], row['per_card_weight_bytes'] / GB, row['per_card_kv_bytes'] / GB,
            row['per_card_GB'], '是' if row['fits'] else '否', row['headroom_GB']))
    lines += ['', '## 每步协作的数据量', '',
              '| 卡数 | 每步交换次数 | 单次张量 | 每卡每次收发 | 每卡每步合计 |',
              '| ---: | ---: | ---: | ---: | ---: |']
    for row in col_rows:
        if row['cards'] == 1:
            lines.append('| 1 | 0 | — | — | 0 |')
        else:
            lines.append('| %d | %d | %.2f MB | %.2f MB | %.1f MB |' % (
                row['cards'], row['exchanges_per_step'], row['payload_per_exchange_bytes'] / 1e6,
                row['bytes_per_card_per_exchange'] / 1e6, row['bytes_per_card_per_step'] / 1e6))
    lines += ['', '## 一步 decode 的三项时间', '',
              '| 卡数 | 互联 | 容量 | 读取 | 计算 | 协作 | 重叠下界 | 主导 |',
              '| ---: | --- | :---: | ---: | ---: | ---: | ---: | --- |']
    for row in time_rows:
        lines.append('| %d | %s | %s | %.2f ms | %.2f ms | %.2f ms | %.2f ms | %s |' % (
            row['cards'], row['link'], '通过' if row['fits'] else '不通过',
            row['read_seconds'] * 1e3, row['compute_seconds'] * 1e3, row['comm_seconds'] * 1e3,
            row['overlapped_lower_bound_seconds'] * 1e3, row['dominant']))
    lines += ['', '![每步协作](collaboration.svg)', '']
    with open(os.path.join(RESULTS, 'multi-card.md'), 'w') as fh:
        fh.write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
