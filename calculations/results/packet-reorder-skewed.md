# packet-reorder — 

输入：`{"lost_packets": [], "model": "qwen3-8b", "packet_bytes": 1024, "path_bytes_per_second": 1000000000, "path_delays_ns": [1000, 9000], "recovery_delay_ns": 20000, "tokens": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| payload_bytes | 8,192 |
| packet_count | 8 |
| retransmitted_bytes | 0 |
| sent_bytes | 8,192 |
| received_bytes | 8,192 |
| declared_lost_bytes | 0 |
| suffix_replay_counterfactual_bytes | 0 |
| peak_retained_reorder_bytes | 3,072 |
| peak_retained_packets | 3 |
| reorder_area_exact_byte_ns | `"21430272"` |
| first_ordered_delivery_exact_ns | `"2024"` |
| completion_exact_ns | `"13096"` |

| 到达 ns（精确） | 到达序号 | 释放序号 | 保留 bytes |
| ---: | --- | --- | ---: |
| 2024 | [0] | [0] | 0 |
| 3048 | [2] | [] | 1024 |
| 4072 | [4] | [] | 2048 |
| 5096 | [6] | [] | 3072 |
| 10024 | [1] | [1, 2] | 2048 |
| 11048 | [3] | [3, 4] | 1024 |
| 12072 | [5] | [5, 6] | 0 |
| 13096 | [7] | [7] | 0 |

计量条件：

- 官方模型hidden_size确定单个BF16 [tokens,H]载荷；报文大小、独立路径速率和延迟均为教学输入，不是网卡规格。只算payload，不含头部、ACK、编码或物理多跳流量。
- 按序号轮转路径，各路径独立串行发送，原始报文优先于重传。显式声明原始丢包；在其发送结束后给定recovery_delay_ns进入重传队列，每包仅重传一次且成功。此延迟不是由ACK或超时协议推导，不模拟虚假重传。
- 接收端无限乱序缓冲，每个同刻事件先合并到达，再释放连续前缀。保留峰值不含入口暂存；乱序payload容量与协议SRAM状态、位图、描述符大小不同。
- suffix_replay_counterfactual_bytes仅为从最早丢失序号到消息末尾重发一遍的字节对照，不模拟Go-Back-N时序或宣称实际协议会这样重传。
- 完成时间是该消息全部按序交付时刻；没有随机分布、拥塞控制、有限窗口、接收缓冲溢出或OpenURMA版本行为校准。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
