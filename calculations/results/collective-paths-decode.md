# qwen-collective-physical-paths — qwen3-8b

输入：`{"bandwidth_bytes_per_second": 50000000000, "participants": 16, "rounds": 3, "tokens": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| payload_bytes_per_rank | 8,192 |
| enumerated_messages | 96 |
| recursive_physical_link_bytes | 196,608 |
| swing_physical_link_bytes | 147,456 |
| recursive_prefix_lower_seconds | 2.4576e-07 |
| swing_prefix_lower_seconds | 1.6384e-07 |
| full_all_reduce_seconds | `null` |
| measured_network_seconds | `null` |

| 路径模式 | 轮 | 消息 bytes | 跳数 | 峰值链路消息 | 峰值链路 bytes | 全网物理 bytes | 下界 us |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| recursive | 0 | 4096 | [1] | 1 | 4096 | 65536 | 0.081920 |
| recursive | 1 | 2048 | [2] | 2 | 4096 | 65536 | 0.081920 |
| recursive | 2 | 1024 | [4] | 4 | 4096 | 65536 | 0.081920 |
| swing | 0 | 4096 | [1] | 1 | 4096 | 65536 | 0.081920 |
| swing | 1 | 2048 | [1] | 1 | 2048 | 32768 | 0.040960 |
| swing | 2 | 1024 | [3] | 2 | 2048 | 49152 | 0.040960 |

完整逐消息路径及有向链路计数保留在同名JSON。

计量条件：

- 官方Qwen BF16[tokens,H]输入，默认8MiB；固定16物理节点双向环，仅枚举reduce-scatter前三轮4/2/1MiB消息，不是Qwen推荐部署，也不是完整all-reduce。
- 递归对端r XOR 2^s；Swing按官方论文式2，rho=sum((-2)^i)，偶数r加rho、奇数r减rho再模16。只采用已核对的前三轮路径，不复现完整块归约／重排或非二次幂算法正确性。
- 消息沿唯一最短路径，正反方向是独立有向资源，每经过一条链路计一次发送字节，不再加接收副本。平均跳数与最忙链路消息数分别枚举。
- 每条有向链路50GB/s是教学有效带宽；单轮下界为最大链路bytes/B，轮间屏障下界相加。未计启动、逐跳延迟、路由／端口共享、归约、包级阻塞和后续轮次。
- physical_account同时保存全程聚合资源下界与逐轮下界，不能以聚合平均代替有屏障调度；前三轮下界比值不代表完整集合通信或训练加速比。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/collective-paths/nsdi24-de-sensi.txt](https://www.usenix.org/system/files/nsdi24-de-sensi.pdf)，SHA256 `f2cf73aa5a9ca20fd41c8e88bfb7379f190ebab262968a8bea974b10ce5390cb`。
