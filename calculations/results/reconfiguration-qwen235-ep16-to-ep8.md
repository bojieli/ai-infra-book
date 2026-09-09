# TP/EP 重配置迁移子账

范围：静止快照、BF16、PP=DP=1；资源下界不是实际运行时间，原 C52 完整部署成本尚未闭合。

## 输入

```json
{
  "model": "qwen3-235b-a22b",
  "source": {
    "tp": 1,
    "ep": 16,
    "devices": [
      "g0",
      "g1",
      "g2",
      "g3",
      "g4",
      "g5",
      "g6",
      "g7",
      "g8",
      "g9",
      "g10",
      "g11",
      "g12",
      "g13",
      "g14",
      "g15"
    ]
  },
  "target": {
    "tp": 1,
    "ep": 8,
    "devices": [
      "g0",
      "g1",
      "g2",
      "g3",
      "g4",
      "g5",
      "g6",
      "g7"
    ]
  },
  "batch": 2,
  "history": 8192,
  "state_identity_verified": true,
  "bandwidth": {
    "fabric_bytes_per_second": 1000000000,
    "sender_bytes_per_second": 100000000,
    "receiver_bytes_per_second": 200000000
  },
  "auxiliary_state_bytes": 4096,
  "same_weight_version": true,
  "runtime_seconds": {
    "drain": null,
    "group_setup": null,
    "weight_repack": null,
    "state_validation": null,
    "compile_graph": null,
    "atomic_cutover": null,
    "replay_prefill": null,
    "queue_clearance": null,
    "local_materialization": null
  },
  "capacity_bytes_by_device": {
    "g15": 80000000000,
    "g10": 80000000000,
    "g5": 80000000000,
    "g8": 80000000000,
    "g13": 80000000000,
    "g14": 80000000000,
    "g7": 80000000000,
    "g3": 80000000000,
    "g0": 80000000000,
    "g12": 80000000000,
    "g9": 80000000000,
    "g1": 80000000000,
    "g2": 80000000000,
    "g11": 80000000000,
    "g6": 80000000000,
    "g4": 80000000000
  },
  "extra_live_bytes_by_device": {
    "g15": 2147483648,
    "g10": 2147483648,
    "g5": 2147483648,
    "g8": 2147483648,
    "g13": 2147483648,
    "g14": 2147483648,
    "g7": 2147483648,
    "g3": 2147483648,
    "g0": 2147483648,
    "g12": 2147483648,
    "g9": 2147483648,
    "g1": 2147483648,
    "g2": 2147483648,
    "g11": 2147483648,
    "g6": 2147483648,
    "g4": 2147483648
  },
  "amortization": {
    "extra_seconds": 10,
    "seconds_saved_per_step": "0.0002",
    "extra_cost": null,
    "cost_saved_per_step": null
  },
  "deployment_cost": {
    "currency": "hypothetical_credit",
    "terms": {
      "startup": null,
      "steady_service": null,
      "routing_and_cache": null,
      "migration": null,
      "warm_overlap": null,
      "recovery_and_replay": null,
      "failed_attempts": null,
      "backlog_clearance": null,
      "network_storage": null,
      "host_control_plane": null
    },
    "slo_valid_completed_requests": null
  },
  "annotation": "All rates, capacities, runtime, cost and savings are declared teaching inputs. State identity is an assumption, not checked by an engine."
}
```

## 载荷与本地物化

| 类别 | 本地源 bytes | 网络 bytes |
| --- | ---: | ---: |
| weight | 156342870016 | 425805742080 |
| kv | 25232932864 | 0 |
| auxiliary | 256 | 3840 |

本地源仍创建目标缓冲；不假设零复制别名。读写接口为本地载荷的两倍。

## 逐卡容量

| 设备 | 旧 bytes | 目标 bytes | 保留旧缓冲时峰值 bytes | 声明容量 bytes | 可容纳 |
| --- | ---: | ---: | ---: | ---: | --- |
| g0 | 47535643904 | 75922693632 | 125605821184 | 80000000000 | False |
| g1 | 47535643904 | 75922693632 | 125605821184 | 80000000000 | False |
| g10 | 47535643904 | 0 | 49683127552 | 80000000000 | True |
| g11 | 47535643904 | 0 | 49683127552 | 80000000000 | True |
| g12 | 47535643904 | 0 | 49683127552 | 80000000000 | True |
| g13 | 47535643904 | 0 | 49683127552 | 80000000000 | True |
| g14 | 47535643904 | 0 | 49683127552 | 80000000000 | True |
| g15 | 47535643904 | 0 | 49683127552 | 80000000000 | True |
| g2 | 47535643904 | 75922693632 | 125605821184 | 80000000000 | False |
| g3 | 47535643904 | 75922693632 | 125605821184 | 80000000000 | False |
| g4 | 47535643904 | 75922693632 | 125605821184 | 80000000000 | False |
| g5 | 47535643904 | 75922693632 | 125605821184 | 80000000000 | False |
| g6 | 47535643904 | 75922693632 | 125605821184 | 80000000000 | False |
| g7 | 47535643904 | 75922693632 | 125605821184 | 80000000000 | False |
| g8 | 47535643904 | 0 | 49683127552 | 80000000000 | True |
| g9 | 47535643904 | 0 | 49683127552 | 80000000000 | True |

## 资源下界与声明时间

以下秒数为精确有理数。缺项保持未知；即使容量合格，也不推出切换可达、SLO合格或恢复成功。

| 字段 | 值 |
| --- | --- |
| fabric_bytes_per_second | 332660739/781250 |
| sender_bytes_per_second | 110886913/390625 |
| receiver_bytes_per_second | 110886913/390625 |
| network_bytes | 425805745920 |
| transfer_lower_bound_exact_seconds | 332660739/781250 |
| partial_known_transfer_bound_exact_seconds | 332660739/781250 |
| missing_runtime_terms | ['local_materialization', 'drain', 'group_setup', 'weight_repack', 'state_validation', 'compile_graph', 'atomic_cutover', 'replay_prefill', 'queue_clearance'] |
| known_serial_runtime_seconds_exact | 0 |
| conditional_serial_switch_lower_bound_exact_seconds | 未知 |
| supplied_network_transfer_seconds_exact | 未知 |
| declared_serial_switch_seconds_exact | 未知 |
| local_materialization_read_write_bytes | 363151606272 |
| all_declared_capacities_fit | False |
| measured_switch_seconds | 未知 |
| predicted_end_to_end_seconds | 未知 |

## 传输端点汇总

每个目标坐标只选一个源，优先同卡，再按设备名字排序。完整 tensor/axis 坐标保留在 JSON；这不是最优链路调度。

| 类别 | 源 | 目标 | 本地 | bytes |
| --- | --- | --- | --- | ---: |
| auxiliary | g0 | g0 | True | 256 |
| auxiliary | g1 | g0 | False | 256 |
| auxiliary | g10 | g5 | False | 256 |
| auxiliary | g11 | g5 | False | 256 |
| auxiliary | g12 | g6 | False | 256 |
| auxiliary | g13 | g6 | False | 256 |
| auxiliary | g14 | g7 | False | 256 |
| auxiliary | g15 | g7 | False | 256 |
| auxiliary | g2 | g1 | False | 256 |
| auxiliary | g3 | g1 | False | 256 |
| auxiliary | g4 | g2 | False | 256 |
| auxiliary | g5 | g2 | False | 256 |
| auxiliary | g6 | g3 | False | 256 |
| auxiliary | g7 | g3 | False | 256 |
| auxiliary | g8 | g4 | False | 256 |
| auxiliary | g9 | g4 | False | 256 |
| kv | g0 | g0 | True | 3154116608 |
| kv | g1 | g1 | True | 3154116608 |
| kv | g2 | g2 | True | 3154116608 |
| kv | g3 | g3 | True | 3154116608 |
| kv | g4 | g4 | True | 3154116608 |
| kv | g5 | g5 | True | 3154116608 |
| kv | g6 | g6 | True | 3154116608 |
| kv | g7 | g7 | True | 3154116608 |
| weight | g0 | g0 | True | 44381527040 |
| weight | g1 | g0 | False | 28387049472 |
| weight | g1 | g1 | True | 15994477568 |
| weight | g10 | g5 | False | 28387049472 |
| weight | g11 | g5 | False | 28387049472 |
| weight | g12 | g6 | False | 28387049472 |
| weight | g13 | g6 | False | 28387049472 |
| weight | g14 | g7 | False | 28387049472 |
| weight | g15 | g7 | False | 28387049472 |
| weight | g2 | g1 | False | 28387049472 |
| weight | g2 | g2 | True | 15994477568 |
| weight | g3 | g1 | False | 28387049472 |
| weight | g3 | g3 | True | 15994477568 |
| weight | g4 | g2 | False | 28387049472 |
| weight | g4 | g4 | True | 15994477568 |
| weight | g5 | g2 | False | 28387049472 |
| weight | g5 | g5 | True | 15994477568 |
| weight | g6 | g3 | False | 28387049472 |
| weight | g6 | g6 | True | 15994477568 |
| weight | g7 | g3 | False | 28387049472 |
| weight | g7 | g7 | True | 15994477568 |
| weight | g8 | g4 | False | 28387049472 |
| weight | g9 | g4 | False | 28387049472 |

## 条件摊销与剩余步数

```json
{
  "time": {
    "status": "conditional",
    "continuous_steps_exact": "50000",
    "break_even_steps": 50000,
    "strictly_better_steps": 50001,
    "remaining_steps": null,
    "strictly_better_within_horizon": null,
    "scope": "Caller incremental overhead and equal-work per-step saving; independent of unmeasured switch latency. Capacity and SLO feasibility must be checked separately."
  },
  "money": {
    "status": "missing_input",
    "break_even_steps": null,
    "strictly_better_steps": null,
    "remaining_steps": null,
    "strictly_better_within_horizon": null,
    "scope": "Caller incremental overhead and equal-work per-step saving; independent of unmeasured switch latency. Capacity and SLO feasibility must be checked separately."
  }
}
```

## 声明生命周期费用

```json
{
  "currency": "hypothetical_credit",
  "subtotals_exact": {
    "startup": null,
    "steady_service": null,
    "routing_and_cache": null,
    "migration": null,
    "warm_overlap": null,
    "recovery_and_replay": null,
    "failed_attempts": null,
    "backlog_clearance": null,
    "network_storage": null,
    "host_control_plane": null
  },
  "known_subtotal_exact": "0",
  "missing_terms": [
    "startup",
    "steady_service",
    "routing_and_cache",
    "migration",
    "warm_overlap",
    "recovery_and_replay",
    "failed_attempts",
    "backlog_clearance",
    "network_storage",
    "host_control_plane"
  ],
  "full_declared_cost_exact": null,
  "cost_per_slo_valid_request_exact": null,
  "observed_or_measured": false
}
```

## 假设与未闭合项

- One inference TP×EP group, PP=DP=1. EP owns contiguous quotient/remainder expert IDs; nonexpert weights and the SAME request KV replicate across EP groups. No independent EP request batches inferred.
- BF16 full weights and BF16 GQA KV; all routed experts included. TP follows dense_placement axes, whole KV heads replicate when TP exceeds KV heads. Router/norm weights replicate.
- Same layer/head/token/position/model-version/format identities are caller-verified assertions, not engine validation. Auxiliary bytes describe caller-defined flat immutable snapshot state, not inferred optimizer/WAL contents.
- Direct unicast selects a local source then first device lexicographically; source replicas are not double counted. Byte intervals on sharding axes are logical rectangles; column slices require packing, not contiguous file reads.
- Snapshot is quiescent. No background mutation, dirty KV chase, automatic retry or failed-source reconstruction. Replay transfers no old KV but target KV capacity remains budgeted; replay/token-log availability and time must be supplied.
- Same-card local_bytes means destination materialization from a local source, not zero-copy retained buffers. Its read+write interfaces are reported; local_materialization time is separately required. Partial tensor aliases are not assumed.
- Bandwidths are hypothetical effective aggregate fabric and per-device rates. Maximum resource bound is necessary only; known serial runtime sum is a declared schedule, not measured readiness or SLO.
- Peak uses old+fully materialized target+declared extras per physical device, with old buffers held until release. Extra graph/workspace/allocator/transfer scratch require caller budgeting; fit is only for declared allocations.
- Cost ledger includes all declared lifecycle terms and extra categories; unknown terms stay null. Quantities/rates, SLO counts and per-step savings are teaching inputs, not measured data or prices. Categories must be disjoint to avoid double charging.

## 固定官方来源

```json
[
  {
    "file": "configs/models/qwen3-235b-a22b/config.json",
    "url": "https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json",
    "revision": "8efa61729e24bd65b1d152b5ab5409052aa80e65",
    "sha256": "0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4"
  },
  {
    "file": "sources/qwen3-235b-a22b/model.safetensors.index.json",
    "url": "https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json",
    "revision": "8efa61729e24bd65b1d152b5ab5409052aa80e65",
    "sha256": "53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78"
  },
  {
    "file": "sources/qwen3/modeling_qwen3.py",
    "url": "https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py",
    "revision": "0720e206c6ba28887e4d60ef60a6a089f6c1cc76",
    "sha256": "704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2"
  },
  {
    "file": "sources/qwen3/modeling_qwen3_moe.py",
    "url": "https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py",
    "revision": "0720e206c6ba28887e4d60ef60a6a089f6c1cc76",
    "sha256": "3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8"
  }
]
```
