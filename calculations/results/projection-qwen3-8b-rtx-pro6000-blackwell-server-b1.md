# q_projection_resource_bound — qwen3-8b

输入：`{"accumulator_precision": "FP32", "batch": 1, "beta": 0, "device": "rtx-pro6000-blackwell-server", "execution_unit": "tensor", "input_precision": "BF16", "output_precision": "BF16", "sparsity": "dense", "tokens": 1}`

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
| memory_service_seconds | 2.1021174702567314e-05 |
| roofline_lower_bound_seconds | `null` |
| ridge_point_flops_per_byte | `null` |

计量条件：

- 仅一层 Q 投影 GEMM，M=B×T、K=hidden_size、N=query_heads×head_dim；Q width 不假定等于 hidden_size。
- A/W/Y 按 BF16 计、FP32 累加在片上、beta=0；不计 QK Norm、RoPE、其余层与输出头。
- 冷内存情景：A/W 起始于所选显存/统一内存接口外侧，Y 最终写回该接口；各传一次是此情景的服务量下界。跨调用缓存命中不适用此输入。
- tile 重读、布局、量化、片上约束、启动、依赖和实际有效供给另算；本结果不是已实现 kernel 的预测。
- 缺失匹配算力时只保留已知的 memory_service_seconds，roofline_lower_bound_seconds=null；不能称为完整 Roofline 或 GPU 性能。
- 只使用单设备规格。名义容量、可分配空间和整模型驻留可行性不由此单 GEMM 验证。
- 1597GB/s、120TFLOPS FP32、最高600W 是 Server Edition 的独立数据表；Workstation 的1792GB/s、503.8 dense BF16 不移用。
- 此数据表的 4 PFLOPS 和产品页其他 Tensor 值没有可绑定的 sparsity／accumulator 脚注，保留原值但不可当 BF16 dense 分母。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/hardware/nvidia-ptx-isa-9-3.html](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html)，SHA256 `940cc68f858cefdf82425b47ee3bac3afde447c8a85b95f43d7d6fb1f46b4413`。
- [sources/hardware/nvidia-rtxpro6000-server-page.html](https://www.nvidia.com/en-us/data-center/rtx-pro-6000-blackwell-server-edition/)，SHA256 `cc3d248d8dc405f48367b63707449b1d47005aed0897dfc95b05dcee835a4638`。
- [sources/hardware/nvidia-rtxpro6000-server-specs.pdf](https://dam-cdn.nvd.orangelogic.com/AssetLink/707m1632ypg4du1fj3ci1jo3h4w1k78j.pdf)，SHA256 `a9fbf9e9340b4852270196e2b599bfeec4e5028527b550fa76160aed7a5c4d50`。
