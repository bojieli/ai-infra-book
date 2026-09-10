#!/usr/bin/env python3
"""实验 1-8：历史设计的量化推演（第 1 章配套延伸，进阶）。

规则：每个案例只用**当年可知**的公开条件做推算，写出当年应该给出的建议，
再与公开选择对照；当时未知的应用与资源条件单独保留，最后标出后来的观察
改变了哪一项判断。

三个案例：
  A. TPU（2013 年的需求预测）
  B. SmartNIC（2016 年前后的主机网络处理）
  C. Unified Bus（2019 与 2020 两个时点的模型容量）

只依赖 Python 3 标准库。所有“当年未知”的量保持为 None，不填造。
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results')
GB = 10 ** 9


# ---------- 案例 A：TPU，2013 ----------

def case_tpu():
    """当年可知：三分钟/人/天语音搜索会让数据中心计算需求翻倍。"""
    added_units = 1.0                     # 现有容量归一化为 1
    # 当年能推的问题：专用路线要多大的有效容量倍数，才能把新增控制在 X 以内
    targets = [0.5, 0.2, 0.1, 0.05]
    breakeven = [dict(target_added_units=t, required_effective_gain=added_units / t)
                 for t in targets]
    return dict(
        case='A. TPU（2013）',
        era_known=[
            '语音搜索使用率预测：3 分钟/人/天。',
            '该使用率会使数据中心计算需求翻倍（新增 = 现有容量 ×1）。',
            '通用服务器的采购与供电成本按现有容量线性外推。',
        ],
        era_computation=dict(added_capacity_units=added_units,
                             breakeven_gain_for_target=breakeven),
        era_recommendation=(
            '需求侧规模明确：不做任何事就要再建一整份数据中心计算容量。'
            '因此值得为这一类负载做专用化——但只有当专用路线对这部分负载的'
            '有效容量至少 10×（把新增压到 0.1 个单位）时，投入才明显优于直接扩容。'
            '低于 2× 时不必立项，扩容更省事。'),
        public_choice='Google 立项并部署了 TPU v1，论文给出的设计目标是相对通用方案约 10× 的性价比。',
        era_unknown=[
            '实际用户数与服务器台数（论文未提供）。',
            '语音模型未来两年的结构变化幅度。',
            '专用芯片的研发周期能否赶上需求增长。',
            '除语音外还会出现哪些模型负载。',
        ],
        later_observation=(
            '后来推理负载从语音扩展到 CNN、RNN 与更大的语言模型，'
            '“为单一负载专用化”的风险比当年估计的低——因为矩阵乘这一共同内核在各类负载中都成立。'),
        judgment_changed='把专用化的适用范围从“语音搜索”改判为“矩阵乘为主的推理负载”，这让投入的摊销台数远大于当年推算。',
        actual_cost=None, actual_server_count=None,
    )


# ---------- 案例 B：SmartNIC，2016 ----------

def case_smartnic():
    """当年可知：40 Gbps 链路约 60 Mpps；简单转发 10–20 Mpps/核。"""
    link_bps = 40_000_000_000
    wire_bytes = 64 + 20
    pps = link_bps / 8 / wire_bytes
    rows = []
    for rate in (10e6, 20e6):
        for retained, label in ((1.0, '全部主机处理'), (0.1, '卸载后保留 10%')):
            cores = math.ceil(pps * retained / rate)
            rows.append(dict(baseline_mpps_per_core=rate / 1e6, retained=retained,
                             label=label, cores=cores))
    return dict(
        case='B. SmartNIC（2016）',
        era_known=[
            '数据中心链路正从 10 Gbps 升到 40 Gbps，下一步是 100 Gbps。',
            '40 Gbps 满线速最小帧约 60 Mpps；简单转发的单核能力 10–20 Mpps。',
            '虚拟化网络还要做封装、隔离、限速与转发查表，每包工作量高于简单转发。',
            'FPGA 可编程网卡已可获得，单板功耗与成本在服务器预算内。',
        ],
        era_computation=dict(packets_per_second=pps, cpu_rows=rows),
        era_recommendation=(
            '按 %.1f Mpps 计，只做简单转发就要 3–6 个核；加上封装与隔离，'
            '每台服务器要为网络留出接近两位数的核。这些核不产生业务收入。'
            '建议把与包数成正比、逻辑固定的工作（校验、封装/解封装、转发查表、限速）'
            '下沉到可编程网卡，主机只保留与连接状态和策略相关的部分；'
            '保留 10%% 时主机侧回到 1 个核以内。'
            '前提是必须同时核算 PCIe 带宽与在途事务，它们不随卸载消失。' % (pps / 1e6)),
        public_choice='微软在 Azure 大规模部署 FPGA SmartNIC（Catapult／AccelNet）承担虚拟网络处理；作者的 ClickNP、KV-Direct 属同期研究路线。',
        era_unknown=[
            '真实流量的包长分布（按最小帧配核会大幅过配）。',
            '可编程网卡的开发效率与运维成本。',
            '网卡上做有状态处理时，状态容量与访问延迟是否够用。',
        ],
        later_observation=(
            '后来的实际部署显示：包长分布使平均包率比最小帧低一个量级，'
            '但卸载的价值并没有因此消失——真正的收益来自延迟抖动下降和主机核的确定性释放，'
            '而不只是核数的平均节省。'),
        judgment_changed='把卸载的主要理由从“省多少核”改判为“把与包数成正比的抖动移出主机”，评价指标随之改变。',
    )


# ---------- 案例 C：Unified Bus，2019 与 2020 ----------

def case_ub():
    """当年可知：两个时点上，公开最大模型的驻留需求与单卡容量。"""
    anchors = [
        dict(year=2019, model='BERT-large', parameters=340_000_000, card='V100 32 GB', card_bytes=32 * GB),
        dict(year=2019, model='GPT-2', parameters=1_500_000_000, card='V100 32 GB', card_bytes=32 * GB),
        dict(year=2020, model='GPT-3', parameters=175_000_000_000, card='A100 40 GB', card_bytes=40 * GB),
    ]
    rows = []
    for a in anchors:
        weights = a['parameters'] * 2                       # FP16/BF16 权重
        training_state = a['parameters'] * 16               # FP32 参数＋梯度＋两个动量
        rows.append(dict(**a,
                         inference_weight_bytes=weights,
                         inference_cards=math.ceil(weights / a['card_bytes']),
                         training_state_bytes=training_state,
                         training_cards=math.ceil(training_state / a['card_bytes'])))
    return dict(
        case='C. Unified Bus（2019 与 2020）',
        era_known=[
            '2019：公开最大模型 BERT-large 340M、GPT-2 1.5B；单卡 V100 32 GB。',
            '2020：GPT-3 175B 公开；单卡 A100 40 GB。',
            '训练状态按 FP32 参数＋梯度＋两个动量 = 16 bytes/参数计。',
            '跨卡协作的每步交换随并行度增加，互联带宽与延迟直接进入执行时间。',
        ],
        era_computation=dict(rows=rows),
        era_recommendation=(
            '在 2019 年的条件下：1.5B 模型的训练状态 24 GB 仍装得进一张 32 GB 卡，'
            '推理权重只要 3 GB。为“扩大协作范围”做统一互联的投入，当年很难用容量论证——'
            '只能用长期趋势论证，而趋势在当时是未知量。'
            '在 2020 年的条件下：175B 的推理权重 350 GB 要 9 张 40 GB 卡，'
            '训练状态 2.8 TB 要 70 张卡；单卡容量不再是可选项，'
            '互联从“优化项”变成“可行性前提”。建议在这个时点加大投入。'),
        public_choice='统一互联的研究早于 GPT-3；2020 年的需求转折促成了更大投入，后续形成 UB 方向。',
        era_unknown=[
            '模型规模会不会继续以这个速率增长。',
            '稀疏／MoE 会不会把有效参数量拉回单卡范围。',
            '单卡容量（HBM）会以多快速度增长。',
            '推理与训练哪一侧先成为部署主体。',
        ],
        later_observation=(
            '模型规模确实继续增长，同时 MoE 让激活参数与总参数分离；'
            '单卡容量从 32 GB 涨到 80／96／192 GB，但没有追上总参数增长。'
            '推理（而不是训练）成为部署主体，长上下文让 KV 状态成为新的容量项。'),
        judgment_changed=(
            '把“扩大协作范围”的主要驱动从“训练放不下”改判为“推理的权重＋KV 放不下且必须低延迟协作”，'
            '这提高了对互联延迟（而不只是带宽）的要求。'),
    )


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    cases = [case_tpu(), case_smartnic(), case_ub()]
    result = dict(schema_version=1, experiment='1-8', title='历史设计的量化推演',
                  rule='每个案例只用当年可知的公开条件推算，未知条件单独保留，不用后见之明补齐输入。',
                  cases=cases,
                  assumptions=[
                      '“当年可知”指该时点已公开的论文、规格或使用预测，不含内部数据与后来的观察。',
                      '容量与核数换算都是显式声明的线性模型，用于比较量级，不是历史系统的实际配置。',
                      '公开选择一栏只陈述已公开的结果，不推断决策过程与内部讨论。',
                      '“后来观察改变了哪一项判断”是本实验的结论，不是历史当事人的说法。',
                  ],
                  python_version=sys.version)
    with open(os.path.join(RESULTS, 'historical.json'), 'w') as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
        fh.write('\n')

    lines = ['# 实验 1-8 结果：历史设计的量化推演', '',
             '规则：只用当年可知的条件推算，未知条件单独保留。', '']
    for c in cases:
        lines += ['## ' + c['case'], '', '**当年可知**', ''] + ['- ' + x for x in c['era_known']]
        lines += ['', '**当年的推算**', '']
        if c['case'].startswith('A'):
            lines += ['| 目标：新增容量压到 | 需要的有效容量倍数 |', '| ---: | ---: |']
            for row in c['era_computation']['breakeven_gain_for_target']:
                lines.append('| %.2f 单位 | %.0f× |' % (row['target_added_units'], row['required_effective_gain']))
        elif c['case'].startswith('B'):
            lines += ['满线速最小帧 %.1f Mpps。' % (c['era_computation']['packets_per_second'] / 1e6), '',
                      '| 单核能力 | 主机保留 | 需要的核 |', '| ---: | --- | ---: |']
            for row in c['era_computation']['cpu_rows']:
                lines.append('| %.0f Mpps | %s | %d |' % (row['baseline_mpps_per_core'], row['label'], row['cores']))
        else:
            lines += ['| 年份 | 模型 | 参数 | 推理权重 | 需要卡数 | 训练状态 | 需要卡数 |',
                      '| ---: | --- | ---: | ---: | ---: | ---: | ---: |']
            for row in c['era_computation']['rows']:
                lines.append('| %d | %s | %.3g | %.1f GB | %d | %.1f GB | %d |' % (
                    row['year'], row['model'], row['parameters'],
                    row['inference_weight_bytes'] / GB, row['inference_cards'],
                    row['training_state_bytes'] / GB, row['training_cards']))
        lines += ['', '**当年应给的建议**', '', c['era_recommendation'], '',
                  '**公开选择**', '', c['public_choice'], '',
                  '**当年未知**', ''] + ['- ' + x for x in c['era_unknown']]
        lines += ['', '**后来的观察**', '', c['later_observation'], '',
                  '**改变了哪一项判断**', '', c['judgment_changed'], '']
    with open(os.path.join(RESULTS, 'historical.md'), 'w') as fh:
        fh.write('\n'.join(lines))
    print('\n'.join(lines[:40]))
    print('...\n完整结果写入 results/historical.md')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
