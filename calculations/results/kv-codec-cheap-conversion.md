# kv-codec — 

输入：`{"append_encode_ns": 20000, "bandwidth_bytes_per_second": 1000000000000, "batch": 1, "decode_fixed_ns": 100000, "decode_ns_per_value": "1/10000", "length": 8192, "model": "qwen3-8b"}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| values_per_cached_position | 73,728 |
| bf16_history_bytes | 1,207,959,552 |
| bf16_next_token_append_bytes | 147,456 |
| baseline_read_append_ns_exact | `"151013376/125"` |

| 格式 | 历史bytes | scale bytes | 追加bytes | 融合总ns | 物化总ns | 融合省ns | 长历史持续获益起点 |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| BF16 | 1207959552 | 0 | 147456 | 151013376/125 | 151013376/125 | 0 | None |
| Q8_0 | 641728512 | 37748736 | 78336 | 513878016/625 | 2023827456/625 | 241188864/625 | 1943 |
| Q4_0 | 339738624 | 37748736 | 41472 | 325111296/625 | 1835060736/625 | 429955584/625 | 1216 |

计量条件：

- 官方Qwen full GQA，每token每K/V head一行head_dim值；Q8_0每32值32码值bytes+2bytes FP16 scale，Q4_0每32值16码值bytes+2bytes scale，来源为固定GGML官方结构体。BF16是容量基线，不是Q8/Q4输出类型。
- 存储与执行分开：假定量化KV恢复后仍按原Attention精度使用，不套INT8/FP4 Tensor峰值。量化误差、质量、实际后端支持及内核算术尚未验证。
- 查询读取length条已有KV并编码／写入一个新位置；baseline按BF16旧读+新增写。融合路径不把完整解码KV写回外存；物化路径另加BF16历史写一次／读一次及一份临时历史buffer。
- 带宽和decode_fixed_ns、decode_ns_per_value、append_encode_ns均是显式教学输入，转换成本采用独立串行服务账；append_encode_ns是整个batch一次新增编码成本，不随history增长。不能当作GPU实测或声称转换与访存无重叠。
- 只比较KV读／写与转换子账，未包含目标矩阵、softmax、分页、对齐、索引、数据布局重打包及工作区其它部分。转换固定成本与每值成本可替换，交叉点仅对当前线性子账成立。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/gguf-headers/ggml-common.h](https://raw.githubusercontent.com/ggml-org/ggml/e91ded11bdcd78c42f9c8d3978ff6686eb4c1226/src/ggml-common.h)，SHA256 `0061131b615c5721fc88a78feeb22c1f8c450f1c2646a317d80796a653bf595c`。
- [sources/gguf-headers/ggml.h](https://raw.githubusercontent.com/ggml-org/ggml/e91ded11bdcd78c42f9c8d3978ff6686eb4c1226/include/ggml.h)，SHA256 `34192eac913444df9dc1d23025a618448cdee1ee7d78597af4979d8edc77b695`。
