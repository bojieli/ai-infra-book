# 实验 7-1 结果：八卡服务器之间的模型切分

每卡 80 GB，每机 8 卡；每次交接 = α + 载荷/有效带宽。

## 容量下界

| 模型 | 阶段 | 统一 BF16 权重 | 状态 | 最少卡数 | 最少服务器 |
| --- | --- | ---: | ---: | ---: | ---: |
| deepseek-v4-pro | prefill 8192 | 3146.0 GB | 0.11 GB | 40 | 5 |
| deepseek-v4-pro | decode b64 h8192 | 3146.0 GB | 6.87 GB | 40 | 5 |
| kimi-k3 | prefill 8192 | 5559.0 GB | 0.68 GB | 70 | 9 |
| kimi-k3 | decode b64 h8192 | 5559.0 GB | 43.58 GB | 71 | 9 |

## 通信预算

| 模型 | 阶段 | 互联 | 方案 | 每次载荷 | 交接次数 | 通信时间 |
| --- | --- | --- | --- | ---: | ---: | ---: |
| deepseek-v4-pro | prefill 8192 | InfiniBand 400 Gb/s（50 GB/s）、α=5 μs | B 服务器间 PP（只传段边界） | 112.00 MiB | 4 | 9.42 ms |
| deepseek-v4-pro | prefill 8192 | InfiniBand 400 Gb/s（50 GB/s）、α=5 μs | C 跨服务器 TP／EP（每层跨机） | 112.00 MiB | 61 | 143.58 ms |
| deepseek-v4-pro | prefill 8192 | 以太网 200 Gb/s（25 GB/s）、α=20 μs | B 服务器间 PP（只传段边界） | 112.00 MiB | 4 | 18.87 ms |
| deepseek-v4-pro | prefill 8192 | 以太网 200 Gb/s（25 GB/s）、α=20 μs | C 跨服务器 TP／EP（每层跨机） | 112.00 MiB | 61 | 287.77 ms |
| deepseek-v4-pro | decode b64 h8192 | InfiniBand 400 Gb/s（50 GB/s）、α=5 μs | B 服务器间 PP（只传段边界） | 0.88 MiB | 4 | 0.09 ms |
| deepseek-v4-pro | decode b64 h8192 | InfiniBand 400 Gb/s（50 GB/s）、α=5 μs | C 跨服务器 TP／EP（每层跨机） | 0.88 MiB | 61 | 1.42 ms |
| deepseek-v4-pro | decode b64 h8192 | 以太网 200 Gb/s（25 GB/s）、α=20 μs | B 服务器间 PP（只传段边界） | 0.88 MiB | 4 | 0.23 ms |
| deepseek-v4-pro | decode b64 h8192 | 以太网 200 Gb/s（25 GB/s）、α=20 μs | C 跨服务器 TP／EP（每层跨机） | 0.88 MiB | 61 | 3.46 ms |
| kimi-k3 | prefill 8192 | InfiniBand 400 Gb/s（50 GB/s）、α=5 μs | B 服务器间 PP（只传段边界） | 112.00 MiB | 8 | 18.83 ms |
| kimi-k3 | prefill 8192 | InfiniBand 400 Gb/s（50 GB/s）、α=5 μs | C 跨服务器 TP／EP（每层跨机） | 112.00 MiB | 93 | 218.90 ms |
| kimi-k3 | prefill 8192 | 以太网 200 Gb/s（25 GB/s）、α=20 μs | B 服务器间 PP（只传段边界） | 112.00 MiB | 8 | 37.74 ms |
| kimi-k3 | prefill 8192 | 以太网 200 Gb/s（25 GB/s）、α=20 μs | C 跨服务器 TP／EP（每层跨机） | 112.00 MiB | 93 | 438.74 ms |
| kimi-k3 | decode b64 h8192 | InfiniBand 400 Gb/s（50 GB/s）、α=5 μs | B 服务器间 PP（只传段边界） | 0.88 MiB | 8 | 0.19 ms |
| kimi-k3 | decode b64 h8192 | InfiniBand 400 Gb/s（50 GB/s）、α=5 μs | C 跨服务器 TP／EP（每层跨机） | 0.88 MiB | 93 | 2.17 ms |
| kimi-k3 | decode b64 h8192 | 以太网 200 Gb/s（25 GB/s）、α=20 μs | B 服务器间 PP（只传段边界） | 0.88 MiB | 8 | 0.45 ms |
| kimi-k3 | decode b64 h8192 | 以太网 200 Gb/s（25 GB/s）、α=20 μs | C 跨服务器 TP／EP（每层跨机） | 0.88 MiB | 93 | 5.27 ms |
