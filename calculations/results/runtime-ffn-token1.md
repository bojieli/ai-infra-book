# recorded-qwen-ffn-runtime — qwen3-8b

输入：`{"tokens": 1}`

本机FFN计时与Nsight事件来自固定实验；MPK为作者另机报告，二者不可混算。

| 结果 | 值 |
| --- | ---: |
| timing_cases | 5 |
| trace_ranges | 0 |
| weight_bytes | 301,989,888 |
| real_matrix_flops_per_chain | 301,989,888 |
| measured_full_model_seconds | `null` |

| 方案 | 微批数 | 中位 us | 最小 us | 最大 us | 主机提交中位 us | 张量 bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| eager | 1 | 243.254399 | 239.587212 | 474.567986 | 66.622254 | 114688 |
| fused | 1 | 242.000008 | 238.691211 | 473.328018 | 72.720554 | 90112 |
| graph | 1 | 240.745592 | 239.955211 | 283.345604 | 5.828007 | 114688 |
| fused_graph | 1 | 239.443207 | 238.145590 | 470.641613 | 5.419750 | 90112 |
| fused_graph_copy | 1 | 245.793605 | 242.289591 | 436.263990 | 24.922949 | 90112 |

另列MPK作者结果与环境：`{"evidence_kind": "author_report_not_this_experiment", "source_url": "https://arxiv.org/html/2512.22219v2", "source_snapshot": "mpk-v2.txt", "model": "Qwen3-8B", "gpu": "NVIDIA A100; memory SKU not inferred from the cited latency sentence", "batch_size": 1, "precision": "BF16", "metric": "full-model decode per-token latency in milliseconds", "baseline_vllm_sglang_ms": 14.5, "mpk_ms": 12.5, "artifact_conditions": {"cuda": "12.8", "torch": "2.7", "transformers": "4.57.1", "prompt_tokens": 64, "decode_tokens": 1024, "decoding": "greedy", "warmup_iterations": 4, "reported_statistic": "median of five runs", "declared_single_gpu_targets": ["A100", "H100 SXM", "B200"]}, "comparison_boundary": "The two paper latency values compare the same model and A100 within the paper. They are not measurements of this RTX FFN, and their ratio must not be multiplied with this experiment's local speed changes. MPK was not run on RTX SM120.", "reported_latency_ratio_exact": "29/25", "reported_latency_ratio": 1.16}`

计量条件：

- 记录为RTX PRO 6000 Blackwell上的随机BF16权重单层FFN，形状与官方Qwen配置逐项匹配；不是下载完整权重后的全模型执行。
- 无分析器计时从全部11个样本重算中位数和范围，不丢弃长尾；共享GPU、未清L2，CPU提交不含最终同步，CUDA event包含暴露提交间隙，二者不能相加。
- Nsight仅有32-token各三次调用的独立采集，按事件重新计Launch API、GraphLaunch、kernel和copy。设备活动取区间并集，未覆盖区间不证明整卡空闲；分析器时间不替代无分析器计时。
- 逻辑链操作数是三个矩阵加独立SiLU/Mul或融合激活；库可能拆成更多kernel。微批在同一卡顺序执行，全部块缓冲同时保留，未增加跨设备流水，不把变慢全部归因于启动。
- 张量账含输入／输出和源码显式中间量，不含权重、外部原始输入、验证张量或库工作区。图allocator增量不是完整图内存；准备包含捕获、实例化、首次重放和同步，排除预热JIT。
- MPK仅列作者Qwen3-8B/A100 BF16全模型decode14.5/12.5ms及29/25比值；其输入与环境保留，未在本机运行，也不与RTX局部比值相乘。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/runtime-traces/results.json](../experiments/ch05/05-08/results/results.json)，SHA256 `24764c130e19ab0f232f44296da0dba1b3049e98ba5c425b639585f0367dcc28`。
- [sources/runtime-traces/trace-analysis.json](../experiments/ch05/05-08/results/trace-analysis.json)，SHA256 `16447fc693cfe411dc65663188044067d2e49259dfaac1294aa8564ba68e9573`。
- [sources/runtime-traces/paper-case.json](../experiments/ch05/05-08/sources/paper-case.json)，SHA256 `63e2c14ee1f24ba1fb8c1a75a2ea6e0610fc230b62f262abe4b2e82bd7b5cee6`。
- [sources/runtime-traces/mpk-v2.txt](../experiments/ch05/05-08/sources/mpk-v2.txt)，SHA256 `76630ab4bf33add0eb95bfaf5b9ca5ae590ca787eeafc4bb1f7856137e5668c4`。
- [sources/runtime-traces/run.py](../experiments/ch05/05-08/run.py)，SHA256 `33c506f40abb880318b685511de144079ac893b55d58405e809b4ee621717251`。
- [sources/runtime-traces/analyze.py](../experiments/ch05/05-08/analyze.py)，SHA256 `56c822bf2865934b2d8281395309595496f6bc55008004a1994eb2e8686ebd9d`。
