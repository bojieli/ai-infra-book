# checkpoint-async — qwen3-8b

输入：`{"buffer_slots": 2, "durability_delay_ns": 0, "failure_ns": 50000000000, "first_capture_ns": 20000000000, "interval_ns": 20000000000, "model": "qwen3-8b", "payload_bytes": 112000000000, "snapshots": 2, "staging_ns": 500000000, "upload_bytes_per_second": 8000000000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| official_parameters | 8,190,735,360 |
| official_14_byte_payload | 114,670,295,040 |
| payload_bytes | 112,000,000,000 |
| payload_origin | `"explicit teaching payload override"` |
| upload_service_exact_seconds | `"14"` |
| requested_payload_bytes_per_second_exact | `"5600000000"` |
| requested_upload_utilization_exact | `"7/10"` |
| requested_cadence_has_upload_slack | `true` |
| requested_cadence_has_staging_slack | `true` |
| snapshot_buffer_reserved_bytes | 224,000,000,000 |
| snapshot_buffer_live_peak_bytes | 112,000,000,000 |
| total_training_barrier_union_exact_seconds | `"1"` |
| final_durable_exact_seconds | `"109/2"` |
| completed_durable_at_failure | 1 |
| latest_recoverable_snapshot | 0 |
| recovery_capture_exact_seconds | `"20"` |
| elapsed_since_recovery_capture_exact_seconds | `"30"` |
| live_snapshot_buffers_at_failure | 1 |

以下为无故障计划；故障后的行是反事实。durable才表示本模型声明的可恢复点。

| 快照 | 槽 | 请求 s | 实际capture s | staging完成 s | upload开始 s | upload完成 s | durable s |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 20 | 20 | 41/2 | 41/2 | 69/2 | 69/2 |
| 1 | 1 | 40 | 40 | 81/2 | 81/2 | 109/2 | 109/2 |

| 训练屏障并集起点 s | 终点 s |
| --- | --- |
| 20 | 41/2 |
| 40 | 81/2 |

计量条件：

- 默认官方Qwen完整参数的BF16权重＋FP32 master/m/v共14bytes/参数；payload_bytes显式覆盖用于取整8B等教学例，不更改官方参数量。未计梯度、CPU数据状态、metadata、压缩或副本。
- 保存请求按固定墙钟到达，FIFO且不合并。训练在请求点等待槽／stage通路，再暂停staging；实际capture为staging开始，不能把延后的快照标签仍记成原请求时间。重叠暂停取区间并集，不逐请求重复相加。
- 一条staging通路、一条后台upload通路，不同快照可重叠；完整缓冲从capture持有到upload读取完成，容量不足施加背压，不丢弃请求。带宽与staging时长是有效教学输入，不是设备实测或框架默认。
- durability_delay为写完后的独立确认延迟，不占upload通路和已消费的快照槽；durable事件声明所有必需状态可恢复，实际StorageWriter语义必须另查，不把API返回或staging完成当持久化。
- failure_ns为无故障计划上的截面；之后行仅为反事实计划，不表示故障后仍写成功。同刻durable先于故障，故使用<=；无可用快照则恢复点及回退时长为null，不假定初始快照存在。
- 回退量为故障到快照capture的墙钟差，不等于丢失的训练计算、token或有效进展。没有加载时间、恢复执行、故障概率及后台争用造成的训练降速，不能据此声称完整ETTR。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
