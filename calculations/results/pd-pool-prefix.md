# pd-pool — 

输入：`{"arrival_requests_per_second": "4", "cached_prefix_tokens": 6144, "model": "qwen3-8b", "network_bytes_per_second": 25000000000, "output_tokens": 129, "prompt_tokens": 8192, "workers": [{"count": 4, "decode_tokens_per_second": 64, "name": "prefill-oriented", "prefill_tokens_per_second": 16384}, {"count": 4, "decode_tokens_per_second": 256, "name": "decode-oriented", "prefill_tokens_per_second": 4096}]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| new_prefill_tokens_per_request | 2,048 |
| decode_calls_per_request | 128 |
| full_prompt_state_bytes | 1,207,959,552 |
| pd_transfer_bytes_per_request | 1,207,959,552 |
| network_capacity_requests_per_second_exact | `"48828125/2359296"` |
| assignments | 25 |
| best_prefill_workers | `{"prefill-oriented": 2, "decode-oriented": 0}` |
| best_decode_workers | `{"prefill-oriented": 2, "decode-oriented": 4}` |
| best_pd_bound_requests_per_second_exact | `"9"` |
| colocated_bound_requests_per_second_exact | `"100/17"` |
| pd_to_colocated_bound_ratio_exact | `"153/100"` |
| best_bottlenecks | `["decode"]` |
| arrival_strictly_below_best_pd_bound | `true` |
| arrival_strictly_below_colocated_bound | `true` |

| worker类型 | 副本数 | 每请求P资源秒 | 每请求D资源秒 | 单副本共置请求/s |
| --- | ---: | --- | --- | --- |
| prefill-oriented | 4 | 1/8 | 2 | 8/17 |
| decode-oriented | 4 | 1/2 | 1/2 | 1 |

| P分配 | D分配 | P请求/s | D请求/s | 联合上界请求/s | 限制资源 | 到达率严格低于上界 |
| --- | --- | --- | --- | --- | --- | --- |
| {'prefill-oriented': 0, 'decode-oriented': 0} | {'prefill-oriented': 4, 'decode-oriented': 4} | 0 | 10 | 0 | ['prefill'] | False |
| {'prefill-oriented': 0, 'decode-oriented': 1} | {'prefill-oriented': 4, 'decode-oriented': 3} | 2 | 8 | 2 | ['prefill'] | False |
| {'prefill-oriented': 0, 'decode-oriented': 2} | {'prefill-oriented': 4, 'decode-oriented': 2} | 4 | 6 | 4 | ['prefill'] | False |
| {'prefill-oriented': 0, 'decode-oriented': 3} | {'prefill-oriented': 4, 'decode-oriented': 1} | 6 | 4 | 4 | ['decode'] | False |
| {'prefill-oriented': 0, 'decode-oriented': 4} | {'prefill-oriented': 4, 'decode-oriented': 0} | 8 | 2 | 2 | ['decode'] | False |
| {'prefill-oriented': 1, 'decode-oriented': 0} | {'prefill-oriented': 3, 'decode-oriented': 4} | 8 | 19/2 | 8 | ['prefill'] | True |
| {'prefill-oriented': 1, 'decode-oriented': 1} | {'prefill-oriented': 3, 'decode-oriented': 3} | 10 | 15/2 | 15/2 | ['decode'] | True |
| {'prefill-oriented': 1, 'decode-oriented': 2} | {'prefill-oriented': 3, 'decode-oriented': 2} | 12 | 11/2 | 11/2 | ['decode'] | True |
| {'prefill-oriented': 1, 'decode-oriented': 3} | {'prefill-oriented': 3, 'decode-oriented': 1} | 14 | 7/2 | 7/2 | ['decode'] | False |
| {'prefill-oriented': 1, 'decode-oriented': 4} | {'prefill-oriented': 3, 'decode-oriented': 0} | 16 | 3/2 | 3/2 | ['decode'] | False |
| {'prefill-oriented': 2, 'decode-oriented': 0} | {'prefill-oriented': 2, 'decode-oriented': 4} | 16 | 9 | 9 | ['decode'] | True |
| {'prefill-oriented': 2, 'decode-oriented': 1} | {'prefill-oriented': 2, 'decode-oriented': 3} | 18 | 7 | 7 | ['decode'] | True |
| {'prefill-oriented': 2, 'decode-oriented': 2} | {'prefill-oriented': 2, 'decode-oriented': 2} | 20 | 5 | 5 | ['decode'] | True |
| {'prefill-oriented': 2, 'decode-oriented': 3} | {'prefill-oriented': 2, 'decode-oriented': 1} | 22 | 3 | 3 | ['decode'] | False |
| {'prefill-oriented': 2, 'decode-oriented': 4} | {'prefill-oriented': 2, 'decode-oriented': 0} | 24 | 1 | 1 | ['decode'] | False |
| {'prefill-oriented': 3, 'decode-oriented': 0} | {'prefill-oriented': 1, 'decode-oriented': 4} | 24 | 17/2 | 17/2 | ['decode'] | True |
| {'prefill-oriented': 3, 'decode-oriented': 1} | {'prefill-oriented': 1, 'decode-oriented': 3} | 26 | 13/2 | 13/2 | ['decode'] | True |
| {'prefill-oriented': 3, 'decode-oriented': 2} | {'prefill-oriented': 1, 'decode-oriented': 2} | 28 | 9/2 | 9/2 | ['decode'] | True |
| {'prefill-oriented': 3, 'decode-oriented': 3} | {'prefill-oriented': 1, 'decode-oriented': 1} | 30 | 5/2 | 5/2 | ['decode'] | False |
| {'prefill-oriented': 3, 'decode-oriented': 4} | {'prefill-oriented': 1, 'decode-oriented': 0} | 32 | 1/2 | 1/2 | ['decode'] | False |
| {'prefill-oriented': 4, 'decode-oriented': 0} | {'prefill-oriented': 0, 'decode-oriented': 4} | 32 | 8 | 8 | ['decode'] | True |
| {'prefill-oriented': 4, 'decode-oriented': 1} | {'prefill-oriented': 0, 'decode-oriented': 3} | 34 | 6 | 6 | ['decode'] | True |
| {'prefill-oriented': 4, 'decode-oriented': 2} | {'prefill-oriented': 0, 'decode-oriented': 2} | 36 | 4 | 4 | ['decode'] | False |
| {'prefill-oriented': 4, 'decode-oriented': 3} | {'prefill-oriented': 0, 'decode-oriented': 1} | 38 | 2 | 2 | ['decode'] | False |
| {'prefill-oriented': 4, 'decode-oriented': 4} | {'prefill-oriented': 0, 'decode-oriented': 0} | 40 | 0 | 0 | ['decode'] | False |

计量条件：

- 两个教学worker类型不是A100/H20规格或实测；每个worker代表已能容纳该完整模型与所需KV的独立服务副本，可为一组设备。模型放置、并行组、实际内存可行性须另外验收。
- 输入阶段token/s必须对应相同模型、精度、上下文、batch和质量条件下的有效服务能力。prefill按新处理token数，decode按调用次数；prefill最后logits产生首输出，所以G输出需要G-1次decode。
- 每个worker固定分配P或D，池内允许理想流量分配；独立资源容量取min，异构副本的请求/s先相加。共置每副本先加两个阶段的资源秒再取倒数，假定阶段共享资源且无额外混跑惩罚。
- 这是给定服务能力的稳态上界。没有请求排队、时变负载、启动同步、流水填充、transfer窗口限制、SLO、能耗或费用，不能把低于上界视为稳定性或尾延迟保证。
- P已命中前缀仅减少其新token工作；假设D冷缓存，仍交接完整prompt状态。跨长度复用相同token/s只是一项教学敏感性假设，实际需重新校准。
- KV使用state模块的默认BF16与模型状态约定，不含格式转换、分片复制、路由元数据或双端temporary。网络给共享有效单向payload带宽上界，收发不重复相加。
- 仅一个输出时不需要D调用或KV交接，最优把全部worker给P；多输出时要求两个池都有正能力。到达率恰等容量不标为严格低于，余量也不代替SLO证据。
- 枚举内最大值只对当前整数候选与假设成立；同值选输入顺序中的首项，不是唯一配比或真实系统最优。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
