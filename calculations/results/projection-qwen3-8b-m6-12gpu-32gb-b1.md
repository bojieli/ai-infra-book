# q_projection_resource_bound — qwen3-8b

输入：`{"accumulator_precision": "FP32", "batch": 1, "beta": 0, "device": "m6-12gpu-32gb", "execution_unit": "tensor", "input_precision": "BF16", "output_precision": "BF16", "sparsity": "dense", "tokens": 1}`

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
| memory_service_seconds | 0.0001974753882352941 |
| roofline_lower_bound_seconds | `null` |
| ridge_point_flops_per_byte | `null` |

计量条件：

- 仅一层 Q 投影 GEMM，M=B×T、K=hidden_size、N=query_heads×head_dim；Q width 不假定等于 hidden_size。
- A/W/Y 按 BF16 计、FP32 累加在片上、beta=0；不计 QK Norm、RoPE、其余层与输出头。
- 冷内存情景：A/W 起始于所选显存/统一内存接口外侧，Y 最终写回该接口；各传一次是此情景的服务量下界。跨调用缓存命中不适用此输入。
- tile 重读、布局、量化、片上约束、启动、依赖和实际有效供给另算；本结果不是已实现 kernel 的预测。
- 缺失匹配算力时只保留已知的 memory_service_seconds，roofline_lower_bound_seconds=null；不能称为完整 Roofline 或 GPU 性能。
- 只使用单设备规格。名义容量、可分配空间和整模型驻留可行性不由此单 GEMM 验证。
- 本资料未给出可按输入／累加精度及稀疏口径使用的 GPU 峰值；Neural Engine 和 GPU 内 Neural Accelerator 分别处理，不能替代 Metal GPU FLOPs。
- 电源适配器／整机最大连续功率不作为 GPU TDP。
- Apple 2026-08-25 发布；此处使用 2026-09-08 产品技术规格快照。M6 16GB 与较大内存配置的带宽分别为 153 和 170GB/s。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/hardware/apple-m6-m5ultra-launch.html](https://www.apple.com/newsroom/2026/08/apple-introduces-m6-and-m5-ultra-for-a-big-leap-in-performance-and-ai-compute/)，SHA256 `1186e6e38c8178ea91745c0f587c5491fbe9e16d8bbfd23dbf8e107cbdaf7d90`。
- [sources/hardware/apple-macmini-current-specs.html](https://www.apple.com/mac-mini/specs/)，SHA256 `2807ca4664dc42820d0c7d009dcfc89fdd118ac9362dd2dd526266a80814da83`。
