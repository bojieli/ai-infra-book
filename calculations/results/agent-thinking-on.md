# measured-agent-trace-accounting — qwen3-8b

输入：`{"model_speedup": 1, "selected_turn": null, "trace": "thinking-on"}`

模型／工具墙钟来自固定实验记录；矩阵与 KV 为分析计量，条件式替换另列。

| 结果 | 值 |
| --- | ---: |
| turns | 4 |
| input_tokens | 5,297 |
| cached_input_tokens | 4,480 |
| uncached_input_tokens | 817 |
| output_tokens | 2,733 |
| cached_prefill_matrix_flops | 11,976,253,571,072 |
| cold_prefill_matrix_flops | 76,195,573,465,088 |
| decode_matrix_flops | 43,622,472,024,064 |
| measured_model_seconds | 76.29364280123264 |
| measured_tool_seconds | 0.0777023951523006 |
| measured_other_seconds | 0.13893395266495645 |
| measured_elapsed_seconds | 76.5102791490499 |
| counterfactual_elapsed_seconds | 76.5102791490499 |
| counterfactual_speedup | 1.0 |
| hypothetical_tool_wait_kv_byte_seconds | 23,552,252.509357452 |
| maximum_round_logical_kv_bytes | 362,446,848 |
| evaluation_cases | 1,013 |
| value_and_input_passed | 1,013 |
| including_alias_check_passed | 710 |
| actual_cache_peak_bytes | `null` |

| 轮 | 输入 | 命中 | 输出 | 模型墙钟 s | 工具墙钟 s | 冷/命中 prefill FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 206 | 0 | 1200 | 36.375312 | 0.000063 | 2875476475904 / 2875476475904 |
| 1 | 1443 | 1392 | 1016 | 26.427640 | 0.003335 | 20661235220480 / 752367828992 |
| 2 | 1656 | 1440 | 383 | 10.034447 | 0.074244 | 23814862536704 / 3199098159104 |
| 3 | 1992 | 1648 | 134 | 3.456244 | 0.000061 | 28843999232000 / 5149311107072 |

计量条件：

- 输入来自本书真实人工任务夹具的两条串行 Qwen3-8B/vLLM 轨迹，独立副本逐文件核对 SHA256 与原实验 manifest，模型 revision 对上官方 config。这里只读取数据，不执行模型生成代码。
- prompt/output 长度取实际 token ID；命中取引擎 cached_tokens，不按文本相似度推算。未缓存输入不等于新增语义内容，thinking 截断与失败轮次均保留。两次结果不能当一般成功率或同工作量速度对照。
- 矩阵子账按有效因果位置与 last 输出头计量，冷前缀为相同输入完全重算的对照。实际引擎 chunked prefill/tile/转换/调度和采样另算，不由矩阵差额按比例缩放实测时间。prefill 产生第一个输出，之后 G−1 次 decode。
- 主机记录的模型墙钟包含调度和交付，工具墙钟不等于 CPU 核时；other 保留准备、间隙和最终验证等全部剩余时间。counterfactual 只替换指定模型段，其他阶段与质量假设不变；不保证更快模型仍会生成同一工具轨迹。
- 工具等待 KV 预算假设保留本轮全部已处理 P+G−1 个 BF16 槽，面积仅覆盖记录的工具执行区间；未证明引擎缓存实际保留这些块，不包括跨轮间隙、历史闲置块、分页对齐、并行复制或其它请求。实际缓存峰值留空。
- 原任务返回值／调用后输入不变通过数，与额外输出别名检查分别报告；失败任务所有轮次仍计成本，不用输出 token 总数冒充成功产出。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/agent-traces/thinking-on/rounds.jsonl](../sources/agent-traces/thinking-on/rounds.jsonl)，SHA256 `e8a017dc55d449a13ae677ced255ee5ada56ff7e21c9b6c8c6dbcaa2749d807c`。
- [sources/agent-traces/thinking-on/environment.json](../sources/agent-traces/thinking-on/environment.json)，SHA256 `ace022d0a900319da962822abebad8621f979f46aead342d9b8f92671b9656c7`。
- [sources/agent-traces/thinking-on/final.json](../sources/agent-traces/thinking-on/final.json)，SHA256 `abb2814b4c2eb8e95b75ab0008270f3da5000869f9192335c7548b64baf7fd2f`。
- [sources/agent-traces/thinking-on/independent-checks-v2.json](../sources/agent-traces/thinking-on/independent-checks-v2.json)，SHA256 `ac88c70f2c0fc6c066c94db80507950d4976322fcb3378e970d4e1eea56e7a66`。
