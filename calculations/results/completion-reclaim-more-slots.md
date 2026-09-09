# completion-reclaim — 

输入：`{"completion_entry_bytes": 64, "model": "qwen3-8b", "operations": 16, "poll_batch": 4, "poll_interval_ns": 20000, "slots": 16, "submit_interval_ns": 1000, "tokens": 1, "transfer_latency_ns": 5000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| payload_bytes_per_operation | 8,192 |
| total_payload_bytes | 131,072 |
| reserved_slot_payload_bytes | 131,072 |
| peak_outstanding | 16 |
| peak_in_flight | 5 |
| peak_unconsumed_completions | 15 |
| peak_retained_completion_bytes | 960 |
| last_submit_ns | 15,000 |
| all_transfers_complete_ns | 20,000 |
| all_slots_reclaimed_ns | 80,000 |
| total_submission_delay_ns | 0 |
| total_reclaim_wait_ns | 600,000 |
| max_submission_delay_ns | 0 |

| 操作 | 槽位 | 提交 ns | 传输完成 ns | 消费回收 ns |
| --- | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 5000 | 20000 |
| 1 | 1 | 1000 | 6000 | 20000 |
| 2 | 2 | 2000 | 7000 | 20000 |
| 3 | 3 | 3000 | 8000 | 20000 |
| 4 | 4 | 4000 | 9000 | 40000 |
| 5 | 5 | 5000 | 10000 | 40000 |
| 6 | 6 | 6000 | 11000 | 40000 |
| 7 | 7 | 7000 | 12000 | 40000 |
| 8 | 8 | 8000 | 13000 | 60000 |
| 9 | 9 | 9000 | 14000 | 60000 |
| 10 | 10 | 10000 | 15000 | 60000 |
| 11 | 11 | 11000 | 16000 | 60000 |
| 12 | 12 | 12000 | 17000 | 80000 |
| 13 | 13 | 13000 | 18000 | 80000 |
| 14 | 14 | 14000 | 19000 | 80000 |
| 15 | 15 | 15000 | 20000 | 80000 |

计量条件：

- 每操作载荷为官方BF16 [tokens,H]；间隔、固定传输延迟、轮询周期、每次消费条数及64-byte完成项均为教学输入，不是NIC/QP规格或测量。
- 本模型一个credit同时覆盖提交后在途与已完成未消费阶段，消费完成项后才回收。不是所有真实队列都采用此生命周期；传输完成不代表本例槽位可复用。固定延迟使完成顺序等于提交顺序。
- 最早在poll_interval_ns时轮询，之后固定周期，每次至多poll_batch条，FIFO消费。传输在同刻完成可先被轮询消费，再用释放槽位提交；半开区间峰值不包含同刻入口瞬态。
- 轮询消费本身视为瞬时，每次条数限制表示给定服务预算；提交有最小间隔。各操作传输可并行，不另建共享带宽、CQ独立容量、丢弃、地址转换或异常恢复。
- slots*payload是预留缓冲预算；完成项为独立元数据，不与payload混淆。各操作等待之和是操作时间积分，不能相加到墙钟；传输完毕和全部回收时刻分列。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
