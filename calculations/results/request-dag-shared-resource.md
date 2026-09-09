# request-dag — 

输入：`{"duration_overrides": {"hotspot": 15000}, "resource_overrides": {"parallel": "compute"}, "tasks": [{"deps": [], "duration_ns": 10000, "id": "prepare", "resource": "host"}, {"deps": ["prepare"], "duration_ns": 60000, "id": "hotspot", "resource": "compute"}, {"deps": ["prepare"], "duration_ns": 40000, "id": "parallel", "resource": "transfer"}, {"deps": ["hotspot", "parallel"], "duration_ns": 10000, "id": "finish", "resource": "host"}]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| baseline_finish_ns | 80,000 |
| modified_finish_ns | 75,000 |
| request_speedup | 1.0666666666666667 |
| baseline_critical_path | `["prepare", "hotspot", "finish"]` |
| modified_critical_path | `["prepare", "hotspot", "parallel", "finish"]` |
| serial_equivalent_before_ns | 120,000 |
| serial_equivalent_after_ns | 75,000 |
| serial_equivalent_speedup | 1.6 |
| frozen_old_path_ns | 35,000 |
| actual_measured_request_ns | `null` |

baseline

| 节点 | 资源 | 开始 ns | 完成 ns | 限制前序 |
| --- | --- | ---: | ---: | --- |
| prepare | host | 0 | 10000 | None |
| hotspot | compute | 10000 | 70000 | prepare |
| parallel | transfer | 10000 | 50000 | prepare |
| finish | host | 70000 | 80000 | hotspot |

modified

| 节点 | 资源 | 开始 ns | 完成 ns | 限制前序 |
| --- | --- | ---: | ---: | --- |
| prepare | host | 0 | 10000 | None |
| hotspot | compute | 10000 | 25000 | prepare |
| parallel | compute | 25000 | 65000 | hotspot |
| finish | host | 65000 | 75000 | parallel |

计量条件：

- 默认四节点是教学请求依赖图，prepare10us、hotspot60us、并行分支40us、finish10us；只将hotspot改为15us，不假称真实模型trace。
- 显式依赖完成后节点才可启动；相同resource为容量一的不可抢占串行资源，null表示不约束资源。调度选择最早可启动节点，同刻按输入顺序，记录资源前序形成的等待边，不声称全局最优调度。
- 完成定义为全部给定节点完成，不包含未输入的到达排队、启动或外部工作。资源为抽象互斥通路，不把不同资源名自动当成真实GPU可独占分区的证据。
- 关键路径在依赖与实际资源顺序构成的图上重算；frozen_old_path只展示旧路径换时长的值，不把它当优化后请求耗时。并行分支或资源顺序改变可能转移瓶颈。
- serial_equivalent是将全部任务串行化后可用Amdahl比较的成本，不能把并行trace中kernel时间求和占比直接套到请求墙钟。
- duration/resource覆盖支持显式校准或争用情景；共享资源减速不是由本模型自动预测，必须另给并发时长或经过验证的资源映射。无实验5-9替换前后记录时不声明真实请求收益。

固定来源：

