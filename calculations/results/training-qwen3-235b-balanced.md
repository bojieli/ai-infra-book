# qwen-training-matrix — qwen3-235b-a22b

输入：`{"batch": 1, "gradient_bytes": 4, "head_strategy": "dense", "master_weight_bytes": 4, "routing": "balanced", "supervised_tokens": 8192, "tokens": 8192}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 235,093,634,560 |
| input_tokens | 8,192 |
| loss_tokens | 8,192 |
| expert_assignments_per_layer | 65,536 |
| active_experts_per_layer | 128 |
| executed_head_rows | 8,192 |
| forward_matrix_flops | 456,730,848,788,480 |
| backward_matrix_flops | 913,461,697,576,960 |
| training_matrix_flops | 1,370,192,546,365,440 |
| attention_training_matrix_flops | 310,100,128,432,128 |
| six_nd_flops | 11,555,322,325,893,120 |
| matrix_minus_six_nd_flops | -10,185,129,779,527,680 |
| matrix_to_six_nd_ratio | 0.11857674824830443 |
| unsharded_parameter_state_bytes | 4,231,685,422,080 |
| activation_peak_bytes | `null` |
| complete_training_step_flops | `null` |
| predicted_step_seconds | `null` |

| 矩阵 | 重复 | 单次前向 FLOPs | 每个梯度 FLOPs | 训练矩阵总 FLOPs |
| --- | ---: | ---: | ---: | ---: |
| q_proj | 94 | 549755813888 | 549755813888 | 155031139516416 |
| k_proj | 94 | 34359738368 | 34359738368 | 9689446219776 |
| v_proj | 94 | 34359738368 | 34359738368 | 9689446219776 |
| qk | 94 | 549822922752 | 549822922752 | 155050064216064 |
| pv | 94 | 549822922752 | 549822922752 | 155050064216064 |
| o_proj | 94 | 549755813888 | 549755813888 | 155031139516416 |
| router | 94 | 8589934592 | 8589934592 | 2422361554944 |
| expert_gate_proj | 94 | 824633720832 | 824633720832 | 232546709274624 |
| expert_up_proj | 94 | 824633720832 | 824633720832 | 232546709274624 |
| expert_down_proj | 94 | 824633720832 | 824633720832 | 232546709274624 |
| lm_head | 1 | 10196252360704 | 10196252360704 | 30588757082112 |

每项包含两个梯度，形状与梯度名称见 JSON；参数状态按声明格式分列：

| 状态 | bytes |
| --- | ---: |
| bf16_weights | 470187269120 |
| gradients | 940374538240 |
| master_weights | 940374538240 |
| adam_first_moment_fp32 | 940374538240 |
| adam_second_moment_fp32 | 940374538240 |

计量条件：

- MoE 的每层路由直方图是显式情景，无 token drop 或容量填充；专家矩阵按各 n_e 求和。top-k 离散选择固定，router 矩阵仍计梯度，概率、合并、辅助损失和选择反向不在矩阵子账内。全部专家参数都纳入常驻状态，未激活专家不执行矩阵乘；6ND 用总参数仅作不适用的对照，不能预测 MoE 工作。
- 固定官方 Qwen3 Dense/MoE 配置，全参数训练，无历史 KV、无重计算；每个序列 T 个输入位置，D=B*T。loss_tokens 为调用方在移位、padding 和 mask 后给定的有效标签数，未假定等于原始文本 token 数。
- 每个线性矩阵列出前向、输入梯度、权重梯度；每次乘加计 2。QK/PV 各有两个输入梯度，按有效因果位置计数学工作；GQA 共享头的梯度归并算术另计，不用本表推断后端 tile 或矩形 kernel 工作。
- dense 输出头始终执行 B*T 行，loss mask 不自动降低矩阵 FLOPs。compact 明确假设先 gather 有监督 hidden 再计算输出头；backbone 仍执行全部行，未根据标签位置剪枝，gather/scatter 与稀疏梯度特化未计。
- 6ND 的 N 是全部参数，包括 embedding 查表与 norm；它们并非每 token 都执行参数矩阵乘。实际矩阵账单列输出头与因果注意力，因此差额不必为正。
- 状态是无分片、无 offload 的声明方案：BF16 权重、显式梯度字节和 master 字节、FP32 Adam 两份 moment；不声称是某框架默认，master=0 仅代表取消独立副本。
- 未包含 embedding 梯度 scatter、归一化/激活/softmax/损失的前反向、优化器更新算术、激活存储、重计算、通信、临时缓冲及格式转换；这是训练矩阵子账，不是完整训练 FLOPs 或设备容量需求。

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
