#!/usr/bin/env python3
"""实验 1-5：语音需求与专用化决策（第 1 章配套延伸）。

历史锚点只有一条：TPU v1 论文第 2 节记载，2013 年若每人每天使用三分钟
语音搜索，数据中心的计算需求将**翻倍**。论文没有给出用户数，也没有给出
服务器台数，因此本实验把“现有计算容量”归一化为 1，把这条预测读成
“再增加 1 个单位”，其余全部是显式声明的线性外推。

计算三件事：
  1. 三个使用率下的增量容量；
  2. 同样需求下，通用扩容与专用加速两条路线各需要多少容量单位；
  3. 结论还依赖哪些供数、成本与交付条件（不填数，只列出）。

只依赖 Python 3 标准库。分数全程用 fractions.Fraction，不引入浮点误差。
"""
import json
import os
import sys
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results')

ANCHOR_MINUTES = F(3)          # 论文记载的使用率锚点
ANCHOR_ADDED_CAPACITY = F(1)   # 该使用率下新增的容量＝现有容量的一倍

USAGE_CASES = [F(1), F(3), F(6)]           # 三个使用率（分钟／人／天）
GAIN_CASES = [F(1), F(10), F(30)]          # 专用路线的有效容量倍数（声明输入）


def added_capacity(minutes, population=F(1), work_per_second=F(1), peak=F(1)):
    """线性外推：使用率、人口、每秒音频工作量与峰值系数各自成比例。"""
    return ANCHOR_ADDED_CAPACITY * (minutes / ANCHOR_MINUTES) * population * work_per_second * peak


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    usage_rows = []
    for minutes in USAGE_CASES:
        added = added_capacity(minutes)
        usage_rows.append(dict(
            minutes_per_person_day=str(minutes),
            added_capacity_units=str(added),
            added_capacity_float=float(added),
            total_capacity_units=str(1 + added),
            total_capacity_float=float(1 + added),
            is_paper_anchor=(minutes == ANCHOR_MINUTES),
        ))

    route_rows = []
    for minutes in USAGE_CASES:
        added = added_capacity(minutes)
        for gain in GAIN_CASES:
            # 有效容量倍数只作用于新增的语音负载，原有负载仍占 1 个单位
            needed = added / gain
            route_rows.append(dict(
                minutes_per_person_day=str(minutes),
                effective_capacity_gain=str(gain),
                route='通用扩容' if gain == 1 else '专用加速（声明 %s×）' % gain,
                added_capacity_units=str(needed),
                added_capacity_float=float(needed),
                total_capacity_units=str(1 + needed),
                total_capacity_float=float(1 + needed),
                capacity_saved_units=str(added - needed),
            ))

    # 敏感性：只改一个因子，看增量容量怎样变
    sensitivity = []
    for name, kwargs in [('人口翻倍', dict(population=F(2))),
                         ('每秒音频工作量减半（更小模型）', dict(work_per_second=F(1, 2))),
                         ('峰值是均值的 2 倍', dict(peak=F(2))),
                         ('三项同时发生', dict(population=F(2), work_per_second=F(1, 2), peak=F(2)))]:
        added = added_capacity(ANCHOR_MINUTES, **kwargs)
        sensitivity.append(dict(change=name, added_capacity_units=str(added),
                                added_capacity_float=float(added)))

    result = dict(
        schema_version=1, experiment='1-5', title='语音需求与专用化决策',
        anchor=dict(source='TPU v1 论文第 2 节（2013 年预测）',
                    minutes_per_person_day=str(ANCHOR_MINUTES),
                    statement='数据中心计算需求翻倍，即在现有容量之外再加 1 个单位',
                    existing_capacity_units=1),
        usage_scan=usage_rows,
        route_comparison=route_rows,
        sensitivity=sensitivity,
        still_needed=[
            '供数：语音模型每秒音频要读多少权重与状态，专用芯片能否喂饱阵列。',
            '成本：单位容量的采购、供电与散热成本，以及研发投入的摊销台数。',
            '交付：从立项到上线的周期，是否赶得上需求增长的时间点。',
            '负载稳定性：模型结构在交付周期内是否会变，专用化会不会做完就过时。',
            '延迟目标：语音搜索的响应时限，决定能否靠排队提高利用率。',
            '异构主机：专用加速器仍需 CPU、内存与网络配套，这部分容量没有被替代。',
        ],
        unfilled=dict(historical_user_count=None, historical_server_count=None,
                      actual_accelerator_count=None, actual_cost=None,
                      note='论文未提供，本实验不填造。'),
        assumptions=[
            '现有计算容量归一化为 1；“翻倍”读成新增 1 个单位。',
            '使用率、人口、每秒音频工作量与峰值系数均按线性外推，这是教学假设而非历史观察。',
            '有效容量倍数只作用于新增语音负载；论文的 10× 性价比设计目标不是有效吞吐倍数，本实验把倍数作为可调输入，不默认取用。',
            '容量单位是同质归一化，不代表放置、功耗、延迟或加速器台数。',
        ],
        python_version=sys.version,
    )
    with open(os.path.join(RESULTS, 'tpu-demand.json'), 'w') as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
        fh.write('\n')

    lines = ['# 实验 1-5 结果：语音需求与专用化', '',
             '锚点：每人每天 3 分钟语音搜索 → 数据中心计算需求翻倍（现有容量归一化为 1，新增 1 个单位）。', '',
             '## 三个使用率下的增量容量', '',
             '| 使用率 | 新增容量 | 总容量 | 备注 |', '| ---: | ---: | ---: | --- |']
    for row in usage_rows:
        lines.append('| %s 分钟/人/天 | %.3g 单位 | %.3g 单位 | %s |' % (
            row['minutes_per_person_day'], row['added_capacity_float'],
            row['total_capacity_float'], '论文锚点' if row['is_paper_anchor'] else '线性外推'))
    lines += ['', '## 扩容与专用化的容量对比', '',
              '| 使用率 | 路线 | 新增容量 | 总容量 | 省下 |', '| ---: | --- | ---: | ---: | ---: |']
    for row in route_rows:
        lines.append('| %s 分钟 | %s | %.4g | %.4g | %.4g |' % (
            row['minutes_per_person_day'], row['route'], row['added_capacity_float'],
            row['total_capacity_float'], float(F(row['capacity_saved_units']))))
    lines += ['', '## 单因子敏感性（固定 3 分钟锚点）', '',
              '| 改变 | 新增容量 |', '| --- | ---: |']
    for row in sensitivity:
        lines.append('| %s | %.4g 单位 |' % (row['change'], row['added_capacity_float']))
    lines += ['', '## 结论还依赖什么', ''] + ['- ' + item for item in result['still_needed']] + ['']
    with open(os.path.join(RESULTS, 'tpu-demand.md'), 'w') as fh:
        fh.write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
