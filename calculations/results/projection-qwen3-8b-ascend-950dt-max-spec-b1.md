# q_projection_resource_bound — qwen3-8b

输入：`{"accumulator_precision": "FP32", "batch": 1, "beta": 0, "device": "ascend-950dt-max-spec", "execution_unit": "cube", "input_precision": "BF16", "output_precision": "BF16", "sparsity": "dense", "tokens": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| matrix_flops | 33,554,432 |
| input_read_bytes | 8,192 |
| weight_read_bytes | 33,554,432 |
| output_write_bytes | 8,192 |
| cold_memory_payload_bytes | 33,570,816 |
| arithmetic_intensity_flops_per_byte | 0.9995119570522206 |
| compute_service_seconds | `null` |
| memory_service_seconds | 8.392704e-06 |
| roofline_lower_bound_seconds | `null` |
| ridge_point_flops_per_byte | `null` |

计量条件：

- 仅一层 Q 投影 GEMM，M=B×T、K=hidden_size、N=query_heads×head_dim；Q width 不假定等于 hidden_size。
- A/W/Y 按 BF16 计、FP32 累加在片上、beta=0；不计 QK Norm、RoPE、其余层与输出头。
- 冷内存情景：A/W 起始于所选显存/统一内存接口外侧，Y 最终写回该接口；各传一次是此情景的服务量下界。跨调用缓存命中不适用此输入。
- tile 重读、布局、量化、片上约束、启动、依赖和实际有效供给另算；本结果不是已实现 kernel 的预测。
- 缺失匹配算力时只保留已知的 memory_service_seconds，roofline_lower_bound_seconds=null；不能称为完整 Roofline 或 GPU 性能。
- 只使用单设备规格。名义容量、可分配空间和整模型驻留可行性不由此单 GEMM 验证。
- 表中列的是多种核数、容量档位；本记录为各项上限，不证明某个已交付 SKU 同时满足所有上限。
- 表 3-1 未明确 dense/sparse 与 accumulator，因此暂不自动用于矩阵 Roofline；Cube+Vector 宣传总数不作为一个 GEMM 的峰值。
- 完整保留 FP8、MXFP8、HiF8、MXFP4 等格式名称；相同宣传吞吐不代表相同编码、block scale 或 kernel 支持。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [../references/files/specs/ascend-950-official.pdf](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf)，SHA256 `ece3405e6a17fabdd462338fb94266558649a6407a2f28008403211387b3a927`。
