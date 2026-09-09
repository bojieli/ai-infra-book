# TP/EP 重配置迁移子账

范围：静止快照、BF16、PP=DP=1；资源下界不是实际运行时间，原 C52 完整部署成本尚未闭合。

## 输入

```json
{
  "model": "qwen3-8b",
  "source": {
    "tp": 4,
    "ep": 1,
    "devices": [
      "g0",
      "g1",
      "g2",
      "g3"
    ]
  },
  "target": {
    "tp": 4,
    "ep": 1,
    "devices": [
      "new0",
      "new1",
      "new2",
      "new3"
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
    "drain": 0,
    "group_setup": 2,
    "weight_repack": 0,
    "state_validation": 1,
    "compile_graph": 10,
    "atomic_cutover": 0,
    "replay_prefill": 3,
    "queue_clearance": 4,
    "local_materialization": null
  },
  "capacity_bytes_by_device": {
    "g3": 80000000000,
    "g1": 80000000000,
    "g2": 80000000000,
    "g0": 80000000000
  },
  "extra_live_bytes_by_device": {
    "g3": 2147483648,
    "g1": 2147483648,
    "g2": 2147483648,
    "g0": 2147483648
  },
  "amortization": {
    "extra_seconds": 10,
    "seconds_saved_per_step": "0.0002",
    "extra_cost": "0.1",
    "cost_saved_per_step": "0.00001"
  },
  "deployment_cost": {
    "currency": "hypothetical_credit",
    "terms": {
      "startup": [
        {
          "quantity": 16,
          "rate": "0.001",
          "unit": "GPU_seconds"
        }
      ],
      "steady_service": [
        {
          "quantity": 14400,
          "rate": "0.001",
          "unit": "GPU_seconds"
        }
      ],
      "routing_and_cache": [
        {
          "quantity": 3600,
          "rate": "0.0001",
          "unit": "service_seconds"
        }
      ],
      "migration": [
        {
          "quantity": 40,
          "rate": "0.001",
          "unit": "GPU_seconds"
        }
      ],
      "warm_overlap": [
        {
          "quantity": 40,
          "rate": "0.001",
          "unit": "GPU_seconds"
        }
      ],
      "recovery_and_replay": [
        {
          "quantity": 16,
          "rate": "0.001",
          "unit": "GPU_seconds"
        }
      ],
      "failed_attempts": [
        {
          "quantity": 2,
          "rate": "0.01",
          "unit": "attempts"
        }
      ],
      "backlog_clearance": [
        {
          "quantity": 16,
          "rate": "0.001",
          "unit": "GPU_seconds"
        }
      ],
      "network_storage": [
        {
          "quantity": 100,
          "rate": "0.001",
          "unit": "declared_GB"
        }
      ],
      "host_control_plane": [
        {
          "quantity": 3600,
          "rate": "0.0001",
          "unit": "host_seconds"
        }
      ]
    },
    "slo_valid_completed_requests": 1000
  },
  "annotation": "All rates, capacities, runtime, cost and savings are declared teaching inputs. State identity is an assumption, not checked by an engine.",
  "state_policy": "replay"
}
```

## 载荷与本地物化

| 类别 | 本地源 bytes | 网络 bytes |
| --- | ---: | ---: |
| weight | 0 | 16383320064 |
| kv | 0 | 0 |
| auxiliary | 0 | 4096 |

本地源仍创建目标缓冲；不假设零复制别名。读写接口为本地载荷的两倍。

## 逐卡容量

| 设备 | 旧 bytes | 目标 bytes | 保留旧缓冲时峰值 bytes | 声明容量 bytes | 可容纳 |
| --- | ---: | ---: | ---: | ---: | --- |
| g0 | 4699810816 | 0 | 6847294464 | 80000000000 | True |
| g1 | 4699810816 | 0 | 6847294464 | 80000000000 | True |
| g2 | 4699810816 | 0 | 6847294464 | 80000000000 | True |
| g3 | 4699810816 | 0 | 6847294464 | 80000000000 | True |
| new0 | 0 | 4699810816 | 4699810816 | 未知 | 未知 |
| new1 | 0 | 4699810816 | 4699810816 | 未知 | 未知 |
| new2 | 0 | 4699810816 | 4699810816 | 未知 | 未知 |
| new3 | 0 | 4699810816 | 4699810816 | 未知 | 未知 |

## 资源下界与声明时间

以下秒数为精确有理数。缺项保持未知；即使容量合格，也不推出切换可达、SLO合格或恢复成功。

| 字段 | 值 |
| --- | --- |
| fabric_bytes_per_second | 6399736/390625 |
| sender_bytes_per_second | 16006564/390625 |
| receiver_bytes_per_second | 1599934/78125 |
| network_bytes | 16383324160 |
| transfer_lower_bound_exact_seconds | 16006564/390625 |
| partial_known_transfer_bound_exact_seconds | 16006564/390625 |
| missing_runtime_terms | ['local_materialization'] |
| known_serial_runtime_seconds_exact | 20 |
| conditional_serial_switch_lower_bound_exact_seconds | 未知 |
| supplied_network_transfer_seconds_exact | 未知 |
| declared_serial_switch_seconds_exact | 未知 |
| local_materialization_read_write_bytes | 0 |
| all_declared_capacities_fit | 未知 |
| measured_switch_seconds | 未知 |
| predicted_end_to_end_seconds | 未知 |

## 传输端点汇总

每个目标坐标只选一个源，优先同卡，再按设备名字排序。完整 tensor/axis 坐标保留在 JSON；这不是最优链路调度。

| 类别 | 源 | 目标 | 本地 | bytes |
| --- | --- | --- | --- | ---: |
| auxiliary | g0 | new0 | False | 1024 |
| auxiliary | g1 | new1 | False | 1024 |
| auxiliary | g2 | new2 | False | 1024 |
| auxiliary | g3 | new3 | False | 1024 |
| weight | g0 | new0 | False | 4095830016 |
| weight | g0 | new1 | False | 616448 |
| weight | g0 | new2 | False | 616448 |
| weight | g0 | new3 | False | 616448 |
| weight | g1 | new1 | False | 4095213568 |
| weight | g2 | new2 | False | 4095213568 |
| weight | g3 | new3 | False | 4095213568 |

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
    "status": "conditional",
    "continuous_steps_exact": "10000",
    "break_even_steps": 10000,
    "strictly_better_steps": 10001,
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
    "startup": "2/125",
    "steady_service": "72/5",
    "routing_and_cache": "9/25",
    "migration": "1/25",
    "warm_overlap": "1/25",
    "recovery_and_replay": "2/125",
    "failed_attempts": "1/50",
    "backlog_clearance": "2/125",
    "network_storage": "1/10",
    "host_control_plane": "9/25"
  },
  "known_subtotal_exact": "1921/125",
  "missing_terms": [],
  "full_declared_cost_exact": "1921/125",
  "cost_per_slo_valid_request_exact": "1921/125000",
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
    "file": "configs/models/qwen3-8b/config.json",
    "url": "https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json",
    "revision": "b968826d9c46dd6066d109eabc6255188de91218",
    "sha256": "f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30"
  },
  {
    "file": "sources/qwen3-8b/model.safetensors.index.json",
    "url": "https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json",
    "revision": "b968826d9c46dd6066d109eabc6255188de91218",
    "sha256": "f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc"
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
