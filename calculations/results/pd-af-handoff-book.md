# pd-af-handoff — 

输入：`{"batch": 1, "decode_steps": 1, "element_bytes": 2, "length": 8192, "model": "teaching-gqa", "network_bandwidth": 25000000000, "path": "direct", "staging_bandwidth": 25000000000, "startup_ns": 5000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| layers | 32 |
| hidden_size | 4,096 |
| kv_heads | 8 |
| head_dim | 128 |
| pd_snapshot_bytes | 1,073,741,824 |
| af_one_direction_bytes | 8,192 |
| af_total_bytes | 524,288 |
| af_directional_messages | 64 |
| hops_per_message | 1 |
| pd_serialized_ns_exact | `"1073866824/25"` |
| af_serialized_ns_exact | `"8524288/25"` |
| byte_matched_extra_ns_exact | `"315000"` |
| equal_time_startup_ns_exact | `"1073217536/1575"` |
| af_faster_at_selected_startup | `true` |

| 交接 | payload bytes | 消息数 | 接口 | 接口bytes | 启动次数 | 载荷ns | 启动ns |
| --- | ---: | ---: | --- | ---: | ---: | --- | ---: |
| PD snapshot | 1073741824 | 1 | network | 1073741824 | 1 | 1073741824/25 | 5000 |
| AF decode activations | 524288 | 64 | network | 524288 | 64 | 524288/25 | 320000 |
| byte-matched repeated handoffs | 1073741824 | 64 | network | 1073741824 | 64 | 1073741824/25 | 320000 |

| 消息缓冲 | 源GPU bytes | 目的GPU bytes | 源host bytes | 目的host bytes |
| --- | ---: | ---: | ---: | ---: |
| pd | 1073741824 | 1073741824 | 0 | 0 |
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

