# qwen-fifo-inference-pipeline — qwen3-8b

输入：`{"buffer_slots": 1, "feedback_ns": 100000, "microbatches": 4, "requests_per_microbatch": 1, "stage_ns": [1000000, 1000000, 1000000, 1000000], "steps": 4, "transfer_ns": [2000000, 2000000, 2000000]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| activation_bytes_per_boundary | 8,192 |
| total_jobs | 16 |
| reserved_boundary_pool_bytes | 49,152 |
| summed_sender_buffer_wait_ns | 28,800,000 |
| summed_receiver_buffer_wait_ns | 0 |
| total_processed_tokens | 16 |
| finish_ns | 55,000,000 |
| first_completion_ns | 10,000,000 |
| last_first_step_completion_ns | 19,000,000 |
| maximum_inter_step_completion_ns | 12,000,000 |
| transfer_payload_bytes | 393,216 |
| declared_boundary_buffer_peak_bytes | 49,152 |
| throughput_tokens_per_second | 290.90909090909093 |
| actual_workspace_peak_bytes | `null` |
| measured_finish_ns | `null` |

| step | 微批 | 阶段 | ready ns | start ns | end ns |
| --- | --- | --- | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 | 0 | 1000000 |
| 0 | 0 | 1 | 3000000 | 3000000 | 4000000 |
| 0 | 0 | 2 | 6000000 | 6000000 | 7000000 |
| 0 | 0 | 3 | 9000000 | 9000000 | 10000000 |
| 0 | 1 | 0 | 0 | 3000000 | 4000000 |
| 0 | 1 | 1 | 6000000 | 6000000 | 7000000 |
| 0 | 1 | 2 | 9000000 | 9000000 | 10000000 |
| 0 | 1 | 3 | 12000000 | 12000000 | 13000000 |
| 0 | 2 | 0 | 0 | 6000000 | 7000000 |
| 0 | 2 | 1 | 9000000 | 9000000 | 10000000 |
| 0 | 2 | 2 | 12000000 | 12000000 | 13000000 |
| 0 | 2 | 3 | 15000000 | 15000000 | 16000000 |
| 0 | 3 | 0 | 0 | 9000000 | 10000000 |
| 0 | 3 | 1 | 12000000 | 12000000 | 13000000 |
| 0 | 3 | 2 | 15000000 | 15000000 | 16000000 |
| 0 | 3 | 3 | 18000000 | 18000000 | 19000000 |
| 1 | 0 | 0 | 10100000 | 12000000 | 13000000 |
| 1 | 0 | 1 | 15000000 | 15000000 | 16000000 |
| 1 | 0 | 2 | 18000000 | 18000000 | 19000000 |
| 1 | 0 | 3 | 21000000 | 21000000 | 22000000 |
| 1 | 1 | 0 | 13100000 | 15000000 | 16000000 |
| 1 | 1 | 1 | 18000000 | 18000000 | 19000000 |
| 1 | 1 | 2 | 21000000 | 21000000 | 22000000 |
| 1 | 1 | 3 | 24000000 | 24000000 | 25000000 |
| 1 | 2 | 0 | 16100000 | 18000000 | 19000000 |
| 1 | 2 | 1 | 21000000 | 21000000 | 22000000 |
| 1 | 2 | 2 | 24000000 | 24000000 | 25000000 |
| 1 | 2 | 3 | 27000000 | 27000000 | 28000000 |
| 1 | 3 | 0 | 19100000 | 21000000 | 22000000 |
| 1 | 3 | 1 | 24000000 | 24000000 | 25000000 |
| 1 | 3 | 2 | 27000000 | 27000000 | 28000000 |
| 1 | 3 | 3 | 30000000 | 30000000 | 31000000 |
| 2 | 0 | 0 | 22100000 | 24000000 | 25000000 |
| 2 | 0 | 1 | 27000000 | 27000000 | 28000000 |
| 2 | 0 | 2 | 30000000 | 30000000 | 31000000 |
| 2 | 0 | 3 | 33000000 | 33000000 | 34000000 |
| 2 | 1 | 0 | 25100000 | 27000000 | 28000000 |
| 2 | 1 | 1 | 30000000 | 30000000 | 31000000 |
| 2 | 1 | 2 | 33000000 | 33000000 | 34000000 |
| 2 | 1 | 3 | 36000000 | 36000000 | 37000000 |
| 2 | 2 | 0 | 28100000 | 30000000 | 31000000 |
| 2 | 2 | 1 | 33000000 | 33000000 | 34000000 |
| 2 | 2 | 2 | 36000000 | 36000000 | 37000000 |
| 2 | 2 | 3 | 39000000 | 39000000 | 40000000 |
| 2 | 3 | 0 | 31100000 | 33000000 | 34000000 |
| 2 | 3 | 1 | 36000000 | 36000000 | 37000000 |
| 2 | 3 | 2 | 39000000 | 39000000 | 40000000 |
| 2 | 3 | 3 | 42000000 | 42000000 | 43000000 |
| 3 | 0 | 0 | 34100000 | 36000000 | 37000000 |
| 3 | 0 | 1 | 39000000 | 39000000 | 40000000 |
| 3 | 0 | 2 | 42000000 | 42000000 | 43000000 |
| 3 | 0 | 3 | 45000000 | 45000000 | 46000000 |
| 3 | 1 | 0 | 37100000 | 39000000 | 40000000 |
| 3 | 1 | 1 | 42000000 | 42000000 | 43000000 |
| 3 | 1 | 2 | 45000000 | 45000000 | 46000000 |
| 3 | 1 | 3 | 48000000 | 48000000 | 49000000 |
| 3 | 2 | 0 | 40100000 | 42000000 | 43000000 |
| 3 | 2 | 1 | 45000000 | 45000000 | 46000000 |
| 3 | 2 | 2 | 48000000 | 48000000 | 49000000 |
| 3 | 2 | 3 | 51000000 | 51000000 | 52000000 |
| 3 | 3 | 0 | 43100000 | 45000000 | 46000000 |
| 3 | 3 | 1 | 48000000 | 48000000 | 49000000 |
| 3 | 3 | 2 | 51000000 | 51000000 | 52000000 |
| 3 | 3 | 3 | 54000000 | 54000000 | 55000000 |

| 阶段 | busy ns | idle ns | 利用率 |
| --- | ---: | ---: | ---: |
| 0 | 16000000 | 39000000 | 0.290909 |
| 1 | 16000000 | 39000000 | 0.290909 |
| 2 | 16000000 | 39000000 | 0.290909 |
| 3 | 16000000 | 39000000 | 0.290909 |

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
