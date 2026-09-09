# kv-pages — 

输入：`{"capacity_bytes": 4718592, "events": [{"id": "a", "op": "create", "tokens": 17}, {"id": "b", "op": "fork", "parent": "a"}, {"id": "c", "op": "fork", "parent": "a"}, {"id": "a", "op": "append", "tokens": 1}, {"id": "b", "op": "append", "tokens": 16}, {"id": "c", "op": "cancel"}], "model": "qwen3-8b", "page_tokens": 16, "reservation_tokens": 64}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| kv_bytes_per_token | 147,456 |
| page_bytes | 2,359,296 |
| capacity_pages | 2 |
| unusable_capacity_bytes | 0 |
| rejected_events | 2 |
| peak_allocated_page_bytes | 4,718,592 |
| final_allocated_page_bytes | 4,718,592 |
| final_logical_request_bytes | 5,013,504 |
| final_unique_live_bytes | 2,506,752 |
| final_unused_page_bytes | 2,211,840 |
| final_private_paged_bytes | 9,437,184 |
| final_fixed_reservation_bytes | 18,874,368 |
| total_copied_valid_bytes | 0 |

| 事件 | 操作 | 接纳 | 逻辑 bytes | 唯一有效 bytes | 分配 bytes | 空位 bytes | COW bytes |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | {'op': 'create', 'id': 'a', 'tokens': 17} | True | 2506752 | 2506752 | 4718592 | 2211840 | 0 |
| 1 | {'op': 'fork', 'parent': 'a', 'id': 'b'} | True | 5013504 | 2506752 | 4718592 | 2211840 | 0 |
| 2 | {'op': 'fork', 'parent': 'a', 'id': 'c'} | True | 7520256 | 2506752 | 4718592 | 2211840 | 0 |
| 3 | {'op': 'append', 'id': 'a', 'tokens': 1} | False | 7520256 | 2506752 | 4718592 | 2211840 | 0 |
| 4 | {'op': 'append', 'id': 'b', 'tokens': 16} | False | 7520256 | 2506752 | 4718592 | 2211840 | 0 |
| 5 | {'op': 'cancel', 'id': 'c'} | True | 5013504 | 2506752 | 4718592 | 2211840 | 0 |

计量条件：

- 官方Qwen BF16完整GQA每token跨全层KV字节；一个逻辑页聚合各层相同token范围，实际引擎可能分层分配。本例不含权重、工作区、块表与引用计数元数据。
- create建立独立序列，fork共享父序列全部页；append只修改尾部。共享未满尾页写前复制，满页后追加新页；只复制有效旧token字节，未初始化空位不复制。真实kernel可能搬整个块，需另核。
- cancel在安全点立即移除该请求引用，只释放引用计数归零页；不是实际异步取消API完成保证。事件之间无在途读写，不需额外延迟回收。
- 逻辑请求字节对每请求分别求和，unique_live去除物理共享，allocated按完整页计，unused=allocated-unique_live。共享节省与尾块碎片分开，不用allocated-logical作为碎片。
- fixed_reservation按每活跃请求显式最大长度预留，private_paged按各请求当前长度分页但不共享；三者在相同事件点比较。最大长度是输入约束，不预测真实生成长度或可接纳吞吐。
- 可选capacity_bytes按完整页取整；create/append在修改前计算新页与共享尾页COW所需页，容量不足整项拒绝，不改变长度、页表、引用或复制账。fork本身无需新KV页，但后续写入仍可能拒绝；不预留未来增长、不自动抢占或排队重试。
- fork假设相同token及计算状态，可共享KV；不同adapter/权重/位置语义不能仅凭文字前缀相同复用。未模拟换出、重算、缓存淘汰或实际vLLM块记录。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
