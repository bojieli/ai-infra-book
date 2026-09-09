# checkpoint-reshard — qwen3-8b

输入：`{"include_optimizer": true, "model": "qwen3-8b", "source_layout": "rows", "source_parts": 8, "target_layout": "rows", "target_parts": 4}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| gate_shape | `[12288, 4096]` |
| parameters | 50,331,648 |
| bytes_per_parameter | 14 |
| logical_checkpoint_bytes | 704,643,072 |
| requested_read_bytes | 704,643,072 |
| destination_payload_bytes | 704,643,072 |
| planned_read_ranges | 32 |
| source_file_count | 32 |
| target_payload_bytes | `[176160768, 176160768, 176160768, 176160768]` |

源文件为原始行主序教学布局；偏移相对各文件及目标分片。完整坐标见JSON。

| 状态 | bytes/element | 各源分片 bytes | 各目标分片 bytes |
| --- | ---: | --- | --- |
| weight_bf16 | 2 | [12582912, 12582912, 12582912, 12582912, 12582912, 12582912, 12582912, 12582912] | [25165824, 25165824, 25165824, 25165824] |
| master_fp32 | 4 | [25165824, 25165824, 25165824, 25165824, 25165824, 25165824, 25165824, 25165824] | [50331648, 50331648, 50331648, 50331648] |
| adam_m_fp32 | 4 | [25165824, 25165824, 25165824, 25165824, 25165824, 25165824, 25165824, 25165824] | [50331648, 50331648, 50331648, 50331648] |
| adam_v_fp32 | 4 | [25165824, 25165824, 25165824, 25165824, 25165824, 25165824, 25165824, 25165824] | [50331648, 50331648, 50331648, 50331648] |

| 源文件 | 目标rank | 全局元素区间 [start,end) | 源偏移 bytes | 目标偏移 bytes | 长度 bytes |
| --- | ---: | --- | ---: | ---: | ---: |
| weight_bf16.rank0.bin | 0 | [0,6291456) | 0 | 0 | 12582912 |
| weight_bf16.rank1.bin | 0 | [6291456,12582912) | 0 | 12582912 | 12582912 |
| weight_bf16.rank2.bin | 1 | [12582912,18874368) | 0 | 0 | 12582912 |
| weight_bf16.rank3.bin | 1 | [18874368,25165824) | 0 | 12582912 | 12582912 |
| weight_bf16.rank4.bin | 2 | [25165824,31457280) | 0 | 0 | 12582912 |
| weight_bf16.rank5.bin | 2 | [31457280,37748736) | 0 | 12582912 | 12582912 |
| weight_bf16.rank6.bin | 3 | [37748736,44040192) | 0 | 0 | 12582912 |
| weight_bf16.rank7.bin | 3 | [44040192,50331648) | 0 | 12582912 | 12582912 |
| master_fp32.rank0.bin | 0 | [0,6291456) | 0 | 0 | 25165824 |
| master_fp32.rank1.bin | 0 | [6291456,12582912) | 0 | 25165824 | 25165824 |
| master_fp32.rank2.bin | 1 | [12582912,18874368) | 0 | 0 | 25165824 |
| master_fp32.rank3.bin | 1 | [18874368,25165824) | 0 | 25165824 | 25165824 |
| master_fp32.rank4.bin | 2 | [25165824,31457280) | 0 | 0 | 25165824 |
| master_fp32.rank5.bin | 2 | [31457280,37748736) | 0 | 25165824 | 25165824 |
| master_fp32.rank6.bin | 3 | [37748736,44040192) | 0 | 0 | 25165824 |
| master_fp32.rank7.bin | 3 | [44040192,50331648) | 0 | 25165824 | 25165824 |
| adam_m_fp32.rank0.bin | 0 | [0,6291456) | 0 | 0 | 25165824 |
| adam_m_fp32.rank1.bin | 0 | [6291456,12582912) | 0 | 25165824 | 25165824 |
| adam_m_fp32.rank2.bin | 1 | [12582912,18874368) | 0 | 0 | 25165824 |
| adam_m_fp32.rank3.bin | 1 | [18874368,25165824) | 0 | 25165824 | 25165824 |
| adam_m_fp32.rank4.bin | 2 | [25165824,31457280) | 0 | 0 | 25165824 |
| adam_m_fp32.rank5.bin | 2 | [31457280,37748736) | 0 | 25165824 | 25165824 |
| adam_m_fp32.rank6.bin | 3 | [37748736,44040192) | 0 | 0 | 25165824 |
| adam_m_fp32.rank7.bin | 3 | [44040192,50331648) | 0 | 25165824 | 25165824 |
| adam_v_fp32.rank0.bin | 0 | [0,6291456) | 0 | 0 | 25165824 |
| adam_v_fp32.rank1.bin | 0 | [6291456,12582912) | 0 | 25165824 | 25165824 |
| adam_v_fp32.rank2.bin | 1 | [12582912,18874368) | 0 | 0 | 25165824 |
| adam_v_fp32.rank3.bin | 1 | [18874368,25165824) | 0 | 25165824 | 25165824 |
| adam_v_fp32.rank4.bin | 2 | [25165824,31457280) | 0 | 0 | 25165824 |
| adam_v_fp32.rank5.bin | 2 | [31457280,37748736) | 0 | 25165824 | 25165824 |
| adam_v_fp32.rank6.bin | 3 | [37748736,44040192) | 0 | 0 | 25165824 |
| adam_v_fp32.rank7.bin | 3 | [44040192,50331648) | 0 | 25165824 | 25165824 |

计量条件：

- 官方Qwen单层gate未融合逻辑矩阵；MoE是单专家，不代表整个checkpoint。行主序、每状态每source rank一个无header原始文件，模型内文件名为计划标识，不声称实际文件存在。
- rows沿输出行按商余数切分；flat沿展平元素按商余数切分，可跨矩阵行边界。无padding、压缩、转置、gate/up融合或文件对齐；真实格式必须先提供逻辑坐标到文件字节的映射。
- 每个交集生成一次连续读取，源文件偏移与目标缓冲偏移分别相对各自分片。目标分片对同一逻辑张量不重叠且完整覆盖；全局读取量等于一次有效载荷，不推断物理磁盘IO或网络重复流量。
- 训练教学保存格式为BF16权重2＋FP32 master/m/v各4＝14bytes/参数，不含梯度、CPU状态、随机数、数据位置、token buffer和调度器；仅权重模式为推理载荷比较。
- 计划没有执行真实checkpoint恢复，也不生成离线重分片文件。这里不计容器metadata、读取启动、共享存储争用、持久化确认、优化器布局转换或完整恢复时间。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
