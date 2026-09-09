# router-pressure — 

输入：`{"experiment": "9-9 queue-pressure"}`

时间与负载来自封存双worker压力实验；目标与两任务完成分开，非预测路由。

| 结果 | 值 |
| --- | ---: |
| conditions | 6 |
| actual_generation_calls | 18 |
| target_prompt_tokens | 3,136 |
| target_saved_seconds_paired_median | 1.0541033938061446 |
| pair_added_seconds_paired_median | 0.1609554411843419 |
| cache_first_target_seconds_median | 1.382794533856213 |
| cache_first_background_seconds_median | 1.3557238220237195 |
| cache_first_pair_completion_seconds_median | 1.3844431459438056 |
| queue_first_target_seconds_median | 0.32863522809930146 |
| queue_first_background_seconds_median | 1.5448370799422264 |
| queue_first_pair_completion_seconds_median | 1.5448370799422264 |

| 轮次 | 策略 | 缓存token | 目标秒 | 后台秒 | 两任务完成秒 | 采样等待峰值 | 最大采样间隔秒 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | queue_first | 0 | 0.32116236980073154 | 1.5431873509660363 | 1.5431873509660363 | 0 | 0.016074280021712184 |
| 0 | cache_first | 3135 | 1.3835607890505344 | 1.3559933931101114 | 1.3851801760029048 | 1 | 0.01722529996186495 |
| 1 | cache_first | 3135 | 1.3818320529535413 | 1.3549884499516338 | 1.383859307039529 | 1 | 0.014786310028284788 |
| 1 | queue_first | 0 | 0.32863522809930146 | 1.5448370799422264 | 1.5448370799422264 | 0 | 0.013681623851880431 |
| 2 | queue_first | 0 | 0.3286911400500685 | 1.5453985871281475 | 1.5453985871281475 | 0 | 0.014455725904554129 |
| 2 | cache_first | 3135 | 1.382794533856213 | 1.3557238220237195 | 1.3844431459438056 | 1 | 0.012201367178931832 |

| 轮次 | queue-first目标节省秒 | 两任务增加秒 | 后台增加秒 |
| ---: | ---: | ---: | ---: |
| 0 | 1.0623984192498028 | 0.15800717496313155 | 0.18719395785592496 |
| 1 | 1.0531968248542398 | 0.16097777290269732 | 0.1898486299905926 |
| 2 | 1.0541033938061446 | 0.1609554411843419 | 0.18967476510442793 |

计量条件：

- 实验9-9补测两个Qwen8 BF16 worker共享RTX PRO，每实例max_running_requests=1，客户端cache_first/queue_first各3轮；不是原生Router策略实现。读取封存原件，不重跑服务。
- 每条件清缓存、预热、后台128输出及目标1输出，共18调用。目标从各自提交算完成；两任务从后台提交算最后完成，不能用目标局部收益替代整组收益。
- 核对实际决策负载、目标在后台活跃期间发出、命中3135/3136或0、输出与预热相同。单token输出与原失败Agent输入不证明任务质量。
- 队列峰值为离散/get_load采样，不是排队持续时间；background_remaining是事后计算，不是路由时的完成时间预测。实际采样最大间隔另列，不假定严格10ms。
- 配对差值先逐trial计算再取中位，另列每组中位，不混用中位数之差。只有3轮、共享GPU和观测开销，不推广跨机、线上p95或任意后台长度。
- 目标矩阵按官方逻辑前向复算，后台及完整服务性能不由此推断；实际部分prefill图仍启用，未称全程eager。事件恢复与预测路由仍待验证。

固定来源：

- [sources/router-pressure/run.py](../../experiments/ch09/09-09/queue-pressure/run.py)，SHA256 `ea54380f0bb13c2301f4b96ebde7c86fa6c4ac084fe09473335ebfa561b857f5`。
- [sources/router-pressure/worker-command.json](../../experiments/ch09/09-09/queue-pressure/worker-command.json)，SHA256 `1840b18b99aeeccf78fe2568c9c8186de7b34f86956745245f7717b5bb5037b9`。
- [sources/router-pressure/agent-prompts.json](../../experiments/ch09/09-09/queue-pressure/agent-prompts.json)，SHA256 `6819e3779cc050416e0c8dd29f10b8f6c6a38b01670141139e20619011f3f4d5`。
- [sources/router-pressure/results/execution.json](../../experiments/ch09/09-09/queue-pressure/results/execution.json)，SHA256 `88f23759ce79f54d55352d64e610d0eb90c388c2f9e7d9ce54f688eccc75c45b`。
- [sources/router-pressure/results/inputs.json](../../experiments/ch09/09-09/queue-pressure/results/inputs.json)，SHA256 `91211dd47a1c714d3b9bd33b8e56069e96a1a43fa3843c6bc412e3eff90d617e`。
- [sources/router-pressure/results/raw.jsonl](../../experiments/ch09/09-09/queue-pressure/results/raw.jsonl)，SHA256 `03c716a9e16d4b7008ef63eb5ae3419e7a9d8ac6da7de0d1d37ba75ddce678c8`。
- [sources/router-pressure/results/order.json](../../experiments/ch09/09-09/queue-pressure/results/order.json)，SHA256 `8243cd76ebf03767f2332aef0b6288cf9b87c0f1fdd76988e6cd3a32e9f93fa3`。
- [sources/router-pressure/manifest.json](../../experiments/ch09/09-09/queue-pressure/manifest.json)，SHA256 `84204ac2d841bceed7c67ef79b12bb0d1e3fe453877245ba352c8a0e7c64e7a1`。
- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
