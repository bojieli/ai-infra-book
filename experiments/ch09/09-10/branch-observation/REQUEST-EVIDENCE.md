# 首完成请求：原始事件索引

每个索引是对应 JSONL 的 PID / seq；seq 从1递增，也等于该文件行号。单调时钟仅在远端事件之间比较。

## 0-native-1 / native-0

| 阶段 | PID / seq | monotonic_ns | 源码行 / 值 |
|---|---|---:|---|
| rate return | 2573055 / 103 | 1128569192416120 | prefetch_rate_limited:1032 / `false` |
| prefetch return | 2573055 / 131 | 1128569192902887 | prefetch_from_storage:1521 / `true` |
| progress final | 2573055 / 5377 | 1128569438696194 | check_prefetch_progress:1412 / `false` |
| pop return | 2573055 / 5384 | 1128569438921697 | pop_prefetch_loaded_tokens:1429 / `1024` |
| prefill call | 2573055 / 5465 | 1128569451104463 | prepare_for_extend:1896 / `{"rid":"native-0","host_hit_length":1008,"storage_hit_length":1024,"extend_input_len":16,"cached_tokens":0,"cached_tokens_device":0,"cached_tokens_host":0,"cached_tokens_storage":0,"already_computed":0,"prefix_indices_len":1008,"output_ids_len":0}` |

API meta_info.id=`native-0`，cached_tokens=1008，end_s换算ns=1128571904914490。

## 0-native-8 / native-4

| 阶段 | PID / seq | monotonic_ns | 源码行 / 值 |
|---|---|---:|---|
| rate return | 2583040 / 1000 | 1128602182200643 | prefetch_rate_limited:1030 / `true` |
| prefetch return | 2583040 / 1003 | 1128602182278316 | prefetch_from_storage:1485 / `false` |
| progress final | 2583040 / 2000 | 1128602226699649 | check_prefetch_progress:1361 / `false` |
| pop return | 2583040 / 2014 | 1128602227240048 | pop_prefetch_loaded_tokens:1429 / `0` |
| prefill call | 2583040 / 2170 | 1128602234040267 | prepare_for_extend:1896 / `{"rid":"native-4","host_hit_length":0,"storage_hit_length":0,"extend_input_len":1024,"cached_tokens":0,"cached_tokens_device":0,"cached_tokens_host":0,"cached_tokens_storage":0,"already_computed":0,"prefix_indices_len":0,"output_ids_len":0}` |

API meta_info.id=`native-4`，cached_tokens=0，end_s换算ns=1128604300880070。

## 1-native-8 / native-4

| 阶段 | PID / seq | monotonic_ns | 源码行 / 值 |
|---|---|---:|---|
| rate return | 2591726 / 1353 | 1128632828538126 | prefetch_rate_limited:1030 / `true` |
| prefetch return | 2591726 / 1356 | 1128632828627023 | prefetch_from_storage:1485 / `false` |
| progress final | 2591726 / 2179 | 1128632860749369 | check_prefetch_progress:1361 / `false` |
| pop return | 2591726 / 2186 | 1128632860846690 | pop_prefetch_loaded_tokens:1429 / `0` |
| prefill call | 2591726 / 2264 | 1128632862116456 | prepare_for_extend:1896 / `{"rid":"native-4","host_hit_length":0,"storage_hit_length":0,"extend_input_len":1024,"cached_tokens":0,"cached_tokens_device":0,"cached_tokens_host":0,"cached_tokens_storage":0,"already_computed":0,"prefix_indices_len":0,"output_ids_len":0}` |

API meta_info.id=`native-4`，cached_tokens=0，end_s换算ns=1128634782296128。

## 1-native-1 / native-0

| 阶段 | PID / seq | monotonic_ns | 源码行 / 值 |
|---|---|---:|---|
| rate return | 2593889 / 103 | 1128662336285127 | prefetch_rate_limited:1032 / `false` |
| prefetch return | 2593889 / 137 | 1128662337707731 | prefetch_from_storage:1521 / `true` |
| progress final | 2593889 / 5310 | 1128662565786785 | check_prefetch_progress:1412 / `false` |
| pop return | 2593889 / 5317 | 1128662565995296 | pop_prefetch_loaded_tokens:1429 / `1024` |
| prefill call | 2593889 / 5398 | 1128662576842217 | prepare_for_extend:1896 / `{"rid":"native-0","host_hit_length":1008,"storage_hit_length":1024,"extend_input_len":16,"cached_tokens":0,"cached_tokens_device":0,"cached_tokens_host":0,"cached_tokens_storage":0,"already_computed":0,"prefix_indices_len":1008,"output_ids_len":0}` |

API meta_info.id=`native-0`，cached_tokens=1008，end_s换算ns=1128664668926771。

