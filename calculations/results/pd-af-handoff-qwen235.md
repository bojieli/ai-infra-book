# pd-af-handoff — 

输入：`{"batch": 4, "decode_steps": 128, "element_bytes": 2, "length": 8192, "model": "qwen3-235b-a22b", "network_bandwidth": 25000000000, "path": "direct", "staging_bandwidth": 25000000000, "startup_ns": 5000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| layers | 94 |
| hidden_size | 4,096 |
| kv_heads | 4 |
| head_dim | 128 |
| pd_snapshot_bytes | 6,308,233,216 |
| af_one_direction_bytes | 32,768 |
| af_total_bytes | 788,529,152 |
| af_directional_messages | 24,064 |
| hops_per_message | 1 |
| pd_serialized_ns_exact | `"6308358216/25"` |
| af_serialized_ns_exact | `"3796529152/25"` |
| byte_matched_extra_ns_exact | `"120315000"` |
| equal_time_startup_ns_exact | `"5519704064/601575"` |
| af_faster_at_selected_startup | `true` |

| 交接 | payload bytes | 消息数 | 接口 | 接口bytes | 启动次数 | 载荷ns | 启动ns |
| --- | ---: | ---: | --- | ---: | ---: | --- | ---: |
| PD snapshot | 6308233216 | 1 | network | 6308233216 | 1 | 6308233216/25 | 5000 |
| AF decode activations | 788529152 | 24064 | network | 788529152 | 24064 | 788529152/25 | 120320000 |
| byte-matched repeated handoffs | 6308233216 | 24064 | network | 6308233216 | 24064 | 6308233216/25 | 120320000 |

| 消息缓冲 | 源GPU bytes | 目的GPU bytes | 源host bytes | 目的host bytes |
| --- | ---: | ---: | ---: | ---: |
| pd | 6308233216 | 6308233216 | 0 | 0 |
| af_one_message | 32768 | 32768 | 0 | 0 |

计量条件：

- teaching-gqa为正文32层示例；Qwen从官方config读取完整GQA。PD每请求一次完整未切分KV，AF仅指定decode_steps次模型调用；两项不代表同一完整请求的替代总成本。
- AF每层将完整hidden激活送到FFN侧，聚合完整结果返回；一次方向交接载荷B*H*element_bytes。MoE路由元数据、top-k复制、跨专家节点dispatch及共享专家的分支未计，不能套用潜空间V4/K3边界。
- 每条消息按hop完全串行，前条全部完成才开始后条；每hop加相同startup_ns，显式包含其启动／同步假设。host-staged为D2H→network→H2D，接口各计发送一次，不把收端重复加到网络。
- 带宽与启动均为教学有效服务输入，不是A100/H20或其他具体机器实测；不推算池服务率、排队、计算、TTFT或TPOT。
- 缓冲为明确的整消息双端分配上界：源GPU载荷、目的GPU载荷和两侧host槽共存；PD源KV与目的KV已包含在这里，不再另加为temporary。AF结果返回复用槽，FFN工作区及原激活保留不在此子账。
- 两端采用相同元素格式，未包含压缩元数据、格式转换、页索引、对齐和重传；不把1-byte存储自动称为受支持FP8执行。
- 相同总字节对照仅均分PD载荷到AF次数，有余数的消息多1byte。它用于隔离启动开销，不是实际KV分层协议。交叉点为上述串行通信模型的等时启动值，严格更快需在相应一侧。

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
