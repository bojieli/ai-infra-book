# qwen-fifo-request-trace — qwen3-8b

输入：`{"kv_capacity_bytes": 536870912, "requests": [{"arrival_ns": 0, "decode_ns": 1000000, "output_tokens": 64, "prefill_ns": 512000, "prompt_tokens": 512}, {"arrival_ns": 500000, "decode_ns": 1000000, "output_tokens": 192, "prefill_ns": 1536000, "prompt_tokens": 1536}, {"arrival_ns": 1000000, "decode_ns": 1000000, "output_tokens": 64, "prefill_ns": 512000, "prompt_tokens": 512}, {"arrival_ns": 1500000, "decode_ns": 1000000, "output_tokens": 192, "prefill_ns": 1536000, "prompt_tokens": 1536}], "workers": 2}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| requests | 4 |
| mean_prompt_tokens | 1,024.0 |
| mean_output_tokens | 128.0 |
| p95_prompt_tokens | 1,536 |
| p95_output_tokens | 192 |
| prefill_matrix_flops | 58,452,101,562,368 |
| decode_matrix_flops | 8,097,326,170,112 |
| mean_waiting_ns | 47,009,000.0 |
| p95_waiting_ns | 125,524,000 |
| p95_ttft_ns | 127,060,000 |
| p95_latency_ns | 318,060,000 |
| finish_ns | 319,560,000 |
| kv_bytes_per_token | 147,456 |
| kv_peak_bytes | 490,733,568 |
| kv_residency_byte_ns | 102,807,927,521,280,000 |
| kv_reservation_peak_bytes | 509,313,024 |
| kv_reservation_byte_ns | 108,831,101,681,664,000 |
| complete_device_peak_bytes | `null` |

| 请求 | worker | 开始 ns | 完成 ns | 等待 ns | TTFT ns | 最后 KV bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 63512000 | 0 | 512000 | 84787200 |
| 1 | 1 | 500000 | 193036000 | 0 | 1536000 | 254656512 |
| 2 | 0 | 63512000 | 127024000 | 62512000 | 63024000 | 84787200 |
| 3 | 0 | 127024000 | 319560000 | 125524000 | 127060000 | 254656512 |
逐请求矩阵工作与完整 KV 存活时间线见 JSON。

计量条件：

- kv_capacity_bytes 仅为这些 worker 共用的逻辑 KV 预算，不含权重、激活或工作区，也不声明物理 KV 池可跨设备免费共享。有限模式在准入时预留 P+G−1 个槽直到完成；G 是本情景声明的输出上限且实际生成恰好达到它，不能把已观察未来长度当成部署时已知信息。
- 同时满足 worker 空闲和 KV 预留可放才准入。单请求超过 KV 预算直接拒绝输入，不制造永不完成的队列。预留峰值／面积与活跃峰值／面积分列；逐时刻检查活跃量不超过预留量、预留量不超过预算。
- 请求记录保留成对输入／输出长度和到达时刻；同刻按输入顺序 FIFO。每个 worker 独占处理一条请求直到完成，无连续 batching、抢占、优先级、缓存共享。可选 KV 容量采用整请求上限预留的 FIFO 准入，后来的小请求不越过队头。
- prefill_ns 与 decode_ns 为显式服务输入，默认仅教学数值，不由矩阵 FLOPs 或官方峰值预测。多个 worker 假设独立服务资源；共享设备争用需要重新校准，不代表同卡并发免费。
- 每条请求使用官方 Qwen 配置、B=1、last 输出头；prefill 产生首 token，仅执行 G−1 次 decode。历史相关注意力按首尾等差求和，MoE 使用 balanced 情景；矩阵账与输入服务耗时独立输出。
- KV 按 BF16 K/V 逻辑载荷，每请求开始即预留 P 个 prompt 槽，每次 decode 开始再预留一个槽，最后输出不再喂回。完成即释放，同刻释放可供新请求复用；这是活跃槽口径，不是分页粒度或完整显存峰值。
- p95 使用 nearest-rank ceil(0.95*n)，小样本时可能就是最大值。TTFT 从到达至首输出，latency 至最后输出；等待与服务分列。KV 面积为存活字节乘纳秒，不能当 HBM 读写流量。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
