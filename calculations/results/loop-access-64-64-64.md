# c-loop-source-accesses — 

输入：`{"k": 64, "m": 64, "n": 64, "tiles": [8, 16, 32, 64, 128, 256]}`

数组访问为源码计数；匹配时长来自固定 CPU 实验，非缓存测量。

| 结果 | 值 |
| --- | ---: |
| mathematical_flops | 524,288 |
| distinct_array_bytes | 49,152 |
| candidates | 8 |
| candidates_with_recorded_samples | 8 |
| measured_cache_misses | `null` |
| measured_hbm_bytes | `null` |

| 方法 | tile | A读 | B读 | C读 | C更新 | C清零 | 源码bytes | 实测中位 μs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ijk | None | 262144 | 262144 | 0 | 4096 | 0 | 2113536 | 119.872181 |
| ikj | None | 4096 | 262144 | 262144 | 262144 | 4096 | 3178496 | 22.5188679 |
| blocked | 8 | 32768 | 262144 | 262144 | 262144 | 4096 | 3293184 | 56.1891891 |
| blocked | 16 | 16384 | 262144 | 262144 | 262144 | 4096 | 3227648 | 40.6317461 |
| blocked | 32 | 8192 | 262144 | 262144 | 262144 | 4096 | 3194880 | 33.8091398 |
| blocked | 64 | 4096 | 262144 | 262144 | 262144 | 4096 | 3178496 | 22.4320558 |
| blocked | 128 | 4096 | 262144 | 262144 | 262144 | 4096 | 3178496 | 22.2979094 |
| blocked | 256 | 4096 | 262144 | 262144 | 262144 | 4096 | 3178496 | 22.2112675 |

计量条件：

- 循环严格对应实验5-1固定 matmul.c：行主序 FP32、ijk 局部 sum、ikj 的 v=a[i,k]，以及 ii-jj-kk-i-k-j blocked。C 源码与原测量数据保存独立哈希副本，未重新执行基准。
- 计数层次是 C 源码数组表达式；sum/v 等局部标量不计数组访问。memset 计零初始化元素与字节，不推断实际 store 指令次数。ijk 直接覆写 C，其他两种先清零再读改写。
- 编译器可能寄存器保留、向量化、提升加载或合并写入，源码字节不等于指令流量，更不等于缓存 miss 或 DRAM 字节；相同逐元素 k 顺序也不证明所有编译选项都逐位相同。
- blocked 的 A 每个列块读取一次，含尾块；B 与 C 读改写仍每乘加一次。B 的最内层地址步长为 ijk 的 N 与其他两者的1，边界跳转另算。
- 测量值从实验原始9次样本重新取中位数，只在形状／方法／tile完全匹配时附上，未匹配留空。数据来自既有 M2 Max 单CPU线程实验，不作为 Qwen GPU 或普遍硬件性能证据。
- 实验计时包括实现内部输出初始化；ijk没有单独清零。不同算法源码数组字节可能更多而运行更快，不能只用本计数解释时间差。

固定来源：

- [sources/cpu-loops/matmul.c](../sources/cpu-loops/matmul.c)，SHA256 `eb33ea890733421ae54e75d641eb380c5c95c086ba483a1783c0094c7b80b1db`。
- [sources/cpu-loops/raw.json](../sources/cpu-loops/raw.json)，SHA256 `c7b00947ab58df192946ecd430ecf988450ec13117f97e15810f66031fe1bedd`。
- [sources/cpu-loops/results.json](../sources/cpu-loops/results.json)，SHA256 `e5087d24f4ebe2a7b6047244aab9aa1240ae9a91e00bfb7e3891e9b53d86510d`。
