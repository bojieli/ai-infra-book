#!/usr/bin/env python3
"""实验 1-6：网络处理的 CPU 预算（第 1 章配套延伸）。

历史基线来自作者博士论文 §4.2.1：40 Gbps 链路约 60 Mpps；简单转发的
单核处理能力约 10–20 Mpps。本实验按这条基线复算 CPU 核数，再依次加入
封装开销、包长分布和链路负载率，最后给出主机与网卡的分工建议。

包长换算全部按“线上占用”计：以太网帧（含 FCS）＋ 8 字节前导/SFD ＋
12 字节帧间隙。分布按**包数**加权，不是按字节加权。

只依赖 Python 3 标准库；分数用 fractions.Fraction 保持精确。
"""
import json
import os
import sys
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results')

LINK_BPS = 40_000_000_000
WIRE_OVERHEAD = 20              # 8 前导/SFD + 12 帧间隙
CORE_RATES = [10_000_000, 20_000_000]   # 论文给出的简单转发单核区间


def packet_rate(mix, utilization=F(1), encapsulation=0):
    """按包数分布求线速包率与平均线上占用。"""
    total_share = sum(F(s) for _, s in mix)
    if total_share != 1:
        raise ValueError('包数占比必须精确加和为 1')
    mean_wire = sum(F(s) * (frame + encapsulation + WIRE_OVERHEAD) for frame, s in mix)
    pps = F(LINK_BPS, 8) * utilization / mean_wire
    return pps, mean_wire


def cores(pps, work_multiplier=F(1), retained=F(1), target_utilization=F(1)):
    rows = []
    for rate in CORE_RATES:
        busy = pps * work_multiplier * retained / F(rate)
        provisioned = busy / target_utilization
        rows.append(dict(baseline_mpps_per_core=rate / 1e6,
                         busy_core_seconds_per_second=float(busy),
                         required_core_equivalents=float(provisioned),
                         dedicated_integer_cores=-(-provisioned.numerator // provisioned.denominator)))
    return rows


def case(label, mix, utilization=F(1), encapsulation=0, work_multiplier=F(1),
         retained=F(1), target_utilization=F(1), note=''):
    pps, mean_wire = packet_rate(mix, utilization, encapsulation)
    return dict(label=label, note=note,
                packet_mix=[dict(frame_bytes=f, share=str(s)) for f, s in mix],
                encapsulation_bytes=encapsulation,
                link_utilization=str(utilization),
                work_multiplier=str(work_multiplier),
                retained_host_work=str(retained),
                target_cpu_utilization=str(target_utilization),
                mean_wire_bytes_per_packet=float(mean_wire),
                packets_per_second=float(pps),
                mpps=float(pps) / 1e6,
                cpu=cores(pps, work_multiplier, retained, target_utilization))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    min_frame = [(64, F(1))]
    # IMIX 近似：按包数 7:4:1 的 64／590／1518 字节
    imix = [(64, F(7, 12)), (590, F(4, 12)), (1518, F(1, 12))]
    cases = [
        case('论文基线：全 64 B 最小帧，满线速', min_frame,
             note='复算 §4.2.1 的 40 Gbps ≈ 60 Mpps'),
        case('加 VXLAN 封装（+50 B 线上）', min_frame, encapsulation=50,
             note='封装增加线上字节，包率反而下降'),
        case('IMIX 包长分布（按包数 7:4:1）', imix,
             note='真实流量不是全最小帧'),
        case('IMIX + 链路负载率 50%', imix, utilization=F(1, 2)),
        case('全 64 B + 链路负载率 50%', min_frame, utilization=F(1, 2)),
        case('全 64 B，每包工作量 ×2（封装+隔离）', min_frame, work_multiplier=F(2),
             note='同样的包率，处理更重'),
        case('全 64 B，CPU 目标利用率 70%', min_frame, target_utilization=F(7, 10),
             note='留排队余量后需要更多核'),
        case('卸载后主机只留 10% 包处理', min_frame, retained=F(1, 10),
             note='SmartNIC 承担其余部分'),
        case('卸载后主机只留 1% 包处理', min_frame, retained=F(1, 100)),
    ]
    result = dict(
        schema_version=1, experiment='1-6', title='网络处理的 CPU 预算',
        baseline=dict(source='作者博士论文 §4.2.1',
                      statement='40 Gbps 约 60 Mpps；简单转发 10–20 Mpps/核',
                      link_bits_per_second=LINK_BPS,
                      wire_overhead_bytes=WIRE_OVERHEAD,
                      core_rates_pps=CORE_RATES),
        cases=cases,
        recommendation=[
            '满线速最小帧是最坏情况：40 Gbps 下 59.5 Mpps，按 10 Mpps/核要 6 核、按 20 Mpps/核要 3 核，只做简单转发就吃掉这些核。',
            '封装先降包率再升每包工作量：加 50 B 线上字节后包率降到 37.3 Mpps，但每包多做封装/解封装，核数不一定同比下降。',
            '真实包长分布把包率降一个量级：IMIX 下只有 13.1 Mpps，2 核以内即可，说明按最小帧配核会大幅过配。',
            '把 CPU 目标利用率从 100% 降到 70%，最小帧场景的核数从 6/3 涨到 9/5：留排队余量本身就是一笔容量。',
            '分工建议：把与包数成正比、逻辑固定的工作（校验、封装/解封装、转发查表、限速）放到网卡；把与连接状态、策略和应用语义相关的工作留在主机。主机只保留 10% 包处理时，最小帧场景降到 1 核以内。',
            '卸载不改变 PCIe 与在途并发限制：即使主机包处理归零，每包仍要过总线，这一项要在第 7 章单独核算。',
        ],
        assumptions=[
            '10–20 Mpps/核是历史论文里“简单转发”的服务能力，不是现代 CPU 基准，也不是完整虚拟化的实测。',
            '线上占用＝以太网帧（含 FCS）＋8 字节前导/SFD＋12 字节帧间隙；帧字节不等于应用载荷。',
            '分布按包数加权；包率是线上字节速率除以加权平均线上占用，不是各类满线速包率的加权平均。',
            '每包工作量倍数、目标利用率与主机保留比例都是声明的对照输入，不是测量值。',
            '多核线性扩展是假设，不是已确立的事实；忙碌核秒与分配的整核数不是同一个量。',
            '本实验只算主机包处理的核预算。网卡自身的处理能力、PCIe 带宽与在途事务、成本和 SLO 都不在内。',
        ],
        python_version=sys.version,
    )
    with open(os.path.join(RESULTS, 'nic-budget.json'), 'w') as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
        fh.write('\n')

    lines = ['# 实验 1-6 结果：网络处理的 CPU 预算', '',
             '基线：40 Gbps ≈ 60 Mpps；简单转发 10–20 Mpps/核（作者博士论文 §4.2.1）。', '',
             '| 场景 | 平均线上占用 | 包率 | 10 Mpps/核 | 20 Mpps/核 |',
             '| --- | ---: | ---: | ---: | ---: |']
    for row in cases:
        lines.append('| %s | %.1f B | %.2f Mpps | %d 核 | %d 核 |' % (
            row['label'], row['mean_wire_bytes_per_packet'], row['mpps'],
            row['cpu'][0]['dedicated_integer_cores'], row['cpu'][1]['dedicated_integer_cores']))
    lines += ['', '## 分工建议', ''] + ['- ' + item for item in result['recommendation']] + ['']
    with open(os.path.join(RESULTS, 'nic-budget.md'), 'w') as fh:
        fh.write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
