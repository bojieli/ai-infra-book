# qwen-graph-execution — qwen3-8b

输入：`{"calls": 1000000, "config_ns": 20000, "config_speedup": 4, "copy_bandwidth_bytes_per_second": 2000000000000, "device_ns": 20000, "device_speedup": 4, "exposed_submit_ns": 20000, "indirect_ns": 6000, "input_tokens": 2048, "metadata_ns": 2000, "padded_tokens": 2048, "real_tokens": 1536, "replay_ns": 3000, "segments": 100, "setup_ns": 1000000000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| input_tensor_bytes | 16,777,216 |
| extra_copy_interface_bytes | 33,554,432 |
| extra_copy_ns | 16,777.216 |
| extra_copy_exact_ns | `"2097152/125"` |
| layer_ffn_matrix_parameters | 150,994,944 |
| real_ffn_matrix_flops | 463,856,467,968 |
| padding_ffn_matrix_flops | 154,618,822,656 |
| padding_over_real_fraction | `"1/3"` |
| minimum_serial_steady_external_input_path | `"indirect"` |
| minimum_lifetime_external_input_path | `"indirect"` |
| actual_gpu_seconds | `null` |

| 路径 | 每次 us | 含准备总计 ms | 不亏调用数 | 严格更快调用数 |
| --- | ---: | ---: | ---: | ---: |
| eager | 40.000000 | 40000.000000 | 1 | None |
| copy | 41.777216 | 42777.216000 | None | None |
| indirect | 31.000000 | 32000.000000 | 111112 | 111112 |
| direct-output | 25.000000 | 26000.000000 | 66667 | 66667 |

| 配置流水变体 | 串行 us | 重叠含填充排空 us |
| --- | ---: | ---: |
| base | 4000.000000 | 2020.000000 |
| faster-device | 2500.000000 | 2005.000000 |
| faster-both | 1000.000000 | 505.000000 |

计量条件：

- 官方Qwen Dense H/F用于BF16边界张量和单层三矩阵FFN；输入拷贝token数与padding例子独立，不能推成两个真实batch执行时间相同。
- 默认设备20us、已暴露提交等待20us、重放3us、元数据2us、间接寻址6us，以及2TB/s有效拷贝流量带宽均是教学供给，不是硬件规格或测量。复制按源读加目的写，正常算子读取仍存在。
- 图路径每条额外准备成本显式设为setup_ns，默认1秒；以串行关键路径相加并计实际calls，分别报告不亏和严格更快的最小正整数次数。每次无正收益时不声称有限回本。
- direct-output仅在上游能直接写入稳定输出时适用，不参与外部输入路径选择；indirect为声明可用的教学路径，未声称已集成GraCE到任意引擎。
- 配置流水假设后段配置不依赖前段输出、缓冲足够且资源独立；启动和排空计入。其重叠时间不可与前面的串行图预算混加。
- padding只算单层FFN三个矩阵有效增量，不按该比例扩大attention或空request槽。图内存池共享、重捕获、KV挤占和实际调度仍需另核。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
