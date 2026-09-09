# router-trace — 

输入：`{"policy": "round_robin"}`

命中、时间和worker身份来自封存原生路由回放，矩阵工作按官方配置复算。

| 结果 | 值 |
| --- | ---: |
| policy | `"round_robin"` |
| requests | 12 |
| prompt_tokens | 19,556 |
| cached_tokens | 13,458 |
| token_weighted_hit_rate | 0.6881775414195132 |
| hit_requests | 10 |
| client_median_s | 0.04552388610318303 |
| replay_window_s | 0.5553878981154412 |
| saved_matrix_flops | 194,131,899,777,024 |

| 策略 | 输入token | 缓存token | token命中率 | 命中请求 | 客户端中位秒 | 节省矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| round_robin | 19556 | 13458 | 0.6881775414195132 | 10/12 | 0.04552388610318303 | 194131899777024 |
| cache_aware | 19556 | 16376 | 0.8373900593168337 | 11/12 | 0.03277028992306441 | 237179353300992 |
| power_of_two | 19556 | 13458 | 0.6881775414195132 | 10/12 | 0.04337059997487813 | 194131899777024 |

| 输入轮次 | worker | 输入token | 缓存token | 客户端秒 | 命中后逻辑FLOPs |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 210 | 0 | 0.021244328934699297 | 2931534528512 |
| 1 | 1 | 316 | 0 | 0.030216317856684327 | 4420511596544 |
| 2 | 0 | 670 | 206 | 0.0873257820494473 | 6566924779520 |
| 3 | 1 | 884 | 312 | 0.041328009916469455 | 8149124120576 |
| 4 | 0 | 1233 | 666 | 0.04279946396127343 | 8195453616128 |
| 5 | 1 | 1447 | 880 | 0.04369553807191551 | 8267021680640 |
| 6 | 0 | 1796 | 1229 | 0.04475917504169047 | 8383737823232 |
| 7 | 1 | 2010 | 1443 | 0.04628859716467559 | 8455305887744 |
| 8 | 0 | 2359 | 1792 | 0.04763426096178591 | 8572022030336 |
| 9 | 1 | 2573 | 2006 | 0.04851574590429664 | 8643590094848 |
| 10 | 0 | 2922 | 2355 | 0.04994999407790601 | 8760306237440 |
| 11 | 1 | 3136 | 2569 | 0.05038848798722029 | 8831874301952 |

计量条件：

- 导入实验9-9正式run-v3封存36请求及两worker原生日志；失败v1/v2不计。每策略同12轮Agent输入，串行一轮、固定策略顺序，两个BF16 worker共用一GPU，非跨机扩展。
- 命中来自模型响应cached_tokens，去向来自worker request.received日志；已核对健康注册、prompt长度、同worker已完成前缀上界及三策略逐请求相同输出。未以router预计命中代替实际命中。
- 真实无host命中或远端KV，复算矩阵是官方Qwen逻辑工作，非实际HBM、tile、融合后issued FLOPs。命中前缀累计节省不是唯一驻留容量。
- 客户端end-start为完整单token请求耗时，不是独立引擎TTFT或远端取回时间。每策略12点、单轮与共享GPU不支持细微性能排名或生产SLO结论。
- 输入源为原始失败Agent轨迹，本次只重放输入，未重跑工具；强制一个输出token及相同输出不证明任务质量。实际部分prefill图仍被捕获，不能称为全程eager。
- 此记录没有事件缺口恢复或持续排队压力，不能据串行缓存亲和行为宣称缓存事件索引已得到验证。

固定来源：

- [sources/router-trace/run.py](../../experiments/ch09/09-09/run.py)，SHA256 `d0a2e352a765a7ccf9303350c40ead87b20ee94e0f8a7808282332587ec5b8b8`。
- [sources/router-trace/agent-prompts.json](../../experiments/ch09/09-09/agent-prompts.json)，SHA256 `6819e3779cc050416e0c8dd29f10b8f6c6a38b01670141139e20619011f3f4d5`。
- [sources/router-trace/results/execution.json](../../experiments/ch09/09-09/results/execution.json)，SHA256 `9c3dc4ce76d7f07f52c97f30c9f8f6abf83f2ef437c150b3cebfb04bf75384d0`。
- [sources/router-trace/results/prompts.json](../../experiments/ch09/09-09/results/prompts.json)，SHA256 `a9e96d517fa97697d9640e24cda469cd8d54ef8ca721df5a4b8a60e6398639ff`。
- [sources/router-trace/results/requests.jsonl](../../experiments/ch09/09-09/results/requests.jsonl)，SHA256 `38b0f09416d133188f63ce0a702acbba1b009056fafcf59e4ad01ff31a4c8cb2`。
- [sources/router-trace/router-package.json](../../experiments/ch09/09-09/router-package.json)，SHA256 `6d1f264c5f61c3b703edabf74d329c7f06acd4c2bd7e8e54fbd486280f661b5b`。
- [sources/router-trace/results/registration-round_robin.jsonl](../../experiments/ch09/09-09/results/registration-round_robin.jsonl)，SHA256 `8c16a2946699823b25efc509a48edd70d3d2316d0973e16375b5bbf8ced50bb4`。
- [sources/router-trace/results/registration-cache_aware.jsonl](../../experiments/ch09/09-09/results/registration-cache_aware.jsonl)，SHA256 `fac0dd83ebbe91339d143e97b86d96a927d1c254541f5cc89093c0ac15451567`。
- [sources/router-trace/results/registration-power_of_two.jsonl](../../experiments/ch09/09-09/results/registration-power_of_two.jsonl)，SHA256 `3ae685e5f2693a94f713b8dd7ead5b32fa27da0934d5c1225d58b338db0aa7f9`。
- [sources/router-trace/results/worker0-requests/ubuntu_0.log](../../experiments/ch09/09-09/results/worker0-requests/ubuntu_0.log)，SHA256 `64701c4a39fd2c29fd522f0df67e9166bd4feb41a3def0c8b98d3c68acb5a685`。
- [sources/router-trace/results/worker1-requests/ubuntu_0.log](../../experiments/ch09/09-09/results/worker1-requests/ubuntu_0.log)，SHA256 `4e3463a48ff69708b1ac5b30ea0acaba460e6bcde39b8c26bb3921483002bcd3`。
- [sources/router-trace/manifest.json](../../experiments/ch09/09-09/manifest.json)，SHA256 `955e14a815315389ae39ad9b990443d8c778a52b85cd96ea738b07a174133118`。
- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
