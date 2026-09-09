# batch-reuse — 

输入：`{"batches": [1, 64, 256, 512], "device": "h100-sxm", "history": 0, "model": "qwen3-8b", "workspace_bytes": 0}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| weight_resident_bytes | 16,381,470,720 |
| shared_decode_weight_read_bytes | 15,136,811,008 |
| kv_bytes_per_request_token | 147,456 |
| per_request_history_read_bytes | 0 |
| nominal_device_capacity_bytes | 80,000,000,000 |
| declared_capacity_max_batch | 431,440 |
| kv_history_equals_weights_batch | `null` |
| compute_memory_crossover_batch | 297 |
| crossover_capacity_feasible | `true` |
| single_request_matrix_flops | 15,136,784,384 |
| hardware_ridge_flops_per_byte_exact | `"19788/67"` |

| batch | 矩阵FLOPs | 旧KV读bytes | 总声明流量bytes | 省权重读bytes | 声明驻留bytes | 容量可行 | 资源主导 |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 15136784384 | 0 | 15136966656 | 0 | 16381618176 | True | memory |
| 64 | 968754200576 | 0 | 15146772480 | 953619093504 | 16390907904 | True | memory |
| 256 | 3875016802304 | 0 | 15176656896 | 3859886807040 | 16419219456 | True | memory |
| 512 | 7750033604608 | 0 | 15216502784 | 7734910425088 | 16456968192 | True | compute |

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
- [sources/hardware/nvidia-h100-page.html](https://www.nvidia.com/en-us/data-center/h100/)，SHA256 `8fe697dfa96dceeeed6e7a16517294e15d9100cc0e9f1e6e5edbce78699b4681`。
- [../references/files/specs/nvidia-h100.pdf](https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf)，SHA256 `3641614979809a027a8aabdc2e77639efb8fcd0f8dc7873a22ba2125489f5a27`。
- [sources/hardware/nvidia-ptx-isa-9-3.html](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html)，SHA256 `940cc68f858cefdf82425b47ee3bac3afde447c8a85b95f43d7d6fb1f46b4413`。
- [research/h05-next-review/cuda-programming-guide-12.8.1.html](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-c-programming-guide/index.html)，SHA256 `cdc49d93372b4e03e94d56f24345373f82ad76b8663c745073463263009637ce`。
