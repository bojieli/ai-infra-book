# qwen-fifo-inference-pipeline — qwen3-8b

输入：`{"buffer_slots": null, "feedback_ns": 100000, "microbatches": 1, "requests_per_microbatch": 1, "stage_ns": [1000000, 1000000, 1000000, 1000000], "steps": 4, "transfer_ns": [100000, 100000, 100000]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| activation_bytes_per_boundary | 8,192 |
| total_jobs | 4 |
| reserved_boundary_pool_bytes | `null` |
| summed_sender_buffer_wait_ns | 0 |
| summed_receiver_buffer_wait_ns | 0 |
| total_processed_tokens | 4 |
| finish_ns | 17,500,000 |
| first_completion_ns | 4,300,000 |
| last_first_step_completion_ns | 4,300,000 |
| maximum_inter_step_completion_ns | 4,400,000 |
| transfer_payload_bytes | 98,304 |
| declared_boundary_buffer_peak_bytes | 16,384 |
| throughput_tokens_per_second | 228.57142857142858 |
| actual_workspace_peak_bytes | `null` |
| measured_finish_ns | `null` |

| step | 微批 | 阶段 | ready ns | start ns | end ns |
| --- | --- | --- | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 | 0 | 1000000 |
| 0 | 0 | 1 | 1100000 | 1100000 | 2100000 |
| 0 | 0 | 2 | 2200000 | 2200000 | 3200000 |
| 0 | 0 | 3 | 3300000 | 3300000 | 4300000 |
| 1 | 0 | 0 | 4400000 | 4400000 | 5400000 |
| 1 | 0 | 1 | 5500000 | 5500000 | 6500000 |
| 1 | 0 | 2 | 6600000 | 6600000 | 7600000 |
| 1 | 0 | 3 | 7700000 | 7700000 | 8700000 |
| 2 | 0 | 0 | 8800000 | 8800000 | 9800000 |
| 2 | 0 | 1 | 9900000 | 9900000 | 10900000 |
| 2 | 0 | 2 | 11000000 | 11000000 | 12000000 |
| 2 | 0 | 3 | 12100000 | 12100000 | 13100000 |
| 3 | 0 | 0 | 13200000 | 13200000 | 14200000 |
| 3 | 0 | 1 | 14300000 | 14300000 | 15300000 |
| 3 | 0 | 2 | 15400000 | 15400000 | 16400000 |
| 3 | 0 | 3 | 16500000 | 16500000 | 17500000 |

| 阶段 | busy ns | idle ns | 利用率 |
| --- | ---: | ---: | ---: |
| 0 | 4000000 | 13500000 | 0.228571 |
| 1 | 4000000 | 13500000 | 0.228571 |
| 2 | 4000000 | 13500000 | 0.228571 |
| 3 | 4000000 | 13500000 | 0.228571 |

传输起止、微批完成序列及双端边界缓冲见 JSON；未将边界缓冲当作完整工作区。

计量条件：

- Each microbatch is a persistent group of requests; each step appends one token per request. All groups are initially ready. This excludes prompt prefill and does not label first completion as real TTFT.
- Durations are explicit teaching or imported observations, not inferred from FLOPs or hardware peak. Stages and boundary links are independent serial resources; compute and transfers may overlap.
- The fixed FIFO job order is step-major then microbatch index, identical at every stage/link. A group next step waits for its previous final-stage completion plus feedback lag. This is a specified policy, not an optimal/work-conserving scheduler claim.
- Feedback is a per-group readiness lag with no shared feedback resource. It can represent assumed sampling/return delay but does not count their traffic or contention.
- Hidden activations are BF16 [requests_per_microbatch,H] using official Qwen width. This models TP=1 pipeline boundaries; TP replication/sharding needs separate mapping.
- With unlimited buffers, sender lifetime starts at production. With finite slots, output storage is conservatively reserved before producer compute and held through transfer completion. Receiver allocation starts at transfer start and ends after consumer compute; copies are separate.
- buffer_slots=None preserves the unlimited-queue baseline. Finite slots constrain each boundary sender and receiver pool separately; earliest-free slots are reused only after recorded release. Producer or transfer waits when no slot is available. This reservation policy is explicit, not a claim of optimal overlap.
- Reserved pool bytes differ from live bytes. Both exclude input/output, intra-stage activations, weights, KV, allocator alignment and scratch. Summed local buffer waits may overlap and must not be added again to makespan.
- Stage idle time over the observed horizon includes fill/drain, feedback, imbalance and link stalls. It cannot all be called a single pipeline bubble percentage or applied to training schedules.

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
