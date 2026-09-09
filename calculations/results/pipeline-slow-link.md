# qwen-fifo-inference-pipeline — qwen3-8b

输入：`{"buffer_slots": null, "feedback_ns": 100000, "microbatches": 4, "requests_per_microbatch": 1, "stage_ns": [1000000, 1000000, 1000000, 1000000], "steps": 4, "transfer_ns": [2000000, 2000000, 2000000]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| activation_bytes_per_boundary | 8,192 |
| total_jobs | 16 |
| reserved_boundary_pool_bytes | `null` |
| summed_sender_buffer_wait_ns | 0 |
| summed_receiver_buffer_wait_ns | 0 |
| total_processed_tokens | 16 |
| finish_ns | 46,300,000 |
| first_completion_ns | 10,000,000 |
| last_first_step_completion_ns | 16,000,000 |
| maximum_inter_step_completion_ns | 10,100,000 |
| transfer_payload_bytes | 393,216 |
| declared_boundary_buffer_peak_bytes | 57,344 |
| throughput_tokens_per_second | 345.5723542116631 |
| actual_workspace_peak_bytes | `null` |
| measured_finish_ns | `null` |

| step | 微批 | 阶段 | ready ns | start ns | end ns |
| --- | --- | --- | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 | 0 | 1000000 |
| 0 | 0 | 1 | 3000000 | 3000000 | 4000000 |
| 0 | 0 | 2 | 6000000 | 6000000 | 7000000 |
| 0 | 0 | 3 | 9000000 | 9000000 | 10000000 |
| 0 | 1 | 0 | 0 | 1000000 | 2000000 |
| 0 | 1 | 1 | 5000000 | 5000000 | 6000000 |
| 0 | 1 | 2 | 8000000 | 8000000 | 9000000 |
| 0 | 1 | 3 | 11000000 | 11000000 | 12000000 |
| 0 | 2 | 0 | 0 | 2000000 | 3000000 |
| 0 | 2 | 1 | 7000000 | 7000000 | 8000000 |
| 0 | 2 | 2 | 10000000 | 10000000 | 11000000 |
| 0 | 2 | 3 | 13000000 | 13000000 | 14000000 |
| 0 | 3 | 0 | 0 | 3000000 | 4000000 |
| 0 | 3 | 1 | 9000000 | 9000000 | 10000000 |
| 0 | 3 | 2 | 12000000 | 12000000 | 13000000 |
| 0 | 3 | 3 | 15000000 | 15000000 | 16000000 |
| 1 | 0 | 0 | 10100000 | 10100000 | 11100000 |
| 1 | 0 | 1 | 13100000 | 13100000 | 14100000 |
| 1 | 0 | 2 | 16100000 | 16100000 | 17100000 |
| 1 | 0 | 3 | 19100000 | 19100000 | 20100000 |
| 1 | 1 | 0 | 12100000 | 12100000 | 13100000 |
| 1 | 1 | 1 | 15100000 | 15100000 | 16100000 |
| 1 | 1 | 2 | 18100000 | 18100000 | 19100000 |
| 1 | 1 | 3 | 21100000 | 21100000 | 22100000 |
| 1 | 2 | 0 | 14100000 | 14100000 | 15100000 |
| 1 | 2 | 1 | 17100000 | 17100000 | 18100000 |
| 1 | 2 | 2 | 20100000 | 20100000 | 21100000 |
| 1 | 2 | 3 | 23100000 | 23100000 | 24100000 |
| 1 | 3 | 0 | 16100000 | 16100000 | 17100000 |
| 1 | 3 | 1 | 19100000 | 19100000 | 20100000 |
| 1 | 3 | 2 | 22100000 | 22100000 | 23100000 |
| 1 | 3 | 3 | 25100000 | 25100000 | 26100000 |
| 2 | 0 | 0 | 20200000 | 20200000 | 21200000 |
| 2 | 0 | 1 | 23200000 | 23200000 | 24200000 |
| 2 | 0 | 2 | 26200000 | 26200000 | 27200000 |
| 2 | 0 | 3 | 29200000 | 29200000 | 30200000 |
| 2 | 1 | 0 | 22200000 | 22200000 | 23200000 |
| 2 | 1 | 1 | 25200000 | 25200000 | 26200000 |
| 2 | 1 | 2 | 28200000 | 28200000 | 29200000 |
| 2 | 1 | 3 | 31200000 | 31200000 | 32200000 |
| 2 | 2 | 0 | 24200000 | 24200000 | 25200000 |
| 2 | 2 | 1 | 27200000 | 27200000 | 28200000 |
| 2 | 2 | 2 | 30200000 | 30200000 | 31200000 |
| 2 | 2 | 3 | 33200000 | 33200000 | 34200000 |
| 2 | 3 | 0 | 26200000 | 26200000 | 27200000 |
| 2 | 3 | 1 | 29200000 | 29200000 | 30200000 |
| 2 | 3 | 2 | 32200000 | 32200000 | 33200000 |
| 2 | 3 | 3 | 35200000 | 35200000 | 36200000 |
| 3 | 0 | 0 | 30300000 | 30300000 | 31300000 |
| 3 | 0 | 1 | 33300000 | 33300000 | 34300000 |
| 3 | 0 | 2 | 36300000 | 36300000 | 37300000 |
| 3 | 0 | 3 | 39300000 | 39300000 | 40300000 |
| 3 | 1 | 0 | 32300000 | 32300000 | 33300000 |
| 3 | 1 | 1 | 35300000 | 35300000 | 36300000 |
| 3 | 1 | 2 | 38300000 | 38300000 | 39300000 |
| 3 | 1 | 3 | 41300000 | 41300000 | 42300000 |
| 3 | 2 | 0 | 34300000 | 34300000 | 35300000 |
| 3 | 2 | 1 | 37300000 | 37300000 | 38300000 |
| 3 | 2 | 2 | 40300000 | 40300000 | 41300000 |
| 3 | 2 | 3 | 43300000 | 43300000 | 44300000 |
| 3 | 3 | 0 | 36300000 | 36300000 | 37300000 |
| 3 | 3 | 1 | 39300000 | 39300000 | 40300000 |
| 3 | 3 | 2 | 42300000 | 42300000 | 43300000 |
| 3 | 3 | 3 | 45300000 | 45300000 | 46300000 |

| 阶段 | busy ns | idle ns | 利用率 |
| --- | ---: | ---: | ---: |
| 0 | 16000000 | 30300000 | 0.345572 |
| 1 | 16000000 | 30300000 | 0.345572 |
| 2 | 16000000 | 30300000 | 0.345572 |
| 3 | 16000000 | 30300000 | 0.345572 |

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
