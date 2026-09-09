# training-history — historical-training-catalog

输入：`{"comparisons": [{"baseline": "qwen3-8b-proxy", "target": "qwen35-397b"}], "duration_scenarios": [], "lifecycle": []}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| models | 13 |
| verified_archives | 16 |

公开字段与代理算量：6ND不是全模型逐算子训练FLOPs。

| 模型 | 总/激活参数（报告值） | 代理N | tokens及范围 | 6ND代理FLOPs | GPU小时/型号 |
| --- | --- | --- | --- | --- | --- |
| llama1-7b | None/None | 6700000000 (nominal_dense_proxy) | 1000000000000 / reported/approximate training scale; see scope notes | 40200000000000000000000 | 82432/A100-80GB |
| llama1-65b | None/None | 65200000000 (nominal_dense_proxy) | 1400000000000 / reported/approximate training scale; see scope notes | 547680000000000000000000 | 1022362/A100-80GB |
| llama2-7b | None/None | 7000000000 (nominal_dense_proxy) | 2000000000000 / reported/approximate training scale; see scope notes | 84000000000000000000000 | 184320/A100-80GB |
| llama2-70b | None/None | 70000000000 (nominal_dense_proxy) | 2000000000000 / reported/approximate training scale; see scope notes | 840000000000000000000000 | 1720320/A100-80GB |
| llama31-8b | None/None | 8000000000 (nominal_dense_proxy) | 15000000000000 / reported/approximate training scale; see scope notes | 720000000000000000000000 | 1460000/H100-80GB |
| llama31-70b | None/None | 70000000000 (nominal_dense_proxy) | 15000000000000 / reported/approximate training scale; see scope notes | 6300000000000000000000000 | 7000000/H100-80GB |
| llama31-405b | None/None | 405000000000 (nominal_dense_proxy) | 15600000000000 / reported/approximate training scale; see scope notes | 37908000000000000000000000 | 30840000/H100-80GB |
| qwen25-7b-proxy | None/None | 7000000000 (nominal_dense_proxy) | 18000000000000 / reported/approximate training scale; see scope notes | 756000000000000000000000 | None/None |
| qwen3-8b-proxy | None/None | 8000000000 (nominal_dense_proxy) | 36000000000000 / reported/approximate training scale; see scope notes | 1728000000000000000000000 | None/None |
| qwen35-397b | None/None | None (nominal_dense_proxy) | None / reported/approximate training scale; see scope notes | None | None/None |
| deepseek-v3-pretraining | 671000000000/37000000000 | 37000000000 (active_parameter_proxy) | 14800000000000 / reported/approximate training scale; see scope notes | 3285600000000000000000000 | 2664000/H800 |
| deepseek-v4-flash | 284000000000/13000000000 | 13000000000 (active_parameter_proxy) | 32000000000000 / reported/approximate training scale; see scope notes | 2496000000000000000000000 | None/None |
| deepseek-v4-pro | 1600000000000/49000000000 | 49000000000 (active_parameter_proxy) | 33000000000000 / reported/approximate training scale; see scope notes | 9702000000000000000000000 | None/None |

| 模型 | D/N精确值 | 卡数角色 | 条件固定卡数天数 | 附同scope条件的最大卡数下界天数 | 来源与范围 |
| --- | --- | --- | --- | --- | --- |
| llama1-7b | 10000/67 | None/None | None | None | llama1-v1 / Tables 2 and 15； |
| llama1-65b | 3500/163 | 2048/reported_configuration | 511181/24576 | None | llama1-v1 / Table 15; section 2.4；Conditional constant-allocation duration; approximately 21 days is a separate narrative value. |
| llama2-7b | 2000/7 | None/None | None | None | llama2 / Tables 1 and 2； |
| llama2-70b | 200/7 | None/None | None | None | llama2 / Tables 1 and 2； |
| llama31-8b | 1875 | None/None | None | None | llama31-card / Training energy use table；15T is an approximate per-model comparison; family card says 15T+. GPU hours are model-card training totals. |
| llama31-70b | 1500/7 | None/None | None | None | llama31-card / Training energy use table；15T approximate; family says 15T+. GPU hours are model-card training totals. |
| llama31-405b | 1040/27 | 16384/reported_maximum | 160625/2048 | 160625/2048 | llama3 / Section 3; Table 4 and Llama3.1 model card；30.84M total model training GPU hours from model card; maximum16384 from report pretraining. Same-scope identity is not established by this cross-source transcription;78.43days is conditional under that additional assumption, not measured calendar time. |
| qwen25-7b-proxy | 18000/7 | None/None | None | None | qwen25-v2 / Sections 3.1–3.2；Family pretraining token scale applied to an explicit 7B label proxy; complete pretraining GPU hours not disclosed in these sources. |
| qwen3-8b-proxy | 4500 | None/None | None | None | qwen3 / Section 3; Table 21 is a DIFFERENT posttraining experiment；Family approximate token scale and nominal 8B proxy, not config-exact parameter count. Table21 RL17920/distillation1800 hours are not pretraining hours. |
| qwen35-397b | None | None/None | None | None | qwen35-blog / Archived official launch page；Native multimodal training; no closed token/GPU-hour combination in snapshot. Do not inherit Qwen3 36T. |
| deepseek-v3-pretraining | 400 | 2048/reported_configuration | 13875/256 | None | deepseek-v3 / Table 1 and section 3；Only pretraining pairs with 14.8T. Context extension119000 and posttraining5000 GPUh separate; 2.788M excludes prior research/ablation costs. |
| deepseek-v4-flash | 32000/13 | None/None | None | None | deepseek-v4 / Section 4.2；Approximate activated parameters are a proxy, not full attention/MTP/precision-aware FLOPs. Training GPU hours not inferred from deployment. |
| deepseek-v4-pro | 33000/49 | None/None | None | None | deepseek-v4 / Section 4.2；Approximate active-parameter proxy, not full training work. |

论文报告的阶段观测（非全程MFU）：

| 模型 | GPU/数量 | 序列长度 | TP/CP/PP/DP | TFLOPs/GPU | BF16 MFU | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| llama31-405b | H100-80GB/8192 | 8192 | 8/1/16/64 | 430 | 43/100 | llama3 / Table4 |
| llama31-405b | H100-80GB/16384 | 8192 | 8/1/16/128 | 400 | 41/100 | llama3 / Table4 |
| llama31-405b | H100-80GB/16384 | 131072 | 8/16/16/8 | 380 | 38/100 | llama3 / Table4 |

stage_reports

- `{"input": {"model": "deepseek-v3", "scope": "reported final training stages; excludes prior research", "parts": {"pretraining": 2664000, "context_extension": 119000, "posttraining": 5000}, "reported_total": 2788000, "source_id": "deepseek-v3"}, "aggregation": "additive", "summed_gpu_hours_exact": "2788000", "reported_total_matches": true}`
- `{"input": {"model": "qwen3-8b-posttraining-experiment", "scope": "alternative Table21 branches, NOT additive or pretraining total", "alternatives": {"reinforcement_learning": 17920, "on_policy_distillation": 1800}, "source_id": "qwen3"}, "aggregation": "alternatives", "summed_gpu_hours_exact": null, "reported_total_matches": null}`

comparisons

- `{"input": {"baseline": "qwen3-8b-proxy", "target": "qwen35-397b"}, "parameter_proxy_growth_exact": null, "training_tokens_growth_exact": null, "proxy_flops_growth_exact": null, "interpretation": "Descriptive proxy ratio; scope, architecture and quality are not controlled."}`

duration_scenarios


lifecycle


None/null为未知；条件卡数时间不是实测日期。Llama405跨模型卡总GPU小时与论文最大卡数仅给附加同scope假设的下界。reported_performance为论文单独报告的阶段观测，不能替代全程MFU。成本使用caller声明单位和范围，不用于不同任务质量的效率排名。

计量条件：

- 6ND is only the declared nominal dense or active-parameter proxy; attention, MTP, recomputation, precision and nonmatrix work are not fully accounted for.
- D/N uses the same proxy N, not an inferred total MoE parameter count. Undisclosed inputs remain null.
- GPU hours across A100, H100 and H800 are not normalized compute or efficiency comparisons. MFU remains null; no hardware peaks or prices are inferred.
- Reported configurations require a constant-count assumption; reported maxima give conditional lower bounds only when GPU hours and count refer to the same scope. Source-scope identity must be affirmed before an unconditional calendar lower bound is populated; neither is a measured date.
- mfu=null means no full-run MFU computed here. reported_performance preserves source stage observations separately; no single observation represents full training.
- DeepSeek-V3 final stages exclude earlier research. Qwen3 Table 21 branches are alternatives and never become pretraining GPU hours.
- Lifecycle costs require caller prices, usage, units, currency and scope. Missing other_cost stays null; use explicit zero only when intentionally excluded. No quality equivalence or scaling law fit is inferred.

固定来源：

- [../references/outline-checks/2026-09-07/scaling-history/llama1-v1.pdf](https://arxiv.org/pdf/2302.13971v1)，SHA256 `2e663675ae36ad12adb2f5a05281bac2747ecf8d23d92bedd9f937a89fee7136`。
- [../references/outline-checks/2026-09-07/scaling-history/llama1-v1.txt](https://arxiv.org/pdf/2302.13971v1)，SHA256 `ffa6cc50e75636630faa072d5c19e76c881426d4cfb88709db532493a23d9288`。
- [../references/files/papers/llama2.pdf](https://arxiv.org/abs/2307.09288)，SHA256 `1df284ce95f783002074bfe8f21d47c646b396ceb1736ea3ec0ea212fc070d91`。
- [../references/text/llama2.txt](https://arxiv.org/abs/2307.09288)，SHA256 `0051a49f7deb19991e05a84f0f86e286d55b29a8fed7ba71a16ba25e6bfa0edf`。
- [../references/outline-checks/2026-09-07/scaling-history/llama31-card.md](https://raw.githubusercontent.com/meta-llama/llama-models/main/models/llama3_1/MODEL_CARD.md)，SHA256 `a37da4be5eb00d97ee0017cadf54c55e8aca84c715fa7d0981d3f2bc13b763ef`。
- [../references/files/papers/llama3.pdf](https://arxiv.org/abs/2407.21783)，SHA256 `481f1599468f95a07d05e97fafe55bbe786dc1624c6f881bcb4c7d14c933d083`。
- [../references/text/llama3.txt](https://arxiv.org/abs/2407.21783)，SHA256 `2f74368b7aca29f248c86ce3f7da4f31b780f9c5d8f5b2565150f3a3893fa600`。
- [../references/outline-checks/2026-09-07/scaling-history/qwen25-v2.pdf](https://arxiv.org/pdf/2412.15115v2)，SHA256 `73b3292bead3ac8896679d3ac8be87439756faf356566cbda3ccc8a3dc7d79d3`。
- [../references/outline-checks/2026-09-07/scaling-history/qwen25-v2.txt](https://arxiv.org/pdf/2412.15115v2)，SHA256 `06a9d66b2079b2fb92d5bd8d61b5c2c4b01dc2f22c18e83e8598cb665acc288f`。
- [../references/files/papers/qwen3.pdf](https://arxiv.org/abs/2505.09388v1)，SHA256 `84a5e2b1fa04bb774bf12ae606d1e6d9dd2147ed2ebe78a4cfeb91ba380ffdd5`。
- [../references/text/qwen3.txt](https://arxiv.org/abs/2505.09388v1)，SHA256 `75f231a33d55a719089ba566e12ce78a2bca6f680a14e9ac8567d72775416a6a`。
- [../references/outline-checks/2026-09-07/scaling-history/qwen35-blog.html](https://qwen.ai/blog?id=qwen3.5)，SHA256 `d7fa9cb22ae0821694f921728c3b556d7fb49dcb5faa9075546b60717858f408`。
- [../references/files/papers/deepseek-v3.pdf](https://arxiv.org/abs/2412.19437)，SHA256 `812a3fd645c80725354de9d831a6785503007a60681461407f64e97305fa9330`。
- [../references/text/deepseek-v3.txt](https://arxiv.org/abs/2412.19437)，SHA256 `a0f38c9e92d97605ef07a8fb6fc144931eb719b5337895d97dfee4ef43f9e3a6`。
- [../references/files/papers/deepseek-v4.pdf](https://arxiv.org/abs/2606.19348)，SHA256 `55b2d72f772ac00de2e470b3ee08443c648d971c7f57c52d6202895665e5978d`。
- [../references/text/deepseek-v4.txt](https://arxiv.org/abs/2606.19348)，SHA256 `3fa26fbc1ca9fdbfee428100894e467e0c1c967945c6f4a1a19203a71730e5d7`。
