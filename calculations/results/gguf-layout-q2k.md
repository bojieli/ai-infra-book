# gguf-layout — 

输入：`{"variant": "Q2_K"}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| tensors | 1,131 |
| parameters | 235,093,634,560 |
| file_bytes | 85,691,002,112 |
| tensor_payload_bytes | 85,684,996,096 |
| code_or_float_bytes | 69,178,275,840 |
| quantization_scale_metadata_bytes | 16,506,720,256 |
| file_header_and_padding_bytes | 6,006,016 |
| payload_bits_per_parameter_exact | `"1338828064/459167255"` |
| file_bits_per_parameter_exact | `"1338921908/459167255"` |
| storage_types | `["F32", "Q2_K", "Q3_K", "Q4_K", "Q6_K"]` |

| 实际类型 | 张量数 | 元素数 | 块元素／bytes | 码值或浮点bytes | 块尺度元数据bytes | 总载荷bytes |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| Q6_K | 1 | 622329856 | 256/210 | 466747392 | 43757568 | 510504960 |
| F32 | 471 | 50081280 | 1/4 | 200325120 | 0 | 200325120 |
| Q2_K | 377 | 155371175936 | 256/84 | 38842793984 | 12138373120 | 50981167104 |
| Q3_K | 188 | 78852915200 | 256/110 | 29569843200 | 4312268800 | 33882112000 |
| Q4_K | 94 | 197132288 | 256/144 | 98566144 | 12320768 | 110886912 |

| 分片 | 文件bytes | header bytes | header对齐bytes | 张量载荷bytes | 张量padding bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q2_K/Qwen3-235B-A22B-Q2_K-00001-of-00002.gguf | 49906752544 | 5976073 | 23 | 49900776448 | 0 |
| Q2_K/Qwen3-235B-A22B-Q2_K-00002-of-00002.gguf | 35784249568 | 29897 | 23 | 35784219648 | 0 |

计量条件：

- 对固定发布Q2_K两片／Q4_K_M三片读取文件头，保存从magic至tensor-data起点的原始字节与SHA；网络Range读取有限前缀后裁掉载荷，只保留完整头。没有下载或校验完整权重数据，不证明量化数值质量。
- GGUF v3 little-endian，张量shape按GGUF内层维优先；按官方Qwen配置核对全部1131张量，包括128专家的三维合并矩阵、Router、输出头和norm。参数与原始模型相同不等于精度或输出相同。
- GGML官方ggml-common.h：Q2_K每256值84bytes（64码值+20尺度／最小值元数据），Q3_K110（96+14），Q4_K144（128+16），Q6_K210（192+18）；F32每值4bytes。每个量化行必须整除block长度，不将文件名位宽套到所有张量。
- 按每张量实际类型计算码值／浮点载荷、块尺度元数据；再按offset核对无重叠／对齐、分片文件头与padding，逐文件字节守恒。未执行GGML解包或反量化，运行时重打包／驻留和scratch不在文件布局中。

固定来源：

- [sources/gguf-qwen235/tree.json](https://huggingface.co/api/models/unsloth/Qwen3-235B-A22B-GGUF/tree/09e11417ffdc30c1c63d0296a40fd8fde0abb180?recursive=true&expand=false)，SHA256 `8f7870b155b8bcaab03e45781211aa67d6d5f28614e55d928d79e32d24fdbcbd`。
- [sources/gguf-headers/gguf.md](https://raw.githubusercontent.com/ggml-org/ggml/e91ded11bdcd78c42f9c8d3978ff6686eb4c1226/docs/gguf.md)，SHA256 `1dead27b6a522709f0127d194e58c21dbbbf00ba1c64fe37c54d1a9048b05020`。
- [sources/gguf-headers/ggml-common.h](https://raw.githubusercontent.com/ggml-org/ggml/e91ded11bdcd78c42f9c8d3978ff6686eb4c1226/src/ggml-common.h)，SHA256 `0061131b615c5721fc88a78feeb22c1f8c450f1c2646a317d80796a653bf595c`。
- [sources/gguf-headers/ggml.h](https://raw.githubusercontent.com/ggml-org/ggml/e91ded11bdcd78c42f9c8d3978ff6686eb4c1226/include/ggml.h)，SHA256 `34192eac913444df9dc1d23025a618448cdee1ee7d78597af4979d8edc77b695`。
- [sources/gguf-headers/Qwen3-235B-A22B-Q2_K-00001-of-00002.gguf.header](https://huggingface.co/unsloth/Qwen3-235B-A22B-GGUF/resolve/09e11417ffdc30c1c63d0296a40fd8fde0abb180/Q2_K/Qwen3-235B-A22B-Q2_K-00001-of-00002.gguf)，SHA256 `bca3798af17d1c1eb86a907049ce0b3a04d67273b1aa2ade06c3c657d8c9199e`。
- [sources/gguf-headers/Qwen3-235B-A22B-Q2_K-00002-of-00002.gguf.header](https://huggingface.co/unsloth/Qwen3-235B-A22B-GGUF/resolve/09e11417ffdc30c1c63d0296a40fd8fde0abb180/Q2_K/Qwen3-235B-A22B-Q2_K-00002-of-00002.gguf)，SHA256 `d9f27622237f26e21f3949446e8073a687b97b99a59653eb5f0964545aef4ebe`。
- [sources/gguf-headers/Qwen3-235B-A22B-Q4_K_M-00001-of-00003.gguf.header](https://huggingface.co/unsloth/Qwen3-235B-A22B-GGUF/resolve/09e11417ffdc30c1c63d0296a40fd8fde0abb180/Q4_K_M/Qwen3-235B-A22B-Q4_K_M-00001-of-00003.gguf)，SHA256 `a75f2105a73c1a2f19fb4e783e3932d6f7c50d9e6a04f59024ef2c86ec552e0b`。
- [sources/gguf-headers/Qwen3-235B-A22B-Q4_K_M-00002-of-00003.gguf.header](https://huggingface.co/unsloth/Qwen3-235B-A22B-GGUF/resolve/09e11417ffdc30c1c63d0296a40fd8fde0abb180/Q4_K_M/Qwen3-235B-A22B-Q4_K_M-00002-of-00003.gguf)，SHA256 `25a481442668c02f7bccb5e30764e046f6fb3fc231bced80e7380095d5d04205`。
- [sources/gguf-headers/Qwen3-235B-A22B-Q4_K_M-00003-of-00003.gguf.header](https://huggingface.co/unsloth/Qwen3-235B-A22B-GGUF/resolve/09e11417ffdc30c1c63d0296a40fd8fde0abb180/Q4_K_M/Qwen3-235B-A22B-Q4_K_M-00003-of-00003.gguf)，SHA256 `0669d11157ad4e72cd541fb7a5ad6e983570cde5ca35442aac1f4d5083280c8c`。
- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
