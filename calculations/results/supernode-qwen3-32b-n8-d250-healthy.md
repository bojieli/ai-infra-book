# 超节点规模：同请求集合、故障、SLO与费用

```json
{
  "model": "qwen3-32b",
  "requests": 8,
  "prompt": 256,
  "outputs": 8,
  "deadline_ms": 250,
  "fault_at_ms": null,
  "recovery_ms": 0,
  "recovery_fee": "0",
  "minimum_valid_fraction": "3/4"
}
```

| 部署 | 容量通过 | SLO有效数 | 完成ms | 全部声明费用 | 每有效请求费用 | 可选 |
|---|---|---:|---:|---:|---:|---|
| tp8-replicas1 | True | 2 | 992 | 992/125 | 496/125 | False |
| tp4-replicas2 | True | 2 | 800 | 32/5 | 16/5 | False |
| tp2-replicas4 | False | None | None | None | None | False |

选择：`{"required_valid_requests": 6, "eligible": [], "minimum_cost_per_valid_request_exact": null, "winners": []}`

| 部署 | 请求 | 副本 | 完成ms | 尝试次数 |
|---|---:|---:|---:|---:|
| tp8-replicas1 | 0 | 0 | 124 | 1 |
| tp8-replicas1 | 1 | 0 | 248 | 1 |
| tp8-replicas1 | 2 | 0 | 372 | 1 |
| tp8-replicas1 | 3 | 0 | 496 | 1 |
| tp8-replicas1 | 4 | 0 | 620 | 1 |
| tp8-replicas1 | 5 | 0 | 744 | 1 |
| tp8-replicas1 | 6 | 0 | 868 | 1 |
| tp8-replicas1 | 7 | 0 | 992 | 1 |
| tp4-replicas2 | 0 | 0 | 200 | 1 |
| tp4-replicas2 | 1 | 1 | 200 | 1 |
| tp4-replicas2 | 2 | 0 | 400 | 1 |
| tp4-replicas2 | 3 | 1 | 400 | 1 |
| tp4-replicas2 | 4 | 0 | 600 | 1 |
| tp4-replicas2 | 5 | 1 | 600 | 1 |
| tp4-replicas2 | 6 | 0 | 800 | 1 |
| tp4-replicas2 | 7 | 1 | 800 | 1 |

同一批requests在t=0到达，相同模型/P/G，静态轮转到服务副本，每副本一次服务一个请求；并发是到达cohort大小，不是tensor batch。全部8卡及全部副本始终预留至cohort完成。
TP8单副本、TP4两副本、TP2四副本均总8卡。每卡24GB与2GiBworkspace为教学预算；真实BF16权重/KV/头归属来自公共适配器，队列不保留已算KV，活跃batch=1。必要容量通过不是运行峰值证明。
prefill产生首输出，之后G−1次decode；最终KV是P+G−1。阶段矩阵工作来自真实模型，声明服务毫秒并非用FLOPs/峰值推算。32B服务倍率2是独立教学假设，不是实测比例。
故障仅影响包含物理卡0的整个服务副本；其他副本按原队列继续。正在运行的请求全量重启，不迁移、不保留KV，也不复用已算token；已完整完成请求不重启，完成与故障同刻时先提交完成。
服务成功只指声明计算cohort完成；无模型输出质量实验。SLO是原始arrival至完整响应的deadline，最低有效比例由输入声明，不把TTFT或流式部分输出混入分母。
恢复停机长度是输入，期间受影响副本无服务。已完成但放弃的阶段FLOPs分列，故障打断阶段的工作未知，绝不按耗时比例推FLOPs。源权重可恢复性、checkpoint加载/重放细节未模拟。
费用按8卡×cohort结束毫秒×1/1000声明credit，含闲置、失败、恢复和重做卡时；recovery_fee仅额外外部服务费，不再收同一GPU时段。其他费用在本教学边界显式设零，非真实TCO或现价。
仅在必要容量及最低SLO有效比例都满足时，按包含所有失败/超时工作的总费用除有效请求数比较，保留持平和无可行候选。图/扫描的选择都以这些假设为条件。

```json
{
  "calculation": "supernode-cohort-cost",
  "scenario": {
    "model": "qwen3-32b",
    "requests": 8,
    "prompt": 256,
    "outputs": 8,
    "deadline_ms": 250,
    "fault_at_ms": null,
    "recovery_ms": 0,
    "recovery_fee": "0",
    "minimum_valid_fraction": "3/4"
  },
  "sources": [
    {
      "file": "configs/models/qwen3-32b/config.json",
      "url": "https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/config.json",
      "revision": "9216db5781bf21249d130ec9da846c4624c16137",
      "sha256": "97e295b63283935788fac5e4f8860862a56d4089538cafc93f0431f2ebe483bb"
    },
    {
      "file": "sources/qwen3-32b/model.safetensors.index.json",
      "url": "https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/model.safetensors.index.json",
      "revision": "9216db5781bf21249d130ec9da846c4624c16137",
      "sha256": "bed42c6c55274bc08a1f616bceb3bcb84b3f02cb6584c573bd18c6519291ecd0"
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
  ],
  "stages": [
    {
      "name": "prefill",
      "matrix_flops": 16047822077952
    },
    {
      "name": "decode0",
      "matrix_flops": 64506036224
    },
    {
      "name": "decode1",
      "matrix_flops": 64508133376
    },
    {
      "name": "decode2",
      "matrix_flops": 64510230528
    },
    {
      "name": "decode3",
      "matrix_flops": 64512327680
    },
    {
      "name": "decode4",
      "matrix_flops": 64514424832
    },
    {
      "name": "decode5",
      "matrix_flops": 64516521984
    },
    {
      "name": "decode6",
      "matrix_flops": 64518619136
    }
  ],
  "candidates": [
    {
      "id": "tp8-replicas1",
      "tp": 8,
      "replicas": 1,
      "total_cards": 8,
      "per_card_capacity_bytes": 24000000000,
      "placement_cards": [
        {
          "replica": 0,
          "tp_rank": 0,
          "weight_bytes": 8191715328,
          "kv_bytes": 8617984,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10347816960,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 1,
          "weight_bytes": 8191715328,
          "kv_bytes": 8617984,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10347816960,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 2,
          "weight_bytes": 8191715328,
          "kv_bytes": 8617984,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10347816960,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 3,
          "weight_bytes": 8191715328,
          "kv_bytes": 8617984,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10347816960,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 4,
          "weight_bytes": 8191715328,
          "kv_bytes": 8617984,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10347816960,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 5,
          "weight_bytes": 8191715328,
          "kv_bytes": 8617984,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10347816960,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 6,
          "weight_bytes": 8191715328,
          "kv_bytes": 8617984,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10347816960,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 7,
          "weight_bytes": 8191715328,
          "kv_bytes": 8617984,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10347816960,
          "fits_declared_budget": true
        }
      ],
      "capacity_fits": true,
      "declared_stage_durations_ms": [
        40,
        12,
        12,
        12,
        12,
        12,
        12,
        12
      ],
      "schedule": {
        "requests": [
          {
            "request": 0,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 124,
            "latency_ms": 124,
            "attempts": 1
          },
          {
            "request": 1,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 248,
            "latency_ms": 248,
            "attempts": 1
          },
          {
            "request": 2,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 372,
            "latency_ms": 372,
            "attempts": 1
          },
          {
            "request": 3,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 496,
            "latency_ms": 496,
            "attempts": 1
          },
          {
            "request": 4,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 620,
            "latency_ms": 620,
            "attempts": 1
          },
          {
            "request": 5,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 744,
            "latency_ms": 744,
            "attempts": 1
          },
          {
            "request": 6,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 868,
            "latency_ms": 868,
            "attempts": 1
          },
          {
            "request": 7,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 992,
            "latency_ms": 992,
            "attempts": 1
          }
        ],
        "attempts": [
          {
            "request": 0,
            "replica": 0,
            "attempt": 0,
            "start_ms": 0,
            "end_ms": 124,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 1,
            "replica": 0,
            "attempt": 0,
            "start_ms": 124,
            "end_ms": 248,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 2,
            "replica": 0,
            "attempt": 0,
            "start_ms": 248,
            "end_ms": 372,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 3,
            "replica": 0,
            "attempt": 0,
            "start_ms": 372,
            "end_ms": 496,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 4,
            "replica": 0,
            "attempt": 0,
            "start_ms": 496,
            "end_ms": 620,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 5,
            "replica": 0,
            "attempt": 0,
            "start_ms": 620,
            "end_ms": 744,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 6,
            "replica": 0,
            "attempt": 0,
            "start_ms": 744,
            "end_ms": 868,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 7,
            "replica": 0,
            "attempt": 0,
            "start_ms": 868,
            "end_ms": 992,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          }
        ],
        "horizon_ms": 992,
        "fault_used": false,
        "abandoned_completed_stage_matrix_flops": 0,
        "abandoned_partial_stage_work_unknown": false
      },
      "cost": {
        "currency": "declared_credit",
        "subtotals_exact": {
          "startup": "0",
          "steady_service": "992/125",
          "routing_and_cache": "0",
          "migration": "0",
          "warm_overlap": "0",
          "recovery_and_replay": "0",
          "failed_attempts": "0",
          "backlog_clearance": "0",
          "network_storage": "0",
          "host_control_plane": "0"
        },
        "known_subtotal_exact": "992/125",
        "missing_terms": [],
        "full_declared_cost_exact": "992/125",
        "cost_per_slo_valid_request_exact": "496/125",
        "observed_or_measured": false
      },
      "valid_requests": 2,
      "slo_eligible": false
    },
    {
      "id": "tp4-replicas2",
      "tp": 4,
      "replicas": 2,
      "total_cards": 8,
      "per_card_capacity_bytes": 24000000000,
      "placement_cards": [
        {
          "replica": 0,
          "tp_rank": 0,
          "weight_bytes": 16382076928,
          "kv_bytes": 17235968,
          "workspace_bytes": 2147483648,
          "resident_bytes": 18546796544,
          "fits_declared_budget": true
        },
        {
          "replica": 1,
          "tp_rank": 0,
          "weight_bytes": 16382076928,
          "kv_bytes": 17235968,
          "workspace_bytes": 2147483648,
          "resident_bytes": 18546796544,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 1,
          "weight_bytes": 16382076928,
          "kv_bytes": 17235968,
          "workspace_bytes": 2147483648,
          "resident_bytes": 18546796544,
          "fits_declared_budget": true
        },
        {
          "replica": 1,
          "tp_rank": 1,
          "weight_bytes": 16382076928,
          "kv_bytes": 17235968,
          "workspace_bytes": 2147483648,
          "resident_bytes": 18546796544,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 2,
          "weight_bytes": 16382076928,
          "kv_bytes": 17235968,
          "workspace_bytes": 2147483648,
          "resident_bytes": 18546796544,
          "fits_declared_budget": true
        },
        {
          "replica": 1,
          "tp_rank": 2,
          "weight_bytes": 16382076928,
          "kv_bytes": 17235968,
          "workspace_bytes": 2147483648,
          "resident_bytes": 18546796544,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 3,
          "weight_bytes": 16382076928,
          "kv_bytes": 17235968,
          "workspace_bytes": 2147483648,
          "resident_bytes": 18546796544,
          "fits_declared_budget": true
        },
        {
          "replica": 1,
          "tp_rank": 3,
          "weight_bytes": 16382076928,
          "kv_bytes": 17235968,
          "workspace_bytes": 2147483648,
          "resident_bytes": 18546796544,
          "fits_declared_budget": true
        }
      ],
      "capacity_fits": true,
      "declared_stage_durations_ms": [
        60,
        20,
        20,
        20,
        20,
        20,
        20,
        20
      ],
      "schedule": {
        "requests": [
          {
            "request": 0,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 200,
            "latency_ms": 200,
            "attempts": 1
          },
          {
            "request": 1,
            "replica": 1,
            "arrival_ms": 0,
            "completion_ms": 200,
            "latency_ms": 200,
            "attempts": 1
          },
          {
            "request": 2,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 400,
            "latency_ms": 400,
            "attempts": 1
          },
          {
            "request": 3,
            "replica": 1,
            "arrival_ms": 0,
            "completion_ms": 400,
            "latency_ms": 400,
            "attempts": 1
          },
          {
            "request": 4,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 600,
            "latency_ms": 600,
            "attempts": 1
          },
          {
            "request": 5,
            "replica": 1,
            "arrival_ms": 0,
            "completion_ms": 600,
            "latency_ms": 600,
            "attempts": 1
          },
          {
            "request": 6,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 800,
            "latency_ms": 800,
            "attempts": 1
          },
          {
            "request": 7,
            "replica": 1,
            "arrival_ms": 0,
            "completion_ms": 800,
            "latency_ms": 800,
            "attempts": 1
          }
        ],
        "attempts": [
          {
            "request": 0,
            "replica": 0,
            "attempt": 0,
            "start_ms": 0,
            "end_ms": 200,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 2,
            "replica": 0,
            "attempt": 0,
            "start_ms": 200,
            "end_ms": 400,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 4,
            "replica": 0,
            "attempt": 0,
            "start_ms": 400,
            "end_ms": 600,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 6,
            "replica": 0,
            "attempt": 0,
            "start_ms": 600,
            "end_ms": 800,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 1,
            "replica": 1,
            "attempt": 0,
            "start_ms": 0,
            "end_ms": 200,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 3,
            "replica": 1,
            "attempt": 0,
            "start_ms": 200,
            "end_ms": 400,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 5,
            "replica": 1,
            "attempt": 0,
            "start_ms": 400,
            "end_ms": 600,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          },
          {
            "request": 7,
            "replica": 1,
            "attempt": 0,
            "start_ms": 600,
            "end_ms": 800,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 16047822077952
              },
              {
                "name": "decode0",
                "matrix_flops": 64506036224
              },
              {
                "name": "decode1",
                "matrix_flops": 64508133376
              },
              {
                "name": "decode2",
                "matrix_flops": 64510230528
              },
              {
                "name": "decode3",
                "matrix_flops": 64512327680
              },
              {
                "name": "decode4",
                "matrix_flops": 64514424832
              },
              {
                "name": "decode5",
                "matrix_flops": 64516521984
              },
              {
                "name": "decode6",
                "matrix_flops": 64518619136
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 16499408371712
          }
        ],
        "horizon_ms": 800,
        "fault_used": false,
        "abandoned_completed_stage_matrix_flops": 0,
        "abandoned_partial_stage_work_unknown": false
      },
      "cost": {
        "currency": "declared_credit",
        "subtotals_exact": {
          "startup": "0",
          "steady_service": "32/5",
          "routing_and_cache": "0",
          "migration": "0",
          "warm_overlap": "0",
          "recovery_and_replay": "0",
          "failed_attempts": "0",
          "backlog_clearance": "0",
          "network_storage": "0",
          "host_control_plane": "0"
        },
        "known_subtotal_exact": "32/5",
        "missing_terms": [],
        "full_declared_cost_exact": "32/5",
        "cost_per_slo_valid_request_exact": "16/5",
        "observed_or_measured": false
      },
      "valid_requests": 2,
      "slo_eligible": false
    },
    {
      "id": "tp2-replicas4",
      "tp": 2,
      "replicas": 4,
      "total_cards": 8,
      "per_card_capacity_bytes": 24000000000,
      "placement_cards": [
        {
          "replica": 0,
          "tp_rank": 0,
          "weight_bytes": 32762800128,
          "kv_bytes": 34471936,
          "workspace_bytes": 2147483648,
          "resident_bytes": 34944755712,
          "fits_declared_budget": false
        },
        {
          "replica": 1,
          "tp_rank": 0,
          "weight_bytes": 32762800128,
          "kv_bytes": 34471936,
          "workspace_bytes": 2147483648,
          "resident_bytes": 34944755712,
          "fits_declared_budget": false
        },
        {
          "replica": 2,
          "tp_rank": 0,
          "weight_bytes": 32762800128,
          "kv_bytes": 34471936,
          "workspace_bytes": 2147483648,
          "resident_bytes": 34944755712,
          "fits_declared_budget": false
        },
        {
          "replica": 3,
          "tp_rank": 0,
          "weight_bytes": 32762800128,
          "kv_bytes": 34471936,
          "workspace_bytes": 2147483648,
          "resident_bytes": 34944755712,
          "fits_declared_budget": false
        },
        {
          "replica": 0,
          "tp_rank": 1,
          "weight_bytes": 32762800128,
          "kv_bytes": 34471936,
          "workspace_bytes": 2147483648,
          "resident_bytes": 34944755712,
          "fits_declared_budget": false
        },
        {
          "replica": 1,
          "tp_rank": 1,
          "weight_bytes": 32762800128,
          "kv_bytes": 34471936,
          "workspace_bytes": 2147483648,
          "resident_bytes": 34944755712,
          "fits_declared_budget": false
        },
        {
          "replica": 2,
          "tp_rank": 1,
          "weight_bytes": 32762800128,
          "kv_bytes": 34471936,
          "workspace_bytes": 2147483648,
          "resident_bytes": 34944755712,
          "fits_declared_budget": false
        },
        {
          "replica": 3,
          "tp_rank": 1,
          "weight_bytes": 32762800128,
          "kv_bytes": 34471936,
          "workspace_bytes": 2147483648,
          "resident_bytes": 34944755712,
          "fits_declared_budget": false
        }
      ],
      "capacity_fits": false,
      "declared_stage_durations_ms": [
        96,
        32,
        32,
        32,
        32,
        32,
        32,
        32
      ],
      "schedule": null,
      "cost": null,
      "valid_requests": null,
      "slo_eligible": false
    }
  ],
  "selection": {
    "required_valid_requests": 6,
    "eligible": [],
    "minimum_cost_per_valid_request_exact": null,
    "winners": []
  },
  "assumptions": [
    "同一批requests在t=0到达，相同模型/P/G，静态轮转到服务副本，每副本一次服务一个请求；并发是到达cohort大小，不是tensor batch。全部8卡及全部副本始终预留至cohort完成。",
    "TP8单副本、TP4两副本、TP2四副本均总8卡。每卡24GB与2GiBworkspace为教学预算；真实BF16权重/KV/头归属来自公共适配器，队列不保留已算KV，活跃batch=1。必要容量通过不是运行峰值证明。",
    "prefill产生首输出，之后G−1次decode；最终KV是P+G−1。阶段矩阵工作来自真实模型，声明服务毫秒并非用FLOPs/峰值推算。32B服务倍率2是独立教学假设，不是实测比例。",
    "故障仅影响包含物理卡0的整个服务副本；其他副本按原队列继续。正在运行的请求全量重启，不迁移、不保留KV，也不复用已算token；已完整完成请求不重启，完成与故障同刻时先提交完成。",
    "服务成功只指声明计算cohort完成；无模型输出质量实验。SLO是原始arrival至完整响应的deadline，最低有效比例由输入声明，不把TTFT或流式部分输出混入分母。",
    "恢复停机长度是输入，期间受影响副本无服务。已完成但放弃的阶段FLOPs分列，故障打断阶段的工作未知，绝不按耗时比例推FLOPs。源权重可恢复性、checkpoint加载/重放细节未模拟。",
    "费用按8卡×cohort结束毫秒×1/1000声明credit，含闲置、失败、恢复和重做卡时；recovery_fee仅额外外部服务费，不再收同一GPU时段。其他费用在本教学边界显式设零，非真实TCO或现价。",
    "仅在必要容量及最低SLO有效比例都满足时，按包含所有失败/超时工作的总费用除有效请求数比较，保留持平和无可行候选。图/扫描的选择都以这些假设为条件。"
  ]
}
```
