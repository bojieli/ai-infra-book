# qwen-stream-buffer — qwen3-8b

输入：`{"block_rows": 64, "blocks": 5, "budget_bytes": 32768, "consume_interval": 2, "first_consume": 5, "first_produce": 4, "produce_interval": 1, "reorder_slots": 2}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| block_bytes | 16,384 |
| total_payload_bytes | 81,920 |
| original_fifo_peak_bytes | 49,152 |
| reorder_reserved_bytes | 32,768 |
| original_handoff_required_bytes | 81,920 |
| original_progress_fits | `false` |
| fifo_available_slots | 0 |
| original_last_take_tick | 13 |
| bounded_last_take_tick | `null` |
| bounded_fifo_peak_bytes | `null` |
| bounded_handoff_peak_bytes | `null` |
| producer_final_delay_ticks | `null` |
| consumer_final_delay_ticks | `null` |
| actual_gpu_seconds | `null` |

original：教学时间格，同格先取走再发布。

| 时间格 | 事件 | 块 | FIFO占用块数 |
| ---: | --- | ---: | ---: |
| 4 | publish | 0 | 1 |
| 5 | take | 0 | 0 |
| 5 | publish | 1 | 1 |
| 6 | publish | 2 | 2 |
| 7 | take | 1 | 1 |
| 7 | publish | 3 | 2 |
| 8 | publish | 4 | 3 |
| 9 | take | 2 | 2 |
| 11 | take | 3 | 1 |
| 13 | take | 4 | 0 |

计量条件：

- BF16块为[block_rows,官方Qwen head_dim]，默认64×128=16KiB；形状来自模型，生产／消费时间格为教学输入，不是GPU周期或实测。
- 单边同序FIFO，消费发生在时间格开始，生产在结束；同格先释放后写入，新发布块最早下一格消费。消费者取走即释放FIFO，后续消费工作区另计。
- 有限FIFO使生产发布停顿，之后的生产间隔从实际发布时刻继续；消费受数据就绪与最小消费间隔共同约束。最后取走时刻不是完整下游计算完成时间。
- 布局转换槽是与FIFO不别名的固定预留，默认双槽32KiB；没有模拟转换指令、任意重排网络或分支汇合。去掉重排槽假定接口已统一布局，不保证改布局没有其它成本。
- 预算扣除布局槽后容不下一个块时，bounded留空；本模型不实现零容量直接交接，不能据此断言所有实现均死锁。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
