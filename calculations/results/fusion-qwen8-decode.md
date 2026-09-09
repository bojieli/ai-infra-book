# qwen-pointwise-fusion-lifetimes — qwen3-8b

输入：`{"layout_copy": false, "tokens": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| elements | 12,288 |
| bf16_intermediate_bytes | 24,576 |
| standalone_layout_read_write_bytes | 0 |
| contiguous_partitions | 4 |
| separate_interface_bytes | 159,744 |
| fused_interface_bytes | 61,440 |
| saved_interface_bytes | 98,304 |
| separate_tensor_peak_bytes | 73,728 |
| fused_tensor_peak_bytes | 61,440 |
| actual_device_peak_bytes | `null` |
| predicted_seconds | `null` |

| 物化边界（算子编号） | 接口 bytes | 节省 bytes | 张量峰值 bytes |
| --- | ---: | ---: | ---: |
| [] | 61440 | 98304 | 61440 |
| [0] | 110592 | 49152 | 73728 |
| [1] | 110592 | 49152 | 73728 |
| [0, 1] | 159744 | 0 | 73728 |
逐组输入／输出、阶段内活跃集合及阶段后释放列表完整保存在 JSON。

计量条件：

- 从官方 Qwen3 单层 FFN 的 gate/up 输出尺寸 M×F 开始，不包含两个投影或 down GEMM；输入与SiLU／乘法中间量BF16，最终声明1-byte量化存储。固定尺度视为已给定的标量，不包含动态amax／scale构建或元数据。
- 枚举链上所有连续分组，边界表示完整张量物化。分组内部逐元素计算、保留原中间舍入语义而不写全张量；这是可消除物化的条件模型，不断言特定后端已融合或能保持相同指令。
- 可选layout_permute为元素双射的物理重排，独立执行读写各一份BF16张量；融合时假设生产者直接按目标索引写出，无需中间全张量。未计地址计算／合并访问损失／tile和真实布局限制。
- 所有外部gate/up起初已存在，所有权允许在最后消费组结束释放。每组先分配独立输出，再释放不再使用的输入，无in-place别名；阶段内活跃张量联合大小决定声明峰值，不把各张量容量直接相加。
- 统计主张量接口载荷，不含固定标量、权重、allocator保留池、临时FP32寄存器／共享内存和同步。融合增加的局部scratch未推断，因此声明张量峰值不等于实际设备峰值。
- 每取消一个只跨单边界的中间张量X，少一次写回和读取2X；多个消费者或重计算会改变这个关系。本例无跨输出tile重读，量化融入GEMM的重读反例另算。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
