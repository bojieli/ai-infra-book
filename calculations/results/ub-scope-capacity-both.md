# UB 协作范围：当代 Qwen 教学计算

此结果是声明容量与串行通信路径预算，不是历史UB负载复原或端到端性能预测。

输入：`{"batch": 1, "capacity_bytes": 10608683008, "decode_steps": 32, "history": 8192, "local_bytes_per_second": 50000000000, "local_startup_ns": 2000, "model": "qwen3-32b", "remote_bytes_per_second": 25000000000, "remote_startup_ns": 5000, "workspace_bytes": 2147483648}`

| 候选 | 每机卡数×服务器 | 末步KV位置 | 最大逐卡bytes | 全卡容量通过 | 通信预算每前向ms | 全部前向ms |
|---|---|---:|---:|---|---:|---:|
| single_server_tp8 | 8×1 | 8224 | 10608683008 | True | 3.688869360 | 118.043819520 |
| two_servers_tp4_pp2 | 4×2 | 8224 | 10608011264 | True | 1.618383680 | 51.788277760 |

## 容量先于选择

比较标签只针对通信；任何逐卡容量不通过的候选不得据此选择。工作区是声明预留，尚非完整运行时峰值。

| 量 | 精确值 |
|---|---|
| comparison | `declared serial communication only; assumes both capacity-feasible` |
| remote_bandwidth_threshold_bytes_per_second_exact | `512050000000000/25901553` |
| bandwidth_threshold_relation | `two-server path is lower strictly above threshold` |
| remote_startup_threshold_seconds_exact | `26006071/25000000000` |
| startup_threshold_relation | `two-server path is lower strictly below threshold` |
| communication_only_preference | `two_servers_tp4_pp2` |
| both_capacity_feasible | `True` |

## single_server_tp8：逐卡与循环

| server/card | PP/TP | 权重bytes | KV bytes | workspace bytes | resident bytes | fit |
|---|---|---:|---:|---:|---:|---|
| 0/0 | 0/0 | 8191715328 | 269484032 | 2147483648 | 10608683008 | True |
| 0/1 | 0/1 | 8191715328 | 269484032 | 2147483648 | 10608683008 | True |
| 0/2 | 0/2 | 8191715328 | 269484032 | 2147483648 | 10608683008 | True |
| 0/3 | 0/3 | 8191715328 | 269484032 | 2147483648 | 10608683008 | True |
| 0/4 | 0/4 | 8191715328 | 269484032 | 2147483648 | 10608683008 | True |
| 0/5 | 0/5 | 8191715328 | 269484032 | 2147483648 | 10608683008 | True |
| 0/6 | 0/6 | 8191715328 | 269484032 | 2147483648 | 10608683008 | True |
| 0/7 | 0/7 | 8191715328 | 269484032 | 2147483648 | 10608683008 | True |

| 操作 | 层/阶段 | 服务接口 | 前向次数 | 每次启动轮 | 每次计费bytes | 所有前向秒（精确） |
|---|---|---|---:|---:|---:|---|
| vocabulary_embedding_reduce | None/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 0/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 0/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 1/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 1/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 2/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 2/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 3/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 3/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 4/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 4/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 5/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 5/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 6/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 6/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 7/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 7/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 8/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 8/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 9/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 9/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 10/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 10/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 11/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 11/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 12/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 12/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 13/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 13/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 14/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 14/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 15/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 15/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 16/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 16/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 17/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 17/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 18/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 18/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 19/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 19/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 20/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 20/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 21/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 21/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 22/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 22/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 23/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 23/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 24/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 24/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 25/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 25/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 26/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 26/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 27/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 27/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 28/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 28/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 29/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 29/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 30/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 30/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 31/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 31/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 32/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 32/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 33/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 33/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 34/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 34/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 35/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 35/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 36/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 36/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 37/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 37/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 38/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 38/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 39/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 39/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 40/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 40/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 41/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 41/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 42/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 42/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 43/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 43/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 44/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 44/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 45/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 45/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 46/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 46/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 47/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 47/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 48/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 48/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 49/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 49/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 50/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 50/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 51/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 51/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 52/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 52/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 53/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 53/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 54/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 54/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 55/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 55/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 56/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 56/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 57/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 57/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 58/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 58/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 59/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 59/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 60/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 60/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 61/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 61/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 62/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 62/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| attention_output_reduce | 63/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| ffn_output_reduce | 63/0 | independent_local_collective_edges | 32 | 14 | 17920 | 8862/9765625 |
| last_position_logits_all_gather | None/0 | independent_local_collective_edges | 32 | 7 | 531776 | 38493/48828125 |
| selected_token_first_stage_broadcast | None/0 | independent_local_collective_edges | 32 | 3 | 12 | 75003/390625000 |

## two_servers_tp4_pp2：逐卡与循环

| server/card | PP/TP | 权重bytes | KV bytes | workspace bytes | resident bytes | fit |
|---|---|---:|---:|---:|---:|---|
| 0/0 | 0/0 | 8191033344 | 269484032 | 2147483648 | 10608001024 | True |
| 0/1 | 0/1 | 8191033344 | 269484032 | 2147483648 | 10608001024 | True |
| 0/2 | 0/2 | 8191033344 | 269484032 | 2147483648 | 10608001024 | True |
| 0/3 | 0/3 | 8191033344 | 269484032 | 2147483648 | 10608001024 | True |
| 1/4 | 1/0 | 8191043584 | 269484032 | 2147483648 | 10608011264 | True |
| 1/5 | 1/1 | 8191043584 | 269484032 | 2147483648 | 10608011264 | True |
| 1/6 | 1/2 | 8191043584 | 269484032 | 2147483648 | 10608011264 | True |
| 1/7 | 1/3 | 8191043584 | 269484032 | 2147483648 | 10608011264 | True |

| 操作 | 层/阶段 | 服务接口 | 前向次数 | 每次启动轮 | 每次计费bytes | 所有前向秒（精确） |
|---|---|---|---:|---:|---:|---|
| vocabulary_embedding_reduce | None/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 0/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 0/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 1/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 1/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 2/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 2/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 3/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 3/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 4/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 4/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 5/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 5/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 6/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 6/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 7/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 7/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 8/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 8/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 9/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 9/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 10/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 10/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 11/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 11/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 12/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 12/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 13/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 13/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 14/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 14/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 15/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 15/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 16/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 16/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 17/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 17/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 18/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 18/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 19/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 19/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 20/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 20/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 21/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 21/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 22/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 22/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 23/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 23/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 24/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 24/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 25/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 25/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 26/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 26/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 27/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 27/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 28/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 28/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 29/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 29/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 30/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 30/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 31/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 31/0 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| pipeline_hidden_transfer | None/0 | shared_interserver_egress | 32 | 1 | 40960 | 4149/19531250 |
| attention_output_reduce | 32/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 32/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 33/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 33/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 34/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 34/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 35/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 35/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 36/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 36/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 37/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 37/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 38/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 38/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 39/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 39/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 40/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 40/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 41/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 41/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 42/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 42/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 43/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 43/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 44/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 44/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 45/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 45/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 46/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 46/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 47/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 47/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 48/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 48/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 49/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 49/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 50/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 50/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 51/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 51/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 52/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 52/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 53/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 53/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 54/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 54/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 55/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 55/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 56/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 56/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 57/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 57/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 58/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 58/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 59/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 59/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 60/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 60/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 61/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 61/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 62/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 62/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| attention_output_reduce | 63/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| ffn_output_reduce | 63/1 | independent_local_collective_edges | 32 | 6 | 15360 | 3846/9765625 |
| last_position_logits_all_gather | None/1 | independent_local_collective_edges | 32 | 3 | 455808 | 23619/48828125 |
| selected_token_to_first_stage | None/1 | shared_interserver_egress | 32 | 1 | 4 | 31251/195312500 |
| selected_token_first_stage_broadcast | None/0 | independent_local_collective_edges | 32 | 2 | 8 | 25001/195312500 |

## 条件与来源

- 同一固定官方当代Qwen3 Dense模型、相同8卡与请求量，单机TP8对双机TP4×PP2；现代模型仅是教学载荷，不代表UB研究开始时已知的需求或历史硬件配置。
- 作者回忆只支持研究早于2020年GPT-3转折、其后获得更大认可和投入的时间线；当年实际模型、接口有效带宽/启动与价格未知，本结果不据此替历史团队作定量结论。
- 逐卡复用dense-placement的BF16权重、真实GQA KV头归属及显式workspace；容量按最后一步history+decode_steps，未声称覆盖全部activation/allocator峰值。DP=1，8张卡均有独立容量检查。
- 逐次复用dense-communication完整声明图：词表embedding规约、每层attention/FFN规约、PP hidden、末位logits收集、所选token返回及首阶段广播。decode_steps是执行次数，预填充不混入此账。
- 每服务器内部TP环边独立；跨机只有一个声明共享出口，4份复制hidden按4倍载荷串行占用出口，随后token反馈另一次启动；不把4个rank发送当4条独立NIC带宽。
- 每个通信图按依赖顺序累加，仅是通信路径预算。计算、采样、排队、重叠、pipeline气泡与SLO未计，communication_only_preference不是模型总时延/吞吐最优决定；容量不合格时不据比较选择该方案。
- 启动按每collective轮/PP服务启动定义，带宽是显式单向有效服务条件，不引用宣传峰值；翻转阈值仅在此固定消息图、共享出口和服务假设下成立。

历史材料仅证明时间线：
- [../references/files/documents/ub-reflection.html](https://01.me/2025/09/a-story-of-unified-bus/) SHA-256 `9ed0f62950241537477bc05ad6ef917b6b31e5c0737a8bff02058449c0051419`

模型固定来源：
- [configs/models/qwen3-32b/config.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/config.json) SHA-256 `97e295b63283935788fac5e4f8860862a56d4089538cafc93f0431f2ebe483bb`
- [sources/qwen3-32b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/model.safetensors.index.json) SHA-256 `bed42c6c55274bc08a1f616bceb3bcb84b3f02cb6584c573bd18c6519291ecd0`
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py) SHA-256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py) SHA-256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`
