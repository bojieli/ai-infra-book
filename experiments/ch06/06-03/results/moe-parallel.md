# 实验 6-3 结果：MoE 结构与并行选择

## 第一组：Qwen3-235B-A22B 的八卡切分

| TP×EP×PP | 位宽 | 八卡物理权重 | 逐卡通过 | 最大并发 | 受限的卡 |
| --- | ---: | ---: | :---: | ---: | --- |
| 1×8×1 | 16 bit | 582.1 GB | 是 | 3 | 全部 |
| 1×8×1 | 8 bit | 305.8 GB | 是 | 25 | 全部 |
| 1×8×1 | 4 bit | 165.5 GB | 是 | 36 | 全部 |
| 2×4×1 | 16 bit | 518.6 GB | 是 | 16 | 全部 |
| 2×4×1 | 8 bit | 268.6 GB | 是 | 56 | 全部 |
| 2×4×1 | 4 bit | 141.7 GB | 是 | 76 | 全部 |
| 4×2×1 | 16 bit | 486.8 GB | 是 | 43 | 全部 |
| 4×2×1 | 8 bit | 250.0 GB | 是 | 118 | 全部 |
| 4×2×1 | 4 bit | 129.8 GB | 是 | 156 | 全部 |
| 8×1×1 | 16 bit | 471.7 GB | 是 | 47 | 全部 |
| 8×1×1 | 8 bit | 241.5 GB | 是 | 120 | 全部 |
| 8×1×1 | 4 bit | 124.4 GB | 是 | 158 | 全部 |
| 2×2×2 | 16 bit | 486.4 GB | 是 | 43 | 全部 |
| 2×2×2 | 8 bit | 249.6 GB | 是 | 118 | 全部 |
| 2×2×2 | 4 bit | 129.4 GB | 是 | 156 | 全部 |

## dispatch／combine：路由分布与互联条件

| 互联 | 每 rank token | 路由 | 本地/远端分派 | dispatch 发送 | 最忙接收 | dispatch+combine |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| 机内 450 GB/s | 1 | balanced | 8/56 | 0.44 MiB | 0.05 MiB | 0.042 ms |
| 机内 450 GB/s | 1 | hotspot | 8/56 | 0.44 MiB | 0.44 MiB | 0.044 ms |
| 机内 450 GB/s | 8 | balanced | 64/448 | 3.50 MiB | 0.44 MiB | 0.044 ms |
| 机内 450 GB/s | 8 | hotspot | 64/448 | 3.50 MiB | 3.50 MiB | 0.058 ms |
| 机内 450 GB/s | 64 | balanced | 512/3584 | 28.00 MiB | 3.50 MiB | 0.058 ms |
| 机内 450 GB/s | 64 | hotspot | 512/3584 | 28.00 MiB | 28.00 MiB | 0.172 ms |
| 机内 450 GB/s | 1024 | balanced | 8192/57344 | 448.00 MiB | 56.00 MiB | 0.303 ms |
| 机内 450 GB/s | 1024 | hotspot | 8192/57344 | 448.00 MiB | 448.00 MiB | 2.130 ms |
| scale-out 50 GB/s | 1 | balanced | 8/56 | 0.44 MiB | 0.05 MiB | 0.072 ms |
| scale-out 50 GB/s | 1 | hotspot | 8/56 | 0.44 MiB | 0.44 MiB | 0.088 ms |
| scale-out 50 GB/s | 8 | balanced | 64/448 | 3.50 MiB | 0.44 MiB | 0.088 ms |
| scale-out 50 GB/s | 8 | hotspot | 64/448 | 3.50 MiB | 3.50 MiB | 0.217 ms |
| scale-out 50 GB/s | 64 | balanced | 512/3584 | 28.00 MiB | 3.50 MiB | 0.217 ms |
| scale-out 50 GB/s | 64 | hotspot | 512/3584 | 28.00 MiB | 28.00 MiB | 1.244 ms |
| scale-out 50 GB/s | 1024 | balanced | 8192/57344 | 448.00 MiB | 56.00 MiB | 2.419 ms |
| scale-out 50 GB/s | 1024 | hotspot | 8192/57344 | 448.00 MiB | 448.00 MiB | 18.860 ms |
| scale-out 50 GB/s、启动 20 μs | 1 | balanced | 8/56 | 0.44 MiB | 0.05 MiB | 0.282 ms |
| scale-out 50 GB/s、启动 20 μs | 1 | hotspot | 8/56 | 0.44 MiB | 0.44 MiB | 0.298 ms |
| scale-out 50 GB/s、启动 20 μs | 8 | balanced | 64/448 | 3.50 MiB | 0.44 MiB | 0.298 ms |
| scale-out 50 GB/s、启动 20 μs | 8 | hotspot | 64/448 | 3.50 MiB | 3.50 MiB | 0.427 ms |
| scale-out 50 GB/s、启动 20 μs | 64 | balanced | 512/3584 | 28.00 MiB | 3.50 MiB | 0.427 ms |
| scale-out 50 GB/s、启动 20 μs | 64 | hotspot | 512/3584 | 28.00 MiB | 28.00 MiB | 1.454 ms |
| scale-out 50 GB/s、启动 20 μs | 1024 | balanced | 8192/57344 | 448.00 MiB | 56.00 MiB | 2.629 ms |
| scale-out 50 GB/s、启动 20 μs | 1024 | hotspot | 8192/57344 | 448.00 MiB | 448.00 MiB | 19.070 ms |

## 第二组：V4-Flash／V4-Pro／K3 的专家台账（batch=64）

| 模型 | 路由 | FFN TFLOPs | 每层专家并集 | 批内权重载荷 |
| --- | --- | ---: | ---: | ---: |
| deepseek-v4-flash | balanced | 0.9754 | 256 | 518.1 GiB |
| deepseek-v4-flash | concentrated | 0.9754 | 6 | 14.2 GiB |
| deepseek-v4-pro | balanced | 3.6321 | 384 | 2890.1 GiB |
| deepseek-v4-pro | concentrated | 3.6321 | 6 | 52.9 GiB |
| kimi-k3 | balanced | 8.5530 | 896 | 5105.4 GiB |
| kimi-k3 | concentrated | 8.5530 | 16 | 124.5 GiB |
