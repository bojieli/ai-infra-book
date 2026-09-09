# qwen-topology-allocation — qwen3-8b

输入：`{"calls": 256, "cut_capacity_bytes_per_second": 50000000000, "extra_setup_ns": 100000000, "flow_demand_bytes_per_second": 25000000000, "flows": 4, "new_bandwidth_bytes_per_second": 25000000000, "old_bandwidth_bytes_per_second": 25000000000, "participants": 8, "startup_ns": 5000, "tokens": 1024}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| message_bytes | 8,388,608 |
| rounds | 14 |
| per_rank_send_bytes | 14,680,064 |
| startup_ns | 70,000 |
| before_exact_ns | `"16430064/25"` |
| after_exact_ns | `"16430064/25"` |
| before_ns | 657,202.56 |
| after_ns | 657,202.56 |
| saving_exact_ns | `"0"` |
| call_speedup | 1.0 |
| before_lifetime_exact_ns | `"4206096384/25"` |
| after_lifetime_exact_ns | `"6706096384/25"` |
| new_path_wins_within_lifetime | `false` |
| break_even_calls | `null` |
| strictly_faster_calls | `null` |
| strip_simultaneous_jobs | 2 |
| checkerboard_simultaneous_jobs | 0 |
| cut_offered_bytes_per_second | 100,000,000,000 |
| cut_demand_fits | `false` |
| equal_flow_rate_upper_exact | `"12500000000"` |
| equal_flow_rate_upper_bytes_per_second | 12,500,000,000.0 |
| full_rate_simultaneous_flows | 2 |
| actual_collective_seconds | `null` |

| 空闲分布 | 空闲数 | 候选窗口数 | 最多同时作业 | 选中单元 |
| --- | ---: | ---: | ---: | --- |
| strip | 8 | 4 | 2 | [[1, 2, 5, 6], [0, 3, 4, 7]] |
| checkerboard | 8 | 0 | 0 | [] |

计量条件：

- 复用官方Qwen BF16激活和ring逐轮载荷，时长为rounds*alpha+每rank发送字节/有效单向带宽；25/75GB/s、alpha5us及重构100ms是教学输入，不是光开关实测或设备规格。
- 两个带宽情景假设所有发送／接收端和物理路径均可支持对应流量；未从设备总端口速率推定切片可用速率。归约算术、HBM供数、其它作业和实际算法选择另核。
- 额外准备相对原路径只计一次，按实际调用寿命摊销，启动项不因带宽增大而缩短。每次无正节省且准备为正时无有限回本。
- 放置独立采用固定4x4周期位置图，边界可环绕，作业必须占一个相邻2x2窗口。两种图各八个空闲位置，穷举不相交窗口最大集合；不是完整TPU允许配置或物理推荐。
- 割集是四条同时经过同一方向容量的流的独立条件模型，均分上限截断于每流需求；反向容量不抵扣正向拥塞。不将空闲位置数量、放置成功和带宽满足混为一谈。
- 放置与割集两个小模型未给出从所选窗口到流路径的映射，不能把它们拼成已验证的端到端可行方案；故障重连与训练状态恢复另计。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
