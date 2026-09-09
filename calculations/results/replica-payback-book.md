# replica-payback — 

输入：`{"batches": 128, "compute_flops_per_second": 100000000000000, "copy_bytes_per_second": 25000000000, "copy_startup_ns": 5000, "extra_budget_bytes_per_rank": 67108864, "interface_bytes_per_second": 1000000000000, "workload": {"replicas": [{"expert": 0, "rank": 1}, {"expert": 1, "rank": 2}, {"expert": 2, "rank": 3}, {"expert": 3, "rank": 4}, {"expert": 4, "rank": 5}, {"expert": 5, "rank": 6}, {"expert": 6, "rank": 7}], "routing": "concentrated"}}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| batches | 128 |
| replica_weight_bytes | 264,241,152 |
| extra_weight_bytes_per_rank | `[0, 37748736, 37748736, 37748736, 37748736, 37748736, 37748736, 37748736]` |
| capacity_feasible | `true` |
| over_budget_ranks | `[]` |
| serialized_copy_setup_ns_exact | `"265116152/25"` |
| baseline_batch_ns_exact | `"115081216/125"` |
| replicated_batch_ns_exact | `"64733184/125"` |
| per_batch_saving_ns_exact | `"50348032/125"` |
| algebraic_strict_payback_batches | 27 |
| feasible_strict_payback_batches | 27 |
| baseline_window_ns_exact | `"14730395648/125"` |
| replicated_window_ns_exact | `"9611428312/125"` |
| window_saving_ns_exact | `"5118967336/125"` |
| selected_deployment | `"replicated"` |
| selected_window_ns_exact | `"9611428312/125"` |

| 部署 | rank | 矩阵服务ns | 指定接口服务ns | rank服务ns |
| --- | ---: | --- | --- | --- |
| baseline | 0 | 1207959552/3125 | 115081216/125 | 115081216/125 |
| baseline | 1 | 0 | 0 | 0 |
| baseline | 2 | 0 | 0 | 0 |
| baseline | 3 | 0 | 0 | 0 |
| baseline | 4 | 0 | 0 | 0 |
| baseline | 5 | 0 | 0 | 0 |
| baseline | 6 | 0 | 0 | 0 |
| baseline | 7 | 0 | 0 | 0 |
| replicated | 0 | 679477248/3125 | 64733184/125 | 64733184/125 |
| replicated | 1 | 75497472/3125 | 7192576/125 | 7192576/125 |
| replicated | 2 | 75497472/3125 | 7192576/125 | 7192576/125 |
| replicated | 3 | 75497472/3125 | 7192576/125 | 7192576/125 |
| replicated | 4 | 75497472/3125 | 7192576/125 | 7192576/125 |
| replicated | 5 | 75497472/3125 | 7192576/125 | 7192576/125 |
| replicated | 6 | 75497472/3125 | 7192576/125 | 7192576/125 |
| replicated | 7 | 75497472/3125 | 7192576/125 | 7192576/125 |

计量条件：

- 复用grouped-experts同一层相同批路由、tile与副本分配；重复batches次完全相同工作，不代表实际生成中历史／路由变化。非均匀副本按各rank真实汇总，不从平均专家任务套时间。
- 每rank服务取max(全补齐矩阵/有效计算能力,指定tile接口bytes/有效带宽)，所有rank完成取max；这是一项教学资源模型，接口不自动等于HBM，不含通信、融合、kernel启动、实际缓存和其他层。
- 首次新增BF16权重经一条共享串行复制资源，每物理副本一次启动；源副本保留，不把网络两端重复计字节。复制在全部批次之前完成，未假设与服务重叠，未含转换和控制协议。
- extra_budget_bytes_per_rank为扣除基础模型、KV、工作区后的净可用预算；逐rank检查新增权重，即使副本未命中也占内存。未验证整个真实部署，仅验证该输入预算下的增量。
- 严格回本要求setup+n*new<n*old；saving≤0时无回本，容量不足时可行回本为null。代数阈值与容量可行性分列，不把预期工作下降自动当部署收益。
- 有效供给是教学参数，实际EPLB须使用固定模型／后端／路由的阶段记录和负载稳定窗口，不据本数值断言真实迁移收益。

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
