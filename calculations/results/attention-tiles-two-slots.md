# qwen-single-head-attention-tiles — qwen3-8b

输入：`{"capacity_bytes": 131072, "causal": false, "kv_blocks": [1, 64, 128], "kv_slots": 2, "tokens": 8192}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| head_dim | 128 |
| one_read_write_qkvo_bytes | 8,388,608 |
| separate_fp32_score_and_probability_bytes | 536,870,912 |
| separate_score_probability_read_write_bytes | 1,073,741,824 |
| valid_matrix_flops | 34,359,738,368 |
| feasible_candidates | 3 |
| best_enumerated_kv_block | 1 |
| best_enumerated_interface_bytes | 213,909,504 |
| measured_hbm_bytes | `null` |
| predicted_kernel_seconds | `null` |

| b | a | 可放 | 接口 bytes | 块对更新 | 旧输出缩放乘法 |
| --- | --- | --- | ---: | ---: | ---: |
| 1 | 166 | True | 213909504 | 409600 | 8588886016 |
| 64 | 94 | True | 373293056 | 11264 | 133169152 |
| 128 | 50 | True | 692060160 | 10496 | 66060288 |

计量条件：

- 固定Qwen3单query head及对应K/V head，head_dim来自官方配置；默认非因果完整注意力隔离分块问题，不冒充Qwen整层因果prefill。GQA跨query head复用未模拟，不能把KV接口简单乘query头数当整卡HBM。
- 外层保留a行Q/部分O，内层扫描b行K/V。Q/K/V及最终O为BF16，S/P与部分O和三个统计向量为FP32；K/V单槽顺序复用，S/P共用槽。预算=2ad+2bd*kv_slots+4ab+4ad+12a，取该候选最大可行整数a。
- kv_slots=2为K/V同时驻留的容量变体，不免费沿用单槽a，也不假设完整预取双缓冲已经实现。容量是抽象快速缓冲，未合并某GPU的寄存器／共享内存／缓存规格。地址、对齐、临时值、流水scratch和训练LSE不在预算内。
- 每个Q块重新读取所需K/V，Q一次读取O一次写回。因果模式跳过全不可见K块，边界块读入实际完整行；有效因果FLOPs、被访问矩形tile工作及完整padding工作分列。
- 每行每个有有效key的K块更新一次状态；非首有效块无条件缩放一次旧输出，按d个乘法计。跳过不变尺度、优化指令或不同算法会改计数；块对更新次数不是主机kernel launch。
- 接口在工作缓冲与下一层之间，可能由L2服务，不特指HBM。最小字节仅为给定候选和排布，不代表全局下界或性能最佳；更小b的循环／缩放开销单列。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
