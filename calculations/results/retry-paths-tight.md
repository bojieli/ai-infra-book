# retry-paths — 

输入：`{"deadline_seconds": "14", "nodes": [{"cost": "1/100", "cpu_seconds": 3, "id": "initial", "outcomes": [{"probability": "4/5", "target": "success"}, {"probability": "3/25", "target": "repair"}, {"probability": "2/25", "target": "upgrade"}], "resident_bytes": 2147483648, "seconds": 10}, {"cost": "3/500", "cpu_seconds": 1, "id": "repair", "outcomes": [{"probability": "3/5", "target": "success"}, {"probability": "2/5", "target": "upgrade"}], "resident_bytes": 2147483648, "seconds": 4}, {"cost": "3/100", "cpu_seconds": 2, "id": "upgrade", "outcomes": [{"probability": "49/50", "target": "success"}, {"probability": "1/50", "target": "failure"}], "resident_bytes": 2147483648, "seconds": 8}], "start": "initial", "submitted_tasks": 1000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| terminal_paths | 6 |
| success_probability_exact | `"3117/3125"` |
| quality_and_deadline_probability_exact | `"109/125"` |
| expected_attempts_exact | `"156/125"` |
| expected_resources_per_submission | `{"cost": "91/6250", "seconds": "1438/125", "cpu_seconds": "422/125", "resident_byte_seconds": "3088081485824/125"}` |
| total_expected_cost_exact | `"364/25"` |
| expected_successes_exact | `"24936/25"` |
| cost_per_quality_success_exact | `"91/6234"` |
| cost_per_quality_and_deadline_success_exact | `"91/5450"` |

| 节点路径 | 终点 | 路径概率 | 全路径费用 | 时间秒 | CPU核秒 | 驻留bytes·s | 质量且按时 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| initial | success | 4/5 | 1/100 | 10 | 3 | 21474836480 | True |
| initial → repair | success | 9/125 | 2/125 | 14 | 4 | 30064771072 | True |
| initial → repair → upgrade | success | 147/3125 | 23/500 | 22 | 6 | 47244640256 | False |
| initial → repair → upgrade | failure | 3/3125 | 23/500 | 22 | 6 | 47244640256 | False |
| initial → upgrade | success | 49/625 | 1/25 | 18 | 5 | 38654705664 | False |
| initial → upgrade | failure | 1/625 | 1/25 | 18 | 5 | 38654705664 | False |

计量条件：

- 默认节点成本、时间、CPU和条件成功概率为假想教学输入；不是供应商报价、模型实测或失败后独立同分布的成功假设。输入概率明确条件于到达该节点，必要时将不同历史拆为不同节点。
- 有限无环图，success/failure为吸收终点。顺序尝试在结果可知后才进入下一节点，没有并行推测、超时中断、无限重试或自动重试到成功。不同路径到同节点的概率汇合，但路径时间与累计费用保留。
- 所有终点包含此前全部消耗，失败和超时成功费用不从分子删除；成功成本为预期费用/预期成功率，不是只取成功路径的条件平均费用。
- deadline仅作完成质量与时限的联合判定，不停止正在执行的节点。零成功分母返回null，不输出0费用或无穷可靠性。
- 节点seconds为含等待的完整阶段墙钟，cpu_seconds为独立累计核秒；resident_bytes在该阶段内恒定，按byte-seconds累加，跨节点不重复持有。共享页、进程峰值、转移/恢复与持久状态需要另给分段。
- 有限图期望资源不是生产稳态吞吐或扩容收益；到达突发、并发准入、队列、实际质量关联和副作用重放仍需真实记录。

固定来源：

