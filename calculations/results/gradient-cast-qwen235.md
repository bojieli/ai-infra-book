# gradient-cast — qwen3-235b-a22b

输入：`{"copy_startup_ns": 0, "cpu_cast_bytes_per_second": 100000000000, "cpu_cast_startup_ns": 0, "extra_gpu_budget_bytes": 268435456, "gpu_cast_bytes_per_second": 1500000000000, "gpu_cast_startup_ns": 0, "host_budget_bytes": 536870912, "link_bytes_per_second": 32000000000, "model": "qwen3-235b-a22b"}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| gate_shape | `[1536, 4096]` |
| gradient_elements | 6,291,456 |
| bf16_bytes | 12,582,912 |
| fp32_bytes | 25,165,824 |
| cast_logical_read_write_bytes | 37,748,736 |
| cpu_cast_exact_seconds | `"18432/48828125"` |
| gpu_cast_exact_seconds | `"6144/244140625"` |
| equal_time_link_bytes_per_second_exact | `"250000000000/7"` |
| fastest_without_capacity | `["cpu"]` |
| fastest_fitting_buffers | `["cpu"]` |

完整梯度串行路径，转换与链路为有效教学吞吐；终点为CPU可消费FP32。

| 转换端 | 就绪 s | D2H bytes | GPU额外峰值 bytes | GPU含源峰值 bytes | 主机峰值 bytes | 缓冲可容纳 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| cpu | 0.000770703 | 12582912 | 0 | 12582912 | 37748736 | True |
| gpu | 0.000811598 | 25165824 | 25165824 | 37748736 | 25165824 | True |

| 路径 | 操作 | 起点 s（精确） | 终点 s（精确） | 逻辑访问／载荷 bytes |
| --- | --- | --- | --- | ---: |
| cpu | d2h_bf16 | 0 | 768/1953125 | 12582912 |
| cpu | cast_on_cpu | 768/1953125 | 37632/48828125 | 37748736 |
| gpu | cast_on_gpu | 0 | 6144/244140625 | 37748736 |
| gpu | d2h_fp32 | 6144/244140625 | 198144/244140625 | 25165824 |

| 路径 | 所在端 | 缓冲 | 起点 s（含） | 终点 s（交接／释放） | bytes |
| --- | --- | --- | --- | --- | ---: |
| cpu | gpu | common_bf16_gradient | 0 | 768/1953125 | 12582912 |
| cpu | host | bf16_staging | 0 | 37632/48828125 | 12582912 |
| cpu | host | fp32_output | 768/1953125 | 37632/48828125 | 25165824 |
| gpu | gpu | common_bf16_gradient | 0 | 6144/244140625 | 12582912 |
| gpu | gpu | fp32_staging | 0 | 198144/244140625 | 25165824 |
| gpu | host | fp32_output | 6144/244140625 | 198144/244140625 | 25165824 |

计量条件：

- 官方Qwen一层gate梯度，MoE为一个专家而非全层专家集合。GPU已有BF16梯度，终点为CPU可消费FP32；主权重、Adam更新、参数回传和其它层不在这段路径内。
- 转换逻辑访问每元素读2写4，共6Nbytes；带宽为针对该操作总读写的有效吞吐输入，不是硬件峰值或实测。链路是有效单向D2H。BF16到FP32不改变有限值表示，未模拟数值内核。
- 同一完整张量内cast/copy顺序执行、不分块、不重叠；相同copy启动两路各付一次，cast启动可不同。CPU转换比GPU转换慢时才有正交点，GPU路径严格更快需要链路超过交点；交点相等保留两者。
- 双方主机缓冲均已锁页、预分配。只报告声明区间内的活跃载荷，缓冲池预留和allocator另计。源梯度为共有输入，GPU净额外预算不重复扣除它。输入在最后读取结束释放，FP32输出在就绪终点交给CPU消费者；消费者之后的生命周期另算。
- CPU路径host输入保留到cast读完，输出从cast开始写入，两者重叠；GPU路径FP32暂存保留到D2H读完。时间为半开区间，全部使用精确有理数。容量通过仅表示这组缓冲可容纳，不证明整个训练步可执行或加速。

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
