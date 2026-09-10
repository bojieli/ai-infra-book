# 实验 3-6 结果：各训练阶段的工作量

## 三个阶段的矩阵工作与 6ND 对照

| 模型 | 阶段 | 计损失 token | 输出头行数 | 前向 TFLOPs | 反向 TFLOPs | 训练矩阵合计 | 其中注意力 | 6ND | 矩阵/6ND |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen3-8b | 预训练（4K 序列，全 token 计损失） | 4096 | 4096 | 66.95 | 133.89 | 200.84 | 14.85 | 201.30 | 0.9977 |
| qwen3-8b | 长上下文中期训练（32K 序列，全 token 计损失） | 32768 | 32768 | 812.65 | 1625.30 | 2437.96 | 950.01 | 1610.36 | 1.5139 |
| qwen3-8b | SFT（4K 序列，仅 1/4 token 计损失） | 1024 | 1024 | 63.12 | 126.25 | 189.37 | 14.85 | 201.30 | 0.9408 |
| deepseek-v4-flash | 预训练（4K 序列，全 token 计损失） | — | — | 无统一训练适配器，改用下方 V4 子账 | | | | | |
| deepseek-v4-flash | 长上下文中期训练（32K 序列，全 token 计损失） | — | — | 无统一训练适配器，改用下方 V4 子账 | | | | | |
| deepseek-v4-flash | SFT（4K 序列，仅 1/4 token 计损失） | — | — | 无统一训练适配器，改用下方 V4 子账 | | | | | |

## V4-Flash 的训练子账（官方源码派生，非完整训练步）

| 子账 | 主要字段 |
| --- | --- |
| `v4-training-primitives` | （见 JSON） |
| `v4-attention-training` | forward_matrix_flops 1.082e+09；backward_matrix_flops 2.164e+09；forward_scalar_flops 2.13e+06；backward_scalar_flops 5.437e+08 |
| `v4-moe-training` | forward_matrix_flops 4.537e+10；backward_matrix_flops 9.073e+10；forward_scalar_flops 8.948e+06；backward_scalar_flops 2.369e+07 |
| `v4-compressor-training` | forward_matrix_flops 2.147e+09；backward_matrix_flops 4.295e+09；forward_scalar_flops 7.889e+05；backward_scalar_flops 1.908e+06 |
| `v4-hc-training` | forward_matrix_flops 1.046e+10；backward_matrix_flops 2.128e+10；forward_scalar_flops 7.367e+08；backward_scalar_flops 9.304e+08 |

## 6ND 漏掉的工作（Qwen3-8B 单步口径）

| 项目 | 数值 |
| --- | ---: |
| 前向标量 FLOPs | 0.566 GFLOPs |
| 反向标量 FLOPs | 1.095 GFLOPs |
| 优化器标量 FLOPs | 114.670 GFLOPs |
| 前向末保存的非线性中间量 | 0.972 GiB |
| 参数状态（未切分） | 137.308 GiB |

特殊函数原语计数：sqrt 8190735360、pow 2、rsqrt 193664、sigmoid 56623104、exp 28958720、max_compare 28811136、sin 16384、cos 16384、log 128

仍未知（不填造）：complete_training_step_flops、complete_activation_peak_bytes、complete_hbm_traffic_bytes、predicted_step_seconds
