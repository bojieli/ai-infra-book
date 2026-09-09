# weight-handoff — qwen3-235b-a22b

输入：`{"capacity_bytes": 68719476736, "common_bytes": 4294967296, "expert_parallel": 7, "kv_bytes": 25769803776, "model": "qwen3-235b-a22b", "producer_bytes_per_second": 50000000000, "receiver_bytes_per_second": 50000000000, "replicas": 1, "training_live_bytes": 42949672960}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| total_bf16_weight_bytes | 470,187,269,120 |
| expert_bf16_weight_bytes | 454,192,791,552 |
| nonexpert_bf16_weight_bytes | 15,994,477,568 |
| recipients | 7 |
| largest_rank_weight_bytes | 83,413,720,064 |
| full_unicast_egress_bytes | 3,291,310,883,840 |
| selective_unicast_egress_bytes | 566,154,134,528 |
| egress_ratio_exact | `"3214170785/552884897"` |
| phase_live_bytes | `{"training": 47244640256, "rollout": 113478491136, "restore_all_before_release": 156428164096, "sync_weights_before_release": 130658360320}` |
| staged_peak_bytes | 130,658,360,320 |
| staged_allocations_fit | `false` |
| restore_all_allocations_fit | `false` |

| 交接阶段 | 同时驻留bytes |
| --- | ---: |
| training | 47244640256 |
| rollout | 113478491136 |
| restore_all_before_release | 156428164096 |
| sync_weights_before_release | 130658360320 |

| rank | 专家区间[start,stop) | 专家bytes | 全部所需权重bytes |
| --- | --- | ---: | ---: |
| 0 | [0,19) | 67419242496 | 83413720064 |
| 1 | [19,38) | 67419242496 | 83413720064 |
| 2 | [38,56) | 63870861312 | 79865338880 |
| 3 | [56,74) | 63870861312 | 79865338880 |
| 4 | [74,92) | 63870861312 | 79865338880 |
| 5 | [92,110) | 63870861312 | 79865338880 |
| 6 | [110,128) | 63870861312 | 79865338880 |

| 单播策略 | 生产端出口bytes | 最大接收bytes | 传输下界秒（精确） |
| --- | ---: | ---: | --- |
| full_to_every_rank | 3291310883840 | 470187269120 | 642834157/9765625 |
| only_owned_experts_plus_common | 566154134528 | 83413720064 | 552884897/48828125 |

计量条件：

- 官方Qwen完整参数BF16载荷；所有routed专家权重计入，不按top-k缩小。EP仅切专家、其余权重每rank完整复制，不含TP/PP；整数专家以连续区间均衡分配，非框架自动布局。
- 每个replica是独立完整EP组。full基线明确为生产端向每rank发送完整模型的单播，再丢弃不归属专家；selective仅发送所需专家和全部非专家。不是树广播、multicast或共享网络缓存，不能把这个生产端字节比称为所有广播算法的加速比。
- 生产端有效聚合出口和各接收端有效带宽为教学输入，时间max两界仅必要下界；训练侧重组、源分片all-gather、启动、拥塞、量化、验证和同步屏障未计。
- phase按最大权重rank独立核算。training_live_bytes已包括训练自身权重/状态，common_bytes为另外共用分配，rollout权重另占空间；无别名共享。先同步权重、释放全部训练分配、再恢复KV，生产端训练分配在同步完成之前保留。
- 阶段容量表只对应selective目标布局，不推断full基线接收缓冲峰值；whole模型是否流式接收/丢弃需另给时间线。默认训练40GiB、KV24GiB、common4GiB为显式教学输入，不能从235B配置推断其真实训练容量。
- 旧KV在权重更新后失效；恢复KV预算指分配空池，未表示旧KV内容可沿用。就绪/版本原子切换、LoRA/MTP与真实引擎交接仍未实现。

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
