# checkpoint-interval — qwen3-8b

输入：`{"common_job_mtbf_seconds": null, "device_mtbf_seconds": 31536000, "devices": 1024, "failure_free": true, "intervals_seconds": [60, 120, 300, 600, 900, 1800, 3600], "model": "qwen3-8b", "recovery_ns": 120000000000, "save_bandwidth_bytes_per_second": 8000000000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 8,190,735,360 |
| checkpoint_payload_bytes | 114,670,295,040 |
| blocking_save_cost_exact_seconds | `"11198271/781250"` |
| job_failure_rate_exact_per_second | `"0"` |
| job_mtbf_exact_seconds | `null` |
| first_order_optimal_useful_interval_seconds | `null` |
| poisson_optimal_useful_interval_seconds | `null` |
| best_enumerated_first_order_intervals | `[3600]` |
| best_enumerated_poisson_intervals | `[3600]` |

tau为新增有用计算秒；近似损失与重试模型的保留比例不能互换。

| tau s | c/tau | lambda*tau/2 | lambda*r | 一阶损失 | 小于1 | Poisson周期期望 s | Poisson保留比例 |
| ---: | --- | --- | --- | ---: | --- | ---: | ---: |
| 60 | 3732757/15625000 | 0 | 0 | 0.238896448 | True | 74.333786880 | 0.807169963 |
| 120 | 3732757/31250000 | 0 | 0 | 0.119448224 | True | 134.333786880 | 0.893297232 |
| 300 | 3732757/78125000 | 0 | 0 | 0.047779290 | True | 314.333786880 | 0.954399471 |
| 600 | 3732757/156250000 | 0 | 0 | 0.023889645 | True | 614.333786880 | 0.976667754 |
| 900 | 3732757/234375000 | 0 | 0 | 0.015926430 | True | 914.333786880 | 0.984323245 |
| 1800 | 3732757/468750000 | 0 | 0 | 0.007963215 | True | 1814.333786880 | 0.992099697 |
| 3600 | 3732757/937500000 | 0 | 0 | 0.003981607 | True | 3614.333786880 | 0.996034183 |

计量条件：

- 官方Qwen全参数14byte检查点，以有效全局写入带宽推保存成本c，整个c阻塞训练；这是串行持久化教学假设，不把异步API暂停替换成c，未含CPU状态、metadata和存储放大。
- tau定义为两次保存之间新增有用计算秒，成功一轮墙钟为tau+c。稀少故障的一阶损失c/tau+lambda*tau/2+lambda*r及sqrt(2c/lambda)按此近似使用；损失超过1不裁剪，也不当有效概率。
- 单设备独立指数故障率叠加为devices/MTBF；common_job项是独立的作业级共同冲击率，只加一次，不乘设备数。不是时间相关故障或相关硬件失效的实测分布，输入均为教学假设。
- 另列Poisson重试模型：计算和保存均可失败；失败即丢弃本轮全部新增工作，固定恢复r期间不会再失败，旧检查点永远可用。E=(exp(lambda*(tau+c))-1)*(1/lambda+r)，保留有用比例tau/E；该模型与一阶近似的假设和分母分别保留。
- Poisson最优用y-1+exp(-y-lambda*c)=0求根，y=lambda*tau；100次二分和expm1为数值求解，不宣称有理数精确。固定不再失败的r只乘E，不改变本模型最优tau。
- 零故障时无有限连续最优，null表示应减少保存次数的边界，有限候选仍可比较。未模拟有限训练终点、异步积压、检测延迟、多层检查点、恢复失败或实际训练质量，不能把这些结果作为生产最优周期。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
