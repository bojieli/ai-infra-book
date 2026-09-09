# checkpoint-async — qwen3-8b

输入：`{"buffer_slots": 2, "durability_delay_ns": 0, "failure_ns": 50000000000, "first_capture_ns": 20000000000, "interval_ns": 10000000000, "model": "qwen3-8b", "payload_bytes": null, "snapshots": 6, "staging_ns": 500000000, "upload_bytes_per_second": 8000000000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| official_parameters | 8,190,735,360 |
| official_14_byte_payload | 114,670,295,040 |
| payload_bytes | 114,670,295,040 |
| payload_origin | `"official full-parameter 14-byte layout"` |
| upload_service_exact_seconds | `"11198271/781250"` |
| requested_payload_bytes_per_second_exact | `"11467029504"` |
| requested_upload_utilization_exact | `"11198271/7812500"` |
| requested_cadence_has_upload_slack | `false` |
| requested_cadence_has_staging_slack | `true` |
| snapshot_buffer_reserved_bytes | 229,340,590,080 |
| snapshot_buffer_live_peak_bytes | 229,340,590,080 |
| total_training_barrier_union_exact_seconds | `"11200397/781250"` |
| final_durable_exact_seconds | `"83205251/781250"` |
| completed_durable_at_failure | 2 |
| latest_recoverable_snapshot | 1 |
| recovery_capture_exact_seconds | `"30"` |
| elapsed_since_recovery_capture_exact_seconds | `"20"` |
| live_snapshot_buffers_at_failure | 2 |

以下为无故障计划；故障后的行是反事实。durable才表示本模型声明的可恢复点。

| 快照 | 槽 | 请求 s | 实际capture s | staging完成 s | upload开始 s | upload完成 s | durable s |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 20 | 20 | 41/2 | 41/2 | 13606948/390625 | 13606948/390625 |
| 1 | 1 | 30 | 30 | 61/2 | 13606948/390625 | 38412167/781250 | 38412167/781250 |
| 2 | 0 | 40 | 40 | 81/2 | 38412167/781250 | 24805219/390625 | 24805219/390625 |
| 3 | 1 | 50 | 50 | 101/2 | 24805219/390625 | 60808709/781250 | 60808709/781250 |
| 4 | 0 | 60 | 24805219/390625 | 50001063/781250 | 60808709/781250 | 7200698/78125 | 7200698/78125 |
| 5 | 1 | 70 | 60808709/781250 | 30599667/390625 | 7200698/78125 | 83205251/781250 | 83205251/781250 |

| 训练屏障并集起点 s | 终点 s |
| --- | --- |
| 20 | 41/2 |
| 30 | 61/2 |
| 40 | 81/2 |
| 50 | 101/2 |
| 60 | 50001063/781250 |
| 70 | 30599667/390625 |

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
