# measured-agent-trace-accounting — qwen3-8b

输入：`{"model_speedup": 1, "selected_turn": null, "trace": "thinking-off"}`

模型／工具墙钟来自固定实验记录；矩阵与 KV 为分析计量，条件式替换另列。

| 结果 | 值 |
| --- | ---: |
| turns | 12 |
| input_tokens | 19,556 |
| cached_input_tokens | 16,304 |
| uncached_input_tokens | 3,252 |
| output_tokens | 765 |
| cached_prefill_matrix_flops | 48,184,267,112,448 |
| cold_prefill_matrix_flops | 284,309,306,474,496 |
| decode_matrix_flops | 12,196,497,063,936 |
| measured_model_seconds | 13.156450202688575 |
| measured_tool_seconds | 0.4764101605396718 |
| measured_other_seconds | 0.16990416473709047 |
| measured_elapsed_seconds | 13.802764527965337 |
| counterfactual_elapsed_seconds | 13.802764527965337 |
| counterfactual_speedup | 1.0 |
| hypothetical_tool_wait_kv_byte_seconds | 120,010,844.97798157 |
| maximum_round_logical_kv_bytes | 465,223,680 |
| evaluation_cases | 1,013 |
| value_and_input_passed | 315 |
| including_alias_check_passed | 1 |
| actual_cache_peak_bytes | `null` |

| 轮 | 输入 | 命中 | 输出 | 模型墙钟 s | 工具墙钟 s | 冷/命中 prefill FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 210 | 0 | 20 | 0.331885 | 0.000155 | 2931534528512 / 2931534528512 |
| 1 | 316 | 192 | 20 | 0.310170 | 0.061239 | 4420511596544 / 1742408646656 |
| 2 | 670 | 304 | 125 | 1.931351 | 0.006279 | 9441156595712 / 5190785761280 |
| 3 | 884 | 656 | 20 | 0.318277 | 0.058633 | 12512082919424 / 3272131346432 |
| 4 | 1233 | 880 | 125 | 1.994325 | 0.084112 | 17578222223360 / 5125032181760 |
| 5 | 1447 | 1216 | 20 | 0.323784 | 0.056065 | 20720211722240 / 3391673335808 |
| 6 | 1796 | 1440 | 125 | 2.210751 | 0.006229 | 25902243774464 / 5286479396864 |
| 7 | 2010 | 1792 | 20 | 0.374284 | 0.067843 | 29115296448512 / 3274097229824 |
| 8 | 2359 | 2000 | 125 | 2.313275 | 0.003019 | 34413221249024 / 5449913729024 |
| 9 | 2573 | 2352 | 20 | 0.380919 | 0.064770 | 37697337098240 / 3392328630272 |
| 10 | 2922 | 2560 | 125 | 2.336330 | 0.006230 | 43111154647040 / 5615335178240 |
| 11 | 3136 | 2912 | 20 | 0.331098 | 0.061836 | 46466333671424 / 3512547147776 |

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
- [sources/agent-traces/thinking-off/rounds.jsonl](../sources/agent-traces/thinking-off/rounds.jsonl)，SHA256 `2be17dc0b78f5c4e9b913906fd7d610d625801a41965d01a0bd50ddfc7c553dc`。
- [sources/agent-traces/thinking-off/environment.json](../sources/agent-traces/thinking-off/environment.json)，SHA256 `2fc2dd9cdc95a418fcd9f69b4706dc000c5e5982f20b9d3676d3c6a6a9dc77fa`。
- [sources/agent-traces/thinking-off/final.json](../sources/agent-traces/thinking-off/final.json)，SHA256 `abf5dbfed5c9031a0f6825a2cce7a85b935bf05fb5b87f159c4e1762fa558987`。
- [sources/agent-traces/thinking-off/independent-checks-v2.json](../sources/agent-traces/thinking-off/independent-checks-v2.json)，SHA256 `c647074034f3f434c8ee8f55190f1c7044b34033b9ce0d9d885d172cf5f5935a`。
