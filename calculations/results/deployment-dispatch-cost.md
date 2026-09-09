# optimization-deployment — 

输入：`{"dispatch_ns": 20000, "extra_setup_ns": 600000000000, "repetitions": 1, "shapes": [{"baseline_ns": 100000, "candidates": {"A": {"ns": 10000, "valid": true}, "B": {"ns": 50000, "valid": true}}, "count": 1, "name": "x"}, {"baseline_ns": 100000, "candidates": {"A": {"ns": 200000, "valid": true}, "B": {"ns": 50000, "valid": true}}, "count": 1, "name": "y"}]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| cohort_calls | 2 |
| best_uniform | `"B"` |
| best_uniform_cohort_ns | 100,000 |
| mixed_cohort_ns | 100,000 |
| mixed_mean_ns | 50,000.0 |
| mixed_saving_per_call_exact_ns | `"0"` |
| mixed_lifetime_total_ns | 600,000,100,000 |
| uniform_lifetime_total_ns | 100,000 |
| break_even_calls | `null` |
| strictly_faster_calls | `null` |
| whole_cohort_thresholds | `{"break_even_calls": null, "strictly_faster_calls": null}` |
| actual_request_seconds | `null` |

| 候选 | 形状等权平均比值 | 频数加权平均 ns | 回退调用数 |
| --- | ---: | ---: | ---: |
| baseline | 1.0 | 100000.0 | 0 |
| A | 5.25 | 105000.0 | 0 |
| B | 2.0 | 50000.0 | 0 |

| 形状 | 调用数 | 选择 | 含分派 ns |
| --- | ---: | --- | ---: |
| x | 1 | A | 30000 |
| y | 1 | B | 70000 |

两形状交叉条件：`{"candidate_a": "A", "candidate_b": "B", "difference_intercept_ns": 150000, "difference_slope_ns": -190000, "equality_first_shape_fraction": "15/19", "a_faster_condition": "intercept + slope * p < 0, with 0 <= p <= 1"}`

计量条件：

- 默认x/y与100/10/200/50us均为正文教学输入，不假称Qwen算子或GPU测量；可输入已核对的逐形状候选时间和频数。
- 形状平均比值等权纳入全部形状，失败／缺失候选记零仅用于本例分数。部署遇已知失败／缺失项按baseline时间回退，不能用零分当零耗时；未模拟运行中失败后再重试。
- 逐形状分派在有效候选和baseline中选择最短时间，再给每次调用加dispatch_ns。统一路径的输入耗时已包含其已有开销；分派策略是固定输入下的理想选择，不证明真实引擎采用。
- extra_setup_ns是相对最佳统一路径的额外准备预算，默认600秒；共同准备成本抵消，不再重复加入。失败搜索、编译、验证若消耗额外串行预算须纳入此输入。
- per-call阈值假定固定频数比例可按平均成本延拓；whole_cohort_thresholds以完整频数组重复，保持整数调用组成。严格更快与恰好摊平分开，节省非正时没有有限回本。
- 时间按串行成本汇总，不是带重叠的请求关键路径；CPU/GPU/API费用及质量影响需要各自资源与验证记录。

固定来源：

