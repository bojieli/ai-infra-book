# 实验 4-1 结果：注意力计算与单元配比

## A. 单 SM 内的三项资源（Qwen3-8B head_dim=128）

| tile | 矩阵周期 | SMEM 周期 | 指数周期 | 下界 | 限制资源 |
| --- | ---: | ---: | ---: | ---: | --- |
| m128-n128-paper-baseline | 1024 | 768 | 1024 | 1024 | matrix、exp |
| m128-n128-matrix-double | 512 | 768 | 1024 | 1024 | exp |
| m128-n128-matrix-exp-double | 512 | 768 | 512 | 768 | smem |
| m128-n128-all-three-double | 512 | 384 | 512 | 512 | matrix、exp |
| m256-n128-paper-baseline | 2048 | 1536 | 2048 | 2048 | matrix、exp |
| m256-n128-matrix-double | 1024 | 1536 | 2048 | 2048 | exp |
| m256-n128-matrix-exp-double | 1024 | 1536 | 1024 | 1536 | smem |
| m256-n128-all-three-double | 1024 | 768 | 1024 | 1024 | matrix、exp |
| m128-n256-paper-baseline | 2048 | 1536 | 2048 | 2048 | matrix、exp |
| m128-n256-matrix-double | 1024 | 1536 | 2048 | 2048 | exp |
| m128-n256-matrix-exp-double | 1024 | 1536 | 1024 | 1536 | smem |
| m128-n256-all-three-double | 1024 | 768 | 1024 | 1024 | matrix、exp |
| m256-n256-paper-baseline | 4096 | 3072 | 4096 | 4096 | matrix、exp |
| m256-n256-matrix-double | 2048 | 3072 | 4096 | 4096 | exp |
| m256-n256-matrix-exp-double | 2048 | 3072 | 2048 | 3072 | smem |
| m256-n256-all-three-double | 2048 | 1536 | 2048 | 2048 | matrix、exp |

## B. 同一注意力工作在各设备上的完成时间

| 上下文 | 设备 | 峰值口径 | 计算下界 | 访存下界 | Roofline 下界 | 主导 |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 8192 | a100-80gb-sxm | BF16/FP32 tensor 312 T | 63.441 ms | 1.185 ms | 63.441 ms | 计算 |
| 8192 | h100-sxm | BF16/FP32 tensor 989 T | 20.006 ms | 0.721 ms | 20.006 ms | 计算 |
| 8192 | b200-sxm | BF16/FP32 tensor 2250 T | 8.797 ms | 0.302 ms | 8.797 ms | 计算 |
| 8192 | ascend-950pr-max-spec | 见备注 | — | 1.510 ms | — | 只能给访存下界 |
| 8192 | ascend-950dt-max-spec | 见备注 | — | 0.604 ms | — | 只能给访存下界 |
| 8192 | m2-max-38gpu-96gb | 见备注 | — | 6.040 ms | — | 只能给访存下界 |
| 8192 | rtx-pro6000-blackwell-ws | BF16/FP32 tensor 504 T | 39.289 ms | 1.348 ms | 39.289 ms | 计算 |
| 32768 | a100-80gb-sxm | BF16/FP32 tensor 312 T | 1014.965 ms | 4.739 ms | 1014.965 ms | 计算 |
| 32768 | h100-sxm | BF16/FP32 tensor 989 T | 320.062 ms | 2.885 ms | 320.062 ms | 计算 |
| 32768 | b200-sxm | BF16/FP32 tensor 2250 T | 140.742 ms | 1.208 ms | 140.742 ms | 计算 |
| 32768 | ascend-950pr-max-spec | 见备注 | — | 6.040 ms | — | 只能给访存下界 |
| 32768 | ascend-950dt-max-spec | 见备注 | — | 2.416 ms | — | 只能给访存下界 |
| 32768 | m2-max-38gpu-96gb | 见备注 | — | 24.159 ms | — | 只能给访存下界 |
| 32768 | rtx-pro6000-blackwell-ws | BF16/FP32 tensor 504 T | 628.561 ms | 5.393 ms | 628.561 ms | 计算 |

## 注意力工作量本身

| 上下文 | 因果注意力 TFLOPs | 新写 KV | 分数张量读写 | exp 次数 |
| ---: | ---: | ---: | ---: | ---: |
| 8192 | 19.794 | 1.125 GiB | 1152.0 GiB | 4.23e+10 |
| 32768 | 316.669 | 4.500 GiB | 18432.0 GiB | 6.33e+11 |
