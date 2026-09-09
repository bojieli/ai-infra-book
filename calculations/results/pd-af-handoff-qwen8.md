# pd-af-handoff — 

输入：`{"batch": 1, "decode_steps": 1, "element_bytes": 2, "length": 8192, "model": "qwen3-8b", "network_bandwidth": 25000000000, "path": "direct", "staging_bandwidth": 25000000000, "startup_ns": 5000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| layers | 36 |
| hidden_size | 4,096 |
| kv_heads | 8 |
| head_dim | 128 |
| pd_snapshot_bytes | 1,207,959,552 |
| af_one_direction_bytes | 8,192 |
| af_total_bytes | 589,824 |
| af_directional_messages | 72 |
| hops_per_message | 1 |
| pd_serialized_ns_exact | `"1208084552/25"` |
| af_serialized_ns_exact | `"9589824/25"` |
| byte_matched_extra_ns_exact | `"355000"` |
| equal_time_startup_ns_exact | `"1207369728/1775"` |
| af_faster_at_selected_startup | `true` |

| 交接 | payload bytes | 消息数 | 接口 | 接口bytes | 启动次数 | 载荷ns | 启动ns |
| --- | ---: | ---: | --- | ---: | ---: | --- | ---: |
| PD snapshot | 1207959552 | 1 | network | 1207959552 | 1 | 1207959552/25 | 5000 |
| AF decode activations | 589824 | 72 | network | 589824 | 72 | 589824/25 | 360000 |
| byte-matched repeated handoffs | 1207959552 | 72 | network | 1207959552 | 72 | 1207959552/25 | 360000 |

| 消息缓冲 | 源GPU bytes | 目的GPU bytes | 源host bytes | 目的host bytes |
| --- | ---: | ---: | ---: | ---: |
| pd | 1207959552 | 1207959552 | 0 | 0 |
| af_one_message | 8192 | 8192 | 0 | 0 |

计量条件：

- teaching-gqa为正文32层示例；Qwen从官方config读取完整GQA。PD每请求一次完整未切分KV，AF仅指定decode_steps次模型调用；两项不代表同一完整请求的替代总成本。
- AF每层将完整hidden激活送到FFN侧，聚合完整结果返回；一次方向交接载荷B*H*element_bytes。MoE路由元数据、top-k复制、跨专家节点dispatch及共享专家的分支未计，不能套用潜空间V4/K3边界。
- 每条消息按hop完全串行，前条全部完成才开始后条；每hop加相同startup_ns，显式包含其启动／同步假设。host-staged为D2H→network→H2D，接口各计发送一次，不把收端重复加到网络。
- 带宽与启动均为教学有效服务输入，不是A100/H20或其他具体机器实测；不推算池服务率、排队、计算、TTFT或TPOT。
- 缓冲为明确的整消息双端分配上界：源GPU载荷、目的GPU载荷和两侧host槽共存；PD源KV与目的KV已包含在这里，不再另加为temporary。AF结果返回复用槽，FFN工作区及原激活保留不在此子账。
- 两端采用相同元素格式，未包含压缩元数据、格式转换、页索引、对齐和重传；不把1-byte存储自动称为受支持FP8执行。
- 相同总字节对照仅均分PD载荷到AF次数，有余数的消息多1byte。它用于隔离启动开销，不是实际KV分层协议。交叉点为上述串行通信模型的等时启动值，严格更快需在相应一侧。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
