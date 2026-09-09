# iteration-batching — 

输入：`{"chunk_tokens": 16, "kv_capacity_bytes": null, "max_sequences": 2, "model": "qwen3-8b", "per_causal_pair_ns": 1, "per_new_token_ns": 1000, "policy": "chunked", "requests": [{"arrival_ns": 0, "id": "r0", "output_tokens": 8, "prompt_tokens": 16}, {"arrival_ns": 0, "id": "r1", "output_tokens": 2, "prompt_tokens": 16}, {"arrival_ns": 20000, "id": "r2", "output_tokens": 2, "prompt_tokens": 128}, {"arrival_ns": 30000, "id": "r3", "output_tokens": 4, "prompt_tokens": 16}], "step_base_ns": 10000, "token_budget": 32}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| requests | 4 |
| iterations | 12 |
| finish_ns | 317,004 |
| total_output_tokens | 16 |
| total_scheduled_tokens | 188 |
| total_matrix_flops | 2,636,833,882,112 |
| peak_live_kv_bytes | 21,676,032 |
| peak_reserved_kv_bytes | 22,413,312 |
| live_kv_byte_ns | 3,892,297,236,480 |
| max_waiting_ns | 191,085 |
| max_ttft_ns | 273,838 |
| max_itl_ns | 28,945 |

| 请求 | 准入ns | TTFT ns | 完成ns | 最大ITL ns | 矩阵FLOPs |
| --- | ---: | ---: | ---: | --- | ---: |
| r0 | 0 | 42272 | 221085 | 28439 | 329625370624 |
| r1 | 0 | 42272 | 54306 | 12034 | 238735654912 |
| r2 | 54306 | 273838 | 305985 | 12147 | 1799442989056 |
| r3 | 221085 | 234893 | 317004 | 28945 | 269029867520 |

| 步开始ns | 步结束ns | 新token | 有效配对 | 步内KV bytes | 请求／阶段／新token |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 42272 | 32 | 272 | 4718592 | r0:prefill:16, r1:prefill:16 |
| 42272 | 54306 | 2 | 34 | 5013504 | r0:decode:1, r1:decode:1 |
| 54306 | 81460 | 17 | 154 | 5013504 | r0:decode:1, r2:prefill:16 |
| 81460 | 108871 | 17 | 411 | 7520256 | r0:decode:1, r2:prefill:16 |
| 108871 | 136539 | 17 | 668 | 10027008 | r0:decode:1, r2:prefill:16 |
| 136539 | 164464 | 17 | 925 | 12533760 | r0:decode:1, r2:prefill:16 |
| 164464 | 192646 | 17 | 1182 | 15040512 | r0:decode:1, r2:prefill:16 |
| 192646 | 221085 | 17 | 1439 | 17547264 | r0:decode:1, r2:prefill:16 |
| 221085 | 264893 | 32 | 1808 | 18874368 | r2:prefill:16, r3:prefill:16 |
| 264893 | 293838 | 17 | 1945 | 21381120 | r3:decode:1, r2:prefill:16 |
| 293838 | 305985 | 2 | 147 | 21676032 | r2:decode:1, r3:decode:1 |
| 305985 | 317004 | 1 | 19 | 2801664 | r3:decode:1 |

计量条件：

- 同一教学请求流：固定批次只在整组退出后补位，连续批处理每个迭代边界补位，两者prefill一次处理完整prompt；chunked在相同连续补位上按decode优先、FIFO prefill分配token预算与单请求块上限。
- 只在迭代边界接纳已到达请求；固定批次不额外等待凑满。每个请求先完成prefill产生首输出，后续输出各消耗一个pending token。最新输出尚未写入KV，最终计算长度为prompt+output-1。
- 每步时长为base+new_tokens*per_new_token_ns+有效因果配对*per_causal_pair_ns，全部显式教学成本，跨请求相加后一次base；它不是实测拟合或硬件峰值预测。官方矩阵另计，非末prefill块不做输出头。
- KV准入按声明最大输出长度预留，严格FIFO不绕过队首；逻辑KV按每步开始分配该步全部新增行、步末完成请求释放。只计KV池，不含权重、页碎片或工作区；无抢占、共享前缀或动态EOS。
- 时间戳是调度模型交付时刻，不模拟HTTP或流式聚合；相同输出数量不证明生成内容或质量一致。maxITL仅对至少两输出请求定义。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
