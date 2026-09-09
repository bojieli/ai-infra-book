# qwen-expert-quantized-gemm-interface — qwen3-235b-a22b

输入：`{"tile_k": 128, "tile_m": 128, "tile_n": 128, "tokens": 4096}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| matrix_flops | 51,539,607,552 |
| fully_padded_matrix_flops | 51,539,607,552 |
| output_tiles | 384 |
| m_blocks | 32 |
| n_blocks | 12 |
| k_blocks | 32 |
| fp16_activation_bytes | 33,554,432 |
| fp8_activation_bytes | 16,777,216 |
| fp8_weight_bytes | 6,291,456 |
| fp16_output_bytes | 12,582,912 |
| retained_fp16_input_per_quantization_row_bytes | 8,192 |
| global_fp32_row_scales_bytes | 16,384 |
| separate_main_bytes | 465,567,744 |
| full_scale_fused_main_bytes | 650,117,120 |
| prefix_scale_fused_main_bytes | 616,562,688 |
| full_scale_fusion_extra_main_bytes | 184,549,376 |
| actual_peak_working_bytes | `null` |
| measured_hbm_bytes | `null` |
| predicted_seconds | `null` |

| 方案 | 主张量 bytes | scale写 bytes | scale读 bytes | 使用最终行尺度 |
| --- | ---: | ---: | ---: | --- |
| separate_full_row_quantization | 465567744 | 16384 | 196608 | True |
| full_row_scale_fused_cast | 650117120 | 16384 | 196608 | True |
| prefix_scale_fused_cast | 616562688 | 0 | 0 | False |

计量条件：

- 固定官方 Qwen3 MoE 的一个专家一支 gate/up 投影，K=hidden_size、N=moe_intermediate_size；M 是该专家此次收到的教学 token 数，不乘专家数、层数或 top-k，也不是实测路由。
- 声明 FP16 激活、FP8 权重／量化激活、FP16 输出与 FP32 累加；这些是格式情景，不由官方 checkpoint dtype 推断实际部署，未选择任何硬件峰值。
- 输出 tile 外层、完整 K 归约保留累加器；不同输出 tile 间无 A/W 复用，每个输出列块重读一次 A、每个输出行块重读一次 W。尾部按有效元素读写，完整padding矩阵工作另列。
- 独立量化先扫描并保留整行FP16输入至最终尺度可用，再写FP8矩阵，输入只读取一次需要每活动行至少2K字节驻留。这里只给该必要载荷，未声称完整工作区可放。
- 最终尺度融合先单独扫描A求全行尺度，随后每个输出tile重读较宽FP16 A并cast。两种全行方案显式存每行一个FP32 scale，按每行每列块读取一次；权重尺度、其它元数据和局部scratch未计，主张量与已声明scale接口分列。
- 前缀尺度融合在K块中更新尺度，省去预扫描和全局scale数组；需局部尺度／累加器调整且改变cast舍入语义。它不是全行量化的等价替换，局部算术与数值误差需另外验证。
- 接口为所声明加载边界，不特指HBM。减少物化量可能增加宽输入重读；增大tile、改变共享或缓存策略会改变结果，不能由这些字节直接推出时延。

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
