# qwen-training-matrix — qwen3-32b

输入：`{"batch": 1, "gradient_bytes": 4, "head_strategy": "dense", "master_weight_bytes": 4, "routing": null, "supervised_tokens": 8192, "tokens": 8192}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 32,762,123,264 |
| input_tokens | 8,192 |
| loss_tokens | 8,192 |
| expert_assignments_per_layer | 0 |
| active_experts_per_layer | 0 |
| executed_head_rows | 8,192 |
| forward_matrix_flops | 594,395,556,478,976 |
| backward_matrix_flops | 1,188,791,112,957,952 |
| training_matrix_flops | 1,783,186,669,436,928 |
| attention_training_matrix_flops | 211,132,002,336,768 |
| six_nd_flops | 1,610,323,882,672,128 |
| matrix_minus_six_nd_flops | 172,862,786,764,800 |
| matrix_to_six_nd_ratio | 1.107346595691021 |
| unsharded_parameter_state_bytes | 589,718,218,752 |
| activation_peak_bytes | `null` |
| complete_training_step_flops | `null` |
| predicted_step_seconds | `null` |

| 矩阵 | 重复 | 单次前向 FLOPs | 每个梯度 FLOPs | 训练矩阵总 FLOPs |
| --- | ---: | ---: | ---: | ---: |
| q_proj | 64 | 687194767360 | 687194767360 | 131941395333120 |
| k_proj | 64 | 85899345920 | 85899345920 | 16492674416640 |
| v_proj | 64 | 85899345920 | 85899345920 | 16492674416640 |
| qk | 64 | 549822922752 | 549822922752 | 105566001168384 |
| pv | 64 | 549822922752 | 549822922752 | 105566001168384 |
| o_proj | 64 | 687194767360 | 687194767360 | 131941395333120 |
| gate_proj | 64 | 2147483648000 | 2147483648000 | 412316860416000 |
| up_proj | 64 | 2147483648000 | 2147483648000 | 412316860416000 |
| down_proj | 64 | 2147483648000 | 2147483648000 | 412316860416000 |
| lm_head | 1 | 12745315450880 | 12745315450880 | 38235946352640 |

每项包含两个梯度，形状与梯度名称见 JSON；参数状态按声明格式分列：

| 状态 | bytes |
| --- | ---: |
| bf16_weights | 65524246528 |
| gradients | 131048493056 |
| master_weights | 131048493056 |
| adam_first_moment_fp32 | 131048493056 |
| adam_second_moment_fp32 | 131048493056 |

计量条件：

- MoE 的每层路由直方图是显式情景，无 token drop 或容量填充；专家矩阵按各 n_e 求和。top-k 离散选择固定，router 矩阵仍计梯度，概率、合并、辅助损失和选择反向不在矩阵子账内。全部专家参数都纳入常驻状态，未激活专家不执行矩阵乘；6ND 用总参数仅作不适用的对照，不能预测 MoE 工作。
- 固定官方 Qwen3 Dense/MoE 配置，全参数训练，无历史 KV、无重计算；每个序列 T 个输入位置，D=B*T。loss_tokens 为调用方在移位、padding 和 mask 后给定的有效标签数，未假定等于原始文本 token 数。
- 每个线性矩阵列出前向、输入梯度、权重梯度；每次乘加计 2。QK/PV 各有两个输入梯度，按有效因果位置计数学工作；GQA 共享头的梯度归并算术另计，不用本表推断后端 tile 或矩形 kernel 工作。
- dense 输出头始终执行 B*T 行，loss mask 不自动降低矩阵 FLOPs。compact 明确假设先 gather 有监督 hidden 再计算输出头；backbone 仍执行全部行，未根据标签位置剪枝，gather/scatter 与稀疏梯度特化未计。
- 6ND 的 N 是全部参数，包括 embedding 查表与 norm；它们并非每 token 都执行参数矩阵乘。实际矩阵账单列输出头与因果注意力，因此差额不必为正。
- 状态是无分片、无 offload 的声明方案：BF16 权重、显式梯度字节和 master 字节、FP32 Adam 两份 moment；不声称是某框架默认，master=0 仅代表取消独立副本。
- 未包含 embedding 梯度 scatter、归一化/激活/softmax/损失的前反向、优化器更新算术、激活存储、重计算、通信、临时缓冲及格式转换；这是训练矩阵子账，不是完整训练 FLOPs 或设备容量需求。

固定来源：

- [configs/models/qwen3-32b/config.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/config.json)，SHA256 `97e295b63283935788fac5e4f8860862a56d4089538cafc93f0431f2ebe483bb`。
- [sources/qwen3-32b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/model.safetensors.index.json)，SHA256 `bed42c6c55274bc08a1f616bceb3bcb84b3f02cb6584c573bd18c6519291ecd0`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
