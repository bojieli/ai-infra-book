# qwen-fifo-inference-pipeline — qwen3-8b

输入：`{"buffer_slots": null, "feedback_ns": 100000, "microbatches": 8, "requests_per_microbatch": 1, "stage_ns": [1000000, 1000000, 1000000, 1000000], "steps": 4, "transfer_ns": [100000, 100000, 100000]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| activation_bytes_per_boundary | 8,192 |
| total_jobs | 32 |
| reserved_boundary_pool_bytes | `null` |
| summed_sender_buffer_wait_ns | 0 |
| summed_receiver_buffer_wait_ns | 0 |
| total_processed_tokens | 32 |
| finish_ns | 35,300,000 |
| first_completion_ns | 4,300,000 |
| last_first_step_completion_ns | 11,300,000 |
| maximum_inter_step_completion_ns | 8,000,000 |
| transfer_payload_bytes | 786,432 |
| declared_boundary_buffer_peak_bytes | 40,960 |
| throughput_tokens_per_second | 906.5155807365439 |
| actual_workspace_peak_bytes | `null` |
| measured_finish_ns | `null` |

| step | 微批 | 阶段 | ready ns | start ns | end ns |
| --- | --- | --- | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 | 0 | 1000000 |
| 0 | 0 | 1 | 1100000 | 1100000 | 2100000 |
| 0 | 0 | 2 | 2200000 | 2200000 | 3200000 |
| 0 | 0 | 3 | 3300000 | 3300000 | 4300000 |
| 0 | 1 | 0 | 0 | 1000000 | 2000000 |
| 0 | 1 | 1 | 2100000 | 2100000 | 3100000 |
| 0 | 1 | 2 | 3200000 | 3200000 | 4200000 |
| 0 | 1 | 3 | 4300000 | 4300000 | 5300000 |
| 0 | 2 | 0 | 0 | 2000000 | 3000000 |
| 0 | 2 | 1 | 3100000 | 3100000 | 4100000 |
| 0 | 2 | 2 | 4200000 | 4200000 | 5200000 |
| 0 | 2 | 3 | 5300000 | 5300000 | 6300000 |
| 0 | 3 | 0 | 0 | 3000000 | 4000000 |
| 0 | 3 | 1 | 4100000 | 4100000 | 5100000 |
| 0 | 3 | 2 | 5200000 | 5200000 | 6200000 |
| 0 | 3 | 3 | 6300000 | 6300000 | 7300000 |
| 0 | 4 | 0 | 0 | 4000000 | 5000000 |
| 0 | 4 | 1 | 5100000 | 5100000 | 6100000 |
| 0 | 4 | 2 | 6200000 | 6200000 | 7200000 |
| 0 | 4 | 3 | 7300000 | 7300000 | 8300000 |
| 0 | 5 | 0 | 0 | 5000000 | 6000000 |
| 0 | 5 | 1 | 6100000 | 6100000 | 7100000 |
| 0 | 5 | 2 | 7200000 | 7200000 | 8200000 |
| 0 | 5 | 3 | 8300000 | 8300000 | 9300000 |
| 0 | 6 | 0 | 0 | 6000000 | 7000000 |
| 0 | 6 | 1 | 7100000 | 7100000 | 8100000 |
| 0 | 6 | 2 | 8200000 | 8200000 | 9200000 |
| 0 | 6 | 3 | 9300000 | 9300000 | 10300000 |
| 0 | 7 | 0 | 0 | 7000000 | 8000000 |
| 0 | 7 | 1 | 8100000 | 8100000 | 9100000 |
| 0 | 7 | 2 | 9200000 | 9200000 | 10200000 |
| 0 | 7 | 3 | 10300000 | 10300000 | 11300000 |
| 1 | 0 | 0 | 4400000 | 8000000 | 9000000 |
| 1 | 0 | 1 | 9100000 | 9100000 | 10100000 |
| 1 | 0 | 2 | 10200000 | 10200000 | 11200000 |
| 1 | 0 | 3 | 11300000 | 11300000 | 12300000 |
| 1 | 1 | 0 | 5400000 | 9000000 | 10000000 |
| 1 | 1 | 1 | 10100000 | 10100000 | 11100000 |
| 1 | 1 | 2 | 11200000 | 11200000 | 12200000 |
| 1 | 1 | 3 | 12300000 | 12300000 | 13300000 |
| 1 | 2 | 0 | 6400000 | 10000000 | 11000000 |
| 1 | 2 | 1 | 11100000 | 11100000 | 12100000 |
| 1 | 2 | 2 | 12200000 | 12200000 | 13200000 |
| 1 | 2 | 3 | 13300000 | 13300000 | 14300000 |
| 1 | 3 | 0 | 7400000 | 11000000 | 12000000 |
| 1 | 3 | 1 | 12100000 | 12100000 | 13100000 |
| 1 | 3 | 2 | 13200000 | 13200000 | 14200000 |
| 1 | 3 | 3 | 14300000 | 14300000 | 15300000 |
| 1 | 4 | 0 | 8400000 | 12000000 | 13000000 |
| 1 | 4 | 1 | 13100000 | 13100000 | 14100000 |
| 1 | 4 | 2 | 14200000 | 14200000 | 15200000 |
| 1 | 4 | 3 | 15300000 | 15300000 | 16300000 |
| 1 | 5 | 0 | 9400000 | 13000000 | 14000000 |
| 1 | 5 | 1 | 14100000 | 14100000 | 15100000 |
| 1 | 5 | 2 | 15200000 | 15200000 | 16200000 |
| 1 | 5 | 3 | 16300000 | 16300000 | 17300000 |
| 1 | 6 | 0 | 10400000 | 14000000 | 15000000 |
| 1 | 6 | 1 | 15100000 | 15100000 | 16100000 |
| 1 | 6 | 2 | 16200000 | 16200000 | 17200000 |
| 1 | 6 | 3 | 17300000 | 17300000 | 18300000 |
| 1 | 7 | 0 | 11400000 | 15000000 | 16000000 |
| 1 | 7 | 1 | 16100000 | 16100000 | 17100000 |
| 1 | 7 | 2 | 17200000 | 17200000 | 18200000 |
| 1 | 7 | 3 | 18300000 | 18300000 | 19300000 |
| 2 | 0 | 0 | 12400000 | 16000000 | 17000000 |
| 2 | 0 | 1 | 17100000 | 17100000 | 18100000 |
| 2 | 0 | 2 | 18200000 | 18200000 | 19200000 |
| 2 | 0 | 3 | 19300000 | 19300000 | 20300000 |
| 2 | 1 | 0 | 13400000 | 17000000 | 18000000 |
| 2 | 1 | 1 | 18100000 | 18100000 | 19100000 |
| 2 | 1 | 2 | 19200000 | 19200000 | 20200000 |
| 2 | 1 | 3 | 20300000 | 20300000 | 21300000 |
| 2 | 2 | 0 | 14400000 | 18000000 | 19000000 |
| 2 | 2 | 1 | 19100000 | 19100000 | 20100000 |
| 2 | 2 | 2 | 20200000 | 20200000 | 21200000 |
| 2 | 2 | 3 | 21300000 | 21300000 | 22300000 |
| 2 | 3 | 0 | 15400000 | 19000000 | 20000000 |
| 2 | 3 | 1 | 20100000 | 20100000 | 21100000 |
| 2 | 3 | 2 | 21200000 | 21200000 | 22200000 |
| 2 | 3 | 3 | 22300000 | 22300000 | 23300000 |
| 2 | 4 | 0 | 16400000 | 20000000 | 21000000 |
| 2 | 4 | 1 | 21100000 | 21100000 | 22100000 |
| 2 | 4 | 2 | 22200000 | 22200000 | 23200000 |
| 2 | 4 | 3 | 23300000 | 23300000 | 24300000 |
| 2 | 5 | 0 | 17400000 | 21000000 | 22000000 |
| 2 | 5 | 1 | 22100000 | 22100000 | 23100000 |
| 2 | 5 | 2 | 23200000 | 23200000 | 24200000 |
| 2 | 5 | 3 | 24300000 | 24300000 | 25300000 |
| 2 | 6 | 0 | 18400000 | 22000000 | 23000000 |
| 2 | 6 | 1 | 23100000 | 23100000 | 24100000 |
| 2 | 6 | 2 | 24200000 | 24200000 | 25200000 |
| 2 | 6 | 3 | 25300000 | 25300000 | 26300000 |
| 2 | 7 | 0 | 19400000 | 23000000 | 24000000 |
| 2 | 7 | 1 | 24100000 | 24100000 | 25100000 |
| 2 | 7 | 2 | 25200000 | 25200000 | 26200000 |
| 2 | 7 | 3 | 26300000 | 26300000 | 27300000 |
| 3 | 0 | 0 | 20400000 | 24000000 | 25000000 |
| 3 | 0 | 1 | 25100000 | 25100000 | 26100000 |
| 3 | 0 | 2 | 26200000 | 26200000 | 27200000 |
| 3 | 0 | 3 | 27300000 | 27300000 | 28300000 |
| 3 | 1 | 0 | 21400000 | 25000000 | 26000000 |
| 3 | 1 | 1 | 26100000 | 26100000 | 27100000 |
| 3 | 1 | 2 | 27200000 | 27200000 | 28200000 |
| 3 | 1 | 3 | 28300000 | 28300000 | 29300000 |
| 3 | 2 | 0 | 22400000 | 26000000 | 27000000 |
| 3 | 2 | 1 | 27100000 | 27100000 | 28100000 |
| 3 | 2 | 2 | 28200000 | 28200000 | 29200000 |
| 3 | 2 | 3 | 29300000 | 29300000 | 30300000 |
| 3 | 3 | 0 | 23400000 | 27000000 | 28000000 |
| 3 | 3 | 1 | 28100000 | 28100000 | 29100000 |
| 3 | 3 | 2 | 29200000 | 29200000 | 30200000 |
| 3 | 3 | 3 | 30300000 | 30300000 | 31300000 |
| 3 | 4 | 0 | 24400000 | 28000000 | 29000000 |
| 3 | 4 | 1 | 29100000 | 29100000 | 30100000 |
| 3 | 4 | 2 | 30200000 | 30200000 | 31200000 |
| 3 | 4 | 3 | 31300000 | 31300000 | 32300000 |
| 3 | 5 | 0 | 25400000 | 29000000 | 30000000 |
| 3 | 5 | 1 | 30100000 | 30100000 | 31100000 |
| 3 | 5 | 2 | 31200000 | 31200000 | 32200000 |
| 3 | 5 | 3 | 32300000 | 32300000 | 33300000 |
| 3 | 6 | 0 | 26400000 | 30000000 | 31000000 |
| 3 | 6 | 1 | 31100000 | 31100000 | 32100000 |
| 3 | 6 | 2 | 32200000 | 32200000 | 33200000 |
| 3 | 6 | 3 | 33300000 | 33300000 | 34300000 |
| 3 | 7 | 0 | 27400000 | 31000000 | 32000000 |
| 3 | 7 | 1 | 32100000 | 32100000 | 33100000 |
| 3 | 7 | 2 | 33200000 | 33200000 | 34200000 |
| 3 | 7 | 3 | 34300000 | 34300000 | 35300000 |

| 阶段 | busy ns | idle ns | 利用率 |
| --- | ---: | ---: | ---: |
| 0 | 32000000 | 3300000 | 0.906516 |
| 1 | 32000000 | 3300000 | 0.906516 |
| 2 | 32000000 | 3300000 | 0.906516 |
| 3 | 32000000 | 3300000 | 0.906516 |

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
