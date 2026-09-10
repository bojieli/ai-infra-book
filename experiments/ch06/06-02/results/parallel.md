# 实验 6-2 结果：Qwen3-8B 的并行组合

八卡、逐卡 80 GB；互联单向 450 GB/s、启动 3.0 μs（声明输入）。

| TP×PP×DP | 历史 | 每副本 batch | 全局并发 | 最忙卡驻留 | 容量 | 逐卡矩阵 GFLOPs | 流水交接 |
| --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: |
| 1×1×8 | 8192 | 1 | 8 | 18.38 GiB | 通过 | 159.75 | 0.00 MiB |
| 1×1×8 | 8192 | 8 | 64 | 26.26 GiB | 通过 | 1277.99 | 0.00 MiB |
| 1×1×8 | 32768 | 1 | 8 | 21.76 GiB | 通过 | 275.71 | 0.00 MiB |
| 1×1×8 | 32768 | 8 | 64 | 53.26 GiB | 通过 | 2205.70 | 0.00 MiB |
| 2×1×4 | 8192 | 1 | 4 | 10.19 GiB | 通过 | 79.87 | 0.00 MiB |
| 2×1×4 | 8192 | 8 | 32 | 14.13 GiB | 通过 | 639.00 | 0.00 MiB |
| 2×1×4 | 32768 | 1 | 4 | 11.88 GiB | 通过 | 137.86 | 0.00 MiB |
| 2×1×4 | 32768 | 8 | 32 | 27.63 GiB | 通过 | 1102.85 | 0.00 MiB |
| 4×1×2 | 8192 | 1 | 2 | 6.10 GiB | 通过 | 39.94 | 0.00 MiB |
| 4×1×2 | 8192 | 8 | 16 | 8.06 GiB | 通过 | 319.50 | 0.00 MiB |
| 4×1×2 | 32768 | 1 | 2 | 6.94 GiB | 通过 | 68.93 | 0.00 MiB |
| 4×1×2 | 32768 | 8 | 16 | 14.81 GiB | 通过 | 551.43 | 0.00 MiB |
| 8×1×1 | 8192 | 1 | 1 | 4.05 GiB | 通过 | 19.97 | 0.00 MiB |
| 8×1×1 | 8192 | 8 | 8 | 5.03 GiB | 通过 | 159.75 | 0.00 MiB |
| 8×1×1 | 32768 | 1 | 1 | 4.47 GiB | 通过 | 34.46 | 0.00 MiB |
| 8×1×1 | 32768 | 8 | 8 | 8.41 GiB | 通过 | 275.71 | 0.00 MiB |
| 2×4×1 | 8192 | 1 | 1 | 4.34 GiB | 通过 | 19.97 | 0.05 MiB |
| 2×4×1 | 8192 | 8 | 8 | 5.32 GiB | 通过 | 159.75 | 0.38 MiB |
| 2×4×1 | 32768 | 1 | 1 | 4.76 GiB | 通过 | 34.46 | 0.05 MiB |
| 2×4×1 | 32768 | 8 | 8 | 8.70 GiB | 通过 | 275.71 | 0.38 MiB |
| 4×2×1 | 8192 | 1 | 1 | 4.05 GiB | 通过 | 19.97 | 0.03 MiB |
| 4×2×1 | 8192 | 8 | 8 | 5.03 GiB | 通过 | 159.75 | 0.25 MiB |
| 4×2×1 | 32768 | 1 | 1 | 4.47 GiB | 通过 | 34.46 | 0.03 MiB |
| 4×2×1 | 32768 | 8 | 8 | 8.41 GiB | 通过 | 275.71 | 0.25 MiB |
| 2×2×2 | 8192 | 1 | 2 | 6.10 GiB | 通过 | 39.94 | 0.03 MiB |
| 2×2×2 | 8192 | 8 | 16 | 8.06 GiB | 通过 | 319.50 | 0.25 MiB |
| 2×2×2 | 32768 | 1 | 2 | 6.94 GiB | 通过 | 68.93 | 0.03 MiB |
| 2×2×2 | 32768 | 8 | 16 | 14.81 GiB | 通过 | 551.43 | 0.25 MiB |

## 每层通信（decode 单步）

| TP×PP×DP | 通信摘要 |
| --- | --- |
| 1×1×8 | activation_bytes 8192；full_last_position_logit_bytes 6.077e+05；vocabulary_logit_shard_bytes 6.077e+05；selected_token_id_bytes 4 |
| 2×1×4 | activation_bytes 8192；full_last_position_logit_bytes 6.077e+05；vocabulary_logit_shard_bytes 3.039e+05；selected_token_id_bytes 4；nonempty_communication_operations 75 |
| 4×1×2 | activation_bytes 8192；full_last_position_logit_bytes 6.077e+05；vocabulary_logit_shard_bytes 1.519e+05；selected_token_id_bytes 4；nonempty_communication_operations 75 |
| 8×1×1 | activation_bytes 8192；full_last_position_logit_bytes 6.077e+05；vocabulary_logit_shard_bytes 7.597e+04；selected_token_id_bytes 4；nonempty_communication_operations 75 |
| 2×4×1 | activation_bytes 8192；full_last_position_logit_bytes 6.077e+05；vocabulary_logit_shard_bytes 3.039e+05；selected_token_id_bytes 4；nonempty_communication_operations 79 |
| 4×2×1 | activation_bytes 8192；full_last_position_logit_bytes 6.077e+05；vocabulary_logit_shard_bytes 1.519e+05；selected_token_id_bytes 4；nonempty_communication_operations 77 |
| 2×2×2 | activation_bytes 8192；full_last_position_logit_bytes 6.077e+05；vocabulary_logit_shard_bytes 3.039e+05；selected_token_id_bytes 4；nonempty_communication_operations 77 |

## 最值得补测的一项

最值得补测的一项：TP=8 时每层 all-reduce 的实际启动开销 α。本表的通信项按声明 α 计算；实验 6-5 已证明通信与计算共享资源时两者都变慢，因此 α 的实测值会同时改变通信项与计算项。
