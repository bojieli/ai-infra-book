# qwen-persistent-tasks — qwen3-8b

输入：`{"activation_elements_per_second": 20000000000, "event_publish_ns": 200, "host_launch_ns": 5000, "matrix_flops_per_second": 200000000000000, "task_dispatch_ns": 500, "tile_rows": 512, "tokens": 512}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| tiles | 1 |
| matrix_flops | 51,539,607,552 |
| activation_elements | 6,291,456 |
| coarse_host_launches | 2 |
| persistent_host_launches | 1 |
| persistent_device_tasks | 2 |
| completion_event_publications | 2 |
| intertask_dependency_edges | 1 |
| event_poll_iterations | `null` |
| task_dispatch_total_ns | 1,000 |
| event_publish_total_ns | 400 |
| intermediate_total_bytes | 12,582,912 |
| intermediate_write_read_bytes | 25,165,824 |
| persistent_intermediate_live_peak_bytes | 12,582,912 |
| barrier_finish_exact_ns | `"1819596368/3125"` |
| barrier_finish_ns | 582,270.83776 |
| persistent_finish_exact_ns | `"1808346368/3125"` |
| persistent_finish_ns | 578,670.83776 |
| hypothetical_speedup | 1.006221153313921 |
| actual_gpu_seconds | `null` |

| 块 | 行数 | 生产开始 us | 数据就绪 us | 消费开始 us | 消费完成 us |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 512 | 5.000000 | 263.398038 | 263.398038 | 578.670838 |

计量条件：

- 官方Qwen Dense单支up投影[M,H]×[H,F]接SiLU，按行切块无跨块归约；不是完整FFN，也不把down投影所需全K依赖忽略。SiLU按元素服务率输入，不将其冒充矩阵FLOPs。
- 生产为一条串行矩阵worker，消费为一条串行向量worker，声明资源独立且可并行。默认200TFLOP/s、20G元素/s、host launch5us、设备任务分派0.5us和完成事件发布0.2us均为教学输入，未借用官方峰值或MPK实测。
- 粗粒度两次主机launch，完整生产结束才启动消费；persistent一次launch，每块两个设备任务、各一次完成事件发布和一条生产到消费依赖。等待由ready时间满足，轮询次数、原子争用和事件表字节未假造。
- 每任务分派及事件发布占用其worker，与同worker后续工作串行；不同worker可重叠，因此元数据总服务量不直接全部加到关键路径。尾块按实际行数重新算工作，但仍各支付一次固定任务开销。
- 中间块从生产任务开始保留至消费完成，报告实际同时存活上界；本表未施加有限槽预算，不保证某个片上池可容纳。没有消除中间张量读写，输入／最终输出／权重／队列及库scratch另算。
- 实际GPU若矩阵／向量争用同一SM、带宽或寄存器，必须另给并发服务率及可驻留证据。单次主机提交不等于只做一次设备工作，本模型不声称实现了MPK。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
