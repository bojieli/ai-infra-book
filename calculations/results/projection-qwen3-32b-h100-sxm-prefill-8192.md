# q_projection_resource_bound — qwen3-32b

输入：`{"accumulator_precision": "FP32", "batch": 1, "beta": 0, "device": "h100-sxm", "execution_unit": "tensor", "input_precision": "BF16", "output_precision": "BF16", "sparsity": "dense", "tokens": 8192}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| matrix_flops | 687,194,767,360 |
| input_read_bytes | 83,886,080 |
| weight_read_bytes | 83,886,080 |
| output_write_bytes | 134,217,728 |
| cold_memory_payload_bytes | 301,989,888 |
| arithmetic_intensity_flops_per_byte | 2,275.5555555555557 |
| compute_service_seconds | 0.0006945570723266626 |
| memory_service_seconds | 9.01462352238806e-05 |
| roofline_lower_bound_seconds | 0.0006945570723266626 |
| ridge_point_flops_per_byte | 295.34328358208955 |

计量条件：

- 仅一层 Q 投影 GEMM，M=B×T、K=hidden_size、N=query_heads×head_dim；Q width 不假定等于 hidden_size。
- A/W/Y 按 BF16 计、FP32 累加在片上、beta=0；不计 QK Norm、RoPE、其余层与输出头。
- 冷内存情景：A/W 起始于所选显存/统一内存接口外侧，Y 最终写回该接口；各传一次是此情景的服务量下界。跨调用缓存命中不适用此输入。
- tile 重读、布局、量化、片上约束、启动、依赖和实际有效供给另算；本结果不是已实现 kernel 的预测。
- 缺失匹配算力时只保留已知的 memory_service_seconds，roofline_lower_bound_seconds=null；不能称为完整 Roofline 或 GPU 性能。
- 只使用单设备规格。名义容量、可分配空间和整模型驻留可行性不由此单 GEMM 验证。
- Table 3 明确列出 FP16/FP32 accumulator 对应峰值；低精度 Tensor 与 FP32/FP64 的 Boost 时钟不同。表中 dense/sparse 已有各自舍入值，直接保存，不强制相差精确两倍。
- 白皮书带宽 3352GB/s（not finalized），产品页为 3.35TB/s；本 ID 的访存分母采用产品页 3350GB/s。

固定来源：

- [configs/models/qwen3-32b/config.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/config.json)，SHA256 `97e295b63283935788fac5e4f8860862a56d4089538cafc93f0431f2ebe483bb`。
- [sources/qwen3-32b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/model.safetensors.index.json)，SHA256 `bed42c6c55274bc08a1f616bceb3bcb84b3f02cb6584c573bd18c6519291ecd0`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/hardware/nvidia-h100-page.html](https://www.nvidia.com/en-us/data-center/h100/)，SHA256 `8fe697dfa96dceeeed6e7a16517294e15d9100cc0e9f1e6e5edbce78699b4681`。
- [../references/files/specs/nvidia-h100.pdf](https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf)，SHA256 `3641614979809a027a8aabdc2e77639efb8fcd0f8dc7873a22ba2125489f5a27`。
- [sources/hardware/nvidia-ptx-isa-9-3.html](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html)，SHA256 `940cc68f858cefdf82425b47ee3bac3afde447c8a85b95f43d7d6fb1f46b4413`。
- [research/h05-next-review/cuda-programming-guide-12.8.1.html](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-c-programming-guide/index.html)，SHA256 `cdc49d93372b4e03e94d56f24345373f82ad76b8663c745073463263009637ce`。
