# feedback-fluid-queue — 

输入：`{"after_feedback_ns": 100000, "buffer_bytes": 1048576, "capacity_bytes_per_second": 50000000000, "feedback_ns": 20000, "initial_queue_bytes": 262144, "offered_bytes_per_second": 80000000000, "reduced_bytes_per_second": 50000000000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| average_offered_bytes_per_second | 55,000,000,000.0 |
| peak_offered_bytes_per_second | 80,000,000,000 |
| arrived_exact_bytes | `"6600000"` |
| served_exact_bytes | `"6000000"` |
| excess_demand_exact_bytes | `"600000"` |
| dropped_exact_bytes | `"0"` |
| dropped_bytes | 0.0 |
| peak_queue_exact_bytes | `"862144"` |
| peak_queue_bytes | 862,144.0 |
| final_queue_exact_bytes | `"862144"` |
| final_queue_bytes | 862,144.0 |
| queue_area_exact_byte_ns | `"97457280000"` |
| mean_queue_bytes | 812,144.0 |
| compatibility_exact | `"9/10"` |
| compatibility | 0.9 |
| last_drain_exact_ns | `null` |
| stop_arrivals_final_drain_exact_ns | `"431072/25"` |
| peak_queue_virtual_wait_exact_ns | `"431072/25"` |
| actual_switch_queue_bytes | `null` |
| actual_job_completion_ns | `null` |
| feedback_applied_ns | 20,000 |
| unbounded_queue_at_feedback_exact_bytes | `"862144"` |
| bounded_queue_at_feedback_exact_bytes | `"862144"` |
| after_feedback_rate_below_capacity | `false` |

| 开始 ms | 结束 ms | 到达 GB/s | 初始队列 MB | 末尾队列 MB | 丢弃 bytes |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.000000 | 0.020000 | 80.000000 | 0.262144 | 0.862144 | 0 |
| 0.020000 | 0.120000 | 50.000000 | 0.862144 | 0.862144 | 0 |

计量条件：

- 反馈教学例：到达80GB/s、出口50GB/s，20us后明确降低到40GB/s，再观察100us；默认初始256KiB、缓冲1MiB。反馈时间与速率是输入，不是DCQCN/PFC算法生成或硬件实测。
- 观察起点积压明确给定；反馈时刻切换到给定速率，观察窗口结束后不自动重复反馈周期。
- 流体队列q=max(0,q+(arrival-capacity)*dt)，有积压时满速服务，无积压时不凭空发送。有限buffer_bytes将队列截断，多余流体字节记为丢弃；精确有理数在区间内部插入排空／填满时刻，再积分队列面积。该丢弃是流体近似，不是包级队列或拥塞控制实现。
- excess_demand是正超额速率积分，peak_queue是带排空过程的实际分析积压，二者一般不同。compatibility=1-excess/(capacity*window)，可为负，不是概率。
- 末尾排空时间假设观察结束后停止所有新输入；周期流继续时不能直接使用。peak_queue/capacity只是流体FIFO虚拟等待上界口径，不是实际请求或训练步耗时。
- 不模拟DCQCN/PFC、通信依赖或GPU反馈改变发送时刻，不将600MB教学积压写成真实交换机队列；稳定错峰还需实际漂移与反馈校准。
- 只观察一次反馈和指定后续窗口，不模拟多轮控制、ECN阈值、PFC暂停、丢弃数据重传或任务完成。减到出口速率只停止增长，不自动清空已有积压；减到出口以下才有余量排空。

固定来源：

