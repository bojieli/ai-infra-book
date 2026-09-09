# qwen-activation-host-transfer — qwen3-8b

输入：`{"bandwidth_bytes_per_second": 25769803776, "blocks": 8, "consume_ns": 4000000, "device_slots": 1, "host_slots": 2, "prepare_ns": 1000000, "tokens": 8192}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| block_bytes | 67,108,864 |
| total_h2d_bytes | 536,870,912 |
| copy_seconds | 0.0026041666666666665 |
| copy_exact_seconds | `"1/384"` |
| serial_seconds | 0.060833333333333336 |
| ideal_unconstrained_pipeline_seconds | 0.035604166666666666 |
| scheduled_finish_seconds | 0.05383333333333333 |
| scheduled_finish_exact_seconds | `"323/6000"` |
| host_reserved_pool_bytes | 134,217,728 |
| device_reserved_pool_bytes | 67,108,864 |
| host_live_peak_bytes | 134,217,728 |
| device_live_peak_bytes | 67,108,864 |
| combined_live_peak_bytes | 201,326,592 |
| hypothetical_speedup | 1.130030959752322 |
| actual_gpu_seconds | `null` |

| 块 | 主机槽 | 设备槽 | 准备开始 ms | H2D开始 ms | H2D完成 ms | 消费完成 ms |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 0.000000 | 1.000000 | 3.604167 | 7.604167 |
| 1 | 1 | 0 | 1.000000 | 7.604167 | 10.208333 | 14.208333 |
| 2 | 0 | 0 | 3.604167 | 14.208333 | 16.812500 | 20.812500 |
| 3 | 1 | 0 | 10.208333 | 20.812500 | 23.416667 | 27.416667 |
| 4 | 0 | 0 | 16.812500 | 27.416667 | 30.020833 | 34.020833 |
| 5 | 1 | 0 | 23.416667 | 34.020833 | 36.625000 | 40.625000 |
| 6 | 0 | 0 | 30.020833 | 40.625000 | 43.229167 | 47.229167 |
| 7 | 1 | 0 | 36.625000 | 47.229167 | 49.833333 | 53.833333 |

计量条件：

- 对象为固定Qwen3 Dense的[tokens,hidden_size] BF16激活；不是全模型激活峰值。默认每块64MiB，准备1ms、单向有效H2D24GiB/s、消费4ms，均为教学供给，未引用硬件峰值或实测。
- 准备、H2D和消费各有一条串行通路，不同块可跨阶段重叠；同块消费必须等复制结束。主机槽从准备开始占用至DMA读完，设备槽从复制开始占用至消费结束。分别追踪槽编号和可复用时间。
- FIFO提交，使用最早释放槽。服务时间按Fraction精确递推，JSON同时保存有理数秒和浮点显示，避免把每块复制时长先舍入后累加。
- 串行与无限缓冲流水公式仅是声明独立资源的对照；有限池可能使实际调度更长。增加slot不等于链路带宽增加，未模拟共享内存带宽争用、copy-engine限制变化或调度开销。
- 准备已包含本例必需的主机复制；初次分配／锁页、pageable staging、D2H与其它工作区另计。池预留与实际同时存活峰值分列，同刻释放后复用，不把两侧池当同一设备显存。
- 不由non_blocking或Async名称推断完成／重叠；本表时序是显式依赖模型，真实API事件与并发服务条件必须另测。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
