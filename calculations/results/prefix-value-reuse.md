# prefix-value — 

输入：`{"budget_bytes": 188743680, "candidates": [{"expected_reuses": "1", "id": "512", "prefix_tokens": 512, "suffix_tokens": 1}, {"expected_reuses": "1", "id": "768", "prefix_tokens": 768, "suffix_tokens": 1}, {"expected_reuses": "3", "id": "1024", "prefix_tokens": 1024, "suffix_tokens": 1}], "model": "qwen3-8b", "page_tokens": 16}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| kv_bytes_per_token | 147,456 |
| optimal_selected | `["1024"]` |
| optimal_resident_bytes | 150,994,944 |
| optimal_expected_saved_matrix_flops_exact | `"43603413958656"` |
| density_greedy_selected | `["1024"]` |
| density_greedy_resident_bytes | 150,994,944 |
| density_greedy_expected_saved_matrix_flops_exact | `"43603413958656"` |
| optimal_minus_greedy_flops_exact | `"0"` |

| 前缀 | 常驻 bytes | 完整矩阵 FLOPs | 命中后矩阵 FLOPs | 预期节省 FLOPs |
| --- | ---: | ---: | ---: | ---: |
| 512 | 75497472 | 7205365022720 | 15438774272 | 7189926248448 |
| 768 | 113246208 | 10858461200384 | 15589769216 | 10842871431168 |
| 1024 | 150994944 | 14550212083712 | 15740764160 | 43603413958656 |

计量条件：

- 每候选来自独立前缀身份，不共享物理页或互相包含；同模型、格式和位置语义满足复用条件。整前缀准入或不准入，不做部分命中；页尾按完整页占用。
- 每次后续请求还有至少一个suffix token以重算末端logits。官方Qwen full前向与history=prefix的suffix前向相减，已命中历史仍参与suffix注意力；不能把命中token直接当全部注意力免算。
- 目标仅为有限候选集合中最大化预期节省的矩阵FLOPs，expected_reuses是显式非负有理数假设，不是从模型配置推断的命中率。线性期望无需假设候选复用独立，但未模拟复用时间或TTL。
- 精确0/1选择与单位字节价值贪心对照；不可拆分大小使贪心可能留下不可用余量。精确最优只针对此静态独立候选模型，不是最优在线淘汰策略。
- 省下FLOPs不等于省下墙钟：不含取回延迟、调度、查表和质量差异；scalar／special运算不纳入此单一目标。留存容量对其它活跃请求的代价需服务层另算。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
