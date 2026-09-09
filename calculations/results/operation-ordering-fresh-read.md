# operation-ordering — 

输入：`{"independent_ns": 10000, "model": "qwen3-8b", "notification_ns": 2000, "read_example": {"data_visible_ns": 2000, "flag_read_ns": 4000, "flag_visible_ns": 3000, "reread_latency_ns": 2000, "response_ns": 5000, "speculative_read_ns": 2000}, "recovery_ns": 80000, "shared_resource": false, "tokens": 1, "write_ns": 20000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| each_data_transfer_bytes | 8,192 |
| strict_all_done_ns | 112,000 |
| dependency_all_done_ns | 102,000 |
| strict_independent_done_ns | 112,000 |
| dependency_independent_done_ns | 10,000 |
| notification_visible_ns | 102,000 |
| all_done_saved_ns | 10,000 |
| stale_response_valid | `true` |
| reread_required | `false` |
| validated_read_delivery_ns | 5,000 |

| 取值／交付事件 | 时间 ns | 值 |
| --- | ---: | ---: |
| sample_data | 2000 | 1 |
| data_visible | 2000 | 1 |
| flag_visible | 3000 | 1 |
| sample_flag | 4000 | 1 |
| deliver_flag_then_saved_data | 5000 | 1 |
| deliver_validated_data | 5000 | 1 |

strict

| 节点 | 资源 | 开始 ns | 完成 ns | 限制前序 |
| --- | --- | ---: | ---: | --- |
| write_data | publication | 0 | 20000 | None |
| recover_and_make_visible | publication | 20000 | 100000 | write_data |
| publish_notification | publication | 100000 | 102000 | recover_and_make_visible |
| independent_transfer | independent | 102000 | 112000 | publish_notification |

necessary_dependencies

| 节点 | 资源 | 开始 ns | 完成 ns | 限制前序 |
| --- | --- | ---: | ---: | --- |
| write_data | publication | 0 | 20000 | None |
| independent_transfer | independent | 0 | 10000 | None |
| recover_and_make_visible | publication | 20000 | 100000 | write_data |
| publish_notification | publication | 100000 | 102000 | recover_and_make_visible |

计量条件：

- 两个数据传输各取官方BF16 [tokens,H]载荷，通知大小未指定；时间是教学输入，不从线速推导。写完与恢复后可见分开，通知必须等可见，独立传输没有数据依赖。
- strict为明确的全完成串行教学策略，不等于任意协议的保序语义。necessary_dependencies保留发布依赖；独立资源可并发，共用容量一资源时仍要等待。恢复阶段在本例占用publication抽象资源，不泛化真实网卡行为。
- 取值反例是独立的两个4-byte标量D/F事件模型，与前面BF16消息不同。初始D/F=0，先写D=1再发布F=1；同刻写入视为先于取值。先投机读D再读F，即使响应按F/D交付，缓存旧D仍可能错误。
- 修复假设具备完整冲突检测：若投机读早于数据可见，观察F后重新读取，完成后才能交付D；计额外4-byte读取和显式读取延迟。源端顺序对照为观察F后才读取D。未模拟检测消息、失效传播或实际硬件。
- 这是合法性事件见证和抽象调度，不是无同步C++/NVSHMEM程序，不宣称UB规范或现有网卡实现了远端排序硬件。实际执行序、可见性、完成与回收仍须对应具体规范。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
