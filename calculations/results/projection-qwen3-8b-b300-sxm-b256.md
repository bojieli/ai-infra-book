# q_projection_resource_bound — qwen3-8b

输入：`{"accumulator_precision": "FP32", "batch": 256, "beta": 0, "device": "b300-sxm", "execution_unit": "tensor", "input_precision": "BF16", "output_precision": "BF16", "sparsity": "dense", "tokens": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| matrix_flops | 8,589,934,592 |
| input_read_bytes | 2,097,152 |
| weight_read_bytes | 33,554,432 |
| output_write_bytes | 2,097,152 |
| cold_memory_payload_bytes | 37,748,736 |
| arithmetic_intensity_flops_per_byte | 227.55555555555554 |
| compute_service_seconds | 3.817748707555556e-06 |
| memory_service_seconds | 4.718592e-06 |
| roofline_lower_bound_seconds | 4.718592e-06 |
| ridge_point_flops_per_byte | 281.25 |

计量条件：

- 仅一层 Q 投影 GEMM，M=B×T、K=hidden_size、N=query_heads×head_dim；Q width 不假定等于 hidden_size。
- A/W/Y 按 BF16 计、FP32 累加在片上、beta=0；不计 QK Norm、RoPE、其余层与输出头。
- 冷内存情景：A/W 起始于所选显存/统一内存接口外侧，Y 最终写回该接口；各传一次是此情景的服务量下界。跨调用缓存命中不适用此输入。
- tile 重读、布局、量化、片上约束、启动、依赖和实际有效供给另算；本结果不是已实现 kernel 的预测。
- 缺失匹配算力时只保留已知的 memory_service_seconds，roofline_lower_bound_seconds=null；不能称为完整 Roofline 或 GPU 性能。
- 只使用单设备规格。名义容量、可分配空间和整模型驻留可行性不由此单 GEMM 验证。
- 每 GPU 数值从 HGX 八卡表换算；带宽是 up to；不把 HGX 总内存的舍入值除八替代逐卡规格。累加格式待白皮书核实。
- BF16 累加精度依据 PTX Table 42；FP16 峰值的累加格式继续单独核对。Blackwell 技术简报另有 B300 270GB/7.7TB/s 与 B200 up to 192GB/7.7TB/s 快照，不合并到此 HGX 规格。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/hardware/nvidia-hgx-page.html](https://www.nvidia.com/en-us/data-center/hgx/)，SHA256 `37ed56ca6dbda836f4dd0aaabe4e7f4e898550438b2888db688caeb5a0ed65d7`。
- [sources/hardware/nvidia-hgx-components.html](https://docs.nvidia.com/enterprise-reference-architectures/hgx-ai-factory/latest/components.html)，SHA256 `8db5c1cb160cfb3935d36324a112155d827a9b2e32768e59540ebd56f40840ec`。
- [sources/hardware/nvidia-ptx-isa-9-3.html](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html)，SHA256 `940cc68f858cefdf82425b47ee3bac3afde447c8a85b95f43d7d6fb1f46b4413`。
- [../references/files/specs/nvidia-blackwell-brief.pdf](https://dam-cdn.nvd.orangelogic.com/AssetLink/gl2l4l4812s5fw0p614s6i8bv6mi3vx5.pdf)，SHA256 `df58a797c6bc4236b1877b634fe31ff8da4c82fff289605adfb5aaca424aec69`。
- [research/blackwell-bf16-independent/mma.py](https://raw.githubusercontent.com/NVIDIA/cutlass/147295a3d4b75f3aeff247c25b8927cea9a7006a/python/CuTeDSL/cutlass/cute/nvgpu/tcgen05/mma.py)，SHA256 `abb9b3a8d2b5329677999b00a45c6c6e6ab763fc748cfbeeaa333de0df881baa`。
