# training-state — qwen3-8b

输入：`{"capacity_bytes": 25769803776, "extra_live_bytes": 10737418240, "gradient_bytes": 2, "model": "qwen3-8b", "participants": 8, "partition": "flat"}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 8,190,735,360 |
| tensor_instances | 399 |
| bytes_per_parameter_unsharded | 16 |
| unsharded_persistent_bytes | 131,051,765,760 |
| padded_shard_elements_per_rank | 1,023,841,920 |
| padding_elements_per_sharded_component | 0 |
| minimum_persistent_bytes_per_rank | 16,381,470,720 |
| stages_fitting_specified_allocations | `[]` |

持久状态与输入的额外同时驻留量；通过容量比较不证明实际训练峰值可行。

| ZeRO stage | 每rank持久 bytes | 全组持久 bytes | 所列同时驻留 bytes | 剩余净预算 bytes | 所列分配能容纳 |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 131051765760 | 1048414126080 | 141789184000 | -116019380224 | False |
| 1 | 45049044480 | 360392355840 | 55786462720 | -30016658944 | False |
| 2 | 30715257600 | 245722060800 | 41452675840 | -15682872064 | False |
| 3 | 16381470720 | 131051765760 | 27118888960 | -1349085184 | False |

| stage | 状态 | bytes/element | 分片 | 每rank bytes | 全组padding bytes | 额外复制 bytes |
| ---: | --- | ---: | --- | ---: | ---: | ---: |
| 0 | weights_bf16 | 2 | False | 16381470720 | 0 | 114670295040 |
| 0 | gradients | 2 | False | 16381470720 | 0 | 114670295040 |
| 0 | master_weights_fp32 | 4 | False | 32762941440 | 0 | 229340590080 |
| 0 | adam_m_fp32 | 4 | False | 32762941440 | 0 | 229340590080 |
| 0 | adam_v_fp32 | 4 | False | 32762941440 | 0 | 229340590080 |
| 1 | weights_bf16 | 2 | False | 16381470720 | 0 | 114670295040 |
| 1 | gradients | 2 | False | 16381470720 | 0 | 114670295040 |
| 1 | master_weights_fp32 | 4 | True | 4095367680 | 0 | 0 |
| 1 | adam_m_fp32 | 4 | True | 4095367680 | 0 | 0 |
| 1 | adam_v_fp32 | 4 | True | 4095367680 | 0 | 0 |
| 2 | weights_bf16 | 2 | False | 16381470720 | 0 | 114670295040 |
| 2 | gradients | 2 | True | 2047683840 | 0 | 0 |
| 2 | master_weights_fp32 | 4 | True | 4095367680 | 0 | 0 |
| 2 | adam_m_fp32 | 4 | True | 4095367680 | 0 | 0 |
| 2 | adam_v_fp32 | 4 | True | 4095367680 | 0 | 0 |
| 3 | weights_bf16 | 2 | True | 2047683840 | 0 | 0 |
| 3 | gradients | 2 | True | 2047683840 | 0 | 0 |
| 3 | master_weights_fp32 | 4 | True | 4095367680 | 0 | 0 |
| 3 | adam_m_fp32 | 4 | True | 4095367680 | 0 | 0 |
| 3 | adam_v_fp32 | 4 | True | 4095367680 | 0 | 0 |

计量条件：

- 全参数Adam教学配置：BF16参数2bytes，梯度显式BF16/FP32，FP32 master及两个moment各4bytes。16/18bytes由此得到，不代表所有BF16优化器实现的默认值。
- ZeRO stage1分片optimizer（含master），stage2再分片梯度，stage3再分片参数；无TP/PP/EP、offload或冻结参数。MoE总持久状态包含所有专家，不按top-k缩小。
- flat把完整参数展平后补齐到DP整数倍；per_tensor逐物理张量补齐后每rank等长。两者是声明的布局模型，具体框架bucket、对齐、持久化阈值需另核验。
- 这里只计已物化的持久状态：初始化懒分配、完整梯度临时值、all-gather、prefetch、casting、激活、通信bucket和allocator另计。extra_live_bytes须是同一峰值时刻额外分配且不重复计算的输入，默认0不等于实际额外开销0。
- 容量为输入的净预算，不是某设备的官方容量。specified_allocations_fit仅表示所列分配能放下，不能证明训练峰值、拓扑或吞吐可行；张量清单存JSON供独立核算。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/training-state/zero3.rst](https://raw.githubusercontent.com/deepspeedai/DeepSpeed/0e741714f5a708b75a4db0a8140f9016f3aa5fd3/docs/code-docs/source/zero3.rst)，SHA256 `e8eeb0ccfd067c371e522b494d70e0a233e7aeda4d5ccf6dd1a200d01a4b6847`。
