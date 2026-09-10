#!/usr/bin/env python3
"""实验 1-2：把资源卡变成可用的数字。

独立可运行，只依赖 Python 3 标准库。三件事分开算：
  1. 教学 70B 模型在两种存储位宽下的纯权重字节，以及能否放进给定显存；
  2. 400 Gb/s 链路的字节速率；
  3. 给定载荷的传输时间，并标明每个结果用的是容量、带宽还是延迟。

十进制 GB=10^9、二进制 GiB=2^30 全程分开，不混用。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results')

GB = 10 ** 9
GiB = 2 ** 30

# 教学输入（第 1 章正文固定）
PARAMETERS = 70_000_000_000          # 名义 70B，不是任何 checkpoint 的实际计数
CARD_CAPACITY_BYTES = 80 * GB        # H100 SXM 标称 80 GB
LINK_BITS_PER_SECOND = 400_000_000_000
STARTUP_SECONDS = 3e-6               # 教学用小消息启动时间，非实测
WIDTHS = (16, 8)                     # 两种存储位宽
PAYLOADS = (
    ('1 KiB 控制消息', 1024),
    ('1 MiB 激活块', 1 * 2 ** 20),
    ('64 MiB 激活块', 64 * 2 ** 20),
    ('70 GB 纯权重（1 byte/参数）', 70 * GB),
    ('140 GB 纯权重（2 bytes/参数）', 140 * GB),
)


def packed_weight_bytes(parameters: int, bits: int) -> int:
    """按位宽打包后的纯权重字节，向上取整到字节。"""
    return (parameters * bits + 7) // 8


def capacity_rows() -> list:
    rows = []
    for bits in WIDTHS:
        payload = packed_weight_bytes(PARAMETERS, bits)
        rows.append(dict(
            weight_bits=bits,
            bytes_per_parameter=bits / 8,
            weight_bytes=payload,
            weight_GB=payload / GB,
            weight_GiB=payload / GiB,
            card_capacity_bytes=CARD_CAPACITY_BYTES,
            card_capacity_GB=CARD_CAPACITY_BYTES / GB,
            card_capacity_GiB=CARD_CAPACITY_BYTES / GiB,
            weights_only_fits=payload <= CARD_CAPACITY_BYTES,
            headroom_bytes=CARD_CAPACITY_BYTES - payload,
            headroom_GB=(CARD_CAPACITY_BYTES - payload) / GB,
            cards_needed_for_weights_only=-(-payload // CARD_CAPACITY_BYTES),
            answers='capacity',
        ))
    return rows


def link_rate() -> dict:
    raw = LINK_BITS_PER_SECOND / 8
    return dict(
        link_bits_per_second=LINK_BITS_PER_SECOND,
        raw_bytes_per_second=raw,
        raw_GB_per_second=raw / GB,
        raw_GiB_per_second=raw / GiB,
        note='单向原始速率；双向链路不能把一次单向传输的时间减半。',
        answers='bandwidth',
    )


def transfer_rows(raw_bytes_per_second: float) -> list:
    rows = []
    for label, payload in PAYLOADS:
        service = payload / raw_bytes_per_second
        rows.append(dict(
            payload=label,
            payload_bytes=payload,
            bandwidth_term_seconds=service,
            startup_term_seconds=STARTUP_SECONDS,
            single_message_seconds=STARTUP_SECONDS + service,
            startup_share=STARTUP_SECONDS / (STARTUP_SECONDS + service),
            answers='latency' if STARTUP_SECONDS > service else 'bandwidth',
        ))
    return rows


def crossover(raw_bytes_per_second: float) -> dict:
    """启动时间与传输时间相等的载荷：小于它由延迟主导，大于它由带宽主导。"""
    payload = STARTUP_SECONDS * raw_bytes_per_second
    return dict(startup_seconds=STARTUP_SECONDS, crossover_payload_bytes=payload,
                crossover_payload_KiB=payload / 1024)


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rate = link_rate()
    result = dict(
        schema_version=1,
        experiment='1-2',
        title='把资源卡变成可用的数字',
        inputs=dict(parameters=PARAMETERS, weight_bits=list(WIDTHS),
                    card_capacity_bytes=CARD_CAPACITY_BYTES,
                    link_bits_per_second=LINK_BITS_PER_SECOND,
                    startup_seconds=STARTUP_SECONDS),
        capacity=capacity_rows(),
        bandwidth=rate,
        transfers=transfer_rows(rate['raw_bytes_per_second']),
        startup_bandwidth_crossover=crossover(rate['raw_bytes_per_second']),
        assumptions=[
            '70B 是名义教学参数量（70×10^9），不是某个 checkpoint 的实际计数。',
            '只算纯权重载荷；KV 状态、激活工作区、分配器保留和 checkpoint 元数据全部另列，不含在这里。',
            '存储位宽不是硬件计算精度声明；实际量化还有 scale／zero point／分组填充，需要单独计量。',
            '400 Gb/s 是标称线速；协议头、编码和共享路径的损耗需要另给有效率，不在本算例内。',
            '启动时间 3 μs 是教学输入，用来区分“延迟回答的问题”和“带宽回答的问题”，不是实测 RTT。',
        ],
        python_version=sys.version,
    )
    with open(os.path.join(RESULTS, 'resource-card.json'), 'w') as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
        fh.write('\n')

    lines = ['# 实验 1-2 结果：资源卡换算', '',
             '## 容量：纯权重放得下吗', '',
             '| 存储位宽 | 每参数字节 | 纯权重 | GiB | 80 GB 卡放得下 | 余量 | 回答的问题 |',
             '| --- | ---: | ---: | ---: | :---: | ---: | --- |']
    for row in result['capacity']:
        lines.append('| {bits} bit | {bpp:.2f} | {gb:.1f} GB | {gib:.1f} GiB | {fit} | {head:+.1f} GB | 容量 |'.format(
            bits=row['weight_bits'], bpp=row['bytes_per_parameter'], gb=row['weight_GB'],
            gib=row['weight_GiB'], fit='是' if row['weights_only_fits'] else '否',
            head=row['headroom_GB']))
    lines += ['', '## 带宽：400 Gb/s 是多少字节每秒', '',
              '400 Gb/s ÷ 8 = **{:.0f} GB/s**（{:.2f} GiB/s）单向原始速率。'.format(
                  rate['raw_GB_per_second'], rate['raw_GiB_per_second']),
              '', '## 传输时间：载荷走完要多久', '',
              '| 载荷 | 字节 | 带宽项 | 启动项 | 合计 | 启动占比 | 主导资源 |',
              '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for row in result['transfers']:
        lines.append('| {p} | {b:,} | {bw:.6g} s | {st:.6g} s | {tot:.6g} s | {sh:.1%} | {ans} |'.format(
            p=row['payload'], b=row['payload_bytes'], bw=row['bandwidth_term_seconds'],
            st=row['startup_term_seconds'], tot=row['single_message_seconds'],
            sh=row['startup_share'], ans='延迟' if row['answers'] == 'latency' else '带宽'))
    cross = result['startup_bandwidth_crossover']
    lines += ['', '启动与带宽两项相等的载荷约 **{:.1f} KiB**：更小的消息由延迟决定，更大的块由带宽决定。'.format(
        cross['crossover_payload_KiB']), '']
    with open(os.path.join(RESULTS, 'resource-card.md'), 'w') as fh:
        fh.write('\n'.join(lines))

    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
