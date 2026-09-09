# tpu-demand — 2013 demand projection in TPU v1 paper

输入：`{"baseline_server_equivalents": null, "effective_capacity_gain": null, "minutes_per_person_day": "6", "relative_peak_factor": "1", "relative_population": "1", "relative_work_per_audio_second": "1"}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| reference_minutes_per_person_day | 3 |
| reference_existing_capacity_units | 1 |
| reference_projected_total_capacity_units | 2 |
| requested_minutes_per_person_day_exact | `"6"` |
| incremental_conventional_capacity_exact | `"2"` |
| total_conventional_capacity_exact | `"3"` |
| supplied_effective_capacity_gain_exact | `null` |
| historical_user_count | `null` |
| historical_server_count | `null` |
| actual_accelerator_count | `null` |
| actual_cost | `null` |

| 条件候选 | 增量/原容量 | 总量/原容量 | 声明新增整服务器当量 |
| --- | --- | --- | --- |
| conventional_reference | 2 | 3 | None |
| supplied_effective_gain | None | None | None |

逐因子推算：`[{"factor": "usage_minutes", "multiplier_exact": "2", "input_capacity_exact": "1", "output_capacity_exact": "2"}, {"factor": "population", "multiplier_exact": "1", "input_capacity_exact": "2", "output_capacity_exact": "2"}, {"factor": "work_per_audio_second", "multiplier_exact": "1", "input_capacity_exact": "2", "output_capacity_exact": "2"}, {"factor": "peak_requirement", "multiplier_exact": "1", "input_capacity_exact": "2", "output_capacity_exact": "2"}]`；服务器当量只在显式给出教学基准时计算，不是历史实际数量。

计量条件：

- The archived paper section 2 reports a 2013 projection: three minutes/person/day voice search would require datacenter computation capacity to double. It does not provide user population or server inventory for reproducing an absolute historical count.
- Existing computation capacity is normalized to one; the anchor is interpreted as one additional unit of voice demand. Linear usage, population, per-audio work and peak scaling are explicit teaching assumptions, not additional historical observations.
- Baseline server equivalents, when supplied, are a homogeneous capacity normalization. Integer rounding allocates added units only once. It is not a placement, hardware inventory, power, latency or accelerator-count prediction.
- An optional effective gain affects only the added voice workload, leaving the baseline workload at one unit. The paper's 10x cost-performance design target is not an effective throughput multiplier and is never used automatically.
- No absolute server count or cost is filled without inputs. Queueing, supply bandwidth, latency targets, cost, development, delivery and heterogeneous host requirements remain outside this demand-only calculation.

固定来源：

- [../references/files/papers/tpu-v1.pdf](https://arxiv.org/abs/1704.04760)，SHA256 `19793e4ae1486630ac45a12facabc0e80609dd679db8ca7a3a040f8bf0d8e0be`。
- [../references/text/tpu-v1.txt](https://arxiv.org/abs/1704.04760)，SHA256 `3676cd693c5e9a2f147e6ed8f8ee261bcc7de28b760c5833e71ac42746378802`。
