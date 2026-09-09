# batch-reuse — 

输入：`{"batches": [1, 4, 16, 64], "device": "rtx4090", "history": 8192, "model": "qwen3-8b", "workspace_bytes": 0}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| weight_resident_bytes | 16,381,470,720 |
| shared_decode_weight_read_bytes | 15,136,811,008 |
| kv_bytes_per_request_token | 147,456 |
| per_request_history_read_bytes | 1,207,959,552 |
| nominal_device_capacity_bytes | 24,000,000,000 |
| declared_capacity_max_batch | 6 |
| kv_history_equals_weights_batch | 13 |
| compute_memory_crossover_batch | `null` |
| crossover_capacity_feasible | `false` |
| single_request_matrix_flops | 19,968,622,592 |
| hardware_ridge_flops_per_byte_exact | `"1475/9"` |

| batch | 矩阵FLOPs | 旧KV读bytes | 总声明流量bytes | 省权重读bytes | 声明驻留bytes | 容量可行 | 资源主导 |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 19968622592 | 1207959552 | 16344926208 | 0 | 17589577728 | True | memory |
| 4 | 79874490368 | 4831838208 | 19969271808 | 45410433024 | 21213898752 | True | memory |
| 16 | 319497961472 | 19327352832 | 34466654208 | 227052165120 | 35711182848 | False | memory |
| 64 | 1277991845888 | 77309411328 | 92456183808 | 953619093504 | 93700319232 | False | memory |

计量条件：

- 固定官方Dense Qwen配置，BF16权重／激活／KV；设备峰值严格选择BF16输入、FP32累加、Tensor、dense，不使用稀疏宣传峰值或混入INT8/FP8。MoE路由／专家并集需另一模型。
- 一次迭代每请求生成1token、history相同；矩阵FLOPs来自真实算子，batch线性扩展。非embedding权重理想跨batch读一次，embedding按请求读取一行；驻留仍包含完整embedding。
- 每请求旧KV读一次、新KV写一次；新K/V在片上供当前注意力使用，不另计外部重读。假定GQA共享和融合，逻辑接口字节不等于实际HBM流量；中间激活、转换、tile重读和非矩阵计算未包含。
- 容量按厂商标称GB乘10^9，加入完整权重、步末KV和显式workspace；默认workspace=0表示尚未计，不证明实际引擎可用。容量不通过时可运行时间与吞吐留null。
- 计算／带宽取max只是资源下界，吞吐为该条件下上界；没有执行GPU，不给实测效率、凑批等待、TTFT或SLO保证。
- 计算交叉点解B*F/compute=(shared+B*per_request)/bandwidth；分母非正则无有限计算主导交叉点。KV等权重交叉点只比较旧KV读取与共享权重，两个交叉点不可混同。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/hardware/nvidia-rtx-blackwell-whitepaper.pdf](https://images.nvidia.com/aem-dam/Solutions/geforce/blackwell/nvidia-rtx-blackwell-gpu-architecture.pdf)，SHA256 `906ff2a409d7a7e4cbc56f5d3a179d574120d19aaba99520670e1a0c064595fa`。
- [sources/hardware/nvidia-ptx-isa-9-3.html](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html)，SHA256 `940cc68f858cefdf82425b47ee3bac3afde447c8a85b95f43d7d6fb1f46b4413`。
- [research/hardware-nvidia-closure/rtx4090.html](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/)，SHA256 `2b315d1402135bfe273c3fbde57aa31ca482522ee8928b92af96cab8088906f8`。
