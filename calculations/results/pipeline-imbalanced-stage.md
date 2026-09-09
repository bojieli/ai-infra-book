# qwen-fifo-inference-pipeline — qwen3-8b

输入：`{"buffer_slots": null, "feedback_ns": 100000, "microbatches": 4, "requests_per_microbatch": 1, "stage_ns": [1000000, 2000000, 1000000, 1000000], "steps": 4, "transfer_ns": [100000, 100000, 100000]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| activation_bytes_per_boundary | 8,192 |
| total_jobs | 16 |
| reserved_boundary_pool_bytes | `null` |
| summed_sender_buffer_wait_ns | 0 |
| summed_receiver_buffer_wait_ns | 0 |
| total_processed_tokens | 16 |
| finish_ns | 35,300,000 |
| first_completion_ns | 5,300,000 |
| last_first_step_completion_ns | 11,300,000 |
| maximum_inter_step_completion_ns | 8,000,000 |
| transfer_payload_bytes | 393,216 |
| declared_boundary_buffer_peak_bytes | 40,960 |
| throughput_tokens_per_second | 453.25779036827197 |
| actual_workspace_peak_bytes | `null` |
| measured_finish_ns | `null` |

| step | 微批 | 阶段 | ready ns | start ns | end ns |
| --- | --- | --- | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 | 0 | 1000000 |
| 0 | 0 | 1 | 1100000 | 1100000 | 3100000 |
| 0 | 0 | 2 | 3200000 | 3200000 | 4200000 |
| 0 | 0 | 3 | 4300000 | 4300000 | 5300000 |
| 0 | 1 | 0 | 0 | 1000000 | 2000000 |
| 0 | 1 | 1 | 2100000 | 3100000 | 5100000 |
| 0 | 1 | 2 | 5200000 | 5200000 | 6200000 |
| 0 | 1 | 3 | 6300000 | 6300000 | 7300000 |
| 0 | 2 | 0 | 0 | 2000000 | 3000000 |
| 0 | 2 | 1 | 3100000 | 5100000 | 7100000 |
| 0 | 2 | 2 | 7200000 | 7200000 | 8200000 |
| 0 | 2 | 3 | 8300000 | 8300000 | 9300000 |
| 0 | 3 | 0 | 0 | 3000000 | 4000000 |
| 0 | 3 | 1 | 4100000 | 7100000 | 9100000 |
| 0 | 3 | 2 | 9200000 | 9200000 | 10200000 |
| 0 | 3 | 3 | 10300000 | 10300000 | 11300000 |
| 1 | 0 | 0 | 5400000 | 5400000 | 6400000 |
| 1 | 0 | 1 | 6500000 | 9100000 | 11100000 |
| 1 | 0 | 2 | 11200000 | 11200000 | 12200000 |
| 1 | 0 | 3 | 12300000 | 12300000 | 13300000 |
| 1 | 1 | 0 | 7400000 | 7400000 | 8400000 |
| 1 | 1 | 1 | 8500000 | 11100000 | 13100000 |
| 1 | 1 | 2 | 13200000 | 13200000 | 14200000 |
| 1 | 1 | 3 | 14300000 | 14300000 | 15300000 |
| 1 | 2 | 0 | 9400000 | 9400000 | 10400000 |
| 1 | 2 | 1 | 10500000 | 13100000 | 15100000 |
| 1 | 2 | 2 | 15200000 | 15200000 | 16200000 |
| 1 | 2 | 3 | 16300000 | 16300000 | 17300000 |
| 1 | 3 | 0 | 11400000 | 11400000 | 12400000 |
| 1 | 3 | 1 | 12500000 | 15100000 | 17100000 |
| 1 | 3 | 2 | 17200000 | 17200000 | 18200000 |
| 1 | 3 | 3 | 18300000 | 18300000 | 19300000 |
| 2 | 0 | 0 | 13400000 | 13400000 | 14400000 |
| 2 | 0 | 1 | 14500000 | 17100000 | 19100000 |
| 2 | 0 | 2 | 19200000 | 19200000 | 20200000 |
| 2 | 0 | 3 | 20300000 | 20300000 | 21300000 |
| 2 | 1 | 0 | 15400000 | 15400000 | 16400000 |
| 2 | 1 | 1 | 16500000 | 19100000 | 21100000 |
| 2 | 1 | 2 | 21200000 | 21200000 | 22200000 |
| 2 | 1 | 3 | 22300000 | 22300000 | 23300000 |
| 2 | 2 | 0 | 17400000 | 17400000 | 18400000 |
| 2 | 2 | 1 | 18500000 | 21100000 | 23100000 |
| 2 | 2 | 2 | 23200000 | 23200000 | 24200000 |
| 2 | 2 | 3 | 24300000 | 24300000 | 25300000 |
| 2 | 3 | 0 | 19400000 | 19400000 | 20400000 |
| 2 | 3 | 1 | 20500000 | 23100000 | 25100000 |
| 2 | 3 | 2 | 25200000 | 25200000 | 26200000 |
| 2 | 3 | 3 | 26300000 | 26300000 | 27300000 |
| 3 | 0 | 0 | 21400000 | 21400000 | 22400000 |
| 3 | 0 | 1 | 22500000 | 25100000 | 27100000 |
| 3 | 0 | 2 | 27200000 | 27200000 | 28200000 |
| 3 | 0 | 3 | 28300000 | 28300000 | 29300000 |
| 3 | 1 | 0 | 23400000 | 23400000 | 24400000 |
| 3 | 1 | 1 | 24500000 | 27100000 | 29100000 |
| 3 | 1 | 2 | 29200000 | 29200000 | 30200000 |
| 3 | 1 | 3 | 30300000 | 30300000 | 31300000 |
| 3 | 2 | 0 | 25400000 | 25400000 | 26400000 |
| 3 | 2 | 1 | 26500000 | 29100000 | 31100000 |
| 3 | 2 | 2 | 31200000 | 31200000 | 32200000 |
| 3 | 2 | 3 | 32300000 | 32300000 | 33300000 |
| 3 | 3 | 0 | 27400000 | 27400000 | 28400000 |
| 3 | 3 | 1 | 28500000 | 31100000 | 33100000 |
| 3 | 3 | 2 | 33200000 | 33200000 | 34200000 |
| 3 | 3 | 3 | 34300000 | 34300000 | 35300000 |

| 阶段 | busy ns | idle ns | 利用率 |
| --- | ---: | ---: | ---: |
| 0 | 16000000 | 19300000 | 0.453258 |
| 1 | 32000000 | 3300000 | 0.906516 |
| 2 | 16000000 | 19300000 | 0.453258 |
| 3 | 16000000 | 19300000 | 0.453258 |

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
