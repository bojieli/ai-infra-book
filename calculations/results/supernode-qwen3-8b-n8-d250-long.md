# 超节点规模：同请求集合、故障、SLO与费用

```json
{
  "model": "qwen3-8b",
  "requests": 8,
  "prompt": 256,
  "outputs": 8,
  "deadline_ms": 250,
  "fault_at_ms": 50,
  "recovery_ms": 200,
  "recovery_fee": "1",
  "minimum_valid_fraction": "3/4"
}
```

| 部署 | 容量通过 | SLO有效数 | 完成ms | 全部声明费用 | 每有效请求费用 | 可选 |
|---|---|---:|---:|---:|---:|---|
| tp8-replicas1 | True | 0 | 746 | 871/125 | None | False |
| tp4-replicas2 | True | 2 | 650 | 31/5 | 31/10 | False |
| tp2-replicas4 | True | 3 | 570 | 139/25 | 139/75 | False |

选择：`{"required_valid_requests": 6, "eligible": [], "minimum_cost_per_valid_request_exact": null, "winners": []}`

| 部署 | 请求 | 副本 | 完成ms | 尝试次数 |
|---|---:|---:|---:|---:|
| tp8-replicas1 | 0 | 0 | 312 | 2 |
| tp8-replicas1 | 1 | 0 | 374 | 1 |
| tp8-replicas1 | 2 | 0 | 436 | 1 |
| tp8-replicas1 | 3 | 0 | 498 | 1 |
| tp8-replicas1 | 4 | 0 | 560 | 1 |
| tp8-replicas1 | 5 | 0 | 622 | 1 |
| tp8-replicas1 | 6 | 0 | 684 | 1 |
| tp8-replicas1 | 7 | 0 | 746 | 1 |
| tp4-replicas2 | 0 | 0 | 350 | 2 |
| tp4-replicas2 | 1 | 1 | 100 | 1 |
| tp4-replicas2 | 2 | 0 | 450 | 1 |
| tp4-replicas2 | 3 | 1 | 200 | 1 |
| tp4-replicas2 | 4 | 0 | 550 | 1 |
| tp4-replicas2 | 5 | 1 | 300 | 1 |
| tp4-replicas2 | 6 | 0 | 650 | 1 |
| tp4-replicas2 | 7 | 1 | 400 | 1 |
| tp2-replicas4 | 0 | 0 | 410 | 2 |
| tp2-replicas4 | 1 | 1 | 160 | 1 |
| tp2-replicas4 | 2 | 2 | 160 | 1 |
| tp2-replicas4 | 3 | 3 | 160 | 1 |
| tp2-replicas4 | 4 | 0 | 570 | 1 |
| tp2-replicas4 | 5 | 1 | 320 | 1 |
| tp2-replicas4 | 6 | 2 | 320 | 1 |
| tp2-replicas4 | 7 | 3 | 320 | 1 |

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
    "model": "qwen3-8b",
    "requests": 8,
    "prompt": 256,
    "outputs": 8,
    "deadline_ms": 250,
    "fault_at_ms": 50,
    "recovery_ms": 200,
    "recovery_fee": "1",
    "minimum_valid_fraction": "3/4"
  },
  "sources": [
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
  ],
  "stages": [
    {
      "name": "prefill",
      "matrix_flops": 3576880431104
    },
    {
      "name": "decode0",
      "matrix_flops": 15287779328
    },
    {
      "name": "decode1",
      "matrix_flops": 15288369152
    },
    {
      "name": "decode2",
      "matrix_flops": 15288958976
    },
    {
      "name": "decode3",
      "matrix_flops": 15289548800
    },
    {
      "name": "decode4",
      "matrix_flops": 15290138624
    },
    {
      "name": "decode5",
      "matrix_flops": 15290728448
    },
    {
      "name": "decode6",
      "matrix_flops": 15291318272
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
          "weight_bytes": 2048223232,
          "kv_bytes": 4847616,
          "workspace_bytes": 2147483648,
          "resident_bytes": 4200554496,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 1,
          "weight_bytes": 2048223232,
          "kv_bytes": 4847616,
          "workspace_bytes": 2147483648,
          "resident_bytes": 4200554496,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 2,
          "weight_bytes": 2048223232,
          "kv_bytes": 4847616,
          "workspace_bytes": 2147483648,
          "resident_bytes": 4200554496,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 3,
          "weight_bytes": 2048223232,
          "kv_bytes": 4847616,
          "workspace_bytes": 2147483648,
          "resident_bytes": 4200554496,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 4,
          "weight_bytes": 2048223232,
          "kv_bytes": 4847616,
          "workspace_bytes": 2147483648,
          "resident_bytes": 4200554496,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 5,
          "weight_bytes": 2048223232,
          "kv_bytes": 4847616,
          "workspace_bytes": 2147483648,
          "resident_bytes": 4200554496,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 6,
          "weight_bytes": 2048223232,
          "kv_bytes": 4847616,
          "workspace_bytes": 2147483648,
          "resident_bytes": 4200554496,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 7,
          "weight_bytes": 2048223232,
          "kv_bytes": 4847616,
          "workspace_bytes": 2147483648,
          "resident_bytes": 4200554496,
          "fits_declared_budget": true
        }
      ],
      "capacity_fits": true,
      "declared_stage_durations_ms": [
        20,
        6,
        6,
        6,
        6,
        6,
        6,
        6
      ],
      "schedule": {
        "requests": [
          {
            "request": 0,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 312,
            "latency_ms": 312,
            "attempts": 2
          },
          {
            "request": 1,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 374,
            "latency_ms": 374,
            "attempts": 1
          },
          {
            "request": 2,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 436,
            "latency_ms": 436,
            "attempts": 1
          },
          {
            "request": 3,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 498,
            "latency_ms": 498,
            "attempts": 1
          },
          {
            "request": 4,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 560,
            "latency_ms": 560,
            "attempts": 1
          },
          {
            "request": 5,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 622,
            "latency_ms": 622,
            "attempts": 1
          },
          {
            "request": 6,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 684,
            "latency_ms": 684,
            "attempts": 1
          },
          {
            "request": 7,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 746,
            "latency_ms": 746,
            "attempts": 1
          }
        ],
        "attempts": [
          {
            "request": 0,
            "replica": 0,
            "attempt": 0,
            "start_ms": 0,
            "end_ms": 50,
            "aborted": true,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3653325225984
          },
          {
            "request": 0,
            "replica": 0,
            "attempt": 1,
            "start_ms": 250,
            "end_ms": 312,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 1,
            "replica": 0,
            "attempt": 0,
            "start_ms": 312,
            "end_ms": 374,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 2,
            "replica": 0,
            "attempt": 0,
            "start_ms": 374,
            "end_ms": 436,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 3,
            "replica": 0,
            "attempt": 0,
            "start_ms": 436,
            "end_ms": 498,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 4,
            "replica": 0,
            "attempt": 0,
            "start_ms": 498,
            "end_ms": 560,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 5,
            "replica": 0,
            "attempt": 0,
            "start_ms": 560,
            "end_ms": 622,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 6,
            "replica": 0,
            "attempt": 0,
            "start_ms": 622,
            "end_ms": 684,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 7,
            "replica": 0,
            "attempt": 0,
            "start_ms": 684,
            "end_ms": 746,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          }
        ],
        "horizon_ms": 746,
        "fault_used": true,
        "abandoned_completed_stage_matrix_flops": 3653325225984,
        "abandoned_partial_stage_work_unknown": false
      },
      "cost": {
        "currency": "declared_credit",
        "subtotals_exact": {
          "startup": "0",
          "steady_service": "746/125",
          "routing_and_cache": "0",
          "migration": "0",
          "warm_overlap": "0",
          "recovery_and_replay": "1",
          "failed_attempts": "0",
          "backlog_clearance": "0",
          "network_storage": "0",
          "host_control_plane": "0"
        },
        "known_subtotal_exact": "871/125",
        "missing_terms": [],
        "full_declared_cost_exact": "871/125",
        "cost_per_slo_valid_request_exact": null,
        "observed_or_measured": false
      },
      "valid_requests": 0,
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
          "weight_bytes": 4095830016,
          "kv_bytes": 9695232,
          "workspace_bytes": 2147483648,
          "resident_bytes": 6253008896,
          "fits_declared_budget": true
        },
        {
          "replica": 1,
          "tp_rank": 0,
          "weight_bytes": 4095830016,
          "kv_bytes": 9695232,
          "workspace_bytes": 2147483648,
          "resident_bytes": 6253008896,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 1,
          "weight_bytes": 4095830016,
          "kv_bytes": 9695232,
          "workspace_bytes": 2147483648,
          "resident_bytes": 6253008896,
          "fits_declared_budget": true
        },
        {
          "replica": 1,
          "tp_rank": 1,
          "weight_bytes": 4095830016,
          "kv_bytes": 9695232,
          "workspace_bytes": 2147483648,
          "resident_bytes": 6253008896,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 2,
          "weight_bytes": 4095830016,
          "kv_bytes": 9695232,
          "workspace_bytes": 2147483648,
          "resident_bytes": 6253008896,
          "fits_declared_budget": true
        },
        {
          "replica": 1,
          "tp_rank": 2,
          "weight_bytes": 4095830016,
          "kv_bytes": 9695232,
          "workspace_bytes": 2147483648,
          "resident_bytes": 6253008896,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 3,
          "weight_bytes": 4095830016,
          "kv_bytes": 9695232,
          "workspace_bytes": 2147483648,
          "resident_bytes": 6253008896,
          "fits_declared_budget": true
        },
        {
          "replica": 1,
          "tp_rank": 3,
          "weight_bytes": 4095830016,
          "kv_bytes": 9695232,
          "workspace_bytes": 2147483648,
          "resident_bytes": 6253008896,
          "fits_declared_budget": true
        }
      ],
      "capacity_fits": true,
      "declared_stage_durations_ms": [
        30,
        10,
        10,
        10,
        10,
        10,
        10,
        10
      ],
      "schedule": {
        "requests": [
          {
            "request": 0,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 350,
            "latency_ms": 350,
            "attempts": 2
          },
          {
            "request": 1,
            "replica": 1,
            "arrival_ms": 0,
            "completion_ms": 100,
            "latency_ms": 100,
            "attempts": 1
          },
          {
            "request": 2,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 450,
            "latency_ms": 450,
            "attempts": 1
          },
          {
            "request": 3,
            "replica": 1,
            "arrival_ms": 0,
            "completion_ms": 200,
            "latency_ms": 200,
            "attempts": 1
          },
          {
            "request": 4,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 550,
            "latency_ms": 550,
            "attempts": 1
          },
          {
            "request": 5,
            "replica": 1,
            "arrival_ms": 0,
            "completion_ms": 300,
            "latency_ms": 300,
            "attempts": 1
          },
          {
            "request": 6,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 650,
            "latency_ms": 650,
            "attempts": 1
          },
          {
            "request": 7,
            "replica": 1,
            "arrival_ms": 0,
            "completion_ms": 400,
            "latency_ms": 400,
            "attempts": 1
          }
        ],
        "attempts": [
          {
            "request": 0,
            "replica": 0,
            "attempt": 0,
            "start_ms": 0,
            "end_ms": 50,
            "aborted": true,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3607456579584
          },
          {
            "request": 0,
            "replica": 0,
            "attempt": 1,
            "start_ms": 250,
            "end_ms": 350,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 2,
            "replica": 0,
            "attempt": 0,
            "start_ms": 350,
            "end_ms": 450,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 4,
            "replica": 0,
            "attempt": 0,
            "start_ms": 450,
            "end_ms": 550,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 6,
            "replica": 0,
            "attempt": 0,
            "start_ms": 550,
            "end_ms": 650,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 1,
            "replica": 1,
            "attempt": 0,
            "start_ms": 0,
            "end_ms": 100,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 3,
            "replica": 1,
            "attempt": 0,
            "start_ms": 100,
            "end_ms": 200,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 5,
            "replica": 1,
            "attempt": 0,
            "start_ms": 200,
            "end_ms": 300,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 7,
            "replica": 1,
            "attempt": 0,
            "start_ms": 300,
            "end_ms": 400,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          }
        ],
        "horizon_ms": 650,
        "fault_used": true,
        "abandoned_completed_stage_matrix_flops": 3607456579584,
        "abandoned_partial_stage_work_unknown": false
      },
      "cost": {
        "currency": "declared_credit",
        "subtotals_exact": {
          "startup": "0",
          "steady_service": "26/5",
          "routing_and_cache": "0",
          "migration": "0",
          "warm_overlap": "0",
          "recovery_and_replay": "1",
          "failed_attempts": "0",
          "backlog_clearance": "0",
          "network_storage": "0",
          "host_control_plane": "0"
        },
        "known_subtotal_exact": "31/5",
        "missing_terms": [],
        "full_declared_cost_exact": "31/5",
        "cost_per_slo_valid_request_exact": "31/10",
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
          "weight_bytes": 8191043584,
          "kv_bytes": 19390464,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10357917696,
          "fits_declared_budget": true
        },
        {
          "replica": 1,
          "tp_rank": 0,
          "weight_bytes": 8191043584,
          "kv_bytes": 19390464,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10357917696,
          "fits_declared_budget": true
        },
        {
          "replica": 2,
          "tp_rank": 0,
          "weight_bytes": 8191043584,
          "kv_bytes": 19390464,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10357917696,
          "fits_declared_budget": true
        },
        {
          "replica": 3,
          "tp_rank": 0,
          "weight_bytes": 8191043584,
          "kv_bytes": 19390464,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10357917696,
          "fits_declared_budget": true
        },
        {
          "replica": 0,
          "tp_rank": 1,
          "weight_bytes": 8191043584,
          "kv_bytes": 19390464,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10357917696,
          "fits_declared_budget": true
        },
        {
          "replica": 1,
          "tp_rank": 1,
          "weight_bytes": 8191043584,
          "kv_bytes": 19390464,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10357917696,
          "fits_declared_budget": true
        },
        {
          "replica": 2,
          "tp_rank": 1,
          "weight_bytes": 8191043584,
          "kv_bytes": 19390464,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10357917696,
          "fits_declared_budget": true
        },
        {
          "replica": 3,
          "tp_rank": 1,
          "weight_bytes": 8191043584,
          "kv_bytes": 19390464,
          "workspace_bytes": 2147483648,
          "resident_bytes": 10357917696,
          "fits_declared_budget": true
        }
      ],
      "capacity_fits": true,
      "declared_stage_durations_ms": [
        48,
        16,
        16,
        16,
        16,
        16,
        16,
        16
      ],
      "schedule": {
        "requests": [
          {
            "request": 0,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 410,
            "latency_ms": 410,
            "attempts": 2
          },
          {
            "request": 1,
            "replica": 1,
            "arrival_ms": 0,
            "completion_ms": 160,
            "latency_ms": 160,
            "attempts": 1
          },
          {
            "request": 2,
            "replica": 2,
            "arrival_ms": 0,
            "completion_ms": 160,
            "latency_ms": 160,
            "attempts": 1
          },
          {
            "request": 3,
            "replica": 3,
            "arrival_ms": 0,
            "completion_ms": 160,
            "latency_ms": 160,
            "attempts": 1
          },
          {
            "request": 4,
            "replica": 0,
            "arrival_ms": 0,
            "completion_ms": 570,
            "latency_ms": 570,
            "attempts": 1
          },
          {
            "request": 5,
            "replica": 1,
            "arrival_ms": 0,
            "completion_ms": 320,
            "latency_ms": 320,
            "attempts": 1
          },
          {
            "request": 6,
            "replica": 2,
            "arrival_ms": 0,
            "completion_ms": 320,
            "latency_ms": 320,
            "attempts": 1
          },
          {
            "request": 7,
            "replica": 3,
            "arrival_ms": 0,
            "completion_ms": 320,
            "latency_ms": 320,
            "attempts": 1
          }
        ],
        "attempts": [
          {
            "request": 0,
            "replica": 0,
            "attempt": 0,
            "start_ms": 0,
            "end_ms": 50,
            "aborted": true,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              }
            ],
            "partial_stage": {
              "name": "decode0",
              "elapsed_ms": 2,
              "matrix_flops": null
            },
            "completed_stage_matrix_flops": 3576880431104
          },
          {
            "request": 0,
            "replica": 0,
            "attempt": 1,
            "start_ms": 250,
            "end_ms": 410,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 4,
            "replica": 0,
            "attempt": 0,
            "start_ms": 410,
            "end_ms": 570,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 1,
            "replica": 1,
            "attempt": 0,
            "start_ms": 0,
            "end_ms": 160,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 5,
            "replica": 1,
            "attempt": 0,
            "start_ms": 160,
            "end_ms": 320,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 2,
            "replica": 2,
            "attempt": 0,
            "start_ms": 0,
            "end_ms": 160,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 6,
            "replica": 2,
            "attempt": 0,
            "start_ms": 160,
            "end_ms": 320,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 3,
            "replica": 3,
            "attempt": 0,
            "start_ms": 0,
            "end_ms": 160,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          },
          {
            "request": 7,
            "replica": 3,
            "attempt": 0,
            "start_ms": 160,
            "end_ms": 320,
            "aborted": false,
            "completed_stages": [
              {
                "name": "prefill",
                "matrix_flops": 3576880431104
              },
              {
                "name": "decode0",
                "matrix_flops": 15287779328
              },
              {
                "name": "decode1",
                "matrix_flops": 15288369152
              },
              {
                "name": "decode2",
                "matrix_flops": 15288958976
              },
              {
                "name": "decode3",
                "matrix_flops": 15289548800
              },
              {
                "name": "decode4",
                "matrix_flops": 15290138624
              },
              {
                "name": "decode5",
                "matrix_flops": 15290728448
              },
              {
                "name": "decode6",
                "matrix_flops": 15291318272
              }
            ],
            "partial_stage": null,
            "completed_stage_matrix_flops": 3683907272704
          }
        ],
        "horizon_ms": 570,
        "fault_used": true,
        "abandoned_completed_stage_matrix_flops": 3576880431104,
        "abandoned_partial_stage_work_unknown": true
      },
      "cost": {
        "currency": "declared_credit",
        "subtotals_exact": {
          "startup": "0",
          "steady_service": "114/25",
          "routing_and_cache": "0",
          "migration": "0",
          "warm_overlap": "0",
          "recovery_and_replay": "1",
          "failed_attempts": "0",
          "backlog_clearance": "0",
          "network_storage": "0",
          "host_control_plane": "0"
        },
        "known_subtotal_exact": "139/25",
        "missing_terms": [],
        "full_declared_cost_exact": "139/25",
        "cost_per_slo_valid_request_exact": "139/75",
        "observed_or_measured": false
      },
      "valid_requests": 3,
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
