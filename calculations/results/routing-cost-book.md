# routing-cost — 

输入：`{"b_hit_fraction": "1", "deadline_seconds": 6, "fresh_tokens": 1000, "prefix_tokens": 19000, "tasks": 1000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| cost_crossover_b_hit_fraction_exact | `"1291/1520"` |
| cost_crossover_in_unit_interval | `true` |
| b_cheaper_per_quality_success | `true` |
| target_joint_success_fraction_exact | `"9/10"` |
| minimum_b_hit_for_joint_target_exact | `"45/49"` |
| b_meets_joint_target | `true` |

| 假想服务 | 总费用 | 预期质量成功数 | 每质量成功费用 | 预期质量且按时成功数 | 每联合成功费用 |
| --- | --- | --- | --- | --- | --- |
| A | 109/10 | 800 | 109/8000 | 0 | None |
| B | 41/5 | 980 | 41/4900 | 980 | 41/4900 |

计量条件：

- 正文假想A/B价格：每百万token输入/缓存/输出为A=1/0.1/4、B=2/0.2/8；非供应商价格或实测。A reasoning1800+visible200，B100+200，输出计费包含reasoning一次，不再重复加收。
- A缓存固定全命中，B在指定相同长度前缀上按完整命中/未命中两分支。新输入总按输入价；缓存创建、存储、工具、环境费用在此教学题设为0，实际费用需另计。
- 质量成功率A=0.8、B=0.98为给定输入，与缓存分支独立；分母用预期成功数，分子保留全部提交尝试费用。不是有限样本实测比率，也不假设自动重试到成功。
- 给定完整请求时长A=10秒，B命中4秒/未命中12秒；满足时限使用<=。联合质量/截止时间成功率分开计算，零成功费用比为null，不以平均延迟代替尾部或完成率。
- 成本交点是精确代数值，可能落在[0,1]之外；另给可实现标志。改变前缀/新输入改变费用，但本题保持给定请求时长不变，不冒充token数到延迟的预测模型。

固定来源：

