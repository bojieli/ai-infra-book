# scalar-shared-bank-mapping — 

输入：`{"access": "same-word", "broadcast": false, "ports": 1, "stride_words": 32}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| lanes | 32 |
| banks | 32 |
| word_bytes | 4 |
| logical_tile_bytes | 4,096 |
| allocated_tile_bytes | 4,096 |
| padding_bytes | 0 |
| padding_fraction | 0.0 |
| lane_requested_bytes | 128 |
| distinct_requested_bytes | 4 |
| serviced_word_bytes | 128 |
| service_rounds | 32 |
| predicted_kernel_speedup | `null` |

| bank | lanes | 不同字 | 服务请求 | 轮数 |
| --- | --- | ---: | ---: | ---: |
| 0 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31] | 1 | 32 | 32 |
| 1 | [] | 0 | 0 | 0 |
| 2 | [] | 0 | 0 | 0 |
| 3 | [] | 0 | 0 | 0 |
| 4 | [] | 0 | 0 | 0 |
| 5 | [] | 0 | 0 | 0 |
| 6 | [] | 0 | 0 | 0 |
| 7 | [] | 0 | 0 | 0 |
| 8 | [] | 0 | 0 | 0 |
| 9 | [] | 0 | 0 | 0 |
| 10 | [] | 0 | 0 | 0 |
| 11 | [] | 0 | 0 | 0 |
| 12 | [] | 0 | 0 | 0 |
| 13 | [] | 0 | 0 | 0 |
| 14 | [] | 0 | 0 | 0 |
| 15 | [] | 0 | 0 | 0 |
| 16 | [] | 0 | 0 | 0 |
| 17 | [] | 0 | 0 | 0 |
| 18 | [] | 0 | 0 | 0 |
| 19 | [] | 0 | 0 | 0 |
| 20 | [] | 0 | 0 | 0 |
| 21 | [] | 0 | 0 | 0 |
| 22 | [] | 0 | 0 | 0 |
| 23 | [] | 0 | 0 | 0 |
| 24 | [] | 0 | 0 | 0 |
| 25 | [] | 0 | 0 | 0 |
| 26 | [] | 0 | 0 | 0 |
| 27 | [] | 0 | 0 | 0 |
| 28 | [] | 0 | 0 | 0 |
| 29 | [] | 0 | 0 | 0 |
| 30 | [] | 0 | 0 | 0 |
| 31 | [] | 0 | 0 | 0 |

计量条件：

- 正文 32×32 FP32 暂存块，32 lane 各发一个标量 32-bit 字读取；连续字映射到连续 bank，bank=word_address mod 32。CUDA 13.2.1 官方原件固定在来源中。
- 每 bank 每轮默认一个字端口，所有 bank 同时服务，轮数取各 bank 请求数/端口数向上取整的最大值。ports>1 是假设的端口变体，不声明某张 GPU 具备该规格。
- broadcast 默认关闭，逐 lane 计服务；打开后仅将同一字地址的读取合并，不合并同 bank 的不同地址。这是显式服务语义开关，不处理重复地址写入、原子或向量指令。
- row 访问第0行，column 访问第0列，same-word 全部读取地址0。分配量为32整行乘 stride，含最后行尾部 padding；有效32×32数据量不变。
- 这是单次请求的端口服务模型，不是内核加速比。标量行 padding 与 TMA 的16-byte分组 swizzle不同；未模拟指令拆分、bank宽度变体、同步、跨warp并发或实际分配粒度。

固定来源：

- [sources/hardware/nvidia-async-copies-13-2-1.html](https://docs.nvidia.com/cuda/archive/13.2.1/cuda-programming-guide/04-special-topics/async-copies.html)，SHA256 `e601b5f21450aba8f96d78906d81621745f58758f1b791cf8280ef4be8d2a0c2`。
