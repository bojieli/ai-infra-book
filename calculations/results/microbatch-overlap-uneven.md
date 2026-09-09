# qwen-microbatch-overlap — qwen3-8b

输入：`{"first_tokens": 128, "full_c_ns": 800000, "full_n_ns": 400000, "joint_window_ns": 600000, "split_c_ns": [480000, 490000], "split_n_ns": [200000, 210000], "tokens": 257}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| ffn_parameters | 150,994,944 |
| unique_weight_bytes | 301,989,888 |
| matrix_flops | 77,611,401,216 |
| split_matrix_flops | 77,611,401,216 |
| full_weight_read_once_bytes | 301,989,888 |
| split_cold_weight_read_bytes | 603,979,776 |
| split_compute_service_increase_ns | 170,000 |
| full_finish_ns | 1,200,000 |
| split_serial_finish_ns | 1,380,000 |
| ideal_finish_ns | 1,170,000 |
| paired_finish_ns | 1,290,000 |
| joint_window_strict_upper_bound_ns | 510,000 |
| positive_joint_window_can_win | `true` |
| paired_beats_full | `false` |
| actual_gpu_seconds | `null` |

| 微批 tokens | 矩阵 FLOPs | 无缓存完整权重读取 bytes |
| ---: | ---: | ---: |
| 128 | 38654705664 | 301989888 |
| 129 | 38956695552 | 301989888 |

full

| 节点 | 资源 | 开始 ns | 完成 ns | 限制前序 |
| --- | --- | ---: | ---: | --- |
| N | N | 0 | 400000 | None |
| C | C | 400000 | 1200000 | N |

split_serial

| 节点 | 资源 | 开始 ns | 完成 ns | 限制前序 |
| --- | --- | ---: | ---: | --- |
| N0 | N | 0 | 200000 | None |
| C0 | C | 200000 | 680000 | N0 |
| N1 | N | 680000 | 890000 | C0 |
| C1 | C | 890000 | 1380000 | N1 |

split_ideal

| 节点 | 资源 | 开始 ns | 完成 ns | 限制前序 |
| --- | --- | ---: | ---: | --- |
| N0 | N | 0 | 200000 | None |
| C0 | C | 200000 | 680000 | N0 |
| N1 | N | 200000 | 410000 | N0 |
| C1 | C | 680000 | 1170000 | C0 |

split_paired

| 节点 | 资源 | 开始 ns | 完成 ns | 限制前序 |
| --- | --- | ---: | ---: | --- |
| N0 | N | 0 | 200000 | None |
| C0_and_N1 | paired-window | 200000 | 800000 | N0 |
| C1 | C | 800000 | 1290000 | C0_and_N1 |

计量条件：

- 官方Qwen Dense单层SwiGLU三矩阵参数3HF、矩阵工作2M*3HF，切两份数学工作守恒，允许不等长两份但时长须由输入另给。默认256行拆128/128。
- BF16权重唯一容量288MiB；每份独立完整读一次、无跨微批缓存命中时逻辑读取576MiB，容量没有复制成576MiB。实际HBM须另查tile与缓存。
- N为抽象访存或通信阶段、C为计算阶段，0.4/0.8ms与拆分0.2/0.48ms是独立教学计时，不由FFN FLOPs或权重字节推算成实测。N不一定等于本表权重读，不能用二者反推硬件带宽。
- 理想模式N与C分别串行但可跨资源重叠；成对模式将C0与N1从共同开始到两者均完成作为单一联合窗口，默认0.60ms是反例教学输入，不是NanoFlow实测。窗口内各自完成时刻未知，不造额外重叠。
- 最后C1须等待C0及N1，填充N0、联合窗口和排空C1均计入。小矩阵服务损失与联合争用分别输入；有限缓冲、提交、其它层及队列尚未加入。
- 联合窗口必须严格小于full_finish-N0-C1才比原batch快；阈值非正时任何正窗口都不能获益。该条件限定当前两份依赖结构，不直接推广任意多微批流水。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
