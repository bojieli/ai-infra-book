# connection-states — 

输入：`{"budget_bytes": 1048576, "endpoint_state_bytes": 256, "isolation_classes": 1, "peers": 128, "relation_state_bytes": 64, "relations": "Explicit active relations are preserved in the JSON result.", "threads": 64, "transport_state_bytes": 1024}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| possible_local_relations | 8,192 |
| active_relations | 8,192 |
| allocated_local_endpoints | 64 |
| active_local_endpoints | 64 |
| active_peers | 128 |
| coupled_transport_count | 8,192 |
| shared_transport_count | 128 |
| endpoint_bytes | 16,384 |
| relation_bytes | 524,288 |
| coupled_transport_bytes | 8,388,608 |
| shared_transport_bytes | 131,072 |
| coupled_total_bytes | 8,929,280 |
| shared_total_bytes | 671,744 |
| saved_bytes | 8,257,536 |
| coupled_fits_budget | `false` |
| shared_fits_budget | `true` |
| largest_shared_group_relations | 64 |

计量条件：

- 只计本机threads个已分配端点到peers个远端的有向活跃关系，不是集群全网无向连接数，不对接收端再乘二。默认完整笛卡尔积，可显式给稀疏关系。
- 教学组织一为每活跃关系独立传输状态，组织二按(peer, thread modulo isolation_classes)复用。关系绑定仍逐项保留，所有本地端点仍计容量；不跨隔离类共享。
- 默认端点256、关系绑定64、传输1024 bytes和1MiB预算均为显式教学假设，不是UB Jetty/TP或任何网卡/QP官方结构大小。计数映射不冒称实际实现。
- 共享组人数只描述共享范围，不是吞吐、公平、热点流量或队头阻塞预测。共享并未消除关系管理；队列、完成项、包缓存、页表和动态故障状态需另行给定。

固定来源：

