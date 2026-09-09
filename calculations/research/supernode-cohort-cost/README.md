# 实验6-10：同请求集合的超节点条件比较候选

同总8卡，比较TP8单副本、TP4两副本、TP2四副本。54组场景改变真实Dense模型、同步到达请求数、完整响应deadline及故障恢复条件。最低75%请求按时完成后，才比较包含失败和重做的总费用/有效请求。

所有阶段服务时长、24GB每卡/2GiB工作区、信用费率和确定故障事件都是教学假设。逐卡参数/KV来自官方配置；不是实测吞吐、现价或可靠性推荐。

[图6-9候选](figure-6-9.svg)从完整响应记录生成整数deadline的精确阶梯，仅绘健康/长恢复两个条件；短恢复另在下表。空段表示容量/SLO条件不满足。

| 模型 | 请求 | deadline ms | 故障条件 | 可选部署 | 最小cost/有效请求 |
|---|---:|---:|---|---|---:|
| qwen3-8b | 1 | 80 | healthy | tp8-replicas1 | 62/125 |
| qwen3-8b | 1 | 80 | short | 无 | None |
| qwen3-8b | 1 | 80 | long | 无 | None |
| qwen3-8b | 1 | 250 | healthy | tp8-replicas1 | 62/125 |
| qwen3-8b | 1 | 250 | short | tp8-replicas1 | 132/125 |
| qwen3-8b | 1 | 250 | long | 无 | None |
| qwen3-8b | 1 | 600 | healthy | tp8-replicas1 | 62/125 |
| qwen3-8b | 1 | 600 | short | tp8-replicas1 | 132/125 |
| qwen3-8b | 1 | 600 | long | tp8-replicas1 | 437/125 |
| qwen3-8b | 4 | 80 | healthy | 无 | None |
| qwen3-8b | 4 | 80 | short | 无 | None |
| qwen3-8b | 4 | 80 | long | 无 | None |
| qwen3-8b | 4 | 250 | healthy | tp2-replicas4 | 8/25 |
| qwen3-8b | 4 | 250 | short | tp2-replicas4 | 23/50 |
| qwen3-8b | 4 | 250 | long | tp2-replicas4 | 107/75 |
| qwen3-8b | 4 | 600 | healthy | tp2-replicas4 | 8/25 |
| qwen3-8b | 4 | 600 | short | tp2-replicas4 | 23/50 |
| qwen3-8b | 4 | 600 | long | tp2-replicas4 | 107/100 |
| qwen3-8b | 8 | 80 | healthy | 无 | None |
| qwen3-8b | 8 | 80 | short | 无 | None |
| qwen3-8b | 8 | 80 | long | 无 | None |
| qwen3-8b | 8 | 250 | healthy | 无 | None |
| qwen3-8b | 8 | 250 | short | 无 | None |
| qwen3-8b | 8 | 250 | long | 无 | None |
| qwen3-8b | 8 | 600 | healthy | tp2-replicas4 | 8/25 |
| qwen3-8b | 8 | 600 | short | tp2-replicas4 | 39/100 |
| qwen3-8b | 8 | 600 | long | tp2-replicas4 | 139/200 |
| qwen3-32b | 1 | 80 | healthy | 无 | None |
| qwen3-32b | 1 | 80 | short | 无 | None |
| qwen3-32b | 1 | 80 | long | 无 | None |
| qwen3-32b | 1 | 250 | healthy | tp8-replicas1 | 124/125 |
| qwen3-32b | 1 | 250 | short | tp8-replicas1 | 194/125 |
| qwen3-32b | 1 | 250 | long | 无 | None |
| qwen3-32b | 1 | 600 | healthy | tp8-replicas1 | 124/125 |
| qwen3-32b | 1 | 600 | short | tp8-replicas1 | 194/125 |
| qwen3-32b | 1 | 600 | long | tp8-replicas1 | 499/125 |
| qwen3-32b | 4 | 80 | healthy | 无 | None |
| qwen3-32b | 4 | 80 | short | 无 | None |
| qwen3-32b | 4 | 80 | long | 无 | None |
| qwen3-32b | 4 | 250 | healthy | 无 | None |
| qwen3-32b | 4 | 250 | short | 无 | None |
| qwen3-32b | 4 | 250 | long | 无 | None |
| qwen3-32b | 4 | 600 | healthy | tp4-replicas2 | 4/5 |
| qwen3-32b | 4 | 600 | short | tp4-replicas2 | 47/50 |
| qwen3-32b | 4 | 600 | long | tp4-replicas2 | 31/15 |
| qwen3-32b | 8 | 80 | healthy | 无 | None |
| qwen3-32b | 8 | 80 | short | 无 | None |
| qwen3-32b | 8 | 80 | long | 无 | None |
| qwen3-32b | 8 | 250 | healthy | 无 | None |
| qwen3-32b | 8 | 250 | short | 无 | None |
| qwen3-32b | 8 | 250 | long | 无 | None |
| qwen3-32b | 8 | 600 | healthy | tp4-replicas2 | 16/15 |
| qwen3-32b | 8 | 600 | short | 无 | None |
| qwen3-32b | 8 | 600 | long | 无 | None |

每请求prefill产生首输出，G−1次decode追加，响应全量完成才提交。故障打断请求时整次重启；已完成阶段的浪费矩阵量单列，部分阶段工作未知，不能按耗时比例伪造FLOPs。健康副本按原队列继续，无重路由。

成本中8卡预留×cohort结束时间已包含闲置/失败/恢复/重做；额外recovery_fee只是外部服务费，不能重复收同一GPU时段。整个候选未通过必要容量时，不给服务/成本排名。

读取[计算脚本](calculate.py)、[完整结果](result.json)及[逐点数据](curve-data.json)。公共CLI/固定场景/正文与统一图校验仍待接入；不据研究候选勾选C36。
