# 已实现计算的结果索引

由 `python3 calculations/calc.py reproduce` 生成；全书未完成项见 [计划](../PLAN.md)。

所有值是固定输入的分析结果。矩阵 FLOPs 包含选定输出头，不把特殊函数折算为矩阵吞吐。

| 场景 | 矩阵 TFLOPs | 权重 GiB | KV 结束时 GiB | 新写 KV GiB |
| --- | ---: | ---: | ---: | ---: |
| [qwen3-8b-prefill-8192](qwen3-8b-prefill-8192.md) | 133.594323354 | 15.256433487 | 1.125000000 | 1.125000000 |
| [qwen3-8b-decode-b1-s8192](qwen3-8b-decode-b1-s8192.md) | 0.019968623 | 15.256433487 | 1.125137329 | 0.000137329 |
| [qwen3-8b-decode-b64-s8192](qwen3-8b-decode-b64-s8192.md) | 1.277991846 | 15.256433487 | 72.008789062 | 0.008789062 |
| [qwen3-8b-prefix-6144-plus-2048](qwen3-8b-prefix-6144-plus-2048.md) | 37.110366077 | 15.256433487 | 1.125000000 | 0.281250000 |
| [qwen3-32b-prefill-8192](qwen3-32b-prefill-8192.md) | 581.651796853 | 61.024209976 | 2.000000000 | 2.000000000 |
| [qwen3-30b-a3b-prefill-8192](qwen3-30b-a3b-prefill-8192.md) | 71.128501977 | 56.870510101 | 0.750000000 | 0.750000000 |
| [qwen3-30b-a3b-decode-b1-s8192](qwen3-30b-a3b-decode-b1-s8192.md) | 0.012526551 | 56.870510101 | 0.750091553 | 0.000091553 |
| [qwen3-30b-a3b-decode-b64-s8192-balanced](qwen3-30b-a3b-decode-b64-s8192-balanced.md) | 0.801699267 | 56.870510101 | 48.005859375 | 0.005859375 |
| [qwen3-30b-a3b-decode-b64-s8192-concentrated](qwen3-30b-a3b-decode-b64-s8192-concentrated.md) | 0.801699267 | 56.870510101 | 48.005859375 | 0.005859375 |
| [qwen3-235b-a22b-prefill-8192](qwen3-235b-a22b-prefill-8192.md) | 446.535841087 | 437.896018028 | 1.468750000 | 1.468750000 |
| [qwen3-235b-a22b-decode-b1-s8192](qwen3-235b-a22b-decode-b1-s8192.md) | 0.068371284 | 437.896018028 | 1.468929291 | 0.000179291 |
| [qwen3-235b-a22b-decode-b64-s8192-balanced](qwen3-235b-a22b-decode-b64-s8192-balanced.md) | 4.375762174 | 437.896018028 | 94.011474609 | 0.011474609 |
| [qwen3-235b-a22b-decode-b64-s8192-concentrated](qwen3-235b-a22b-decode-b64-s8192-concentrated.md) | 4.375762174 | 437.896018028 | 94.011474609 | 0.011474609 |
| [llama70-prefill-8192](llama70-prefill-8192.md) | 1209.475629318 | 131.416519165 | 2.500000000 | 2.500000000 |
| [llama70-decode-8192](llama70-decode-8192.md) | 0.160480887 | 131.416519165 | 2.500305176 | 0.000305176 |
| [llama70-decode-batch8-32768](llama70-decode-batch8-32768.md) | 1.799243170 | 131.416519165 | 80.002441406 | 0.002441406 |
| [llama70-prefill-all-head-512](llama70-prefill-all-head-512.md) | 71.514024051 | 131.416519165 | 0.156250000 | 0.156250000 |
| [qwen3-32b-decode-b1-s32768](qwen3-32b-decode-b1-s32768.md) | 0.132688642 | 61.024209976 | 8.000244141 | 0.000244141 |
| [qwen3-32b-decode-b64-s32768](qwen3-32b-decode-b64-s32768.md) | 8.492073091 | 61.024209976 | 512.015625000 | 0.015625000 |
| [qwen3-30b-a3b-decode-b1-s32768](qwen3-30b-a3b-decode-b1-s32768.md) | 0.031853904 | 56.870510101 | 3.000091553 | 0.000091553 |
| [qwen3-30b-a3b-decode-b64-s32768-balanced](qwen3-30b-a3b-decode-b64-s32768-balanced.md) | 2.038649848 | 56.870510101 | 192.005859375 | 0.005859375 |

MoE 路由是显式场景输入；专家权重载荷按每层访问的专家并集计，不能当作实测 HBM。每专家矩阵见各场景明细。

| 场景 | 每层分派数 | 每层专家并集 | 专家矩阵 TFLOPs | 专家权重载荷 GiB |
| --- | ---: | ---: | ---: | ---: |
| [qwen3-30b-a3b-prefill-8192](qwen3-30b-a3b-prefill-8192.md) | 65536 | 128 | 29.686813950 | 54.000000000 |
| [qwen3-30b-a3b-decode-b1-s8192](qwen3-30b-a3b-decode-b1-s8192.md) | 8 | 8 | 0.003623879 | 3.375000000 |
| [qwen3-30b-a3b-decode-b64-s8192-balanced](qwen3-30b-a3b-decode-b64-s8192-balanced.md) | 512 | 128 | 0.231928234 | 54.000000000 |
| [qwen3-30b-a3b-decode-b64-s8192-concentrated](qwen3-30b-a3b-decode-b64-s8192-concentrated.md) | 512 | 8 | 0.231928234 | 3.375000000 |
| [qwen3-235b-a22b-prefill-8192](qwen3-235b-a22b-prefill-8192.md) | 65536 | 128 | 232.546709275 | 423.000000000 |
| [qwen3-235b-a22b-decode-b1-s8192](qwen3-235b-a22b-decode-b1-s8192.md) | 8 | 8 | 0.028387049 | 26.437500000 |
| [qwen3-235b-a22b-decode-b64-s8192-balanced](qwen3-235b-a22b-decode-b64-s8192-balanced.md) | 512 | 128 | 1.816771166 | 423.000000000 |
| [qwen3-235b-a22b-decode-b64-s8192-concentrated](qwen3-235b-a22b-decode-b64-s8192-concentrated.md) | 512 | 8 | 1.816771166 | 26.437500000 |
| [qwen3-30b-a3b-decode-b1-s32768](qwen3-30b-a3b-decode-b1-s32768.md) | 8 | 8 | 0.003623879 | 3.375000000 |
| [qwen3-30b-a3b-decode-b64-s32768-balanced](qwen3-30b-a3b-decode-b64-s32768-balanced.md) | 512 | 128 | 0.231928234 | 54.000000000 |

V4／K3 的 FFN 矩阵台账单列，尚非完整前向。统一 2-byte 对照载荷不代表实际混合量化格式。

| 场景 | FFN 矩阵 TFLOPs | routed TFLOPs | shared TFLOPs | latent TFLOPs | dense 首层 TFLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| [experts-deepseek-v4-flash-b64-balanced](experts-deepseek-v4-flash-b64-balanced.md) | 0.975360229 | 0.831076172 | 0.138512695 | 0.000000000 | 0.000000000 |
| [experts-deepseek-v4-flash-b64-concentrated](experts-deepseek-v4-flash-b64-concentrated.md) | 0.975360229 | 0.831076172 | 0.138512695 | 0.000000000 | 0.000000000 |
| [experts-deepseek-v4-pro-b64-balanced](experts-deepseek-v4-pro-b64-balanced.md) | 3.632082715 | 3.094792372 | 0.515798729 | 0.000000000 | 0.000000000 |
| [experts-deepseek-v4-pro-b64-concentrated](experts-deepseek-v4-pro-b64-concentrated.md) | 3.632082715 | 3.094792372 | 0.515798729 | 0.000000000 | 0.000000000 |
| [experts-kimi-k3-b64-balanced](experts-kimi-k3-b64-balanced.md) | 8.552957608 | 6.223407612 | 1.555851903 | 0.605053518 | 0.093012886 |
| [experts-kimi-k3-b64-concentrated](experts-kimi-k3-b64-concentrated.md) | 8.552957608 | 6.223407612 | 1.555851903 | 0.605053518 | 0.093012886 |

V4 mHC 独立子账（不含注意力／专家／词表头）：

| 场景 | 混合投影 GFLOPs | 普通算术 GFLOPs | mHC FP32 参数 MiB |
| --- | ---: | ---: | ---: |
| [hc-deepseek-v4-flash-b1-t8192](hc-deepseek-v4-flash-b1-t8192.md) | 555.124523 | 148.981473 | 129.258877 |
| [hc-deepseek-v4-flash-b64-t1](hc-deepseek-v4-flash-b64-t1.md) | 4.336910 | 1.163918 | 129.258877 |
| [hc-deepseek-v4-pro-b1-t8192](hc-deepseek-v4-pro-b1-t8192.md) | 1377.342325 | 368.094306 | 320.700085 |
| [hc-deepseek-v4-pro-b64-t1](hc-deepseek-v4-pro-b64-t1.md) | 10.760487 | 2.875737 | 320.700085 |

V4 注意力矩阵子账：投影、有效 QK/PV 与参考实现矩形索引点积分别计量。

| 场景 | 投影 TFLOPs | 有效 QK/PV TFLOPs | 参考索引 TFLOPs |
| --- | ---: | ---: | ---: |
| [attention-deepseek-v4-flash-b1-t8192-s0](attention-deepseek-v4-flash-b1-t8192-s0.md) | 83.309481 | 16.641044 | 5.772436 |
| [attention-deepseek-v4-flash-b64-t1-s8192](attention-deepseek-v4-flash-b64-t1-s8192.md) | 0.650855 | 0.147103 | 0.045097 |
| [attention-deepseek-v4-pro-b1-t8192-s0](attention-deepseek-v4-pro-b1-t8192-s0.md) | 318.877699 | 68.205087 | 8.246337 |
| [attention-deepseek-v4-pro-b64-t1-s8192](attention-deepseek-v4-pro-b64-t1-s8192.md) | 2.491232 | 0.679679 | 0.064425 |

V4 基础前向汇总：完整混合存储／访存仍未知，coverage 列明缺项；矩阵总数不可直接当时延。

| 场景 | 有效注意力口径 TFLOPs | 已知稀疏／专家 tile 口径 TFLOPs | 基础逻辑参数 |
| --- | ---: | ---: | ---: |
| [forward-deepseek-v4-flash-b1-t8192-s0](forward-deepseek-v4-flash-b1-t8192-s0.md) | 231.125253 | 233.313346 | 284,332,240,471 |
| [forward-deepseek-v4-flash-b64-t1-s8192](forward-deepseek-v4-flash-b64-t1-s8192.md) | 1.890532 | 18.789081 | 284,332,240,471 |
| [forward-deepseek-v4-pro-b1-t8192-s0](forward-deepseek-v4-pro-b1-t8192-s0.md) | 861.614907 | 880.408677 | 1,572,997,201,763 |
| [forward-deepseek-v4-pro-b64-t1-s8192](forward-deepseek-v4-pro-b64-t1-s8192.md) | 6.996793 | 102.935357 | 1,572,997,201,763 |

Kimi K3 文本前向：有效因果 MLA，递推或块式 KDA 数学口径；实际量化／后端工作仍见 coverage。

| 场景 | 矩阵 TFLOPs | 逻辑文本参数 | 持久状态 MiB |
| --- | ---: | ---: | ---: |
| [forward-kimi-k3-b1-t8192-s0-expanded](forward-kimi-k3-b1-t8192-s0-expanded.md) | 1744.701011 | 2,779,484,476,000 | 11953.406250 |
| [forward-kimi-k3-b1-t8192-s0-compact](forward-kimi-k3-b1-t8192-s0-compact.md) | 1863.462762 | 2,779,484,476,000 | 649.406250 |
| [forward-kimi-k3-b1-t1-s8192-expanded](forward-kimi-k3-b1-t1-s8192-expanded.md) | 0.220444 | 2,779,484,476,000 | 11954.812500 |
| [forward-kimi-k3-b1-t1-s8192-compact](forward-kimi-k3-b1-t1-s8192-compact.md) | 0.249438 | 2,779,484,476,000 | 649.432617 |

Kimi K3 MLA 两路径：compact 为代数替代方案，expanded 为固定 HF 缓存路径。

| 场景 | 投影 TFLOPs | 有效注意力 TFLOPs | MLA 缓存 MiB |
| --- | ---: | ---: | ---: |
| [k3-mla-expanded-b1-t8192-s0](k3-mla-expanded-b1-t8192-s0.md) | 91.302415 | 49.484063 | 11520.000000 |
| [k3-mla-expanded-b64-t1-s8192](k3-mla-expanded-b64-t1-s8192.md) | 0.713300 | 0.773188 | 737370.000000 |
| [k3-mla-compact-b1-t8192-s0](k3-mla-compact-b1-t8192-s0.md) | 91.302415 | 168.245814 | 216.000000 |
| [k3-mla-compact-b64-t1-s8192](k3-mla-compact-b64-t1-s8192.md) | 0.713300 | 2.628841 | 13825.687500 |

Kimi K3 KDA：投影和递推数学基线，T>1 不是实际 chunk kernel 工作。

| 场景 | 投影 TFLOPs | 递推等普通算术 GFLOPs | FP32 状态 MiB |
| --- | ---: | ---: | ---: |
| [k3-kda-b1-t1-s8192](k3-kda-b1-t1-s8192.md) | 0.061214 | 0.790223 | 414.000000 |
| [k3-kda-b64-t1-s8192](k3-kda-b64-t1-s8192.md) | 3.917702 | 50.574293 | 26496.000000 |
| [k3-kda-b1-t8192-s0](k3-kda-b1-t8192-s0.md) | 501.465886 | 6473.509503 | 414.000000 |

Kimi K3 AttnRes：块堆栈仅在一次 forward 内随深度保留，不是跨 token KV。

| 场景 | 加权矩阵 GFLOPs | 普通算术 GFLOPs | 最后块堆栈 MiB |
| --- | ---: | ---: | ---: |
| [k3-attn-res-b1-t8192](k3-attn-res-b1-t8192.md) | 117.675393 | 304.665123 | 896.000000 |
| [k3-attn-res-b64-t1](k3-attn-res-b64-t1.md) | 0.919339 | 2.381519 | 7.000000 |

KDA chunk 的已确认存活子集：不含所有输入／工作区，不是完整峰值。

| 场景 | 每层 chunk state MiB | 已知存活子集最大 MiB |
| --- | ---: | ---: |
| [k3-kda-chunk-t8192-c64](k3-kda-chunk-t8192-c64.md) | 384.000000 | 1926.000000 |
| [k3-kda-chunk-t65-c64](k3-kda-chunk-t65-c64.md) | 6.000000 | 24.187500 |
| [k3-kda-chunk-t8192-c32](k3-kda-chunk-t8192-c32.md) | 768.000000 | 2214.000000 |

整段生成缓存：历史逻辑读取／追加写入／最终容量分别计量，非实际 HBM。

| 场景 | 累计旧历史读取 GiB | 累计追加 GiB | 最终持久状态 GiB |
| --- | ---: | ---: | ---: |
| [cache-sequence-qwen3-8b-b1](cache-sequence-qwen3-8b-b1.md) | 1223.929688 | 0.140625 | 1.265625 |
| [cache-sequence-qwen3-8b-b64](cache-sequence-qwen3-8b-b64.md) | 78331.500000 | 9.000000 | 81.000000 |
| [cache-sequence-qwen3-235b-a22b-b1](cache-sequence-qwen3-235b-a22b-b1.md) | 1597.908203 | 0.183594 | 1.652344 |
| [cache-sequence-qwen3-235b-a22b-b64](cache-sequence-qwen3-235b-a22b-b64.md) | 102266.125000 | 11.750000 | 105.750000 |
| [cache-sequence-kimi-k3-b1](cache-sequence-kimi-k3-b1.md) | 12239.296875 | 1.406250 | 13.079498 |
| [cache-sequence-kimi-k3-b64](cache-sequence-kimi-k3-b64.md) | 783315.000000 | 90.000000 | 837.087891 |

第 1 章教学单位与容量：不是某个真实 checkpoint 的部署证明。

| 场景 | 权重 GB | 权重 GiB | 总容量够 | 每卡预算够 | 串行传输模型 ms |
| --- | ---: | ---: | --- | --- | ---: |
| [basics-70b-bf16-one-card](basics-70b-bf16-one-card.md) | 140.000000 | 130.385160 | False | False | 2800.003000 |
| [basics-70b-bf16-balanced](basics-70b-bf16-balanced.md) | 140.000000 | 130.385160 | True | True | 2800.003000 |
| [basics-70b-bf16-skewed](basics-70b-bf16-skewed.md) | 140.000000 | 130.385160 | True | False | 2800.003000 |
| [basics-70b-int8-one-card](basics-70b-int8-one-card.md) | 70.000000 | 65.192580 | True | True | 1400.003000 |
| [basics-small-message](basics-small-message.md) | 140.000000 | 130.385160 | True | True | 0.003082 |
| [basics-large-message](basics-large-message.md) | 140.000000 | 130.385160 | True | True | 1.680722 |

独立访存窗口：同一 Qwen KV 载荷，接口／延迟／事务并发均为声明的教学条件。

| 场景 | 所需事务数 | 吞吐上界 GB/s | KV 服务下界 ms |
| --- | ---: | ---: | ---: |
| [window-qwen3-8b-n128](window-qwen3-8b-n128.md) | 3907 | 32.768000 | 36.864000 |
| [window-qwen3-8b-n4096](window-qwen3-8b-n4096.md) | 3907 | 1000.000000 | 1.207960 |
| [window-qwen3-8b-double-bandwidth](window-qwen3-8b-double-bandwidth.md) | 7813 | 1048.576000 | 1.152000 |
| [window-qwen3-8b-longer-latency](window-qwen3-8b-longer-latency.md) | 6250 | 655.360000 | 1.843200 |
| [window-qwen3-8b-rtx4090-n128](window-qwen3-8b-rtx4090-n128.md) | 3938 | 32.768000 | 36.864000 |
| [window-qwen3-8b-rtx4090-n4096](window-qwen3-8b-rtx4090-n4096.md) | 3938 | 1008.000000 | 1.198373 |
| [window-qwen3-8b-rtx5090-n4096](window-qwen3-8b-rtx5090-n4096.md) | 7000 | 1048.576000 | 1.152000 |
| [window-qwen3-8b-rtx5090-l800](window-qwen3-8b-rtx5090-l800.md) | 11200 | 655.360000 | 1.843200 |
| [remote-window-book](remote-window-book.md) | 391 | 16.384000 | 73.728000 |
| [remote-window-serial](remote-window-serial.md) | 391 | 2.560000 | 471.859200 |
| [remote-window-source-wait](remote-window-source-wait.md) | 391 | 0.128000 | 9437.184000 |
| [remote-window-enlarged](remote-window-enlarged.md) | 391 | 2.560000 | 471.859200 |
| [remote-window-fast-service](remote-window-fast-service.md) | 391 | 42.666667 | 28.311552 |

70B 初步解码预算：声明存储位宽与 BF16 计算分开，容量失败不输出可运行下界。

| 场景 | 计算服务 ms | 内存服务 ms | 声明预算可容纳 | 交叉 batch |
| --- | ---: | ---: | --- | ---: |
| [decode-budget-base](decode-budget-base.md) | 0.141500 | 20.895522 | True | 148 |
| [decode-budget-double-compute](decode-budget-double-compute.md) | 0.070750 | 20.895522 | True | 296 |
| [decode-budget-double-bandwidth](decode-budget-double-bandwidth.md) | 0.141500 | 10.447761 | True | 74 |
| [decode-budget-four-bit](decode-budget-four-bit.md) | 0.141500 | 10.447761 | True | 74 |
| [decode-budget-bf16-capacity-fail](decode-budget-bf16-capacity-fail.md) | 0.141500 | 41.791045 | False | 296 |
| [decode-budget-b64](decode-budget-b64.md) | 9.055994 | 20.895522 | True | 148 |
| [decode-budget-b160](decode-budget-b160.md) | 22.639984 | 20.895522 | True | 148 |
| [decode-budget-b64-kv-capacity-fail](decode-budget-b64-kv-capacity-fail.md) | 9.055994 | 41.408799 | False | None |

Qwen Dense ring：独立有向边、串行 2L 次归约的教学预算。

| 场景 | 每 rank 消息 bytes | 每 rank 发送 bytes | 每次 μs | 2L 次 ms |
| --- | ---: | ---: | ---: | ---: |
| [ring-qwen3-8b-t1-p4](ring-qwen3-8b-t1-p4.md) | 8192 | 12288 | 12.245760 | 0.881695 |
| [ring-qwen3-8b-t1-p8](ring-qwen3-8b-t1-p8.md) | 8192 | 14336 | 28.286720 | 2.036644 |
| [ring-qwen3-8b-t4-p8](ring-qwen3-8b-t4-p8.md) | 32768 | 57344 | 29.146880 | 2.098575 |
| [ring-qwen3-8b-t16-p8](ring-qwen3-8b-t16-p8.md) | 131072 | 229376 | 32.587520 | 2.346301 |
| [ring-qwen3-8b-t8192-p8](ring-qwen3-8b-t8192-p8.md) | 67108864 | 117440512 | 2376.810240 | 171.130337 |
| [ring-qwen3-8b-t1-p8-double-bandwidth](ring-qwen3-8b-t1-p8-double-bandwidth.md) | 8192 | 14336 | 28.143360 | 2.026322 |
| [ring-qwen3-32b-t1-p2-h100](ring-qwen3-32b-t1-p2-h100.md) | 10240 | 10240 | 1.666756 | 0.213345 |
| [ring-qwen3-32b-t1-p4-h100](ring-qwen3-32b-t1-p4-h100.md) | 10240 | 15360 | 4.966133 | 0.635665 |
| [ring-qwen3-32b-t1-p8-h100](ring-qwen3-32b-t1-p8-h100.md) | 10240 | 17920 | 11.547822 | 1.478121 |
| [ring-qwen3-32b-t8192-p8-h100](ring-qwen3-32b-t8192-p8-h100.md) | 83886080 | 146800640 | 337.731644 | 43.229650 |

未分段 binomial tree：与 ring 同输入，独立比较轮次、最忙 rank 与关键路径。

| 场景 | 轮次 | 全网发送 bytes | 最多 rank 发送 bytes | 每次 μs |
| --- | ---: | ---: | ---: | ---: |
| [tree-qwen3-8b-t1-p4](tree-qwen3-8b-t1-p4.md) | 4 | 49152 | 16384 | 8.655360 |
| [tree-qwen3-8b-t1-p8](tree-qwen3-8b-t1-p8.md) | 6 | 114688 | 24576 | 12.983040 |
| [tree-qwen3-8b-t16-p8](tree-qwen3-8b-t16-p8.md) | 6 | 1835008 | 393216 | 27.728640 |
| [tree-qwen3-8b-t8192-p8](tree-qwen3-8b-t8192-p8.md) | 6 | 939524096 | 201326592 | 8065.063680 |
| [tree-qwen3-8b-t1-p5](tree-qwen3-8b-t1-p5.md) | 6 | 65536 | 24576 | 12.983040 |
| [tree-qwen3-32b-t1-p8-h100](tree-qwen3-32b-t1-p8-h100.md) | 6 | 143360 | 30720 | 5.068533 |
| [tree-qwen3-32b-t8192-p8-h100](tree-qwen3-32b-t8192-p8-h100.md) | 6 | 1174405120 | 251658240 | 1123.413067 |

MoE assignment all-to-all：无目的端去重，源—目的计数明确。

| 场景 | Dispatch bytes | 最大 rank 接收 bytes | Dispatch μs |
| --- | ---: | ---: | ---: |
| [all-to-all-qwen235-t1-balanced](all-to-all-qwen235-t1-balanced.md) | 458752 | 57344 | 15.146880 |
| [all-to-all-qwen235-t1-hotspot](all-to-all-qwen235-t1-hotspot.md) | 458752 | 458752 | 23.175040 |
| [all-to-all-qwen235-t64-balanced](all-to-all-qwen235-t64-balanced.md) | 29360128 | 3670016 | 87.400320 |
| [all-to-all-qwen235-t64-hotspot](all-to-all-qwen235-t64-hotspot.md) | 29360128 | 29360128 | 601.202560 |

PCIe／NUMA 中转：逻辑消息不变，逐物理资源载荷随放置变化。

| 场景 | 逻辑发送 MiB | 聚合资源下界 ms | 逐轮资源下界之和 ms |
| --- | ---: | ---: | ---: |
| [staging-all-a-grouped](staging-all-a-grouped.md) | 48.000000 | 3.145728 | 3.145728 |
| [staging-local-grouped](staging-local-grouped.md) | 48.000000 | 1.572864 | 1.572864 |
| [staging-local-alternating](staging-local-alternating.md) | 48.000000 | 3.145728 | 3.145728 |

MoE 目的端去重：显式 token 路由决定复用，不从汇总直方图猜测。

| 场景 | 原 dispatch bytes | 去重 dispatch bytes | 原 combine bytes | 目的端合并返回 bytes |
| --- | ---: | ---: | ---: | ---: |
| [moe-dedup-qwen235-clustered](moe-dedup-qwen235-clustered.md) | 29360128 | 3670016 | 58720256 | 7340032 |
| [moe-dedup-qwen235-spread](moe-dedup-qwen235-spread.md) | 29360128 | 29360128 | 58720256 | 58720256 |

实际权重形状的单设备容量扫描：低位宽是声明的存储方案，非实际部署保证。

| 场景 | BF16 权重 GiB | 8-bit 方案 GiB | 4-bit 方案 GiB | 每请求 KV GiB |
| --- | ---: | ---: | ---: | ---: |
| [capacity-qwen3-8b-n8192](capacity-qwen3-8b-n8192.md) | 15.256433 | 8.888758 | 5.654383 | 1.125000 |
| [capacity-qwen3-8b-n32768](capacity-qwen3-8b-n32768.md) | 15.256433 | 8.888758 | 5.654383 | 4.500000 |
| [capacity-qwen3-32b-n8192](capacity-qwen3-32b-n8192.md) | 61.024210 | 32.415812 | 17.884562 | 2.000000 |
| [capacity-qwen3-32b-n32768](capacity-qwen3-32b-n32768.md) | 61.024210 | 32.415812 | 17.884562 | 8.000000 |
| [capacity-qwen3-235b-a22b-n8192](capacity-qwen3-235b-a22b-n8192.md) | 437.896018 | 223.556052 | 114.684958 | 1.468750 |
| [capacity-qwen3-235b-a22b-n32768](capacity-qwen3-235b-a22b-n32768.md) | 437.896018 | 223.556052 | 114.684958 | 5.875000 |
| [llama70-capacity-8k](llama70-capacity-8k.md) | 131.416519 | 68.662613 | 36.787613 | 2.500000 |
| [llama70-capacity-32k](llama70-capacity-32k.md) | 131.416519 | 68.662613 | 36.787613 | 10.000000 |
| [llama70-capacity-tail-group](llama70-capacity-tail-group.md) | 131.416519 | 67.803543 | 35.928543 | 2.500000 |
| [llama70-capacity-boundary](llama70-capacity-boundary.md) | 131.416519 | 68.662613 | 36.787613 | 2.500000 |

Dense 逐卡 TP/PP/DP：参数复制、KV 头身份和首尾阶段单独处理。

| 场景 | 卡数 | 物理权重 GiB | 最大单卡驻留 GiB | 全卡声明预算够放 |
| --- | ---: | ---: | ---: | --- |
| [placement-qwen8-tp1-pp1-dp8](placement-qwen8-tp1-pp1-dp8.md) | 8 | 122.051468 | 18.381571 | True |
| [placement-qwen8-tp2-pp1-dp4](placement-qwen8-tp2-pp1-dp4.md) | 8 | 61.028030 | 10.191072 | True |
| [placement-qwen8-tp4-pp1-dp2](placement-qwen8-tp4-pp1-dp2.md) | 8 | 30.516312 | 6.095823 | True |
| [placement-qwen8-tp8-pp1-dp1](placement-qwen8-tp8-pp1-dp1.md) | 8 | 15.260452 | 4.048199 | True |
| [placement-qwen8-tp2-pp4-dp1](placement-qwen8-tp2-pp4-dp1.md) | 8 | 15.257008 | 4.337569 | True |
| [placement-qwen8-tp1-pp8-dp1](placement-qwen8-tp1-pp8-dp1.md) | 8 | 15.256433 | 5.112402 | True |
| [placement-qwen8-tp16-pp1-dp1](placement-qwen8-tp16-pp1-dp1.md) | 16 | 15.827545 | 3.129864 | True |
| [placement-qwen32-tp8](placement-qwen32-tp8.md) | 8 | 61.033035 | 9.879160 | True |
| [llama70-placement-tp8](llama70-placement-tp8.md) | 8 | 131.433716 | 18.741753 | True |
| [llama70-placement-tp4-pp2](llama70-placement-tp4-pp2.md) | 8 | 131.423889 | 18.740532 | True |
| [llama70-placement-tp2-pp4](llama70-placement-tp2-pp4.md) | 8 | 131.418976 | 19.229179 | True |
| [llama70-placement-pp8](llama70-placement-pp8.md) | 8 | 131.416519 | 20.207390 | True |
| [llama70-placement-tp4-dp2](llama70-placement-tp4-dp2.md) | 8 | 262.847778 | 35.481049 | False |
| [llama70-placement-tp16-kv-replica](llama70-placement-tp16-kv-replica.md) | 16 | 133.953369 | 10.684624 | True |

Dense 完整基础通信路径：嵌入、层输出、PP、最后 logits、token 回传；非完整迭代时延。

| 场景 | 每副本发送 bytes | 启动 ms | 带宽 ms | 串行通信模型 ms |
| --- | ---: | ---: | ---: | ---: |
| [dense-comm-qwen8-tp8-pp1-t1](dense-comm-qwen8-tp8-pp1-t1.md) | 12626460 | 2.064000 | 0.031566 | 2.095566 |
| [dense-comm-qwen8-tp8-pp1-t8192](dense-comm-qwen8-tp8-pp1-t8192.md) | 68589513244 | 2.064000 | 171.473783 | 173.537783 |
| [dense-comm-qwen8-tp2-pp4-t1](dense-comm-qwen8-tp2-pp4-t1.md) | 1852936 | 0.304000 | 0.018529 | 0.322529 |
| [dense-comm-qwen8-tp1-pp8-t1](dense-comm-qwen8-tp1-pp8-t1.md) | 57348 | 0.016000 | 0.001147 | 0.017147 |

FIFO 生成流水：耗时为显式输入，反馈依赖与边界缓冲分别调度。

| 场景 | 首完成 ms | 全部完成 ms | 边界缓冲存活峰值 bytes |
| --- | ---: | ---: | ---: |
| [pipeline-single-request](pipeline-single-request.md) | 4.300000 | 17.500000 | 16384 |
| [pipeline-four-groups](pipeline-four-groups.md) | 4.300000 | 20.500000 | 40960 |
| [pipeline-eight-groups](pipeline-eight-groups.md) | 4.300000 | 35.300000 | 40960 |
| [pipeline-slow-link](pipeline-slow-link.md) | 10.000000 | 46.300000 | 57344 |
| [pipeline-imbalanced-stage](pipeline-imbalanced-stage.md) | 5.300000 | 35.300000 | 40960 |
| [pipeline-finite-1-slots](pipeline-finite-1-slots.md) | 4.300000 | 20.800000 | 49152 |
| [pipeline-finite-2-slots](pipeline-finite-2-slots.md) | 4.300000 | 20.500000 | 57344 |
| [pipeline-finite-slow-link](pipeline-finite-slow-link.md) | 10.000000 | 55.000000 | 49152 |

Dense 训练矩阵子账：有效因果工作、6ND 与监督 mask 分列。

| 场景 | 训练矩阵 TFLOPs | 6ND TFLOPs | 输出头行数 | 参数状态 GiB |
| --- | ---: | ---: | ---: | ---: |
| [training-qwen3-8b-t8192](training-qwen3-8b-t8192.md) | 431.367993 | 402.591024 | 8192 | 137.307901 |
| [training-qwen3-8b-mask-half](training-qwen3-8b-mask-half.md) | 431.367993 | 402.591024 | 8192 | 137.307901 |
| [training-qwen3-8b-compact-half](training-qwen3-8b-compact-half.md) | 416.073615 | 402.591024 | 4096 | 137.307901 |
| [training-qwen3-8b-t32768](training-qwen3-8b-t32768.md) | 2437.955507 | 1610.364098 | 32768 | 137.307901 |
| [training-qwen3-32b-t8192](training-qwen3-32b-t8192.md) | 1783.186669 | 1610.323883 | 8192 | 549.217890 |
| [training-qwen3-235b-balanced](training-qwen3-235b-balanced.md) | 1370.192546 | 11555.322326 | 8192 | 3941.064162 |
| [training-qwen3-235b-concentrated](training-qwen3-235b-concentrated.md) | 1370.192546 | 11555.322326 | 8192 | 3941.064162 |

RL 同一候选／有效样本批次：矩阵工作与权重交接，非完整周期时延。

| 场景 | 候选 | 接受 | 周期矩阵 TFLOPs | 每有效样本 TFLOPs |
| --- | ---: | ---: | ---: | ---: |
| [rl-qwen8-base](rl-qwen8-base.md) | 32 | 16 | 2181.558727 | 136.347420 |
| [rl-qwen8-low-acceptance](rl-qwen8-low-acceptance.md) | 64 | 16 | 3410.701494 | 213.168843 |
| [rl-qwen8-compact](rl-qwen8-compact.md) | 32 | 16 | 2079.695777 | 129.980986 |
| [rl-qwen8-teacher-update](rl-qwen8-teacher-update.md) | 32 | 16 | 3768.918661 | 235.557416 |
| [rl-qwen235-base](rl-qwen235-base.md) | 32 | 16 | 6420.684167 | 401.292760 |

RL 显式供给情景：共享池需求相加，流水上界不保证可实现。

| 场景 | 串行组件 s | 理想流水间隔下界 s | 限制池 |
| --- | ---: | ---: | --- |
| [rl-supply-base](rl-supply-base.md) | 17.242938 | 8.778509 | ['actor'] |
| [rl-supply-double-actor](rl-supply-double-actor.md) | 12.853683 | 4.762080 | ['learner'] |
| [rl-supply-double-learner](rl-supply-double-learner.md) | 14.861898 | 8.778509 | ['actor'] |
| [rl-supply-low-acceptance](rl-supply-low-acceptance.md) | 29.396166 | 17.557017 | ['actor'] |
| [rl-supply-shared-gpu](rl-supply-shared-gpu.md) | 17.242938 | 16.715308 | ['shared_gpu'] |

成对请求轨迹：服务时长显式输入，FIFO 等待与 KV 存活复算。

| 场景 | 平均输入 | 平均输出 | p95 延迟 ms | KV 峰值 MiB |
| --- | ---: | ---: | ---: | ---: |
| [trace-qwen8-uniform](trace-qwen8-uniform.md) | 1024.0 | 128.0 | 255.048000 | 323.718750 |
| [trace-qwen8-correlated](trace-qwen8-correlated.md) | 1024.0 | 128.0 | 318.060000 | 468.000000 |
| [trace-qwen8-anticorrelated](trace-qwen8-anticorrelated.md) | 1024.0 | 128.0 | 255.548000 | 323.718750 |
| [trace-qwen8-spaced](trace-qwen8-spaced.md) | 1024.0 | 128.0 | 192.536000 | 242.859375 |
| [trace-qwen235-correlated](trace-qwen235-correlated.md) | 1024.0 | 128.0 | 318.060000 | 611.000000 |
| [trace-qwen8-capacity-tight](trace-qwen8-capacity-tight.md) | 1024.0 | 128.0 | 510.596000 | 242.859375 |
| [trace-qwen8-capacity-roomy](trace-qwen8-capacity-roomy.md) | 1024.0 | 128.0 | 318.060000 | 468.000000 |

真实 Agent 轨迹复算：模型墙钟与条件式替换，保留任务质量差异。

| 场景 | 轮数 | 实际总秒数 | 替换后条件秒数 | 原任务检查通过数 |
| --- | ---: | ---: | ---: | ---: |
| [agent-thinking-off](agent-thinking-off.md) | 12 | 13.802765 | 13.802765 | 315/1013 |
| [agent-thinking-on](agent-thinking-on.md) | 4 | 76.510279 | 76.510279 | 1013/1013 |
| [agent-thinking-on-double-model](agent-thinking-on-double-model.md) | 4 | 76.510279 | 38.363458 | 1013/1013 |
| [agent-thinking-on-double-first](agent-thinking-on-double-first.md) | 4 | 76.510279 | 58.322623 | 1013/1013 |

实时音频教学时序：固定截止、实际停顿、抖动缓冲与静音响应分列。

| 场景 | 首次播放 ms | 截止未到块数 | 新增停顿 ms | ready queue bytes |
| --- | ---: | ---: | ---: | ---: |
| [audio-timing-base](audio-timing-base.md) | 78.000000 | 1 | 5.000000 | 2880 |
| [audio-timing-no-buffer](audio-timing-no-buffer.md) | 38.000000 | 1 | 45.000000 | 2880 |
| [audio-timing-large-buffer](audio-timing-large-buffer.md) | 98.000000 | 0 | 0.000000 | 2880 |
| [audio-timing-slow-model](audio-timing-slow-model.md) | 91.000000 | 1 | 15.000000 | 1920 |
| [audio-timing-interrupt](audio-timing-interrupt.md) | 78.000000 | 1 | 5.000000 | 2880 |

Qwen 单支投影分块：候选内最小接口流量，不是 HBM 测量或性能最优。

| 场景 | 可行候选 | 选中 m/k/n | 下一层 bytes |
| --- | ---: | --- | ---: |
| [gemm-tiles-qwen8](gemm-tiles-qwen8.md) | 3 | [128, 32, 128] | 1635778560 |
| [gemm-tiles-qwen8-24k](gemm-tiles-qwen8-24k.md) | 2 | [64, 32, 64] | 3246391296 |
| [gemm-tiles-qwen8-double-buffer](gemm-tiles-qwen8-double-buffer.md) | 2 | [64, 32, 64] | 3246391296 |
| [gemm-tiles-qwen8-partials](gemm-tiles-qwen8-partials.md) | 3 | [128, 32, 128] | 14420017152 |
| [gemm-tiles-qwen8-tail](gemm-tiles-qwen8-tail.md) | 3 | [128, 32, 128] | 1737252864 |

RMSNorm 分片归约：额外输入重读、partial／inverse 与组数，非加速保证。

| 场景 | D | partial bytes | 额外接口 bytes |
| --- | ---: | ---: | ---: |
| [rmsnorm-row1-split8](rmsnorm-row1-split8.md) | 4096 | 32 | 8292 |
| [rmsnorm-row1024-split8](rmsnorm-row1024-split8.md) | 4096 | 32768 | 8491008 |
| [rmsnorm-row1-wide](rmsnorm-row1-wide.md) | 65536 | 32 | 131172 |
| [rmsnorm-row1-tail](rmsnorm-row1-tail.md) | 4096 | 28 | 8280 |

标量 bank 服务：padding／广播只在声明的请求与端口模型下比较。

| 场景 | 分配 bytes | 请求 bytes | 服务轮数 |
| --- | ---: | ---: | ---: |
| [bank-column-stride32](bank-column-stride32.md) | 4096 | 128 | 32 |
| [bank-column-stride33](bank-column-stride33.md) | 4224 | 128 | 1 |
| [bank-row-stride32](bank-row-stride32.md) | 4096 | 128 | 1 |
| [bank-same-word-no-broadcast](bank-same-word-no-broadcast.md) | 4096 | 128 | 32 |
| [bank-same-word-broadcast](bank-same-word-broadcast.md) | 4096 | 128 | 1 |
| [bank-column-two-ports](bank-column-two-ports.md) | 4096 | 128 | 16 |

小矩阵 C 源码数组访问：匹配原实验记录，编译器／缓存流量不推断。

| 场景 | FLOPs | 候选 | 匹配实测候选 |
| --- | ---: | ---: | ---: |
| [loop-access-64-64-64](loop-access-64-64-64.md) | 524288 | 8 | 8 |
| [loop-access-128-512-64](loop-access-128-512-64.md) | 8388608 | 8 | 8 |
| [loop-access-256-128-256](loop-access-256-128-256.md) | 16777216 | 8 | 8 |
| [loop-access-127-257-65](loop-access-127-257-65.md) | 4243070 | 8 | 8 |

点式融合链：完整中间张量物化与生命周期，实际局部scratch另计。

| 场景 | 分开接口 bytes | 融合接口 bytes | 分开张量峰值 bytes | 融合张量峰值 bytes |
| --- | ---: | ---: | ---: | ---: |
| [fusion-qwen8-pointwise](fusion-qwen8-pointwise.md) | 163577856 | 62914560 | 75497472 | 62914560 |
| [fusion-qwen8-layout](fusion-qwen8-layout.md) | 213909504 | 62914560 | 75497472 | 62914560 |
| [fusion-qwen8-decode](fusion-qwen8-decode.md) | 159744 | 61440 | 73728 | 61440 |
| [fusion-qwen32-pointwise](fusion-qwen32-pointwise.md) | 340787200 | 131072000 | 157286400 | 131072000 |

量化融入专家 GEMM：宽输入重读与前缀尺度语义分开。

| 场景 | 独立量化 MiB | 全行尺度融合 MiB | 前缀尺度融合 MiB |
| --- | ---: | ---: | ---: |
| [quant-gemm-qwen235-base](quant-gemm-qwen235-base.md) | 444.000000 | 620.000000 | 588.000000 |
| [quant-gemm-qwen235-wide-tile](quant-gemm-qwen235-wide-tile.md) | 268.000000 | 268.000000 | 236.000000 |
| [quant-gemm-qwen235-tail](quant-gemm-qwen235-tail.md) | 466.065430 | 658.112305 | 626.104492 |
| [quant-gemm-qwen30](quant-gemm-qwen30.md) | 126.000000 | 166.000000 | 150.000000 |

融合数值反例：精确FP8舍入与不可恢复的局部状态。

| 场景 | 整行输出 | 前缀输出 | 精确差值 | FP16后相等 |
| --- | --- | --- | --- | --- |
| [fusion-numerics-small-first](fusion-numerics-small-first.md) | 55/56 | 1 | 1/56 | False |
| [fusion-numerics-large-first](fusion-numerics-large-first.md) | 55/56 | 55/56 | 0 | True |

在线Softmax状态：顺序／树形合并与错误等权平均对照。

| 场景 | 直接输出 | 顺序误差 | 等权平均误差 |
| --- | --- | ---: | ---: |
| [online-softmax-book](online-softmax-book.md) | [-0.14285714285714285] | 0.0 | 0.3095238095238096 |
| [online-softmax-empty](online-softmax-empty.md) | [2.4621171572600096, -0.9242343145200195] | 0.0 | 0.9242343145200195 |
| [online-softmax-all-masked](online-softmax-all-masked.md) | None | None | None |

单头注意力分块：显式容量排布、KV扫描、因果边界与循环缩放。

| 场景 | 有效矩阵 FLOPs | 可行候选 | 候选最少接口 bytes |
| --- | ---: | ---: | ---: |
| [attention-tiles-book](attention-tiles-book.md) | 34359738368 | 3 | 213909504 |
| [attention-tiles-causal](attention-tiles-causal.md) | 17181966336 | 3 | 112503808 |
| [attention-tiles-two-slots](attention-tiles-two-slots.md) | 34359738368 | 3 | 213909504 |
| [attention-tiles-tail](attention-tiles-tail.md) | 4293120 | 1 | 347136 |
| [attention-tiles-rtxpro6000](attention-tiles-rtxpro6000.md) | 34359738368 | 3 | 272629760 |

VL请求阶段连接：视觉编码、语言prefill、增长历史decode。

| 场景 | 总矩阵FLOPs | prompt位置 | decode调用 | 最后KV bytes |
| --- | ---: | ---: | ---: | ---: |
| [vl-request-book](vl-request-book.md) | 22131747848192 | 2000 | 127 | 313638912 |
| [vl-request-all-ec-hit](vl-request-all-ec-hit.md) | 16890545569792 | 2000 | 127 | 313638912 |
| [vl-request-first-output](vl-request-first-output.md) | 20955481374720 | 2000 | 0 | 294912000 |
| [vl-request-single](vl-request-single.md) | 8399740731392 | 800 | 127 | 136691712 |
| [vl-request-long-output](vl-request-long-output.md) | 30700765446144 | 2000 | 1023 | 445759488 |
| [vl-request-mixed](vl-request-mixed.md) | 7422667653120 | 720 | 127 | 124895232 |
| [vl-request-mixed-large-hit](vl-request-mixed-large-hit.md) | 6642057347072 | 720 | 127 | 124895232 |
| [vl-request-balanced-area](vl-request-balanced-area.md) | 7393676623872 | 720 | 127 | 124895232 |
| [vl-position-one-image-first-token](vl-position-one-image-first-token.md) | 1064946434048 | 109 | 0 | 16072704 |
| [vl-position-one-image-cache-hit-decode](vl-position-one-image-cache-hit-decode.md) | 820706803712 | 109 | 3 | 16515072 |
| [vl-position-mixed-images-two-turn-boundaries](vl-position-mixed-images-two-turn-boundaries.md) | 1880394170368 | 212 | 7 | 32292864 |
| [vl-position-four-640-images](vl-position-four-640-images.md) | 22131747848192 | 2000 | 127 | 313638912 |

有限重试路径：所有尝试费用与质量/时限分母。

| 场景 | 成功概率 | 质量且按时概率 | 每质量成功费用 |
| --- | --- | --- | --- |
| [retry-paths-book](retry-paths-book.md) | 3117/3125 | 594/625 | 91/6234 |
| [retry-paths-tight](retry-paths-tight.md) | 3117/3125 | 109/125 | 91/6234 |
| [retry-paths-relaxed](retry-paths-relaxed.md) | 3117/3125 | 3117/3125 | 91/6234 |
| [retry-paths-impossible](retry-paths-impossible.md) | 3117/3125 | 0 | 91/6234 |

视觉编码单独计量：patch、视觉block、merger/DeepStack，不含语言prefill。

| 场景 | 每图矩阵FLOPs | 本请求矩阵FLOPs | 编码次数 |
| --- | ---: | ---: | ---: |
| [vision-encoding-book](vision-encoding-book.md) | 1310300569600 | 5241202278400 | 4 |
| [vision-encoding-single](vision-encoding-single.md) | 1310300569600 | 1310300569600 | 1 |
| [vision-encoding-three-hits](vision-encoding-three-hits.md) | 1310300569600 | 1310300569600 | 1 |
| [vision-encoding-all-hit](vision-encoding-all-hit.md) | 1310300569600 | 0 | 0 |
| [vision-encoding-larger](vision-encoding-larger.md) | 1389027655680 | 5556110622720 | 4 |
| [vision-encoding-fp32](vision-encoding-fp32.md) | 1310300569600 | 5241202278400 | 4 |

生成模型阶段矩阵：执行次数由时间轴/码本/去噪循环明确计入，缺项不冒充总量。

| 场景 | 范围 | 已计矩阵FLOPs |
| --- | --- | ---: |
| [omni-audio-book](omni-audio-book.md) | 音频Transformer与桥接 | 140161941504 |
| [omni-audio-one-frame](omni-audio-one-frame.md) | 音频Transformer与桥接 | 102852239360 |
| [omni-audio-b4](omni-audio-b4.md) | 音频Transformer与桥接 | 560647766016 |
| [fish-audio-book](fish-audio-book.md) | 音频Transformer与桥接 | 196491214848 |
| [fish-audio-long](fish-audio-long.md) | 音频Transformer与桥接 | 2100285145088 |
| [omni-audio-supplied-rates](omni-audio-supplied-rates.md) | 音频Transformer与桥接 | 140161941504 |
| [fish-audio-prompt](fish-audio-prompt.md) | 音频Transformer与桥接 | 305950752768 |
| [image-generation-book](image-generation-book.md) | 图像去噪DiT | 7830392222515200 |
| [image-generation-flux](image-generation-flux.md) | 图像去噪DiT | 139280712204288 |
| [image-generation-no-cfg](image-generation-no-cfg.md) | 图像去噪DiT | 3915196111257600 |
| [image-generation-short-negative](image-generation-short-negative.md) | 图像去噪DiT | 7349133587251200 |
| [image-generation-tall](image-generation-tall.md) | 图像去噪DiT | 17417081349734400 |
| [image-generation-latent](image-generation-latent.md) | 图像去噪DiT | 7830392222515200 |
| [image-generation-shape-cache-warm](image-generation-shape-cache-warm.md) | 图像去噪DiT | 7830392222515200 |
| [image-generation-setup-batch4](image-generation-setup-batch4.md) | 图像去噪DiT | 31321568890060800 |
| [video-generation-book](video-generation-book.md) | 视频matrix-core | 105898354926551040 |
| [video-generation-wan](video-generation-wan.md) | 视频matrix-core | 38269773120798720 |
| [video-generation-two-evaluations](video-generation-two-evaluations.md) | 视频matrix-core | 211796709853102080 |
| [video-generation-regeneration](video-generation-regeneration.md) | 视频matrix-core | 967269379179479040 |
| [video-generation-frame-boundary](video-generation-frame-boundary.md) | 视频matrix-core | 105898354926551040 |

DeepSeek V3基础逻辑前向：expanded MLA参考路径。

| 场景 | 参数 | 矩阵FLOPs | 驻留KV bytes |
| --- | ---: | ---: | ---: |
| [v3-forward-prefill](v3-forward-prefill.md) | 671026419200 | 767753388556288 | 40936407040 |
| [v3-forward-decode](v3-forward-decode.md) | 671026419200 | 114190598144 | 40941404160 |
| [v3-forward-b64](v3-forward-b64.md) | 671026419200 | 7308198281216 | 2620249866240 |
| [v3-forward-eager](v3-forward-eager.md) | 671026419200 | 935408443588608 | 40936407040 |
| [v3-forward-last-head](v3-forward-last-head.md) | 671026419200 | 752572532523008 | 40936407040 |
| [v3-forward-concentrated](v3-forward-concentrated.md) | 671026419200 | 114190598144 | 40941404160 |

真实环境资源：CPU/RSS采样和完整观察窗生命周期。

| 场景 | 数据集 | 报告组/轮数 | 真实OS队列等待 |
| --- | --- | ---: | --- |
| [environment-resources-book](environment-resources-book.md) | processes | 9 | None |
| [environment-resources-wait](environment-resources-wait.md) | processes | 3 | None |
| [environment-resources-cpu-burst](environment-resources-cpu-burst.md) | processes | 3 | None |
| [environment-resources-cpu-stagger](environment-resources-cpu-stagger.md) | processes | 3 | None |
| [environment-resources-controller](environment-resources-controller.md) | controller | 12 | None |

Qwen3-VL完整EC、KV与声明资源池上界。

| 场景 | 每图EC bytes | 每图KV bytes | 请求/s上界 |
| --- | ---: | ---: | --- |
| [multimodal-cache-book](multimodal-cache-book.md) | 8192000 | 58982400 | 6 |
| [multimodal-cache-single](multimodal-cache-single.md) | 8192000 | 58982400 | 12 |
| [multimodal-cache-warm](multimodal-cache-warm.md) | 8192000 | 58982400 | 9375/1024 |
| [multimodal-cache-all-hit](multimodal-cache-all-hit.md) | 8192000 | 58982400 | 9375/1024 |
| [multimodal-cache-larger](multimodal-cache-larger.md) | 8601600 | 61931520 | 6 |
| [multimodal-cache-fp32](multimodal-cache-fp32.md) | 16384000 | 58982400 | 9375/2048 |
| [multimodal-cache-datacenter](multimodal-cache-datacenter.md) | 8192000 | 58982400 | 6 |
| [multimodal-cache-arrival-equality](multimodal-cache-arrival-equality.md) | 8192000 | 58982400 | 9375/1024 |

V4非routed FP8 Linear：官方tile与scale复算。

| 场景 | 有效矩阵FLOPs | tile矩阵FLOPs | scale FLOPs |
| --- | ---: | ---: | ---: |
| [v4-fp8-flash-prefill](v4-fp8-flash-prefill.md) | 72327249264640 | 72327249264640 | 567263887360 |
| [v4-fp8-pro-prefill](v4-fp8-pro-prefill.md) | 304856778670080 | 304856778670080 | 2390997073920 |
| [v4-fp8-flash-decode](v4-fp8-flash-decode.md) | 8829009920 | 282528317440 | 69246080 |
| [v4-fp8-pro-decode](v4-fp8-pro-decode.md) | 37213962240 | 1190846791680 | 291869760 |
| [v4-fp8-flash-b64](v4-fp8-flash-b64.md) | 565056634880 | 565056634880 | 4431749120 |
| [v4-fp8-flash-tail](v4-fp8-flash-tail.md) | 291357327360 | 565056634880 | 2285120640 |

假想服务缓存费用与质量/时限联合完成率。

| 场景 | 费用交点 | B费用更低 | B满足联合90%目标 |
| --- | --- | --- | --- |
| [routing-cost-book](routing-cost-book.md) | 10879/13680 | True | True |
| [routing-cost-half](routing-cost-half.md) | 10879/13680 | False | False |
| [routing-cost-crossover](routing-cost-crossover.md) | 10879/13680 | False | False |
| [routing-cost-joint-target](routing-cost-joint-target.md) | 10879/13680 | True | True |
| [routing-cost-long-deadline](routing-cost-long-deadline.md) | 10879/13680 | False | True |
| [routing-cost-impossible-deadline](routing-cost-impossible-deadline.md) | 10879/13680 | True | False |

权重交接：完整参数、EP所有权、单播出口及分阶段容量。

| 场景 | 全权重 bytes | 最大rank权重 bytes | 选择性出口 bytes |
| --- | ---: | ---: | ---: |
| [weight-handoff-book](weight-handoff-book.md) | 470187269120 | 44381527040 | 710104432640 |
| [weight-handoff-qwen8](weight-handoff-qwen8.md) | 16381470720 | 16381470720 | 16381470720 |
| [weight-handoff-uneven](weight-handoff-uneven.md) | 470187269120 | 83413720064 | 566154134528 |
| [weight-handoff-replicas](weight-handoff-replicas.md) | 470187269120 | 44381527040 | 2840417730560 |
| [weight-handoff-receiver-bound](weight-handoff-receiver-bound.md) | 470187269120 | 44381527040 | 710104432640 |

教师最终hidden与全logits缓存：完整词表与重投影成本。

| 场景 | hidden bytes | logits bytes | 单次head FLOPs |
| --- | ---: | ---: | ---: |
| [teacher-cache-book](teacher-cache-book.md) | 67108864 | 2489319424 | 10196252360704 |
| [teacher-cache-v4-flash](teacher-cache-v4-flash.md) | 67108864 | 2118123520 | 8675833937920 |
| [teacher-cache-v4-pro](teacher-cache-v4-pro.md) | 117440512 | 2118123520 | 15182709391360 |
| [teacher-cache-kimi-k3](teacher-cache-kimi-k3.md) | 117440512 | 2684354560 | 19241453486080 |
| [teacher-cache-qwen235](teacher-cache-qwen235.md) | 67108864 | 2489319424 | 10196252360704 |
| [teacher-cache-fp32](teacher-cache-fp32.md) | 134217728 | 4978638848 | 10196252360704 |
| [teacher-cache-single-replay](teacher-cache-single-replay.md) | 67108864 | 2489319424 | 10196252360704 |

Routing Replay元数据：官方专家几何、ID编码与显式身份字段预算。

| 场景 | MoE层 | top-k | ID bytes | 含声明元数据bytes | 供给有余量 |
| --- | ---: | ---: | ---: | ---: | --- |
| [routing-metadata-book](routing-metadata-book.md) | 48 | 8 | 6291456 | 6489216 | True |
| [routing-metadata-qwen235](routing-metadata-qwen235.md) | 94 | 8 | 12320768 | 12518528 | False |
| [routing-metadata-v4-flash](routing-metadata-v4-flash.md) | 43 | 6 | 4227072 | 4424832 | True |
| [routing-metadata-v4-pro](routing-metadata-v4-pro.md) | 61 | 6 | 5996544 | 6194304 | True |
| [routing-metadata-kimi-k3](routing-metadata-kimi-k3.md) | 92 | 16 | 24117248 | 24315008 | False |
| [routing-metadata-int32](routing-metadata-int32.md) | 48 | 8 | 12582912 | 12780672 | False |
| [routing-metadata-retained](routing-metadata-retained.md) | 48 | 8 | 6291456 | 6489216 | True |

名义Dense 6ND：固定数据与按参数增长的数据预算分开。

| 场景 | 规则 | 设备配置 | 时间行数 | 参数界行数 |
| --- | --- | ---: | ---: | ---: |
| [dense-training-scale-book](dense-training-scale-book.md) | linear in N at fixed D | 3 | 27 | 18 |
| [dense-training-scale-proportional](dense-training-scale-proportional.md) | quadratic in N when D=kN | 3 | 27 | 18 |
| [dense-training-scale-half-fleet](dense-training-scale-half-fleet.md) | linear in N at fixed D | 3 | 27 | 18 |
| [dense-training-scale-calendar](dense-training-scale-calendar.md) | linear in N at fixed D | 3 | 27 | 18 |

训练期限：官方逐矩阵工作与BF16/FP32 dense设备峰值，必要下界非部署保证。

| 场景 | task矩阵 FLOPs | 持久状态 bytes | 可用训练秒 | 缺少可选峰值的型号 |
| --- | ---: | ---: | ---: | --- |
| [training-deadline-book](training-deadline-book.md) | 5265722561667444768768 | 131051765760 | 2592000 | ['a800-40gb-active', 'h20-sxm5-141gb'] |
| [training-deadline-long-sequence](training-deadline-long-sequence.md) | 7440049621676781993984 | 131051765760 | 2592000 | ['a800-40gb-active', 'h20-sxm5-141gb'] |
| [training-deadline-qwen235](training-deadline-qwen235.md) | 16725983173863322681344 | 3761498152960 | 2592000 | ['a800-40gb-active', 'h20-sxm5-141gb'] |
| [training-deadline-calendar](training-deadline-calendar.md) | 5265722561667444768768 | 131051765760 | 2160000 | ['a800-40gb-active', 'h20-sxm5-141gb'] |
| [training-deadline-capacity](training-deadline-capacity.md) | 52657212971947130880 | 147433236480 | 2592000 | ['a800-40gb-active', 'h20-sxm5-141gb'] |

实际DCP重分片恢复：完整逻辑载荷、容器与下一步更新分列。

| 场景 | 逻辑 bytes | 实际文件 bytes | metadata bytes | 恢复rank数 |
| --- | ---: | ---: | ---: | ---: |
| [checkpoint-resume-book](checkpoint-resume-book.md) | 463688 | 518512 | 6393 | 6 |

实际DCP提交前终止：已写数据不等于可恢复，未完成时间保留null。

| 场景 | 已提交 | 未提交 | 未提交数据 bytes | 恢复cursor | 待重做更新数 |
| --- | ---: | ---: | ---: | ---: | ---: |
| [checkpoint-fault-book](checkpoint-fault-book.md) | 3 | 1 | 12622659 | 3 | 40 |

实际CPU保存基线：配对差值与全窗口，非Qwen性能。

| 场景 | 运行数 | 已核验恢复数 | 异步−无保存窗口中位差 s | 异步−无保存训练中位差 s |
| --- | ---: | ---: | ---: | ---: |
| [checkpoint-baseline-book](checkpoint-baseline-book.md) | 15 | 10 | 0.005172588862478733 | 0.0029596358072012663 |

保存周期：一阶近似与指定Poisson重试模型分开，故障率为教学输入。

| 场景 | 保存c秒 | 作业MTBF秒 | 一阶最优tau秒 | Poisson最优tau秒 |
| --- | --- | --- | --- | --- |
| [checkpoint-interval-book](checkpoint-interval-book.md) | 6399012/390625 | 28440 | 965.2865142296354 | 954.3965630587674 |
| [checkpoint-interval-common-shock](checkpoint-interval-common-shock.md) | 6399012/390625 | 6825600/319 | 837.2719042643316 | 826.3867220685526 |
| [checkpoint-interval-high-failure](checkpoint-interval-high-failure.md) | 11198271/781250 | 675/8 | 49.18156703481498 | 40.12701873240485 |
| [checkpoint-interval-no-failure](checkpoint-interval-no-failure.md) | 11198271/781250 | None | None | None |
| [checkpoint-interval-long-recovery](checkpoint-interval-long-recovery.md) | 11198271/781250 | 246375/8 | 939.6125188821188 | 930.0810557494722 |

异步检查点：有限缓冲、背压和完整持久化，教学时序。

| 场景 | 载荷 bytes | upload s | 活跃缓冲峰值 bytes | 故障可恢复capture s |
| --- | ---: | --- | ---: | --- |
| [checkpoint-async-book](checkpoint-async-book.md) | 114670295040 | 11198271/781250 | 229340590080 | 30 |
| [checkpoint-async-rounded](checkpoint-async-rounded.md) | 112000000000 | 16 | 112000000000 | 20 |
| [checkpoint-async-fast](checkpoint-async-fast.md) | 112000000000 | 28/5 | 112000000000 | 40 |
| [checkpoint-async-one-slot](checkpoint-async-one-slot.md) | 112000000000 | 14 | 112000000000 | 69/2 |
| [checkpoint-async-delayed-commit](checkpoint-async-delayed-commit.md) | 112000000000 | 14 | 112000000000 | None |

检查点逻辑重分片：各目标范围与文件偏移，无真实存储IO计时。

| 场景 | 逻辑checkpoint bytes | 请求读取 bytes | 源文件数 | 连续读取范围数 |
| --- | ---: | ---: | ---: | ---: |
| [checkpoint-reshard-book](checkpoint-reshard-book.md) | 704643072 | 704643072 | 16 | 32 |
| [checkpoint-reshard-weights](checkpoint-reshard-weights.md) | 100663296 | 100663296 | 4 | 8 |
| [checkpoint-reshard-reverse](checkpoint-reshard-reverse.md) | 704643072 | 704643072 | 32 | 32 |
| [checkpoint-reshard-flat](checkpoint-reshard-flat.md) | 704643072 | 704643072 | 28 | 44 |
| [checkpoint-reshard-qwen235](checkpoint-reshard-qwen235.md) | 88080384 | 88080384 | 16 | 32 |

梯度转换位置：单张量顺序路径与同时存活缓冲，吞吐是教学输入。

| 场景 | BF16 bytes | FP32 bytes | 等时链路 bytes/s | 容量内最快 |
| --- | ---: | ---: | ---: | --- |
| [gradient-cast-book](gradient-cast-book.md) | 100663296 | 201326592 | 10752000000000/73 | ['cpu'] |
| [gradient-cast-fast-link](gradient-cast-fast-link.md) | 100663296 | 201326592 | 10752000000000/73 | ['gpu'] |
| [gradient-cast-tight-gpu](gradient-cast-tight-gpu.md) | 100663296 | 201326592 | 250000000000/7 | ['cpu'] |
| [gradient-cast-equality](gradient-cast-equality.md) | 100663296 | 201326592 | 4000000000 | ['cpu', 'gpu'] |
| [gradient-cast-qwen235](gradient-cast-qwen235.md) | 12582912 | 25165824 | 250000000000/7 | ['cpu'] |

全参数Adam／ZeRO持久状态：精度与分片布局显式输入，未证明训练峰值可行。

| 场景 | 总参数 | 未分片 bytes | stage3每rank bytes | 所列分配可容纳stage |
| --- | ---: | ---: | ---: | --- |
| [training-state-book](training-state-book.md) | 8190735360 | 131051765760 | 16381470720 | [3] |
| [training-state-fp32-gradient](training-state-fp32-gradient.md) | 8190735360 | 147433236480 | 18429154560 | [3] |
| [training-state-extra-live](training-state-extra-live.md) | 8190735360 | 131051765760 | 16381470720 | [] |
| [training-state-qwen235](training-state-qwen235.md) | 235093634560 | 3761498152960 | 58773408640 | [3] |
| [training-state-flat-seven](training-state-flat-seven.md) | 8190735360 | 131051765760 | 18721680832 | [3] |
| [training-state-tensor-seven](training-state-tensor-seven.md) | 8190735360 | 131051765760 | 18721685472 | [3] |

多级不可变页驻留：同层并集、跨层副本与容量预算，区间为教学输入。

| 场景 | 峰值实体 bytes | 实体 byte-seconds | 跨层副本 byte-seconds | 容量可行 |
| --- | ---: | ---: | ---: | --- |
| [cache-residency-book](cache-residency-book.md) | 905969664 | 25216155648 | 7549747200 | True |
| [cache-residency-tight](cache-residency-tight.md) | 905969664 | 25216155648 | 7549747200 | False |
| [cache-residency-qwen235](cache-residency-qwen235.md) | 1182793728 | 32921092096 | 9856614400 | True |

实际坏页预取策略：成功回退、未完成观察和存储状态分列。

| 场景 | 策略数 | 完成请求 | 未完成观察 |
| --- | ---: | ---: | ---: |
| [cache-fault-book](cache-fault-book.md) | 3 | 2 | 1 |

实际缺页恢复：连续前缀、重算及BF16逐位差异分列。

| 场景 | 条件数 | 请求数 | 输出与参考一致 |
| --- | ---: | ---: | --- |
| [cache-missing-book](cache-missing-book.md) | 2 | 6 | True |

实际KV正常重启：文件载荷、读取和可复用前缀分账，非物理磁盘IO。

| 场景 | 文件数 | 库存bytes | get文件bytes | 可复用bytes |
| --- | ---: | ---: | ---: | ---: |
| [cache-restart-book](cache-restart-book.md) | 65 | 153354240 | 150994944 | 148635648 |

真实队列压力：目标节省与整组完成增加分列，三轮配对差值。

| 场景 | 目标节省秒中位 | 整组增加秒中位 | 生成调用 |
| --- | ---: | ---: | ---: |
| [router-pressure-book](router-pressure-book.md) | 1.0541033938061446 | 0.1609554411843419 | 18 |

真实原生路由回放：模型响应命中与worker日志身份，固定单token串行请求。

| 场景 | 缓存token | 输入token | 命中请求 | 中位客户端秒 | 逻辑节省FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| [router-trace-round_robin](router-trace-round_robin.md) | 13458 | 19556 | 10 | 0.04552388610318303 | 194131899777024 |
| [router-trace-cache_aware](router-trace-cache_aware.md) | 16376 | 19556 | 11 | 0.03277028992306441 | 237179353300992 |
| [router-trace-power_of_two](router-trace-power_of_two.md) | 13458 | 19556 | 10 | 0.04337059997487813 | 194131899777024 |

缓存路由：同一请求的队列／就绪依赖和两点失效概率。

| 场景 | 前缀bytes | A期望ns | A p99 ns | A达标概率 | 已确认有效时最快路径 |
| --- | ---: | --- | --- | --- | --- |
| [cache-route-book](cache-route-book.md) | 1207959552 | 277000000 | 430000000 | 0 | B recompute |
| [cache-route-fast-remote](cache-route-fast-remote.md) | 1207959552 | 277000000 | 430000000 | 0 | B remote through host |
| [cache-route-stale](cache-route-stale.md) | 1207959552 | 107000000 | 260000000 | 9/10 | A valid HBM |
| [cache-route-after-queue](cache-route-after-queue.md) | 1207959552 | 107000000 | 260000000 | 9/10 | A valid HBM |
| [cache-route-quantile-equality](cache-route-quantile-equality.md) | 1207959552 | 91700000 | 90000000 | 99/100 | A valid HBM |

专家复制回本：同一批次重复、串行冷复制与逐rank增量容量。

| 场景 | 复制bytes | setup ns | 每批节省ns | 可行严格回本批数 | 选定部署 |
| --- | ---: | --- | --- | --- | --- |
| [replica-payback-book](replica-payback-book.md) | 264241152 | 265116152/25 | 50348032/125 | 27 | replicated |
| [replica-payback-short](replica-payback-short.md) | 264241152 | 265116152/25 | 50348032/125 | 27 | baseline |
| [replica-payback-boundary](replica-payback-boundary.md) | 264241152 | 265116152/25 | 50348032/125 | 27 | replicated |
| [replica-payback-capacity](replica-payback-capacity.md) | 264241152 | 265116152/25 | 50348032/125 | None | baseline |
| [replica-payback-padding](replica-payback-padding.md) | 37748736 | 37873736/25 | 0 | None | baseline |

Grouped专家矩阵：独立tile补齐与每rank工作，不是实测kernel时长。

| 场景 | 有效FLOPs | 完全补齐FLOPs | padding倍数 | 最忙rank补齐FLOPs |
| --- | ---: | ---: | --- | ---: |
| [grouped-experts-book](grouped-experts-book.md) | 38654705664 | 309237645312 | 8 | 38654705664 |
| [grouped-experts-concentrated](grouped-experts-concentrated.md) | 38654705664 | 38654705664 | 1 | 38654705664 |
| [grouped-experts-striped](grouped-experts-striped.md) | 38654705664 | 38654705664 | 1 | 4831838208 |
| [grouped-experts-prefill](grouped-experts-prefill.md) | 618475290624 | 618475290624 | 1 | 77309411328 |
| [grouped-experts-small-tile](grouped-experts-small-tile.md) | 38654705664 | 38654705664 | 1 | 4831838208 |
| [grouped-experts-replica-one](grouped-experts-replica-one.md) | 38654705664 | 38654705664 | 1 | 36238786560 |
| [grouped-experts-replica-padding](grouped-experts-replica-padding.md) | 9965666304 | 21743271936 | 24/11 | 19327352832 |
| [grouped-experts-replica-seven](grouped-experts-replica-seven.md) | 38654705664 | 38654705664 | 1 | 21743271936 |
| [grouped-experts-replica-idle](grouped-experts-replica-idle.md) | 38654705664 | 38654705664 | 1 | 38654705664 |

专家就地执行：单层非驻留专家，理想权重复用与教学服务能力。

| 场景 | 不同专家 | token—专家任务 | 权重bytes | 激活往返bytes | CPU ns | 搬权重GPU ns |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| [expert-locality-book](expert-locality-book.md) | 96 | 768 | 3623878656 | 12582912 | 4932260352/275 | 1166997048576/7775 |
| [expert-locality-single](expert-locality-single.md) | 8 | 8 | 301989888 | 131072 | 400929152/275 | 97249754048/7775 |
| [expert-locality-prefill](expert-locality-prefill.md) | 96 | 12288 | 3623878656 | 201326592 | 6667777536/25 | 1166997048576/7775 |
| [expert-locality-hot](expert-locality-hot.md) | 0 | 0 | 0 | 0 | 0 | 0 |
| [expert-locality-long](expert-locality-long.md) | 96 | 49152 | 3623878656 | 805306368 | 26599110144/25 | 255659465472/1625 |
| [expert-locality-avx512](expert-locality-avx512.md) | 8 | 8 | 301989888 | 131072 | 400929152/275 | 97249754048/7775 |
| [expert-locality-avx512-128](expert-locality-avx512-128.md) | 8 | 1024 | 301989888 | 16777216 | 555648128/25 | 97249754048/7775 |
| [expert-locality-amx](expert-locality-amx.md) | 8 | 8 | 301989888 | 131072 | 400929152/275 | 97249754048/7775 |
| [expert-locality-amx-128](expert-locality-amx-128.md) | 8 | 1024 | 301989888 | 16777216 | 4554407808/1775 | 97249754048/7775 |

PD整数配比：有效阶段token/s转为同一请求单位，非设备峰值或SLO。

| 场景 | P新token | D调用 | 最佳PD请求/s | 共置请求/s | KV交接bytes/请求 |
| --- | ---: | ---: | --- | --- | ---: |
| [pd-pool-book](pd-pool-book.md) | 8192 | 1024 | 125000000/27447469 | 23814473165145361328125/7894003424232391199952 | 1207959552 |
| [pd-pool-homogeneous](pd-pool-homogeneous.md) | 8192 | 1024 | 19912109375/7026552064 | 776572265625/254401730888 | 1207959552 |
| [pd-pool-all-h20](pd-pool-all-h20.md) | 8192 | 1024 | 1806640625/652316032 | 46250000000/15514838277 | 1207959552 |
| [pd-pool-network](pd-pool-network.md) | 8192 | 1024 | 1 | 23814473165145361328125/7894003424232391199952 | 1207959552 |
| [pd-pool-prefix](pd-pool-prefix.md) | 2048 | 1024 | 19982421875/3513276032 | 256487948263131103515625/52380045623862003966864 | 1207959552 |
| [pd-pool-first-output](pd-pool-first-output.md) | 8192 | 0 | 1123046875/163079008 | 1123046875/163079008 | 0 |
| [pd-pool-short-output](pd-pool-short-output.md) | 8192 | 128 | 4130859375/652316032 | 107017375648195361328125/18336603070164270072616 | 1207959552 |
| [pd-pool-mla](pd-pool-mla.md) | 8192 | 1024 | 125000000/27447469 | 23814473165145361328125/7894003424232391199952 | 575668224 |
| [pd-pool-mla-50gbps](pd-pool-mla-50gbps.md) | 8192 | 1024 | 125000000/27447469 | 23814473165145361328125/7894003424232391199952 | 575668224 |
| [pd-pool-50gbps](pd-pool-50gbps.md) | 8192 | 1024 | 125000000/27447469 | 23814473165145361328125/7894003424232391199952 | 1207959552 |
| [pd-pool-4k-output](pd-pool-4k-output.md) | 8192 | 4096 | 19982421875/15865043456 | 16381836027532861328125/14290259391494986733328 | 1207959552 |

PD／AF串行交接：载荷、方向次数与双端staging分列，不含计算和排队。

| 场景 | PD bytes | AF bytes | AF方向次数 | PD ns | AF ns |
| --- | ---: | ---: | ---: | --- | --- |
| [pd-af-handoff-book](pd-af-handoff-book.md) | 1073741824 | 524288 | 64 | 1073866824/25 | 8524288/25 |
| [pd-af-handoff-staged](pd-af-handoff-staged.md) | 1073741824 | 524288 | 64 | 3221600472/25 | 25572864/25 |
| [pd-af-handoff-high-startup](pd-af-handoff-high-startup.md) | 1073741824 | 524288 | 64 | 1098741824/25 | 1600524288/25 |
| [pd-af-handoff-qwen8](pd-af-handoff-qwen8.md) | 1207959552 | 589824 | 72 | 1208084552/25 | 9589824/25 |
| [pd-af-handoff-qwen235](pd-af-handoff-qwen235.md) | 6308233216 | 788529152 | 24064 | 6308358216/25 | 3796529152/25 |
| [pd-af-handoff-qwen8-mla](pd-af-handoff-qwen8-mla.md) | 575668224 | 589824 | 72 | 575793224/25 | 9589824/25 |
| [pd-af-handoff-qwen8-50gbps](pd-af-handoff-qwen8-50gbps.md) | 1207959552 | 589824 | 72 | 604104776/25 | 9294912/25 |
| [pd-af-handoff-qwen8-mla-50gbps](pd-af-handoff-qwen8-mla-50gbps.md) | 575668224 | 589824 | 72 | 287959112/25 | 9294912/25 |
| [pd-af-handoff-qwen8-1024](pd-af-handoff-qwen8-1024.md) | 1207959552 | 603979776 | 73728 | 1208084552/25 | 9819979776/25 |
| [pd-af-handoff-qwen8-mla-1024](pd-af-handoff-qwen8-mla-1024.md) | 575668224 | 603979776 | 73728 | 575793224/25 | 9819979776/25 |

实际KV池与自然检索质量：八任务重复执行，Q精度控制分列。

| 场景 | 自然正确／执行 | token槽 | 实际唯一storage bytes |
| --- | --- | ---: | ---: |
| [kv-quality-bf16](kv-quality-bf16.md) | 28/32 | 87376 | 12884115456 |
| [kv-quality-fp8](kv-quality-fp8.md) | 26/32 | 174752 | 12884115456 |
| [kv-quality-fp8_qbf16](kv-quality-fp8_qbf16.md) | 28/32 | 174752 | 12884115456 |

FFN卸载容量／流量与安全缓冲复用。

| 场景 | 净省GPU bytes | 每forward H2D bytes | 完成ns | 暴露等待ns |
| --- | ---: | ---: | --- | --- |
| [weight-offload-book](weight-offload-book.md) | 2415919104 | 2717908992 | 114468750 | 78468750 |
| [weight-offload-two-slots](weight-offload-two-slots.md) | 2113929216 | 2717908992 | 106468750 | 70468750 |
| [weight-offload-fast-link](weight-offload-fast-link.md) | 2415919104 | 2717908992 | 36000000 | 0 |
| [weight-offload-wrap](weight-offload-wrap.md) | 2113929216 | 2717908992 | 211937500 | 139937500 |
| [weight-offload-batch4](weight-offload-batch4.md) | 2415919104 | 2717908992 | 114468750 | 78468750 |
| [weight-offload-prefill](weight-offload-prefill.md) | 2415919104 | 2717908992 | 114468750 | 78468750 |

KV块格式与转换子账：存储位宽不代表执行精度。

| 场景 | BF16历史bytes | 每新增位置BF16 bytes |
| --- | ---: | ---: |
| [kv-codec-book](kv-codec-book.md) | 1207959552 | 147456 |
| [kv-codec-short](kv-codec-short.md) | 150994944 | 147456 |
| [kv-codec-qwen235](kv-codec-qwen235.md) | 1577058304 | 192512 |
| [kv-codec-cheap-conversion](kv-codec-cheap-conversion.md) | 1207959552 | 147456 |

实际GGUF头：混合张量类型与块尺度／文件开销分账。

| 场景 | 张量载荷bytes | 块尺度元数据bytes（载荷内） | 文件头和padding bytes |
| --- | ---: | ---: | ---: |
| [gguf-layout-q2k](gguf-layout-q2k.md) | 85684996096 | 16506720256 | 6006016 |
| [gguf-layout-q4km](gguf-layout-q4km.md) | 142148069376 | 14985244672 | 6006112 |

实际GGUF分片与声明内存预算：不等同实际驻留。

| 场景 | 扣预留后bytes | 独立BF16 KV bytes/请求 |
| --- | ---: | ---: |
| [gguf-inventory-8k](gguf-inventory-8k.md) | 87410065408 | 1577058304 |
| [gguf-inventory-32k](gguf-inventory-32k.md) | 87410065408 | 6308233216 |
| [gguf-inventory-no-reserve](gguf-inventory-no-reserve.md) | 96000000000 | 1577058304 |
| [gguf-inventory-192gb](gguf-inventory-192gb.md) | 183410065408 | 1577058304 |

真实请求回放：相同请求的联合计时达标与观测窗。

| 场景 | 达标／总请求 | 总窗口秒 | timing goodput请求/秒 |
| --- | --- | ---: | ---: |
| [service-replay-chunk512](service-replay-chunk512.md) | 9/18 | 7.541148112155497 | 1.193452225861072 |
| [service-replay-chunk8192](service-replay-chunk8192.md) | 13/18 | 6.777983905747533 | 1.9179744568257795 |
| [service-replay-nochunk8192](service-replay-nochunk8192.md) | 13/18 | 6.926419684896246 | 1.8768715427896763 |
| [service-replay-graph512](service-replay-graph512.md) | 8/18 | 7.470910331234336 | 1.0708199731100572 |

固定／连续／分块调度：同一请求与官方工作，教学成本。

| 场景 | 迭代 | 完成ns | 最大ITL ns | 峰值KV bytes | 矩阵FLOPs |
| --- | ---: | ---: | --- | ---: | ---: |
| [iteration-batching-fixed](iteration-batching-fixed.md) | 12 | 317004 | 12146 | 21528576 | 2636833882112 |
| [iteration-batching-continuous](iteration-batching-continuous.md) | 8 | 277004 | 147274 | 21823488 | 2636833882112 |
| [iteration-batching-chunked](iteration-batching-chunked.md) | 12 | 317004 | 28945 | 21676032 | 2636833882112 |
| [iteration-batching-capacity](iteration-batching-capacity.md) | 21 | 407004 | 12034 | 19021824 | 2636833882112 |

Dense batch权重复用与KV交叉点：BF16/FP32 dense峰值。

| 场景 | 声明容量最大batch | 旧KV达到权重batch | 计算／带宽交叉batch |
| --- | ---: | --- | --- |
| [batch-reuse-h100-2k](batch-reuse-h100-2k.md) | 210 | 51 | None |
| [batch-reuse-h100-8k](batch-reuse-h100-8k.md) | 52 | 13 | None |
| [batch-reuse-4090-2k](batch-reuse-4090-2k.md) | 25 | 51 | None |
| [batch-reuse-4090-8k](batch-reuse-4090-8k.md) | 6 | 13 | None |
| [batch-reuse-no-history](batch-reuse-no-history.md) | 431440 | None | 297 |
| [batch-reuse-rtxpro6000-mix](batch-reuse-rtxpro6000-mix.md) | 196 | 38 | None |

固定512-token块的真实区间与官方工作。

| 场景 | 首块中位ms | 末块中位ms | 配对比例中位 | backbone工作比例 |
| --- | ---: | ---: | ---: | --- |
| [chunk-history-book](chunk-history-book.md) | 25.300640106201172 | 35.07001495361328 | 1.3884246512899991 | 62977/47617 |

官方DFlash草稿：独立权重、共享目标头、非因果块工作。

| 场景 | 草稿矩阵FLOPs | 目标验证FLOPs | 新特征bytes | 草稿KV峰值bytes |
| --- | ---: | ---: | ---: | ---: |
| [dflash-work-book](dflash-work-book.md) | 51909754880 | 251923005440 | 163840 | 21299200 |
| [dflash-work-first](dflash-work-first.md) | 308601159680 | 251923005440 | 41943040 | 21299200 |
| [dflash-work-block4](dflash-work-block4.md) | 12794986496 | 62966595584 | 163840 | 21053440 |
| [dflash-work-long](dflash-work-long.md) | 93517250560 | 551496974336 | 163840 | 671416320 |

有限输出草稿预算：首次准备、末轮截断与逐状态选择。

| 场景 | 输出数 | 首次动作 | 最优期望ns | 相对普通decode速度比 |
| --- | ---: | --- | --- | --- |
| [speculative-budget-book](speculative-budget-book.md) | 16 | draft-4 | 171167129471875/16777216 | 85899345920/54773481431 |
| [speculative-budget-short](speculative-budget-short.md) | 1 | baseline | 1000000 | 1 |
| [speculative-budget-expensive-setup](speculative-budget-expensive-setup.md) | 16 | baseline | 16000000 | 1 |
| [speculative-budget-prepared](speculative-budget-prepared.md) | 16 | draft-4 | 137612697471875/16777216 | 85899345920/44036063191 |

投机采样概率：精确枚举拒绝修正与错误重采样。

| 场景 | 接受概率 | 正确输出总变差 | 错误输出总变差 |
| --- | --- | --- | --- |
| [speculative-sampling-book](speculative-sampling-book.md) | 2/3 | 0 | 1/6 |
| [speculative-sampling-equal](speculative-sampling-equal.md) | 1 | 0 | 0 |
| [speculative-sampling-disjoint](speculative-sampling-disjoint.md) | 0 | 0 | 0 |
| [speculative-sampling-zero-proposal](speculative-sampling-zero-proposal.md) | 1/2 | 0 | 1/4 |

投机轮次收支：接受草稿、额外交付与KV回滚。

| 场景 | 草稿接受率 | 平均交付 | 每交付token ns | 匹配速度比 |
| --- | --- | --- | --- | --- |
| [speculative-round-book](speculative-round-book.md) | 5/8 | 7/2 | 300000/7 | 7/6 |
| [speculative-round-output-limit](speculative-round-output-limit.md) | 5/8 | 1 | 150000 | 1/3 |
| [speculative-round-expensive-draft](speculative-round-expensive-draft.md) | 5/8 | 7/2 | 60000 | 5/6 |
| [speculative-round-no-accept](speculative-round-no-accept.md) | 0 | 1 | 150000 | 1/3 |

真实Agent APC回放：实际命中和官方矩阵工作分列。

| 场景 | 命中token | 请求命中占比 | token加权命中 | 省下矩阵 FLOPs |
| --- | ---: | --- | --- | ---: |
| [apc-trace-cache6](apc-trace-cache6.md) | 16304 | 11/12 | 4076/4889 | 236125039362048 |
| [apc-trace-gap6](apc-trace-gap6.md) | 16304 | 11/12 | 4076/4889 | 236125039362048 |
| [apc-trace-pressure1](apc-trace-pressure1.md) | 0 | 0 | 0 | 0 |
| [apc-trace-pressure6](apc-trace-pressure6.md) | 16304 | 11/12 | 4076/4889 | 236125039362048 |
| [apc-trace-nocache6](apc-trace-nocache6.md) | 0 | 0 | 0 | 0 |

独立前缀静态选择：预期省下矩阵工作与不可分容量。

| 场景 | 精确选择 | 贪心选择 | 精确占用 bytes | 多省 FLOPs |
| --- | --- | --- | ---: | ---: |
| [prefix-value-book](prefix-value-book.md) | ['512', '768'] | ['1024'] | 188743680 | 3498326360064 |
| [prefix-value-roomy](prefix-value-roomy.md) | ['512', '768', '1024'] | ['1024', '768', '512'] | 339738624 | 0 |
| [prefix-value-no-capacity](prefix-value-no-capacity.md) | [] | [] | 0 | 0 |
| [prefix-value-reuse](prefix-value-reuse.md) | ['1024'] | ['1024'] | 150994944 | 0 |

决策请求（共享一次前向、不生成 token）与 LLM 路径的 GPU 秒、牌价与升级份额：

| 结果 | 输入 token | 决策路径 GPU 秒 | 决策路径 $/M 输入 | V4.1 Flash CED $/M 输入 | Jev 定价/稠密下界 | LLM 路径 GPU 秒 | LLM 路径延迟 s |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| [decision-request-book](decision-request-book.md) | 1929 | 0.070509 | 0.0203 | 0.0254 | 2.07 | [0.090281, 0.240958] | [0.651, 4.787] |
| [decision-request-long-state](decision-request-long-state.md) | 8192 | 0.337586 | 0.0229 | 0.0247 | 1.83 | [0.392093, 0.789777] | [0.953, 5.335] |
| [decision-request-a100](decision-request-a100.md) | 1929 | 0.178876 | 0.0515 | 0.0645 | 0.82 | [0.211361, 0.458917] | [1.132, 7.927] |

KV保留／换出／重算：恢复等待和容量释放窗口。

| 场景 | KV bytes | 重算矩阵 FLOPs | 换出取回等待 ns | 重算等待 ns |
| --- | ---: | ---: | ---: | ---: |
| [kv-restore-book](kv-restore-book.md) | 150994944 | 14534471319552 | 0 | 30000000 |
| [kv-restore-short-window](kv-restore-short-window.md) | 150994944 | 14534471319552 | 177489888/25 | 45000000 |
| [kv-restore-long-window](kv-restore-long-window.md) | 150994944 | 14534471319552 | 0 | 0 |
| [kv-restore-host-capacity](kv-restore-host-capacity.md) | 150994944 | 14534471319552 | 0 | 30000000 |

真实KV块记录：保留块、抢占与取消释放。

| 场景 | 池块数 | 请求峰值块 | 抢占数 | 调度位置 |
| --- | ---: | ---: | ---: | ---: |
| [kv-trace-small](kv-trace-small.md) | 455 | 454 | 1 | 9993 |
| [kv-trace-large](kv-trace-large.md) | 910 | 512 | 0 | 8188 |
| [kv-trace-cancel](kv-trace-cancel.md) | 455 | 419 | 0 | 7805 |

KV分页与分支：逻辑、唯一有效和分配字节分别计量。

| 场景 | 页 bytes | 最终分配 bytes | 最终空位 bytes | COW有效复制 bytes |
| --- | ---: | ---: | ---: | ---: |
| [kv-pages-branches](kv-pages-branches.md) | 2359296 | 9437184 | 4276224 | 294912 |
| [kv-pages-aligned](kv-pages-aligned.md) | 2359296 | 7077888 | 2211840 | 0 |
| [kv-pages-qwen235](kv-pages-qwen235.md) | 3080192 | 12320768 | 5582848 | 385024 |
| [kv-pages-release](kv-pages-release.md) | 2359296 | 0 | 0 | 294912 |
| [kv-pages-capacity-two](kv-pages-capacity-two.md) | 2359296 | 4718592 | 2211840 | 0 |
| [kv-pages-capacity-three](kv-pages-capacity-three.md) | 2359296 | 7077888 | 4276224 | 147456 |
| [kv-pages-capacity-retry](kv-pages-capacity-retry.md) | 2359296 | 4718592 | 2064384 | 0 |
| [kv-pages-capacity-qwen235](kv-pages-capacity-qwen235.md) | 3080192 | 0 | 0 | 0 |

不变KV快照复用：远程访问与搬回本地，含容量门槛。

| 场景 | 快照 bytes | 远程总 ns | 搬回总 ns | 可放入 | 选择 |
| --- | ---: | ---: | ---: | --- | --- |
| [remote-state-once](remote-state-once.md) | 150994944 | 75622472/25 | 5227750568/1675 | True | direct |
| [remote-state-reused](remote-state-reused.md) | 150994944 | 302489888/25 | 5459267984/1675 | True | stage |
| [remote-state-window-limited](remote-state-window-limited.md) | 150994944 | 9221000 | 5227750568/1675 | True | stage |
| [remote-state-capacity](remote-state-capacity.md) | 150994944 | 302489888/25 | 5459267984/1675 | False | direct |

封存RPC实测：客户端CPU、应用字节及同轮配对差。

| 场景 | JSON CPU ns | binary CPU ns | 配对节省中位 ns | 正差次数/20 |
| --- | ---: | ---: | ---: | ---: |
| [rpc-trace-1024](rpc-trace-1024.md) | 422000.0 | 319000.0 | 15500.5 | 10 |
| [rpc-trace-65536](rpc-trace-65536.md) | 1608000.0 | 424000.0 | 1667812.5 | 12 |
| [rpc-trace-1048576](rpc-trace-1048576.md) | 9774500.0 | 1084500.0 | 10093646.5 | 11 |

有限credit与完成消费：传输完成和资源回收分列。

| 场景 | 传输全完 ns | 全回收 ns | 未消费峰值 | 最长提交等待 ns |
| --- | ---: | ---: | ---: | ---: |
| [completion-reclaim-book](completion-reclaim-book.md) | 48000 | 80000 | 8 | 28000 |
| [completion-reclaim-fast-poll](completion-reclaim-fast-poll.md) | 22000 | 25000 | 4 | 2000 |
| [completion-reclaim-more-slots](completion-reclaim-more-slots.md) | 20000 | 80000 | 15 | 0 |
| [completion-reclaim-small-batch](completion-reclaim-small-batch.md) | 165000 | 320000 | 8 | 145000 |

必要发布依赖与独立事务：另含投机旧数据见证。

| 场景 | 全串行 ns | 必要依赖 ns | 独立完成 ns | 旧响应有效 |
| --- | ---: | ---: | ---: | --- |
| [operation-ordering-book](operation-ordering-book.md) | 112000 | 102000 | 10000 | False |
| [operation-ordering-shared](operation-ordering-shared.md) | 112000 | 112000 | 112000 | False |
| [operation-ordering-no-recovery](operation-ordering-no-recovery.md) | 32000 | 22000 | 10000 | False |
| [operation-ordering-fresh-read](operation-ordering-fresh-read.md) | 112000 | 102000 | 10000 | True |

本地活跃关系与共享传输状态：显式隔离和容量假设。

| 场景 | 活跃关系 | 独立传输数 | 共享传输数 | 共享总 bytes |
| --- | ---: | ---: | ---: | ---: |
| [connection-states-full](connection-states-full.md) | 8192 | 8192 | 128 | 671744 |
| [connection-states-isolated](connection-states-isolated.md) | 8192 | 8192 | 1024 | 1589248 |
| [connection-states-dedicated](connection-states-dedicated.md) | 8192 | 8192 | 8192 | 8929280 |
| [connection-states-hot-peer](connection-states-hot-peer.md) | 64 | 64 | 1 | 21504 |

就绪偏差与完成分布：显式有限记录的配对反事实。

| 场景 | 原平均 ns | 交换加速平均 ns | 原 p99 ns |
| --- | ---: | ---: | ---: |
| [collective-tail-book](collective-tail-book.md) | 2400000 | 2200000 | 2400000 |
| [collective-tail-mixed](collective-tail-mixed.md) | 520000 | 320000 | 2400000 |
| [collective-tail-postcompute](collective-tail-postcompute.md) | 3400000 | 3200000 | 3400000 |
| [collective-tail-fault-heavy](collective-tail-fault-heavy.md) | 620000 | 420000 | 10400000 |

多路径乱序及显式丢失恢复：按序交付、保留payload和重传字节。

| 场景 | 完成 ns | 乱序保留峰值 bytes | 重传 bytes |
| --- | ---: | ---: | ---: |
| [packet-reorder-balanced](packet-reorder-balanced.md) | 33192/25 | 0 | 0 |
| [packet-reorder-skewed](packet-reorder-skewed.md) | 233192/25 | 12288 | 0 |
| [packet-reorder-loss](packet-reorder-loss.md) | 529096/25 | 28672 | 4096 |
| [packet-reorder-late](packet-reorder-late.md) | 1029096/25 | 28672 | 4096 |

反馈期间有限缓冲：到达、服务、丢弃及残留守恒。

| 场景 | 峰值积压 bytes | 丢弃 bytes | 窗口结束积压 bytes |
| --- | ---: | ---: | ---: |
| [feedback-queue-roomy](feedback-queue-roomy.md) | 1262144.0 | 0.0 | 262144.0 |
| [feedback-queue-overflow](feedback-queue-overflow.md) | 524288.0 | 737856.0 | 0.0 |
| [feedback-queue-late](feedback-queue-late.md) | 524288.0 | 1737856.0 | 0.0 |
| [feedback-queue-no-drain](feedback-queue-no-drain.md) | 1048576.0 | 213568.0 | 1048576.0 |

周期通信需求：流体队列、错峰及漂移，非反馈网络仿真。

| 场景 | 峰值需求 bytes/s | 队列峰值 bytes | 兼容度 | 末尾队列 bytes |
| --- | ---: | ---: | ---: | ---: |
| [periodic-queue-aligned](periodic-queue-aligned.md) | 100000000000 | 1000000000.0 | 0.8 | 0.0 |
| [periodic-queue-staggered](periodic-queue-staggered.md) | 50000000000 | 0.0 | 1.0 | 0.0 |
| [periodic-queue-drift](periodic-queue-drift.md) | 100000000000 | 250000000.0 | 0.95 | 0.0 |
| [periodic-queue-overloaded](periodic-queue-overloaded.md) | 150000000000 | 10000000000.0 | -1.0 | 10000000000.0 |
| [periodic-queue-wrapped](periodic-queue-wrapped.md) | 100000000000 | 750000000.0 | 0.85 | 0.0 |

物理有向环前三轮：消息数与每条链路载荷分别枚举。

| 场景 | 枚举消息数 | 递归物理 bytes | Swing物理 bytes |
| --- | ---: | ---: | ---: |
| [collective-paths-book](collective-paths-book.md) | 96 | 201326592 | 150994944 |
| [collective-paths-decode](collective-paths-decode.md) | 96 | 196608 | 147456 |
| [collective-paths-half-bandwidth](collective-paths-half-bandwidth.md) | 96 | 201326592 | 150994944 |

周期位置分配、割集与重构：容量／速率／使用寿命分别检验。

| 场景 | 消息 bytes | 原路径 us | 新路径 us | 严格回本次数 |
| --- | ---: | ---: | ---: | ---: |
| [topology-allocation-prefill](topology-allocation-prefill.md) | 8388608 | 657.202560 | 265.734187 | 256 |
| [topology-allocation-decode](topology-allocation-decode.md) | 8192 | 70.573440 | 70.191147 | 261580 |
| [topology-allocation-short-life](topology-allocation-short-life.md) | 8388608 | 657.202560 | 265.734187 | 256 |
| [topology-allocation-no-bandwidth-gain](topology-allocation-no-bandwidth-gain.md) | 8388608 | 657.202560 | 657.202560 | None |

两微批切分与争用：数学工作不变，逻辑读取与联合窗口单列。

| 场景 | 原batch ms | 拆分串行 ms | 理想重叠 ms | 含争用完成 ms |
| --- | ---: | ---: | ---: | ---: |
| [microbatch-overlap-book](microbatch-overlap-book.md) | 1.200000 | 1.360000 | 1.160000 | 1.280000 |
| [microbatch-overlap-break-even](microbatch-overlap-break-even.md) | 1.200000 | 1.360000 | 1.160000 | 1.200000 |
| [microbatch-overlap-low-contention](microbatch-overlap-low-contention.md) | 1.200000 | 1.360000 | 1.160000 | 1.180000 |
| [microbatch-overlap-uneven](microbatch-overlap-uneven.md) | 1.200000 | 1.380000 | 1.170000 | 1.290000 |

请求依赖图：时长替换后重新调度资源并检查关键路径转移。

| 场景 | 原请求 ns | 改后请求 ns | 改后关键路径 |
| --- | ---: | ---: | --- |
| [request-dag-path-switch](request-dag-path-switch.md) | 80000 | 60000 | prepare → parallel → finish |
| [request-dag-no-gain](request-dag-no-gain.md) | 80000 | 80000 | prepare → hotspot → finish |
| [request-dag-shared-resource](request-dag-shared-resource.md) | 80000 | 75000 | prepare → hotspot → parallel → finish |
| [request-dag-contention](request-dag-contention.md) | 80000 | 110000 | prepare → parallel → finish |

按块就绪的设备任务：独立worker与显式分派／发布开销。

| 场景 | 设备任务数 | 屏障 us | 按块就绪 us | 中间存活 bytes |
| --- | ---: | ---: | ---: | ---: |
| [persistent-tiles-base](persistent-tiles-base.md) | 16 | 582.270838 | 358.085055 | 6291456 |
| [persistent-tiles-slow-dispatch](persistent-tiles-slow-dispatch.md) | 16 | 582.270838 | 803.585055 | 4718592 |
| [persistent-tiles-tail](persistent-tiles-tail.md) | 18 | 583.388554 | 359.399455 | 6291456 |
| [persistent-one-tile](persistent-one-tile.md) | 2 | 582.270838 | 578.670838 | 12582912 |
| [persistent-tiles-rtxpro6000](persistent-tiles-rtxpro6000.md) | 16 | 126.345151 | 113.737151 | 3145728 |

原始FFN运行记录：无分析器计时与Nsight事件分别核算。

| 场景 | 计时方案 | 时间线区间 | 单链真实矩阵 FLOPs |
| --- | ---: | ---: | ---: |
| [runtime-ffn-token1](runtime-ffn-token1.md) | 5 | 0 | 301989888 |
| [runtime-ffn-token32](runtime-ffn-token32.md) | 9 | 9 | 9663676416 |
| [runtime-ffn-token257](runtime-ffn-token257.md) | 7 | 0 | 77611401216 |

形状特化：同一频数组，准备缓存与分桶补齐重新核算。

| 场景 | 每组调用数 | 真实矩阵 FLOPs | 含准备最优策略 |
| --- | ---: | ---: | --- |
| [specialization-short](specialization-short.md) | 10 | 1700807049216 | generic |
| [specialization-medium](specialization-medium.md) | 10 | 1700807049216 | bucket |
| [specialization-long](specialization-long.md) | 10 | 1700807049216 | specialized |
| [specialization-cache](specialization-cache.md) | 10 | 1700807049216 | specialized |
| [specialization-fallback](specialization-fallback.md) | 10 | 1700807049216 | specialized |

候选分数与部署：频数、失败回退和额外准备分别计入。

| 场景 | 最佳统一候选 | 分派平均 ns | 摊平调用数 | 严格收益调用数 |
| --- | --- | ---: | ---: | ---: |
| [deployment-equal](deployment-equal.md) | B | 30000.0 | 30000000 | 30000001 |
| [deployment-skewed](deployment-skewed.md) | A | 14000.0 | 40000000 | 40000001 |
| [deployment-dispatch-cost](deployment-dispatch-cost.md) | B | 50000.0 | None | None |
| [deployment-validation-failure](deployment-validation-failure.md) | B | 50000.0 | None | None |

图边界成本：教学串行预算，稳态与实例寿命分别选择。

| 场景 | 额外复制 bytes | FFN padding FLOPs | 稳态路径 | 寿命路径 |
| --- | ---: | ---: | --- | --- |
| [graph-small-input](graph-small-input.md) | 4194304 | 154618822656 | copy | copy |
| [graph-large-input](graph-large-input.md) | 33554432 | 154618822656 | indirect | eager |
| [graph-long-lived](graph-long-lived.md) | 33554432 | 154618822656 | indirect | indirect |
| [graph-no-padding](graph-no-padding.md) | 4194304 | 0 | copy | copy |
| [graph-small-input-rtxpro6000](graph-small-input-rtxpro6000.md) | 4194304 | 154618822656 | copy | copy |
| [graph-large-input-rtxpro6000](graph-large-input-rtxpro6000.md) | 33554432 | 154618822656 | indirect | eager |

FIFO与独立重排槽：原进度容量及背压后的最后取走时刻。

| 场景 | 原进度需 bytes | 可维持 | 背压最后取走格 |
| --- | ---: | --- | ---: |
| [stream-buffer-book](stream-buffer-book.md) | 81920 | False | 13 |
| [stream-buffer-layout-unified](stream-buffer-layout-unified.md) | 49152 | True | 13 |
| [stream-buffer-one-slot](stream-buffer-one-slot.md) | 81920 | False | 13 |
| [stream-buffer-slow-producer](stream-buffer-slow-producer.md) | 49152 | True | 17 |
| [stream-buffer-no-slot](stream-buffer-no-slot.md) | 81920 | False | None |

主机准备／H2D／消费：双端槽复用与精确有理数时序。

| 场景 | H2D bytes | 串行 ms | 槽约束完成 ms |
| --- | ---: | ---: | ---: |
| [host-transfer-double](host-transfer-double.md) | 536870912 | 60.833333 | 35.604167 |
| [host-transfer-single-device](host-transfer-single-device.md) | 536870912 | 60.833333 | 53.833333 |
| [host-transfer-single-host](host-transfer-single-host.md) | 536870912 | 60.833333 | 35.604167 |
| [host-transfer-half-bandwidth](host-transfer-half-bandwidth.md) | 536870912 | 81.666667 | 46.666667 |

状态与选中历史载荷单列。K3 的 recurrent 读写不包含在历史载荷中；V4 resident 含压缩器固定槽。

| 模型／场景 | 当前状态 MiB | 选中历史载荷 MiB |
| --- | ---: | ---: |
| [state-qwen3-8b-n8192-b1-native](state-qwen3-8b-n8192-b1-native.md) | 1152.000000 | 1152.000000 |
| [state-qwen3-32b-n8192-b1-native](state-qwen3-32b-n8192-b1-native.md) | 2048.000000 | 2048.000000 |
| [state-qwen3-30b-a3b-n8192-b1-native](state-qwen3-30b-a3b-n8192-b1-native.md) | 768.000000 | 768.000000 |
| [state-qwen3-235b-a22b-n8192-b1-native](state-qwen3-235b-a22b-n8192-b1-native.md) | 1504.000000 | 1504.000000 |
| [state-deepseek-v4-flash-n8192-b1-native](state-deepseek-v4-flash-n8192-b1-native.md) | 70.765625 | 27.625000 |
| [state-deepseek-v4-flash-n131072-b1-native](state-deepseek-v4-flash-n131072-b1-native.md) | 877.015625 | 203.875000 |
| [state-deepseek-v4-flash-n1048576-b64-native](state-deepseek-v4-flash-n1048576-b64-native.md) | 441409.000000 | 97272.000000 |
| [state-deepseek-v4-pro-n8192-b1-native](state-deepseek-v4-pro-n8192-b1-native.md) | 102.406250 | 54.562500 |
| [state-deepseek-v4-pro-n131072-b1-native](state-deepseek-v4-pro-n131072-b1-native.md) | 1256.468750 | 308.625000 |
| [state-deepseek-v4-pro-n1048576-b64-native](state-deepseek-v4-pro-n1048576-b64-native.md) | 631902.000000 | 141160.000000 |
| [state-kimi-k3-n8192-b1-compact](state-kimi-k3-n8192-b1-compact.md) | 649.406250 | 216.000000 |
| [state-kimi-k3-n8192-b1-expanded](state-kimi-k3-n8192-b1-expanded.md) | 11953.406250 | 11520.000000 |
| [state-kimi-k3-n1048576-b64-compact](state-kimi-k3-n1048576-b64-compact.md) | 1797210.000000 | 1769472.000000 |

真实 Q 投影：单层、BF16 输入／输出、FP32 累加、dense、冷内存服务量下界。未知算力仅给内存服务时间，不能称完整 Roofline 或模型时延。

| 场景 | M×K×N | AI FLOPs/byte | 计算服务 μs | 内存服务 μs | Roofline 下界 μs |
| --- | --- | ---: | ---: | ---: | ---: |
| [projection-qwen3-8b-rtx4090-b1](projection-qwen3-8b-rtx4090-b1.md) | 1×4096×4096 | 0.999512 | 0.203114 | 33.304381 | 33.304381 |
| [projection-qwen3-8b-rtx4090-b256](projection-qwen3-8b-rtx4090-b256.md) | 256×4096×4096 | 227.555556 | 51.997183 | 37.449143 | 51.997183 |
| [projection-qwen3-8b-rtx5090-b1](projection-qwen3-8b-rtx5090-b1.md) | 1×4096×4096 | 0.999512 | 0.160164 | 18.733714 | 18.733714 |
| [projection-qwen3-8b-rtx5090-b256](projection-qwen3-8b-rtx5090-b256.md) | 256×4096×4096 | 227.555556 | 41.002074 | 21.065143 | 41.002074 |
| [projection-qwen3-8b-rtx-pro6000-blackwell-ws-b1](projection-qwen3-8b-rtx-pro6000-blackwell-ws-b1.md) | 1×4096×4096 | 0.999512 | 0.066603 | 18.733714 | 18.733714 |
| [projection-qwen3-8b-rtx-pro6000-blackwell-ws-b256](projection-qwen3-8b-rtx-pro6000-blackwell-ws-b256.md) | 256×4096×4096 | 227.555556 | 17.050287 | 21.065143 | 21.065143 |
| [projection-qwen3-8b-rtx-pro6000-blackwell-server-b1](projection-qwen3-8b-rtx-pro6000-blackwell-server-b1.md) | 1×4096×4096 | 0.999512 | 未知 | 21.021175 | 未知 |
| [projection-qwen3-8b-rtx-pro6000-blackwell-server-b256](projection-qwen3-8b-rtx-pro6000-blackwell-server-b256.md) | 256×4096×4096 | 227.555556 | 未知 | 23.637280 | 未知 |
| [projection-qwen3-8b-a100-80gb-sxm-b1](projection-qwen3-8b-a100-80gb-sxm-b1.md) | 1×4096×4096 | 0.999512 | 0.107546 | 16.464353 | 16.464353 |
| [projection-qwen3-8b-a100-80gb-sxm-b256](projection-qwen3-8b-a100-80gb-sxm-b256.md) | 256×4096×4096 | 227.555556 | 27.531842 | 18.513358 | 27.531842 |
| [projection-qwen3-8b-h100-sxm-b1](projection-qwen3-8b-h100-sxm-b1.md) | 1×4096×4096 | 0.999512 | 0.033914 | 10.021139 | 10.021139 |
| [projection-qwen3-8b-h100-sxm-b256](projection-qwen3-8b-h100-sxm-b256.md) | 256×4096×4096 | 227.555556 | 8.681963 | 11.268279 | 11.268279 |
| [projection-qwen3-8b-h200-sxm-b1](projection-qwen3-8b-h200-sxm-b1.md) | 1×4096×4096 | 0.999512 | 0.033910 | 6.993920 | 6.993920 |
| [projection-qwen3-8b-h200-sxm-b256](projection-qwen3-8b-h200-sxm-b256.md) | 256×4096×4096 | 227.555556 | 8.681086 | 7.864320 | 8.681086 |
| [projection-qwen3-8b-b200-sxm-b1](projection-qwen3-8b-b200-sxm-b1.md) | 1×4096×4096 | 0.999512 | 0.014913 | 4.196352 | 4.196352 |
| [projection-qwen3-8b-b200-sxm-b256](projection-qwen3-8b-b200-sxm-b256.md) | 256×4096×4096 | 227.555556 | 3.817749 | 4.718592 | 4.718592 |
| [projection-qwen3-8b-b300-sxm-b1](projection-qwen3-8b-b300-sxm-b1.md) | 1×4096×4096 | 0.999512 | 0.014913 | 4.196352 | 4.196352 |
| [projection-qwen3-8b-b300-sxm-b256](projection-qwen3-8b-b300-sxm-b256.md) | 256×4096×4096 | 227.555556 | 3.817749 | 4.718592 | 4.718592 |
| [projection-qwen3-8b-ascend-950dt-max-spec-b1](projection-qwen3-8b-ascend-950dt-max-spec-b1.md) | 1×4096×4096 | 0.999512 | 未知 | 8.392704 | 未知 |
| [projection-qwen3-8b-ascend-950dt-max-spec-b256](projection-qwen3-8b-ascend-950dt-max-spec-b256.md) | 256×4096×4096 | 227.555556 | 未知 | 9.437184 | 未知 |
| [projection-qwen3-8b-m2-max-38gpu-96gb-b1](projection-qwen3-8b-m2-max-38gpu-96gb-b1.md) | 1×4096×4096 | 0.999512 | 未知 | 83.927040 | 未知 |
| [projection-qwen3-8b-m2-max-38gpu-96gb-b256](projection-qwen3-8b-m2-max-38gpu-96gb-b256.md) | 256×4096×4096 | 227.555556 | 未知 | 94.371840 | 未知 |
| [projection-qwen3-8b-m5-ultra-80gpu-512gb-b1](projection-qwen3-8b-m5-ultra-80gpu-512gb-b1.md) | 1×4096×4096 | 0.999512 | 未知 | 27.975680 | 未知 |
| [projection-qwen3-8b-m5-ultra-80gpu-512gb-b256](projection-qwen3-8b-m5-ultra-80gpu-512gb-b256.md) | 256×4096×4096 | 227.555556 | 未知 | 31.457280 | 未知 |
| [projection-qwen3-8b-m6-12gpu-32gb-b1](projection-qwen3-8b-m6-12gpu-32gb-b1.md) | 1×4096×4096 | 0.999512 | 未知 | 197.475388 | 未知 |
| [projection-qwen3-8b-m6-12gpu-32gb-b256](projection-qwen3-8b-m6-12gpu-32gb-b256.md) | 256×4096×4096 | 227.555556 | 未知 | 222.051388 | 未知 |
| [projection-qwen3-32b-h100-sxm-prefill-8192](projection-qwen3-32b-h100-sxm-prefill-8192.md) | 8192×5120×8192 | 2275.555556 | 694.557072 | 90.146235 | 694.557072 |

环境创建、克隆与预热：

- [environment-lifecycle-default](environment-lifecycle-default.md)：声明容量/创建路径/预热期望及独立本地记录，实际云端创建时间未测。
- [environment-lifecycle-no-hit](environment-lifecycle-no-hit.md)：声明容量/创建路径/预热期望及独立本地记录，实际云端创建时间未测。
- [environment-lifecycle-ready-hit](environment-lifecycle-ready-hit.md)：声明容量/创建路径/预热期望及独立本地记录，实际云端创建时间未测。
- [environment-lifecycle-small-delta](environment-lifecycle-small-delta.md)：声明容量/创建路径/预热期望及独立本地记录，实际云端创建时间未测。
- [environment-lifecycle-tight-budget](environment-lifecycle-tight-budget.md)：声明容量/创建路径/预热期望及独立本地记录，实际云端创建时间未测。

UB现代教学组织对照：容量与串行通信分列，非历史参数复原。

- [ub-scope-qwen32-default](ub-scope-qwen32-default.md)：two_servers_tp4_pp2（仅通信比较，须另查容量）
- [ub-scope-remote-below](ub-scope-remote-below.md)：single_server_tp8（仅通信比较，须另查容量）
- [ub-scope-remote-tie](ub-scope-remote-tie.md)：tie（仅通信比较，须另查容量）
- [ub-scope-remote-above](ub-scope-remote-above.md)：two_servers_tp4_pp2（仅通信比较，须另查容量）
- [ub-scope-capacity-none](ub-scope-capacity-none.md)：two_servers_tp4_pp2（仅通信比较，须另查容量）
- [ub-scope-capacity-dual-only](ub-scope-capacity-dual-only.md)：two_servers_tp4_pp2（仅通信比较，须另查容量）
- [ub-scope-capacity-both](ub-scope-capacity-both.md)：two_servers_tp4_pp2（仅通信比较，须另查容量）
- [ub-scope-startup-blocked](ub-scope-startup-blocked.md)：single_server_tp8（仅通信比较，须另查容量）
- [ub-scope-b2-seven](ub-scope-b2-seven.md)：two_servers_tp4_pp2（仅通信比较，须另查容量）
- [ub-scope-one-forward](ub-scope-one-forward.md)：two_servers_tp4_pp2（仅通信比较，须另查容量）

UB 互联从第一性原理推导：状态按 N+M 增长、上下文缓存溢出点、一次 64 B 读取的阶段和、连接建立与硅面积代价。

| 场景 | 1024×1024 状态比 | RoCE 溢出端点数 | UB 溢出端点数 | LD/ST 往返 ns | RoCE 往返 ns | 缓存内主机数 RoCE/UB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [ub-fabric-book](ub-fabric-book.md) | 4854.8 | 23 | 2428 | 419 | 2222 | 8/4674 |
| [ub-fabric-64-apps](ub-fabric-64-apps.md) | 4854.8 | 23 | 2428 | 419 | 2222 | 1/4622 |
| [ub-fabric-1mib-cache](ub-fabric-1mib-cache.md) | 4854.8 | 46 | 9710 | 419 | 2222 | 32/18718 |

公开训练投入与条件预算：

- [training-history-published](training-history-published.md)：13模型公开字段；代理工作、阶段观测与声明成本分列。
- [training-history-growth](training-history-growth.md)：13模型公开字段；代理工作、阶段观测与声明成本分列。
- [training-history-unknown-growth](training-history-unknown-growth.md)：13模型公开字段；代理工作、阶段观测与声明成本分列。
- [training-history-count-range](training-history-count-range.md)：13模型公开字段；代理工作、阶段观测与声明成本分列。
- [training-history-declared-cost](training-history-declared-cost.md)：13模型公开字段；代理工作、阶段观测与声明成本分列。

Scaling-law教学拟合与生命周期预算：

- [scaling-law-teaching](scaling-law-teaching.md)：预测验证损失下的候选最优N=4000000000.0；非实际任务质量排名。
- [scaling-law-perturbed](scaling-law-perturbed.md)：预测验证损失下的候选最优N=4000000000.0；非实际任务质量排名。
- [scaling-law-zero-demand](scaling-law-zero-demand.md)：预测验证损失下的候选最优N=8000000000.0；非实际任务质量排名。

TP/EP迁移子账：资源下界、声明串行时间和容量分别检查；不代表完整部署验收。

- [reconfiguration-dense-tp4-to-tp8](reconfiguration-dense-tp4-to-tp8.md)：网络 16449646080 bytes；传输下界 18356228/390625 s；声明串行切换 None s；容量 True。
- [reconfiguration-dense-gqa-tp8-to-tp16](reconfiguration-dense-gqa-tp8-to-tp16.md)：网络 20458065664 bytes；传输下界 10652674/390625 s；声明串行切换 None s；容量 True。
- [reconfiguration-qwen235-ep8-to-ep16](reconfiguration-qwen235-ep8-to-ep16.md)：网络 578994499328 bytes；传输下界 709280481/390625 s；声明串行切换 None s；容量 False。
- [reconfiguration-qwen235-ep16-to-ep8](reconfiguration-qwen235-ep16-to-ep8.md)：网络 425805745920 bytes；传输下界 332660739/781250 s；声明串行切换 None s；容量 False。
- [reconfiguration-qwen30-uneven-ep7-to-ep5](reconfiguration-qwen30-uneven-ep7-to-ep5.md)：网络 42127592418 bytes；传输下界 8153727561/100000000 s；声明串行切换 None s；容量 True。
- [reconfiguration-qwen30-tp2-ep4-to-tp4-ep2](reconfiguration-qwen30-tp2-ep4-to-tp4-ep2.md)：网络 48153755648 bytes；传输下界 1497088/15625 s；声明串行切换 None s；容量 True。
- [reconfiguration-dense-disjoint-replay](reconfiguration-dense-disjoint-replay.md)：网络 16383324160 bytes；传输下界 16006564/390625 s；声明串行切换 None s；容量 None。
- [reconfiguration-declared-serial](reconfiguration-declared-serial.md)：网络 16449646080 bytes；传输下界 18356228/390625 s；声明串行切换 109 s；容量 True。
- [reconfiguration-same-card-materialization](reconfiguration-same-card-materialization.md)：网络 0 bytes；传输下界 0 s；声明串行切换 9 s；容量 True。

[官方硬件规格表](hardware.md)记录每项精度、累加格式、稀疏条件与仍待核实的字段。


Qwen3.5 基础文本参考路径（非实际运行时间）：


Qwen3.6-35B-A3B真实混合MoE：逐算子与必要容量，非实际运行时间。


TLS/QUIC消息依赖与长早期上传：

- [handshake-tcp_tls13-fresh](handshake-tcp_tls13-fresh.md)
- [handshake-tcp_tls13-resume](handshake-tcp_tls13-resume.md)
- [handshake-tcp_tls13-early_accept](handshake-tcp_tls13-early_accept.md)
- [handshake-tcp_tls13-early_reject](handshake-tcp_tls13-early_reject.md)
- [handshake-tcp_tls13-reused](handshake-tcp_tls13-reused.md)
- [handshake-tcp_tls13-wait](handshake-tcp_tls13-wait.md)
- [handshake-tcp_tls13-reject-no-retry](handshake-tcp_tls13-reject-no-retry.md)
- [handshake-quic_v1-fresh](handshake-quic_v1-fresh.md)
- [handshake-quic_v1-resume](handshake-quic_v1-resume.md)
- [handshake-quic_v1-early_accept](handshake-quic_v1-early_accept.md)
- [handshake-quic_v1-early_reject](handshake-quic_v1-early_reject.md)
- [handshake-quic_v1-reused](handshake-quic_v1-reused.md)
- [handshake-quic_v1-wait](handshake-quic_v1-wait.md)
- [handshake-quic_v1-reject-no-retry](handshake-quic_v1-reject-no-retry.md)
- [handshake-quic-budget-3600-ack-False](handshake-quic-budget-3600-ack-False.md)
- [handshake-quic-budget-4800-ack-False](handshake-quic-budget-4800-ack-False.md)
- [handshake-quic-budget-4800-ack-True](handshake-quic-budget-4800-ack-True.md)
- [early-stream-30mb-accept-retry-True](early-stream-30mb-accept-retry-True.md)
- [early-stream-30mb-reject-retry-True](early-stream-30mb-reject-retry-True.md)
- [early-stream-30mb-reject-retry-False](early-stream-30mb-reject-retry-False.md)
- [early-stream-small-accept-retry-True](early-stream-small-accept-retry-True.md)
- [early-stream-small-reject-retry-True](early-stream-small-reject-retry-True.md)
- [early-stream-small-reject-retry-False](early-stream-small-reject-retry-False.md)
- [early-stream-oracle-accept-retry-True](early-stream-oracle-accept-retry-True.md)
- [early-stream-oracle-reject-retry-True](early-stream-oracle-reject-retry-True.md)
- [early-stream-oracle-reject-retry-False](early-stream-oracle-reject-retry-False.md)
- [early-stream-mid-packet-keys-accept](early-stream-mid-packet-keys-accept.md)
- [early-stream-mid-packet-keys-reject](early-stream-mid-packet-keys-reject.md)
- [early-stream-4800-server-flight-ack-False](early-stream-4800-server-flight-ack-False.md)
- [early-stream-4800-server-flight-ack-True](early-stream-4800-server-flight-ack-True.md)
- [protocol-retry-none-retry-True](protocol-retry-none-retry-True.md)
- [protocol-retry-none-retry-False](protocol-retry-none-retry-False.md)
- [protocol-retry-hrr-retry-True](protocol-retry-hrr-retry-True.md)
- [protocol-retry-hrr-retry-False](protocol-retry-hrr-retry-False.md)
- [protocol-retry-retry-retry-True](protocol-retry-retry-retry-True.md)
- [protocol-retry-retry-retry-False](protocol-retry-retry-retry-False.md)
- [protocol-retry-psk_unknown_fallback-retry-True](protocol-retry-psk_unknown_fallback-retry-True.md)
- [protocol-retry-psk_unknown_fallback-retry-False](protocol-retry-psk_unknown_fallback-retry-False.md)
- [protocol-retry-psk_unknown_abort-retry-True](protocol-retry-psk_unknown_abort-retry-True.md)
- [protocol-retry-psk_unknown_abort-retry-False](protocol-retry-psk_unknown_abort-retry-False.md)
- [protocol-retry-selected_binder_invalid-retry-True](protocol-retry-selected_binder_invalid-retry-True.md)
- [protocol-retry-selected_binder_invalid-retry-False](protocol-retry-selected_binder_invalid-retry-False.md)
- [protocol-retry-retry-then-tls-reject-reattempt](protocol-retry-retry-then-tls-reject-reattempt.md)
- [protocol-retry-retry-then-tls-reject-wait_1rtt](protocol-retry-retry-then-tls-reject-wait_1rtt.md)
- [protocol-retry-noearly-none](protocol-retry-noearly-none.md)
- [protocol-retry-noearly-hrr](protocol-retry-noearly-hrr.md)
- [protocol-retry-noearly-retry](protocol-retry-noearly-retry.md)
- [protocol-retry-noearly-psk_unknown_fallback](protocol-retry-noearly-psk_unknown_fallback.md)
- [protocol-retry-retry-token-three-initials](protocol-retry-retry-token-three-initials.md)
- [protocol-retry-retry-invalid-token](protocol-retry-retry-invalid-token.md)
- [shared-media-hol-connection](shared-media-hol-connection.md)
- [shared-media-hol-per_stream](shared-media-hol-per_stream.md)
- [shared-media-schedule-fifo](shared-media-schedule-fifo.md)
- [shared-media-schedule-priority](shared-media-schedule-priority.md)
- [shared-media-credit-1-streams](shared-media-credit-1-streams.md)
- [shared-media-credit-3-streams](shared-media-credit-3-streams.md)
- [shared-media-playback-reliable](shared-media-playback-reliable.md)
- [shared-media-playback-slots](shared-media-playback-slots.md)
- [shared-media-cancel-running-work](shared-media-cancel-running-work.md)
- [shared-media-mixed-fifo](shared-media-mixed-fifo.md)
- [shared-media-mixed-priority](shared-media-mixed-priority.md)
- [shared-media-image-30mb-5mb](shared-media-image-30mb-5mb.md)
- [shared-media-screenshot-complete](shared-media-screenshot-complete.md)
- [shared-media-screenshot-stale](shared-media-screenshot-stale.md)
- [shared-media-mixed-preview-priority](shared-media-mixed-preview-priority.md)
- [shared-media-unreliable-loss-credit](shared-media-unreliable-loss-credit.md)
- [closed-loop-response-dependency](closed-loop-response-dependency.md)
- [closed-loop-cwnd-third-packet](closed-loop-cwnd-third-packet.md)
- [closed-loop-absolute-flow-arrival](closed-loop-absolute-flow-arrival.md)
- [closed-loop-loss-feedback-recovery](closed-loop-loss-feedback-recovery.md)
- [closed-loop-tail-pto-probe](closed-loop-tail-pto-probe.md)
- [closed-loop-ack-loss](closed-loop-ack-loss.md)
- [closed-loop-finite-router-drop](closed-loop-finite-router-drop.md)
- [closed-loop-automatic-consumption](closed-loop-automatic-consumption.md)
- [closed-loop-no-credit-incomplete](closed-loop-no-credit-incomplete.md)
- [closed-loop-book-30mb-5mb](closed-loop-book-30mb-5mb.md)
- [controller-loop-book-newreno](controller-loop-book-newreno.md)
- [controller-loop-router-newreno](controller-loop-router-newreno.md)
- [controller-loop-book-cubic_hystart](controller-loop-book-cubic_hystart.md)
- [controller-loop-router-cubic_hystart](controller-loop-router-cubic_hystart.md)
- [controller-loop-book-bbr](controller-loop-book-bbr.md)
- [controller-loop-router-bbr](controller-loop-router-bbr.md)
- [ack-policy-count-two](ack-policy-count-two.md)
- [ack-policy-tail-deadline](ack-policy-tail-deadline.md)
- [ack-policy-same-time-arrival-deadline](ack-policy-same-time-arrival-deadline.md)
- [ack-policy-lost-first-ack](ack-policy-lost-first-ack.md)
- [ack-policy-max-flow-control](ack-policy-max-flow-control.md)
- [ack-policy-queued-snapshot-refresh](ack-policy-queued-snapshot-refresh.md)
- [ack-policy-queued-deadline-overrun](ack-policy-queued-deadline-overrun.md)
- [ack-policy-book-newreno](ack-policy-book-newreno.md)
- [ack-policy-book-cubic_hystart](ack-policy-book-cubic_hystart.md)
- [ack-policy-book-bbr](ack-policy-book-bbr.md)
- [media-feedback-credit-3-streams](media-feedback-credit-3-streams.md)
- [media-feedback-schedule-fifo](media-feedback-schedule-fifo.md)
- [media-feedback-schedule-priority](media-feedback-schedule-priority.md)
- [media-feedback-playback-reliable](media-feedback-playback-reliable.md)
- [media-feedback-playback-slots](media-feedback-playback-slots.md)
- [media-feedback-cancel-running-work](media-feedback-cancel-running-work.md)
- [media-feedback-screenshot-complete](media-feedback-screenshot-complete.md)
- [media-feedback-screenshot-stale](media-feedback-screenshot-stale.md)
- [media-feedback-unreliable-loss-credit](media-feedback-unreliable-loss-credit.md)
- [media-feedback-one-stream-blocked-other-progress](media-feedback-one-stream-blocked-other-progress.md)
- [media-feedback-reliable-loss-recovery](media-feedback-reliable-loss-recovery.md)
- [media-feedback-shared-credit-consumption](media-feedback-shared-credit-consumption.md)
- [media-feedback-shared-credit-aggregate-ack](media-feedback-shared-credit-aggregate-ack.md)
- [media-feedback-datagram-tail-pto-ping](media-feedback-datagram-tail-pto-ping.md)
- [media-feedback-image-baseline](media-feedback-image-baseline.md)
- [media-feedback-mixed-fifo-immediate](media-feedback-mixed-fifo-immediate.md)
- [media-feedback-mixed-fifo-aggregate](media-feedback-mixed-fifo-aggregate.md)
- [media-feedback-mixed-priority-immediate](media-feedback-mixed-priority-immediate.md)
- [media-feedback-mixed-priority-aggregate](media-feedback-mixed-priority-aggregate.md)
- [shared-airtime-bidirectional-shared](shared-airtime-bidirectional-shared.md)
- [shared-airtime-bidirectional-disabled](shared-airtime-bidirectional-disabled.md)
- [shared-airtime-two-data-immediate](shared-airtime-two-data-immediate.md)
- [shared-airtime-two-data-every2](shared-airtime-two-data-every2.md)
- [shared-airtime-busy-client-ACK-refresh](shared-airtime-busy-client-ACK-refresh.md)
- [shared-airtime-busy-client-ACK-overrun](shared-airtime-busy-client-ACK-overrun.md)
- [shared-airtime-same-PN-MAC-ACK-lost](shared-airtime-same-PN-MAC-ACK-lost.md)
- [shared-airtime-MAC-data-loss-exhaustion-then-PTO](shared-airtime-MAC-data-loss-exhaustion-then-PTO.md)
- [shared-airtime-tail-immediate](shared-airtime-tail-immediate.md)
- [shared-airtime-tail-every4](shared-airtime-tail-every4.md)
- [shared-airtime-mixed-fifo-immediate](shared-airtime-mixed-fifo-immediate.md)
- [shared-airtime-mixed-fifo-aggregate](shared-airtime-mixed-fifo-aggregate.md)
- [shared-airtime-mixed-priority-immediate](shared-airtime-mixed-priority-immediate.md)
- [shared-airtime-mixed-priority-aggregate](shared-airtime-mixed-priority-aggregate.md)
- [shared-airtime-image-baseline](shared-airtime-image-baseline.md)
- [shared-airtime-scan-media-320B-ack1](shared-airtime-scan-media-320B-ack1.md)
- [shared-airtime-scan-media-320B-ack2](shared-airtime-scan-media-320B-ack2.md)
- [shared-airtime-scan-media-320B-ack4](shared-airtime-scan-media-320B-ack4.md)
- [shared-airtime-scan-media-640B-ack1](shared-airtime-scan-media-640B-ack1.md)
- [shared-airtime-scan-media-640B-ack2](shared-airtime-scan-media-640B-ack2.md)
- [shared-airtime-scan-media-640B-ack4](shared-airtime-scan-media-640B-ack4.md)
- [shared-airtime-scan-media-960B-ack1](shared-airtime-scan-media-960B-ack1.md)
- [shared-airtime-scan-media-960B-ack2](shared-airtime-scan-media-960B-ack2.md)
- [shared-airtime-scan-media-960B-ack4](shared-airtime-scan-media-960B-ack4.md)

连续请求与连接窗口：

- [sequence-image-quiet-fresh](sequence-image-quiet-fresh.md)
- [sequence-image-quiet-ticket](sequence-image-quiet-ticket.md)
- [sequence-image-quiet-reuse_reset](sequence-image-quiet-reuse_reset.md)
- [sequence-image-quiet-reuse_warm](sequence-image-quiet-reuse_warm.md)
- [sequence-image-complete_received-fresh](sequence-image-complete_received-fresh.md)
- [sequence-image-complete_received-ticket](sequence-image-complete_received-ticket.md)
- [sequence-image-complete_received-reuse_reset](sequence-image-complete_received-reuse_reset.md)
- [sequence-image-complete_received-reuse_warm](sequence-image-complete_received-reuse_warm.md)
- [sequence-small-quiet-fresh](sequence-small-quiet-fresh.md)
- [sequence-small-quiet-ticket](sequence-small-quiet-ticket.md)
- [sequence-small-quiet-reuse_reset](sequence-small-quiet-reuse_reset.md)
- [sequence-small-quiet-reuse_warm](sequence-small-quiet-reuse_warm.md)
- [sequence-small-complete_received-fresh](sequence-small-complete_received-fresh.md)
- [sequence-small-complete_received-ticket](sequence-small-complete_received-ticket.md)
- [sequence-small-complete_received-reuse_reset](sequence-small-complete_received-reuse_reset.md)
- [sequence-small-complete_received-reuse_warm](sequence-small-complete_received-reuse_warm.md)
- [sequence-image-request2-loss](sequence-image-request2-loss.md)

有限ACK窗口图片请求：

- [window-reused](window-reused.md)
- [window-fresh](window-fresh.md)
- [window-ticket](window-ticket.md)
- [window-receive-limited](window-receive-limited.md)
- [window-loss](window-loss.md)
- [window-payload-baseline](window-payload-baseline.md)

图片分块与预览：

- [image-stream-whole-image-without-preview](image-stream-whole-image-without-preview.md)
- [image-stream-whole-image-with-preview](image-stream-whole-image-with-preview.md)
- [image-stream-independent-blocks-without-preview](image-stream-independent-blocks-without-preview.md)
- [image-stream-independent-blocks-with-preview](image-stream-independent-blocks-with-preview.md)

图片文件请求预算：[图12-1](../figures/image-request/figure.svg)

- [image-request-original](image-request-original.md)
- [image-request-faster-model](image-request-faster-model.md)
- [image-request-connection](image-request-connection.md)
- [image-request-up10](image-request-up10.md)
- [image-request-up20](image-request-up20.md)
- [image-request-up100](image-request-up100.md)
- [image-request-up400](image-request-up400.md)
- [image-request-up800](image-request-up800.md)

概念覆盖补齐（2026-09-11）：交换网络、核内执行、能耗、训练稳定性、广域丢包；声明输入的来源见各结果的 declared_input_sources。


Clos 层数、半分带宽、轨道与在网归约：

- [clos-cut-k64-nonblocking](clos-cut-k64-nonblocking.md)
- [clos-cut-k64-oversub3](clos-cut-k64-oversub3.md)
- [clos-cut-rail-aligned](clos-cut-rail-aligned.md)
- [clos-cut-rail-shifted](clos-cut-rail-shifted.md)
- [clos-cut-in-network](clos-cut-in-network.md)

ECMP 哈希冲突与逐包喷洒：

- [hash-collision-8-on-32](hash-collision-8-on-32.md)
- [hash-collision-8-on-16](hash-collision-8-on-16.md)
- [hash-collision-32-on-32](hash-collision-32-on-32.md)
- [hash-collision-32-on-16](hash-collision-32-on-16.md)
- [hash-collision-128-on-16](hash-collision-128-on-16.md)

incast 反馈时延与缓冲：

- [incast-feedback-book](incast-feedback-book.md)
- [incast-feedback-4mib](incast-feedback-4mib.md)

SM 占用率、延迟隐藏与 MMA 指令数：

- [sm-occupancy-book-tile](sm-occupancy-book-tile.md)
- [sm-occupancy-register-accumulator](sm-occupancy-register-accumulator.md)
- [sm-occupancy-latency-1000ns](sm-occupancy-latency-1000ns.md)

能耗层次、电压、功率密度、机柜与手机：

- [energy-ledger-book](energy-ledger-book.md)

临界批量与数据并行上限：

- [critical-batch-book](critical-batch-book.md)
- [critical-batch-noise-20m](critical-batch-noise-20m.md)

掉队者：最大值步时间、检测与响应：

- [straggler-max-sigma-2pct](straggler-max-sigma-2pct.md)
- [straggler-max-sigma-5pct](straggler-max-sigma-5pct.md)

MoE 容量因子：填充与丢弃：

- [moe-capacity-book](moe-capacity-book.md)

广域丢包：Mathis、BBR、重传尾部与 FEC：

- [wan-loss-model-book](wan-loss-model-book.md)
- [wan-loss-model-p036](wan-loss-model-p036.md)

真实梯度两级集合通信：

- [gradient-fp32-flat-contiguous-nic8](gradient-fp32-flat-contiguous-nic8.md)
- [gradient-fp32-flat-interleaved-nic8](gradient-fp32-flat-interleaved-nic8.md)
- [gradient-fp32-hierarchical-nic8](gradient-fp32-hierarchical-nic8.md)
- [gradient-bf16-flat-contiguous-nic8](gradient-bf16-flat-contiguous-nic8.md)
- [gradient-bf16-flat-interleaved-nic8](gradient-bf16-flat-interleaved-nic8.md)
- [gradient-bf16-hierarchical-nic8](gradient-bf16-hierarchical-nic8.md)
- [gradient-fp32-hierarchical-nic1](gradient-fp32-hierarchical-nic1.md)
- [gradient-fp32-flat-contiguous-two-nic](gradient-fp32-flat-contiguous-two-nic.md)
- [gradient-fp32-flat-interleaved-two-nic](gradient-fp32-flat-interleaved-two-nic.md)
- [gradient-fp32-hierarchical-two-nic](gradient-fp32-hierarchical-two-nic.md)
- [gradient-fp32-flat-contiguous-one-nic](gradient-fp32-flat-contiguous-one-nic.md)
- [gradient-fp32-flat-contiguous-three-nic](gradient-fp32-flat-contiguous-three-nic.md)

超节点规模同cohort比较：[图6-9](../figures/supernode-cost/figure.svg)，全部时长/费率为声明条件。

- [supernode-qwen3-8b-n1-d80-healthy](supernode-qwen3-8b-n1-d80-healthy.md)：符合容量/SLO的最低费用候选['tp8-replicas1']，空集合不选。
- [supernode-qwen3-8b-n1-d80-short](supernode-qwen3-8b-n1-d80-short.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n1-d80-long](supernode-qwen3-8b-n1-d80-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n1-d250-healthy](supernode-qwen3-8b-n1-d250-healthy.md)：符合容量/SLO的最低费用候选['tp8-replicas1']，空集合不选。
- [supernode-qwen3-8b-n1-d250-short](supernode-qwen3-8b-n1-d250-short.md)：符合容量/SLO的最低费用候选['tp8-replicas1']，空集合不选。
- [supernode-qwen3-8b-n1-d250-long](supernode-qwen3-8b-n1-d250-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n1-d600-healthy](supernode-qwen3-8b-n1-d600-healthy.md)：符合容量/SLO的最低费用候选['tp8-replicas1']，空集合不选。
- [supernode-qwen3-8b-n1-d600-short](supernode-qwen3-8b-n1-d600-short.md)：符合容量/SLO的最低费用候选['tp8-replicas1']，空集合不选。
- [supernode-qwen3-8b-n1-d600-long](supernode-qwen3-8b-n1-d600-long.md)：符合容量/SLO的最低费用候选['tp8-replicas1']，空集合不选。
- [supernode-qwen3-8b-n4-d80-healthy](supernode-qwen3-8b-n4-d80-healthy.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n4-d80-short](supernode-qwen3-8b-n4-d80-short.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n4-d80-long](supernode-qwen3-8b-n4-d80-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n4-d250-healthy](supernode-qwen3-8b-n4-d250-healthy.md)：符合容量/SLO的最低费用候选['tp2-replicas4']，空集合不选。
- [supernode-qwen3-8b-n4-d250-short](supernode-qwen3-8b-n4-d250-short.md)：符合容量/SLO的最低费用候选['tp2-replicas4']，空集合不选。
- [supernode-qwen3-8b-n4-d250-long](supernode-qwen3-8b-n4-d250-long.md)：符合容量/SLO的最低费用候选['tp2-replicas4']，空集合不选。
- [supernode-qwen3-8b-n4-d600-healthy](supernode-qwen3-8b-n4-d600-healthy.md)：符合容量/SLO的最低费用候选['tp2-replicas4']，空集合不选。
- [supernode-qwen3-8b-n4-d600-short](supernode-qwen3-8b-n4-d600-short.md)：符合容量/SLO的最低费用候选['tp2-replicas4']，空集合不选。
- [supernode-qwen3-8b-n4-d600-long](supernode-qwen3-8b-n4-d600-long.md)：符合容量/SLO的最低费用候选['tp2-replicas4']，空集合不选。
- [supernode-qwen3-8b-n8-d80-healthy](supernode-qwen3-8b-n8-d80-healthy.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n8-d80-short](supernode-qwen3-8b-n8-d80-short.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n8-d80-long](supernode-qwen3-8b-n8-d80-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n8-d250-healthy](supernode-qwen3-8b-n8-d250-healthy.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n8-d250-short](supernode-qwen3-8b-n8-d250-short.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n8-d250-long](supernode-qwen3-8b-n8-d250-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-8b-n8-d600-healthy](supernode-qwen3-8b-n8-d600-healthy.md)：符合容量/SLO的最低费用候选['tp2-replicas4']，空集合不选。
- [supernode-qwen3-8b-n8-d600-short](supernode-qwen3-8b-n8-d600-short.md)：符合容量/SLO的最低费用候选['tp2-replicas4']，空集合不选。
- [supernode-qwen3-8b-n8-d600-long](supernode-qwen3-8b-n8-d600-long.md)：符合容量/SLO的最低费用候选['tp2-replicas4']，空集合不选。
- [supernode-qwen3-32b-n1-d80-healthy](supernode-qwen3-32b-n1-d80-healthy.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n1-d80-short](supernode-qwen3-32b-n1-d80-short.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n1-d80-long](supernode-qwen3-32b-n1-d80-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n1-d250-healthy](supernode-qwen3-32b-n1-d250-healthy.md)：符合容量/SLO的最低费用候选['tp8-replicas1']，空集合不选。
- [supernode-qwen3-32b-n1-d250-short](supernode-qwen3-32b-n1-d250-short.md)：符合容量/SLO的最低费用候选['tp8-replicas1']，空集合不选。
- [supernode-qwen3-32b-n1-d250-long](supernode-qwen3-32b-n1-d250-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n1-d600-healthy](supernode-qwen3-32b-n1-d600-healthy.md)：符合容量/SLO的最低费用候选['tp8-replicas1']，空集合不选。
- [supernode-qwen3-32b-n1-d600-short](supernode-qwen3-32b-n1-d600-short.md)：符合容量/SLO的最低费用候选['tp8-replicas1']，空集合不选。
- [supernode-qwen3-32b-n1-d600-long](supernode-qwen3-32b-n1-d600-long.md)：符合容量/SLO的最低费用候选['tp8-replicas1']，空集合不选。
- [supernode-qwen3-32b-n4-d80-healthy](supernode-qwen3-32b-n4-d80-healthy.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n4-d80-short](supernode-qwen3-32b-n4-d80-short.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n4-d80-long](supernode-qwen3-32b-n4-d80-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n4-d250-healthy](supernode-qwen3-32b-n4-d250-healthy.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n4-d250-short](supernode-qwen3-32b-n4-d250-short.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n4-d250-long](supernode-qwen3-32b-n4-d250-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n4-d600-healthy](supernode-qwen3-32b-n4-d600-healthy.md)：符合容量/SLO的最低费用候选['tp4-replicas2']，空集合不选。
- [supernode-qwen3-32b-n4-d600-short](supernode-qwen3-32b-n4-d600-short.md)：符合容量/SLO的最低费用候选['tp4-replicas2']，空集合不选。
- [supernode-qwen3-32b-n4-d600-long](supernode-qwen3-32b-n4-d600-long.md)：符合容量/SLO的最低费用候选['tp4-replicas2']，空集合不选。
- [supernode-qwen3-32b-n8-d80-healthy](supernode-qwen3-32b-n8-d80-healthy.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n8-d80-short](supernode-qwen3-32b-n8-d80-short.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n8-d80-long](supernode-qwen3-32b-n8-d80-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n8-d250-healthy](supernode-qwen3-32b-n8-d250-healthy.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n8-d250-short](supernode-qwen3-32b-n8-d250-short.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n8-d250-long](supernode-qwen3-32b-n8-d250-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n8-d600-healthy](supernode-qwen3-32b-n8-d600-healthy.md)：符合容量/SLO的最低费用候选['tp4-replicas2']，空集合不选。
- [supernode-qwen3-32b-n8-d600-short](supernode-qwen3-32b-n8-d600-short.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [supernode-qwen3-32b-n8-d600-long](supernode-qwen3-32b-n8-d600-long.md)：符合容量/SLO的最低费用候选[]，空集合不选。
- [growing-kv-qwen8-all-r1](growing-kv-qwen8-all-r1.md)：增长KV旧历史/追加/副本提交，通信骨架不是实测decode时间。
- [growing-kv-qwen8-all-r2](growing-kv-qwen8-all-r2.md)：增长KV旧历史/追加/副本提交，通信骨架不是实测decode时间。
- [growing-kv-qwen8-prefix-r1](growing-kv-qwen8-prefix-r1.md)：增长KV旧历史/追加/副本提交，通信骨架不是实测decode时间。
- [growing-kv-qwen8-prefix-r2](growing-kv-qwen8-prefix-r2.md)：增长KV旧历史/追加/副本提交，通信骨架不是实测decode时间。
- [growing-kv-qwen36-all-r1](growing-kv-qwen36-all-r1.md)：增长KV旧历史/追加/副本提交，通信骨架不是实测decode时间。
- [growing-kv-qwen36-all-r2](growing-kv-qwen36-all-r2.md)：增长KV旧历史/追加/副本提交，通信骨架不是实测decode时间。
- [growing-kv-qwen36-prefix-r1](growing-kv-qwen36-prefix-r1.md)：增长KV旧历史/追加/副本提交，通信骨架不是实测decode时间。
- [growing-kv-qwen36-prefix-r2](growing-kv-qwen36-prefix-r2.md)：增长KV旧历史/追加/副本提交，通信骨架不是实测decode时间。
- [growing-kv-tail-budget-fail](growing-kv-tail-budget-fail.md)：增长KV旧历史/追加/副本提交，通信骨架不是实测decode时间。
- [memory-pool-copies1](memory-pool-copies1.md)：内存池容量/声明周期读取/副本依赖，见[图6-8](memory-pool-layout.svg)。
- [memory-pool-copies2](memory-pool-copies2.md)：内存池容量/声明周期读取/副本依赖，见[图6-8](memory-pool-layout.svg)。
- [memory-pool-copies3](memory-pool-copies3.md)：内存池容量/声明周期读取/副本依赖，见[图6-8](memory-pool-layout.svg)。
- [v41-forward-prefill-8192-ced](v41-forward-prefill-8192-ced.md)：v41-forward，固定官方输入和明确作用域。
- [v41-forward-prefill-8192-reference](v41-forward-prefill-8192-reference.md)：v41-forward，固定官方输入和明确作用域。
- [v41-forward-decode-8192-ced](v41-forward-decode-8192-ced.md)：v41-forward，固定官方输入和明确作用域。
- [v41-forward-decode-200k-ced](v41-forward-decode-200k-ced.md)：v41-forward，固定官方输入和明确作用域。
- [v41-forward-prefill-128-ced](v41-forward-prefill-128-ced.md)：v41-forward，固定官方输入和明确作用域。
- [v41-forward-decode-1m-ced](v41-forward-decode-1m-ced.md)：v41-forward，固定官方输入和明确作用域。
- [v41-flash-n8192-b1](v41-flash-n8192-b1.md)：v41-flash，固定官方输入和明确作用域。
- [v41-flash-n131072-b1](v41-flash-n131072-b1.md)：v41-flash，固定官方输入和明确作用域。
- [v41-flash-n1048576-b64](v41-flash-n1048576-b64.md)：v41-flash，固定官方输入和明确作用域。
- [kv-comparison-n1-b1](kv-comparison-n1-b1.md)：kv-comparison，固定官方输入和明确作用域。
- [kv-comparison-n8191-b1](kv-comparison-n8191-b1.md)：kv-comparison，固定官方输入和明确作用域。
- [kv-comparison-n8192-b1](kv-comparison-n8192-b1.md)：kv-comparison，固定官方输入和明确作用域。
- [kv-comparison-n8192-b64](kv-comparison-n8192-b64.md)：kv-comparison，固定官方输入和明确作用域。
- [kv-comparison-n131072-b1](kv-comparison-n131072-b1.md)：kv-comparison，固定官方输入和明确作用域。
- [kv-comparison-n1048576-b1](kv-comparison-n1048576-b1.md)：kv-comparison，固定官方输入和明确作用域。
- [qwen36-prefill-8192](qwen36-prefill-8192.md)：qwen36-base-text-ledger，固定官方输入和明确作用域。
- [qwen36-decode-b1](qwen36-decode-b1.md)：qwen36-base-text-ledger，固定官方输入和明确作用域。
- [qwen36-decode-b64](qwen36-decode-b64.md)：qwen36-base-text-ledger，固定官方输入和明确作用域。
- [qwen36-decode-b64-concentrated](qwen36-decode-b64-concentrated.md)：qwen36-base-text-ledger，固定官方输入和明确作用域。
- [qwen36-prefill-tail65](qwen36-prefill-tail65.md)：qwen36-base-text-ledger，固定官方输入和明确作用域。
- [qwen36-prefill-last-head](qwen36-prefill-last-head.md)：qwen36-base-text-ledger，固定官方输入和明确作用域。
- [qwen36-decode-b1-s32768](qwen36-decode-b1-s32768.md)：qwen36-base-text-ledger，固定官方输入和明确作用域。
- [qwen36-decode-b64-s32768](qwen36-decode-b64-s32768.md)：qwen36-base-text-ledger，固定官方输入和明确作用域。
- [qwen36-capacity-b1-n8192](qwen36-capacity-b1-n8192.md)：qwen36-capacity，固定官方输入和明确作用域。
- [qwen36-capacity-b1-n32768](qwen36-capacity-b1-n32768.md)：qwen36-capacity，固定官方输入和明确作用域。
- [qwen36-capacity-b8-n8192](qwen36-capacity-b8-n8192.md)：qwen36-capacity，固定官方输入和明确作用域。
- [qwen36-capacity-b8-n32768](qwen36-capacity-b8-n32768.md)：qwen36-capacity，固定官方输入和明确作用域。
- [qwen36-capacity-b32-n8192](qwen36-capacity-b32-n8192.md)：qwen36-capacity，固定官方输入和明确作用域。
- [qwen36-capacity-b32-n32768](qwen36-capacity-b32-n32768.md)：qwen36-capacity，固定官方输入和明确作用域。
- [qwen36-capacity-all-weights](qwen36-capacity-all-weights.md)：qwen36-capacity，固定官方输入和明确作用域。
- [qwen36-capacity-b1-n131072](qwen36-capacity-b1-n131072.md)：qwen36-capacity，固定官方输入和明确作用域。
- [qwen36-capacity-b1-n262144](qwen36-capacity-b1-n262144.md)：qwen36-capacity，固定官方输入和明确作用域。
- [qwen35-cold-single-token](qwen35-cold-single-token.md)：矩阵工作 59868938432；路径 reference_chunk_nonexport；算子边界与补充接口不可相加为HBM。
- [qwen35-cold-single-record-past](qwen35-cold-single-record-past.md)：矩阵工作 59855667392；路径 reference_chunk_nonexport；算子边界与补充接口不可相加为HBM。
- [qwen35-prefill-8192](qwen35-prefill-8192.md)：矩阵工作 304038065373184；路径 reference_chunk_nonexport；算子边界与补充接口不可相加为HBM。
- [qwen35-decode-b1](qwen35-decode-b1.md)：矩阵工作 36977377472；路径 reference_recurrent；算子边界与补充接口不可相加为HBM。
- [qwen35-decode-b64](qwen35-decode-b64.md)：矩阵工作 2366552158208；路径 reference_recurrent；算子边界与补充接口不可相加为HBM。
- [qwen35-prefix-6144-2048](qwen35-prefix-6144-2048.md)：矩阵工作 76009543991296；路径 reference_chunk_nonexport；算子边界与补充接口不可相加为HBM。
- [qwen35-chunk-tail-65](qwen35-chunk-tail-65.md)：矩阵工作 2179531092160；路径 reference_chunk_nonexport；算子边界与补充接口不可相加为HBM。
- [qwen35-decode-record-past](qwen35-decode-record-past.md)：矩阵工作 36972953792；路径 reference_recurrent；算子边界与补充接口不可相加为HBM。

封存请求画像与离线p95：

- [workload-profiles-02-08](workload-profiles-02-08.md)：44条封存请求，零新增请求。

FLUX VAE解码器（已有阶段的细化，不重复累加）：

- [flux-vae-1024-bf16-sdpa](flux-vae-1024-bf16-sdpa.md)
- [flux-vae-1024-bf16-eager](flux-vae-1024-bf16-eager.md)
- [flux-vae-rectangular-b2](flux-vae-rectangular-b2.md)
- [flux-vae-512-fp32-eager](flux-vae-512-fp32-eager.md)

官方基线与未训练架构变体：

- [architecture-decode](architecture-decode.md)
- [architecture-prefill](architecture-prefill.md)
- [architecture-prefix](architecture-prefix.md)
- [architecture-single-device](architecture-single-device.md)

V4完整前缀状态之后的顺序已知token续算：

- [v4-prefix-flash-6144-2048](v4-prefix-flash-6144-2048.md)：2048次完整基础前向；不是并行chunk prefill。
- [v4-prefix-pro-boundary](v4-prefix-pro-boundary.md)：5次完整基础前向；不是并行chunk prefill。
- [v4-prefix-flash-batch-boundary](v4-prefix-flash-batch-boundary.md)：2次完整基础前向；不是并行chunk prefill。

Qwen235八rank逐张量与条件容量：

- [qwen235-placement-tp2-ep4-pp1-24gb-8192](qwen235-placement-tp2-ep4-pp1-24gb-8192.md)
- [qwen235-placement-tp2-ep4-pp1-24gb-32768](qwen235-placement-tp2-ep4-pp1-24gb-32768.md)
- [qwen235-placement-tp2-ep4-pp1-48gb-8192](qwen235-placement-tp2-ep4-pp1-48gb-8192.md)
- [qwen235-placement-tp2-ep4-pp1-48gb-32768](qwen235-placement-tp2-ep4-pp1-48gb-32768.md)
- [qwen235-placement-tp2-ep4-pp1-80gb-8192](qwen235-placement-tp2-ep4-pp1-80gb-8192.md)
- [qwen235-placement-tp2-ep4-pp1-80gb-32768](qwen235-placement-tp2-ep4-pp1-80gb-32768.md)
- [qwen235-placement-tp4-ep2-pp1-24gb-8192](qwen235-placement-tp4-ep2-pp1-24gb-8192.md)
- [qwen235-placement-tp4-ep2-pp1-24gb-32768](qwen235-placement-tp4-ep2-pp1-24gb-32768.md)
- [qwen235-placement-tp4-ep2-pp1-48gb-8192](qwen235-placement-tp4-ep2-pp1-48gb-8192.md)
- [qwen235-placement-tp4-ep2-pp1-48gb-32768](qwen235-placement-tp4-ep2-pp1-48gb-32768.md)
- [qwen235-placement-tp4-ep2-pp1-80gb-8192](qwen235-placement-tp4-ep2-pp1-80gb-8192.md)
- [qwen235-placement-tp4-ep2-pp1-80gb-32768](qwen235-placement-tp4-ep2-pp1-80gb-32768.md)
- [qwen235-placement-tp2-ep2-pp2-24gb-8192](qwen235-placement-tp2-ep2-pp2-24gb-8192.md)
- [qwen235-placement-tp2-ep2-pp2-24gb-32768](qwen235-placement-tp2-ep2-pp2-24gb-32768.md)
- [qwen235-placement-tp2-ep2-pp2-48gb-8192](qwen235-placement-tp2-ep2-pp2-48gb-8192.md)
- [qwen235-placement-tp2-ep2-pp2-48gb-32768](qwen235-placement-tp2-ep2-pp2-48gb-32768.md)
- [qwen235-placement-tp2-ep2-pp2-80gb-8192](qwen235-placement-tp2-ep2-pp2-80gb-8192.md)
- [qwen235-placement-tp2-ep2-pp2-80gb-32768](qwen235-placement-tp2-ep2-pp2-80gb-32768.md)
- [qwen235-placement-tp1-ep1-pp8-24gb-8192](qwen235-placement-tp1-ep1-pp8-24gb-8192.md)
- [qwen235-placement-tp1-ep1-pp8-24gb-32768](qwen235-placement-tp1-ep1-pp8-24gb-32768.md)
- [qwen235-placement-tp1-ep1-pp8-48gb-8192](qwen235-placement-tp1-ep1-pp8-48gb-8192.md)
- [qwen235-placement-tp1-ep1-pp8-48gb-32768](qwen235-placement-tp1-ep1-pp8-48gb-32768.md)
- [qwen235-placement-tp1-ep1-pp8-80gb-8192](qwen235-placement-tp1-ep1-pp8-80gb-8192.md)
- [qwen235-placement-tp1-ep1-pp8-80gb-32768](qwen235-placement-tp1-ep1-pp8-80gb-32768.md)
- [qwen235-placement-tp8-kv-replica](qwen235-placement-tp8-kv-replica.md)
- [qwen235-placement-ep8-expert-partition](qwen235-placement-ep8-expert-partition.md)

Dense三模型分片后量化与条件容量：

- [dense-quant-qwen3-8b-tp8-pp1-24gb-8192](dense-quant-qwen3-8b-tp8-pp1-24gb-8192.md)
- [dense-quant-qwen3-8b-tp8-pp1-24gb-32768](dense-quant-qwen3-8b-tp8-pp1-24gb-32768.md)
- [dense-quant-qwen3-8b-tp8-pp1-48gb-8192](dense-quant-qwen3-8b-tp8-pp1-48gb-8192.md)
- [dense-quant-qwen3-8b-tp8-pp1-48gb-32768](dense-quant-qwen3-8b-tp8-pp1-48gb-32768.md)
- [dense-quant-qwen3-8b-tp8-pp1-80gb-8192](dense-quant-qwen3-8b-tp8-pp1-80gb-8192.md)
- [dense-quant-qwen3-8b-tp8-pp1-80gb-32768](dense-quant-qwen3-8b-tp8-pp1-80gb-32768.md)
- [dense-quant-qwen3-8b-tp2-pp4-24gb-8192](dense-quant-qwen3-8b-tp2-pp4-24gb-8192.md)
- [dense-quant-qwen3-8b-tp2-pp4-24gb-32768](dense-quant-qwen3-8b-tp2-pp4-24gb-32768.md)
- [dense-quant-qwen3-8b-tp2-pp4-48gb-8192](dense-quant-qwen3-8b-tp2-pp4-48gb-8192.md)
- [dense-quant-qwen3-8b-tp2-pp4-48gb-32768](dense-quant-qwen3-8b-tp2-pp4-48gb-32768.md)
- [dense-quant-qwen3-8b-tp2-pp4-80gb-8192](dense-quant-qwen3-8b-tp2-pp4-80gb-8192.md)
- [dense-quant-qwen3-8b-tp2-pp4-80gb-32768](dense-quant-qwen3-8b-tp2-pp4-80gb-32768.md)
- [dense-quant-qwen3-8b-tp1-pp8-24gb-8192](dense-quant-qwen3-8b-tp1-pp8-24gb-8192.md)
- [dense-quant-qwen3-8b-tp1-pp8-24gb-32768](dense-quant-qwen3-8b-tp1-pp8-24gb-32768.md)
- [dense-quant-qwen3-8b-tp1-pp8-48gb-8192](dense-quant-qwen3-8b-tp1-pp8-48gb-8192.md)
- [dense-quant-qwen3-8b-tp1-pp8-48gb-32768](dense-quant-qwen3-8b-tp1-pp8-48gb-32768.md)
- [dense-quant-qwen3-8b-tp1-pp8-80gb-8192](dense-quant-qwen3-8b-tp1-pp8-80gb-8192.md)
- [dense-quant-qwen3-8b-tp1-pp8-80gb-32768](dense-quant-qwen3-8b-tp1-pp8-80gb-32768.md)
- [dense-quant-qwen3-32b-tp8-pp1-24gb-8192](dense-quant-qwen3-32b-tp8-pp1-24gb-8192.md)
- [dense-quant-qwen3-32b-tp8-pp1-24gb-32768](dense-quant-qwen3-32b-tp8-pp1-24gb-32768.md)
- [dense-quant-qwen3-32b-tp8-pp1-48gb-8192](dense-quant-qwen3-32b-tp8-pp1-48gb-8192.md)
- [dense-quant-qwen3-32b-tp8-pp1-48gb-32768](dense-quant-qwen3-32b-tp8-pp1-48gb-32768.md)
- [dense-quant-qwen3-32b-tp8-pp1-80gb-8192](dense-quant-qwen3-32b-tp8-pp1-80gb-8192.md)
- [dense-quant-qwen3-32b-tp8-pp1-80gb-32768](dense-quant-qwen3-32b-tp8-pp1-80gb-32768.md)
- [dense-quant-qwen3-32b-tp2-pp4-24gb-8192](dense-quant-qwen3-32b-tp2-pp4-24gb-8192.md)
- [dense-quant-qwen3-32b-tp2-pp4-24gb-32768](dense-quant-qwen3-32b-tp2-pp4-24gb-32768.md)
- [dense-quant-qwen3-32b-tp2-pp4-48gb-8192](dense-quant-qwen3-32b-tp2-pp4-48gb-8192.md)
- [dense-quant-qwen3-32b-tp2-pp4-48gb-32768](dense-quant-qwen3-32b-tp2-pp4-48gb-32768.md)
- [dense-quant-qwen3-32b-tp2-pp4-80gb-8192](dense-quant-qwen3-32b-tp2-pp4-80gb-8192.md)
- [dense-quant-qwen3-32b-tp2-pp4-80gb-32768](dense-quant-qwen3-32b-tp2-pp4-80gb-32768.md)
- [dense-quant-qwen3-32b-tp1-pp8-24gb-8192](dense-quant-qwen3-32b-tp1-pp8-24gb-8192.md)
- [dense-quant-qwen3-32b-tp1-pp8-24gb-32768](dense-quant-qwen3-32b-tp1-pp8-24gb-32768.md)
- [dense-quant-qwen3-32b-tp1-pp8-48gb-8192](dense-quant-qwen3-32b-tp1-pp8-48gb-8192.md)
- [dense-quant-qwen3-32b-tp1-pp8-48gb-32768](dense-quant-qwen3-32b-tp1-pp8-48gb-32768.md)
- [dense-quant-qwen3-32b-tp1-pp8-80gb-8192](dense-quant-qwen3-32b-tp1-pp8-80gb-8192.md)
- [dense-quant-qwen3-32b-tp1-pp8-80gb-32768](dense-quant-qwen3-32b-tp1-pp8-80gb-32768.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-24gb-8192](dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-24gb-8192.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-24gb-32768](dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-24gb-32768.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-48gb-8192](dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-48gb-8192.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-48gb-32768](dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-48gb-32768.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-80gb-8192](dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-80gb-8192.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-80gb-32768](dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-80gb-32768.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-24gb-8192](dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-24gb-8192.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-24gb-32768](dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-24gb-32768.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-48gb-8192](dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-48gb-8192.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-48gb-32768](dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-48gb-32768.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-80gb-8192](dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-80gb-8192.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-80gb-32768](dense-quant-deepseek-r1-distill-llama-70b-tp2-pp4-80gb-32768.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-24gb-8192](dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-24gb-8192.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-24gb-32768](dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-24gb-32768.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-48gb-8192](dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-48gb-8192.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-48gb-32768](dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-48gb-32768.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-80gb-8192](dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-80gb-8192.md)
- [dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-80gb-32768](dense-quant-deepseek-r1-distill-llama-70b-tp1-pp8-80gb-32768.md)

统一S/P/G/B的四模型完整请求逻辑预算：

- [request-four-models-book](request-four-models-book.md)
- [request-four-models-first-output](request-four-models-first-output.md)
- [request-four-models-prefix-boundary](request-four-models-prefix-boundary.md)
- [request-four-models-prefix-6144-2048](request-four-models-prefix-6144-2048.md)

Fish CLI代码块到波形导出：

- [fish-wave-two-chunks](fish-wave-two-chunks.md)
- [fish-wave-int32](fish-wave-int32.md)
- [fish-wave-fp32](fish-wave-fp32.md)

实验3-3严格协议与全部候选消耗：

- [strategy-record-cost-03-03](strategy-record-cost-03-03.md)

Qwen8训练非矩阵、AdamW与保存对象：

- [training-nonmatrix-book](training-nonmatrix-book.md)
- [training-nonmatrix-dense-mask](training-nonmatrix-dense-mask.md)
- [training-nonmatrix-compact-mask](training-nonmatrix-compact-mask.md)
- [training-nonmatrix-recompute-silu](training-nonmatrix-recompute-silu.md)
- [training-nonmatrix-8192](training-nonmatrix-8192.md)

真实C4训练点与预定留出拟合：

- [datablations-real-c4-eight-point-fit](datablations-real-c4-eight-point-fit.md)

真实C4拟合的条件生命周期：

- [real-c4-lifecycle-512-128](real-c4-lifecycle-512-128.md)

V4 router与mHC可微训练子图：

- [v4-training-primitives-one-row](v4-training-primitives-one-row.md)
- [v4-training-primitives-128](v4-training-primitives-128.md)
- [v4-training-primitives-batch2](v4-training-primitives-batch2.md)
- [v4-hc-training-one-row](v4-hc-training-one-row.md)
- [v4-hc-training-128](v4-hc-training-128.md)
- [v4-hc-training-batch2](v4-hc-training-batch2.md)
- [v4-attention-training-window128](v4-attention-training-window128.md)
- [v4-attention-training-window129-batch2](v4-attention-training-window129-batch2.md)
- [v4-attention-training-duplicate-fixture](v4-attention-training-duplicate-fixture.md)
- [v4-attention-projections-one-row](v4-attention-projections-one-row.md)
- [v4-attention-projections-128](v4-attention-projections-128.md)
- [v4-attention-projections-batch2](v4-attention-projections-batch2.md)
- [v4-compressor128-one-block](v4-compressor128-one-block.md)
- [v4-compressor128-two-blocks](v4-compressor128-two-blocks.md)
- [v4-compressor128-batch2](v4-compressor128-batch2.md)
- [v4-overlap-tail-only](v4-overlap-tail-only.md)
- [v4-overlap-first-block](v4-overlap-first-block.md)
- [v4-overlap-two-blocks](v4-overlap-two-blocks.md)
- [v4-overlap-tail-state-batch2](v4-overlap-tail-state-batch2.md)

Qwen8 GPipe/1F1B训练流水与激活寿命：

- [training-pipeline-gpipe-m1](training-pipeline-gpipe-m1.md)
- [training-pipeline-gpipe-m4](training-pipeline-gpipe-m4.md)
- [training-pipeline-gpipe-m8](training-pipeline-gpipe-m8.md)
- [training-pipeline-gpipe-m16](training-pipeline-gpipe-m16.md)
- [training-pipeline-gpipe-slow-stage](training-pipeline-gpipe-slow-stage.md)
- [training-pipeline-gpipe-shared-link](training-pipeline-gpipe-shared-link.md)
- [training-pipeline-gpipe-recompute](training-pipeline-gpipe-recompute.md)
- [training-pipeline-1f1b-m1](training-pipeline-1f1b-m1.md)
- [training-pipeline-1f1b-m4](training-pipeline-1f1b-m4.md)
- [training-pipeline-1f1b-m8](training-pipeline-1f1b-m8.md)
- [training-pipeline-1f1b-m16](training-pipeline-1f1b-m16.md)
- [training-pipeline-1f1b-slow-stage](training-pipeline-1f1b-slow-stage.md)
- [training-pipeline-1f1b-shared-link](training-pipeline-1f1b-shared-link.md)
- [training-pipeline-1f1b-recompute](training-pipeline-1f1b-recompute.md)
- [training-pipeline-interleaved-m8](training-pipeline-interleaved-m8.md)
- [training-pipeline-interleaved-m16](training-pipeline-interleaved-m16.md)
- [training-pipeline-zero-bubble-m8](training-pipeline-zero-bubble-m8.md)
- [training-pipeline-zero-bubble-m16](training-pipeline-zero-bubble-m16.md)
- [training-pipeline-dualpipe-m8](training-pipeline-dualpipe-m8.md)
- [training-pipeline-dualpipe-m16](training-pipeline-dualpipe-m16.md)

RGB预处理至视觉编码器入口：

- [vision-preprocess-aligned640](vision-preprocess-aligned640.md)
- [vision-preprocess-nonsquare](vision-preprocess-nonsquare.md)
- [vision-preprocess-min-area](vision-preprocess-min-area.md)
- [vision-preprocess-max-area](vision-preprocess-max-area.md)

stage-resource-bounds：

- [stage-resources-qwen8-b1-prefill128](stage-resources-qwen8-b1-prefill128.md)
- [stage-resources-qwen8-b1-prefill512](stage-resources-qwen8-b1-prefill512.md)
- [stage-resources-qwen8-b1-decode8k](stage-resources-qwen8-b1-decode8k.md)
- [stage-resources-qwen8-b1-decode32k](stage-resources-qwen8-b1-decode32k.md)
- [stage-resources-qwen8-b8-prefill128](stage-resources-qwen8-b8-prefill128.md)
- [stage-resources-qwen8-b8-prefill512](stage-resources-qwen8-b8-prefill512.md)
- [stage-resources-qwen8-b8-decode8k](stage-resources-qwen8-b8-decode8k.md)
- [stage-resources-qwen8-b8-decode32k](stage-resources-qwen8-b8-decode32k.md)
- [stage-resources-qwen8-m4-max-40gpu-128gb](stage-resources-qwen8-m4-max-40gpu-128gb.md)
- [stage-resources-qwen8-atlas-300i-a2-64gb](stage-resources-qwen8-atlas-300i-a2-64gb.md)
- [stage-resources-v4flash-b1-prefill128](stage-resources-v4flash-b1-prefill128.md)
- [stage-resources-v4flash-b1-prefill512](stage-resources-v4flash-b1-prefill512.md)
- [stage-resources-v4flash-b1-decode8k](stage-resources-v4flash-b1-decode8k.md)
- [stage-resources-v4flash-b1-decode32k](stage-resources-v4flash-b1-decode32k.md)
- [stage-resources-v4flash-b8-prefill128](stage-resources-v4flash-b8-prefill128.md)
- [stage-resources-v4flash-b8-prefill512](stage-resources-v4flash-b8-prefill512.md)
- [stage-resources-v4flash-b8-decode8k](stage-resources-v4flash-b8-decode8k.md)
- [stage-resources-v4flash-b8-decode32k](stage-resources-v4flash-b8-decode32k.md)
- [stage-resources-v4flash-m4-max-40gpu-128gb](stage-resources-v4flash-m4-max-40gpu-128gb.md)
- [stage-resources-v4flash-atlas-300i-a2-64gb](stage-resources-v4flash-atlas-300i-a2-64gb.md)
- [stage-resources-qwen8-assumed-special-baseline](stage-resources-qwen8-assumed-special-baseline.md)
- [stage-resources-qwen8-double-matrix_bf16](stage-resources-qwen8-double-matrix_bf16.md)
- [stage-resources-qwen8-double-vector_fp32](stage-resources-qwen8-double-vector_fp32.md)
- [stage-resources-qwen8-double-interface_bytes](stage-resources-qwen8-double-interface_bytes.md)
- [stage-resources-qwen8-double-special-exp](stage-resources-qwen8-double-special-exp.md)

v4-compressor-online：

- [v4-online-r4-tail-emits](v4-online-r4-tail-emits.md)
- [v4-online-r4-no-emit](v4-online-r4-no-emit.md)
- [v4-online-r128-boundary](v4-online-r128-boundary.md)
- [v4-online-r128-two-emits](v4-online-r128-two-emits.md)

训练流水GEMM保存身份与重算：

- [pipeline-gemm-save-1f1b](pipeline-gemm-save-1f1b.md)
- [pipeline-gemm-save-gpipe](pipeline-gemm-save-gpipe.md)
- [pipeline-gemm-recompute-products](pipeline-gemm-recompute-products.md)
- [pipeline-gemm-recompute-products-silu](pipeline-gemm-recompute-products-silu.md)

V4固定选择MoE单层训练：

- [v4-moe-training-balanced](v4-moe-training-balanced.md)
- [v4-moe-training-concentrated](v4-moe-training-concentrated.md)
- [v4-moe-training-hash](v4-moe-training-hash.md)
- [v4-moe-training-batch2](v4-moe-training-batch2.md)

V4 Muon/AdamW优化器分组与逐矩阵计算：


Omni PCM到mel前处理：


training-input-supply：

- [training-supply-default](training-supply-default.md)
- [training-supply-no-checkpoint](training-supply-no-checkpoint.md)
- [training-supply-shared-starvation](training-supply-shared-starvation.md)
- [training-supply-independent-storage](training-supply-independent-storage.md)
- [training-supply-cpu-bottleneck](training-supply-cpu-bottleneck.md)

qwen235-execution：

- [qwen235-ep4-tp2-balanced-80gb](qwen235-ep4-tp2-balanced-80gb.md)
- [qwen235-ep4-tp2-hot-80gb](qwen235-ep4-tp2-hot-80gb.md)
- [qwen235-ep4-pp2-48gb](qwen235-ep4-pp2-48gb.md)
- [qwen235-ep4-tp2-24gb-32k](qwen235-ep4-tp2-24gb-32k.md)
- [qwen235-ep4-tp2-two-requests](qwen235-ep4-tp2-two-requests.md)
- [qwen235-equal-hist-pure](qwen235-equal-hist-pure.md)
- [qwen235-equal-hist-mixed](qwen235-equal-hist-mixed.md)

Qwen235专家颗粒度：

- [qwen235-granularity-baseline](qwen235-granularity-baseline.md)
- [qwen235-granularity-coarse64](qwen235-granularity-coarse64.md)
- [qwen235-granularity-fine256-k16](qwen235-granularity-fine256-k16.md)
- [qwen235-granularity-fine256-k8](qwen235-granularity-fine256-k8.md)
- [qwen235-granularity-aligned160](qwen235-granularity-aligned160.md)
- [qwen235-granularity-hot](qwen235-granularity-hot.md)

架构矩阵与tile补齐：

- [architecture-tile-tail129](architecture-tile-tail129.md)
- [architecture-tile-aligned128](architecture-tile-aligned128.md)
- [architecture-tile-decode8k](architecture-tile-decode8k.md)
- [architecture-tile-custom-rate](architecture-tile-custom-rate.md)

封存Chat轨迹到资源账：

- [sealed-chat-known-prefill](sealed-chat-known-prefill.md)
- [sealed-chat-declared-serial](sealed-chat-declared-serial.md)

四模型请求与精度匹配硬件供给：


权重/KV容量与带宽代际对照：


FA4单SM资源配比：


注意力输入槽与异步流水：


V4共享专家FP8复制坐标：


矩阵—向量交接与完整行依赖：


配对投影费用与功率条件：

- [paired-projection-unknown](paired-projection-unknown.md)
- [paired-projection-declared-2x](paired-projection-declared-2x.md)
- [paired-projection-declared-10x](paired-projection-declared-10x.md)
- [matrix-vector-staged-rows128-slots1](matrix-vector-staged-rows128-slots1.md)
- [matrix-vector-staged-rows32-slots1](matrix-vector-staged-rows32-slots1.md)
- [matrix-vector-staged-rows32-slots2](matrix-vector-staged-rows32-slots2.md)
- [matrix-vector-staged-rows32-slots4](matrix-vector-staged-rows32-slots4.md)
- [matrix-vector-direct-rows128-slots1](matrix-vector-direct-rows128-slots1.md)
- [matrix-vector-direct-rows32-slots1](matrix-vector-direct-rows32-slots1.md)
- [matrix-vector-direct-rows32-slots2](matrix-vector-direct-rows32-slots2.md)
- [matrix-vector-direct-rows32-slots4](matrix-vector-direct-rows32-slots4.md)
- [v4-copy-coordinates-m32](v4-copy-coordinates-m32.md)
- [v4-copy-coordinates-m64](v4-copy-coordinates-m64.md)
- [attention-input-base](attention-input-base.md)
- [attention-input-matrix-double](attention-input-matrix-double.md)
- [attention-input-long-latency](attention-input-long-latency.md)
- [attention-input-tile-k16](attention-input-tile-k16.md)
- [attention-input-tile-k64](attention-input-tile-k64.md)
- [attention-input-capacity-one-slot](attention-input-capacity-one-slot.md)
- [fa4-qwen8-resource-balance](fa4-qwen8-resource-balance.md)
- [storage-generation-qwen8-235](storage-generation-qwen8-235.md)
- [granularity-selection-default](granularity-selection-default.md)
- [granularity-selection-fine150](granularity-selection-fine150.md)
- [granularity-selection-declared-small-remainder](granularity-selection-declared-small-remainder.md)
- [granularity-selection-declared-large-remainder](granularity-selection-declared-large-remainder.md)
- [trace-cache-default](trace-cache-default.md)
- [trace-cache-host50gb](trace-cache-host50gb.md)
- [trace-cache-lookup2ms](trace-cache-lookup2ms.md)
- [v4-mtp-first-call](v4-mtp-first-call.md)
- [v4-mtp-b2-prefill16](v4-mtp-b2-prefill16.md)
- [v4-mtp-prefill129](v4-mtp-prefill129.md)
- [v4-mtp-history128](v4-mtp-history128.md)
- [request-h100-original](request-h100-original.md)
- [request-h100-first-output](request-h100-first-output.md)
- [request-h100-vector-provider](request-h100-vector-provider.md)
- [request-h100-low-capacity](request-h100-low-capacity.md)
- [omni-pcm-1s](omni-pcm-1s.md)
- [omni-pcm-mixed](omni-pcm-mixed.md)
- [omni-pcm-hop-tail](omni-pcm-hop-tail.md)
- [omni-pcm-serialized-limit](omni-pcm-serialized-limit.md)
- [v4-optimizer-flash-base-unresolved](v4-optimizer-flash-base-unresolved.md)
- [v4-optimizer-flash-mtp-declared-row-muon](v4-optimizer-flash-mtp-declared-row-muon.md)
- [v4-optimizer-flash-stored-matrices](v4-optimizer-flash-stored-matrices.md)
- [v4-optimizer-pro-base-declared-row-muon](v4-optimizer-pro-base-declared-row-muon.md)