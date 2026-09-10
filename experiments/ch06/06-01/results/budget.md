# 实验 6-1 结果：模型与硬件的资源收支

逐卡 80 GB／3.35 TB/s／989.4 TFLOPs，scale-up 单向 450 GB/s、启动 3 μs（声明输入）。

| 场景 | 方案 | 逐卡驻留 | 容量 | 算力 | 内存带宽 | 互联 | 首先受限于 |
| --- | --- | ---: | :---: | ---: | ---: | ---: | --- |
| Qwen3-8B prefill 8192 | TP=1 副本×8 | 17.6 GB | 通过 | 135.03 ms | 4.90 ms | 0.00 ms | **算力** |
| Qwen3-8B prefill 8192 | TP=2 | 8.8 GB | 通过 | 67.51 ms | 2.45 ms | 11.17 ms | **算力** |
| Qwen3-8B prefill 8192 | TP=4 | 4.4 GB | 通过 | 33.76 ms | 1.22 ms | 17.40 ms | **算力** |
| Qwen3-8B prefill 8192 | TP=8 | 2.2 GB | 通过 | 16.88 ms | 0.61 ms | 21.81 ms | **互联** |
| Qwen3-8B decode b64 h8192 | TP=1 副本×8 | 93.7 GB | 不通过 | 1.29 ms | 27.60 ms | 0.00 ms | **容量** |
| Qwen3-8B decode b64 h8192 | TP=2 | 46.9 GB | 通过 | 0.65 ms | 13.80 ms | 0.52 ms | **内存带宽** |
| Qwen3-8B decode b64 h8192 | TP=4 | 23.4 GB | 通过 | 0.32 ms | 6.90 ms | 1.42 ms | **内存带宽** |
| Qwen3-8B decode b64 h8192 | TP=8 | 11.7 GB | 通过 | 0.16 ms | 3.45 ms | 3.17 ms | **内存带宽** |
| Qwen3-235B prefill 8192 | TP=1 副本×8 | 471.8 GB | 不通过 | 451.32 ms | 140.47 ms | 0.00 ms | **容量** |
| Qwen3-235B prefill 8192 | TP=2 | 235.9 GB | 不通过 | 225.66 ms | 70.24 ms | 11.17 ms | **容量** |
| Qwen3-235B prefill 8192 | TP=4 | 117.9 GB | 不通过 | 112.83 ms | 35.12 ms | 17.40 ms | **容量** |
| Qwen3-235B prefill 8192 | TP=8 | 59.0 GB | 通过 | 56.41 ms | 17.56 ms | 21.81 ms | **算力** |
| Qwen3-235B decode b64 h8192 | TP=1 副本×8 | 571.1 GB | 不通过 | 4.42 ms | 170.12 ms | 0.00 ms | **容量** |
| Qwen3-235B decode b64 h8192 | TP=2 | 285.6 GB | 不通过 | 2.21 ms | 85.06 ms | 0.52 ms | **容量** |
| Qwen3-235B decode b64 h8192 | TP=4 | 142.8 GB | 不通过 | 1.11 ms | 42.53 ms | 1.42 ms | **容量** |
| Qwen3-235B decode b64 h8192 | TP=8 | 71.4 GB | 通过 | 0.55 ms | 21.26 ms | 3.17 ms | **内存带宽** |
| V4-Flash prefill 8192 | TP=1 副本×8 | 568.7 GB | 不通过 | 233.60 ms | 169.77 ms | 0.00 ms | **容量** |
| V4-Flash prefill 8192 | TP=2 | 284.4 GB | 不通过 | 116.80 ms | 84.89 ms | 11.17 ms | **容量** |
| V4-Flash prefill 8192 | TP=4 | 142.2 GB | 不通过 | 58.40 ms | 42.44 ms | 17.40 ms | **容量** |
| V4-Flash prefill 8192 | TP=8 | 71.1 GB | 通过 | 29.20 ms | 21.22 ms | 21.81 ms | **算力** |
| V4-Flash decode b64 h8192 | TP=1 副本×8 | 573.4 GB | 不通过 | 1.91 ms | 171.17 ms | 0.00 ms | **容量** |
| V4-Flash decode b64 h8192 | TP=2 | 286.7 GB | 不通过 | 0.96 ms | 85.58 ms | 0.52 ms | **容量** |
| V4-Flash decode b64 h8192 | TP=4 | 143.4 GB | 不通过 | 0.48 ms | 42.79 ms | 1.42 ms | **容量** |
| V4-Flash decode b64 h8192 | TP=8 | 71.7 GB | 通过 | 0.24 ms | 21.40 ms | 3.17 ms | **内存带宽** |
