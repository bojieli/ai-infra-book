# cache-residency — 

输入：`{"capacities": {"DRAM": 1073741824, "HBM": 536870912, "SSD": 4294967296}, "intervals": [{"end_ns": 10000000000, "id": "a-short", "prefix_identity": "A", "start_ns": 0, "tier": "HBM", "tokens": 1024}, {"end_ns": 15000000000, "id": "a-long", "prefix_identity": "A", "start_ns": 5000000000, "tier": "HBM", "tokens": 2048}, {"end_ns": 6000000000, "id": "b", "prefix_identity": "B", "start_ns": 2000000000, "tier": "HBM", "tokens": 512}, {"end_ns": 30000000000, "id": "a-host", "prefix_identity": "A", "start_ns": 8000000000, "tier": "DRAM", "tokens": 2048}, {"end_ns": 60000000000, "id": "a-disk", "prefix_identity": "A", "start_ns": 12000000000, "tier": "SSD", "tokens": 2048}], "model": "qwen3-235b-a22b", "page_tokens": 16}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| kv_bytes_per_token | 192,512 |
| kv_page_bytes | 3,080,192 |
| all_tier_peak_physical_bytes | 1,182,793,728 |
| all_tier_physical_byte_seconds_exact | `"32921092096"` |
| globally_unique_byte_seconds_exact | `"23064477696"` |
| cross_tier_copy_byte_seconds_exact | `"9856614400"` |
| all_tiers_capacity_feasible | `true` |

驻留区间为教学输入；同层按物理身份取并集，跨层副本独立计费。

| 层 | 容量 bytes | 峰值 bytes | 实体 byte-seconds | 逻辑 byte-seconds | 共享节省 byte-seconds | 超容量 ns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HBM | 536870912 | 492830720 | 5322571776 | 6308233216 | 985661440 | 0 |
| DRAM | 1073741824 | 394264576 | 8673820672 | 8673820672 | 0 | 0 |
| SSD | 4294967296 | 394264576 | 18924699648 | 18924699648 | 0 | 0 |

| 起点 ns（含） | 终点 ns（不含） | 各层实体 bytes | 全层实体 bytes | 全局唯一比较 bytes |
| ---: | ---: | --- | ---: | ---: |
| 0 | 2000000000 | {"DRAM": 0, "HBM": 197132288, "SSD": 0} | 197132288 | 197132288 |
| 2000000000 | 5000000000 | {"DRAM": 0, "HBM": 295698432, "SSD": 0} | 295698432 | 295698432 |
| 5000000000 | 6000000000 | {"DRAM": 0, "HBM": 492830720, "SSD": 0} | 492830720 | 492830720 |
| 6000000000 | 8000000000 | {"DRAM": 0, "HBM": 394264576, "SSD": 0} | 394264576 | 394264576 |
| 8000000000 | 10000000000 | {"DRAM": 394264576, "HBM": 394264576, "SSD": 0} | 788529152 | 394264576 |
| 10000000000 | 12000000000 | {"DRAM": 394264576, "HBM": 394264576, "SSD": 0} | 788529152 | 394264576 |
| 12000000000 | 15000000000 | {"DRAM": 394264576, "HBM": 394264576, "SSD": 394264576} | 1182793728 | 394264576 |
| 15000000000 | 30000000000 | {"DRAM": 394264576, "HBM": 0, "SSD": 394264576} | 788529152 | 394264576 |
| 30000000000 | 60000000000 | {"DRAM": 0, "HBM": 0, "SSD": 394264576} | 394264576 | 394264576 |

计量条件：

- 官方完整GQA BF16页容量，interval从驻留已完成到最后释放，[start,end)端点释放先于分配。只接纳完整页，部分页写入／COW及混合递推状态未模拟。
- prefix_identity声明同一不可变物理页序列及相同模型版本／adapter／格式／执行状态身份，长度较长者共享原完整页。同token文本并不足以证明KV逐位相同，身份必须由调用方确认；不同identity不猜测共享祖先。
- 同tier同identity的同时驻留按最大前缀长度取并集，跨tier各保留一份实体，不能跨HBM/DRAM/SSD消除物理副本；全局唯一量仅为比较基准。
- 区间与净容量为教学输入，不是实际缓存事件。超容量时保留需求并标记超预算时长，不隐式驱逐或声称部署可运行；未计metadata、allocator、文件padding或备份副本。
- byte-seconds对实际声明驻留积分，空闲间隔不计。没有写入／迁移事件，不从容量变化推断写入字节、磁盘IO、命中率或取回性能。

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
