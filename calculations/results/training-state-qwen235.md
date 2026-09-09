# training-state — qwen3-235b-a22b

输入：`{"capacity_bytes": 80000000000, "extra_live_bytes": 0, "gradient_bytes": 2, "model": "qwen3-235b-a22b", "participants": 64, "partition": "flat"}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 235,093,634,560 |
| tensor_instances | 36,945 |
| bytes_per_parameter_unsharded | 16 |
| unsharded_persistent_bytes | 3,761,498,152,960 |
| padded_shard_elements_per_rank | 3,673,338,040 |
| padding_elements_per_sharded_component | 0 |
| minimum_persistent_bytes_per_rank | 58,773,408,640 |
| stages_fitting_specified_allocations | `[3]` |

持久状态与输入的额外同时驻留量；通过容量比较不证明实际训练峰值可行。

| ZeRO stage | 每rank持久 bytes | 全组持久 bytes | 所列同时驻留 bytes | 剩余净预算 bytes | 所列分配能容纳 |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 3761498152960 | 240735881789440 | 3761498152960 | -3681498152960 | False |
| 1 | 984454594720 | 63005094062080 | 984454594720 | -904454594720 | False |
| 2 | 521614001680 | 33383296107520 | 521614001680 | -441614001680 | False |
| 3 | 58773408640 | 3761498152960 | 58773408640 | 21226591360 | True |

| stage | 状态 | bytes/element | 分片 | 每rank bytes | 全组padding bytes | 额外复制 bytes |
| ---: | --- | ---: | --- | ---: | ---: | ---: |
| 0 | weights_bf16 | 2 | False | 470187269120 | 0 | 29621797954560 |
| 0 | gradients | 2 | False | 470187269120 | 0 | 29621797954560 |
| 0 | master_weights_fp32 | 4 | False | 940374538240 | 0 | 59243595909120 |
| 0 | adam_m_fp32 | 4 | False | 940374538240 | 0 | 59243595909120 |
| 0 | adam_v_fp32 | 4 | False | 940374538240 | 0 | 59243595909120 |
| 1 | weights_bf16 | 2 | False | 470187269120 | 0 | 29621797954560 |
| 1 | gradients | 2 | False | 470187269120 | 0 | 29621797954560 |
| 1 | master_weights_fp32 | 4 | True | 14693352160 | 0 | 0 |
| 1 | adam_m_fp32 | 4 | True | 14693352160 | 0 | 0 |
| 1 | adam_v_fp32 | 4 | True | 14693352160 | 0 | 0 |
| 2 | weights_bf16 | 2 | False | 470187269120 | 0 | 29621797954560 |
| 2 | gradients | 2 | True | 7346676080 | 0 | 0 |
| 2 | master_weights_fp32 | 4 | True | 14693352160 | 0 | 0 |
| 2 | adam_m_fp32 | 4 | True | 14693352160 | 0 | 0 |
| 2 | adam_v_fp32 | 4 | True | 14693352160 | 0 | 0 |
| 3 | weights_bf16 | 2 | True | 7346676080 | 0 | 0 |
| 3 | gradients | 2 | True | 7346676080 | 0 | 0 |
| 3 | master_weights_fp32 | 4 | True | 14693352160 | 0 | 0 |
| 3 | adam_m_fp32 | 4 | True | 14693352160 | 0 | 0 |
| 3 | adam_v_fp32 | 4 | True | 14693352160 | 0 | 0 |

计量条件：

- 全参数Adam教学配置：BF16参数2bytes，梯度显式BF16/FP32，FP32 master及两个moment各4bytes。16/18bytes由此得到，不代表所有BF16优化器实现的默认值。
- ZeRO stage1分片optimizer（含master），stage2再分片梯度，stage3再分片参数；无TP/PP/EP、offload或冻结参数。MoE总持久状态包含所有专家，不按top-k缩小。
- flat把完整参数展平后补齐到DP整数倍；per_tensor逐物理张量补齐后每rank等长。两者是声明的布局模型，具体框架bucket、对齐、持久化阈值需另核验。
- 这里只计已物化的持久状态：初始化懒分配、完整梯度临时值、all-gather、prefetch、casting、激活、通信bucket和allocator另计。extra_live_bytes须是同一峰值时刻额外分配且不重复计算的输入，默认0不等于实际额外开销0。
- 容量为输入的净预算，不是某设备的官方容量。specified_allocations_fit仅表示所列分配能放下，不能证明训练峰值、拓扑或吞吐可行；张量清单存JSON供独立核算。

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/training-state/zero3.rst](https://raw.githubusercontent.com/deepspeedai/DeepSpeed/0e741714f5a708b75a4db0a8140f9016f3aa5fd3/docs/code-docs/source/zero3.rst)，SHA256 `e8eeb0ccfd067c371e522b494d70e0a233e7aeda4d5ccf6dd1a200d01a4b6847`。
