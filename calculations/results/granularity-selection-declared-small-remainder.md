# 专家颗粒度：容量与服务条件

固定16token、TP2/EP4和8192位置，对比未训练的64/3072/k4与256/768/k16变体。有效服务率由输入声明，不是官方峰值或实测。

| 变体 | 必要容量 bytes | 已计串行成本 ms | 给定剩余成本 ms | 容量通过 |
|---|---:|---:|---:|---|
| coarse64 | 67,708,148,736 | 20.618039 | 0.000000 | True |
| fine256-k16 | 67,855,997,952 | 20.538885 | 0.001000 | True |

令 U 为尚未计入的串行阶段耗时，细粒度严格更快的条件是：

`U_fine - U_coarse < 483113/6103515625 秒`（约 79.153234 微秒）。等号表示并列。

共同wire字节相同，共同fabric带宽不能改变两者的差值。逻辑GEMM操作数服务与物理HBM不同；U需要覆盖所选比较中的其余差异工作，不能自动当零。必要容量通过不证明运行时可部署，给定剩余耗时也不证明模型质量相同。

满足必要容量条件后的条件最快方案：['fine256-k16']（null表示剩余输入不足；空列表表示两者均未通过容量条件）。

## 完整输入与计算明细

```json
{
  "calculation": "granularity-conditional-selection",
  "scenario": {
    "coarse_flops_per_second": 100000000000000,
    "fine_flops_per_second": 150000000000000,
    "operand_bytes_per_second": 3000000000000,
    "wire_bytes_per_second": 100000000000,
    "capacity_bytes": 80000000000,
    "router_flops_per_second": 100000000000000,
    "coarse_remaining_ns": 0,
    "fine_remaining_ns": 1000
  },
  "bindings": [
    {
      "file": "results/qwen235-granularity-coarse64.json",
      "sha256": "050f788294c47e7c56a691b9bd9003b51841a53cfa00dda0a8f9b33f39a887b0"
    },
    {
      "file": "results/qwen235-granularity-fine256-k16.json",
      "sha256": "adb3aa0d55db34cd2b0c35164c25f5e6f28c0b8633855ccb23beede48d609141"
    }
  ],
  "variants": [
    {
      "variant": "coarse64",
      "ranks": [
        {
          "rank": 0,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56824922112,
          "necessary_capacity_bytes": 67708148736
        },
        {
          "rank": 1,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56824922112,
          "necessary_capacity_bytes": 67708148736
        },
        {
          "rank": 2,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56824922112,
          "necessary_capacity_bytes": 67708148736
        },
        {
          "rank": 3,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56824922112,
          "necessary_capacity_bytes": 67708148736
        },
        {
          "rank": 4,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56824922112,
          "necessary_capacity_bytes": 67708148736
        },
        {
          "rank": 5,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56824922112,
          "necessary_capacity_bytes": 67708148736
        },
        {
          "rank": 6,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56824922112,
          "necessary_capacity_bytes": 67708148736
        },
        {
          "rank": 7,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56824922112,
          "necessary_capacity_bytes": 67708148736
        }
      ],
      "peak_necessary_capacity_bytes": 67708148736,
      "necessary_capacity_fits": true,
      "max_rank_expert_flops": 56774098944,
      "max_rank_operand_bytes": 56824922112,
      "total_wire_bytes": 108017280,
      "serial_compute_seconds_exact": "3465216/6103515625",
      "serial_operand_seconds_exact": "4624424/244140625",
      "serial_wire_seconds_exact": "168777/156250000",
      "conditional_subaccount_seconds_exact": "2013480329/97656250000",
      "router_gemm_flops_per_rank": 788529152,
      "router_gemm_operand_bytes_per_rank": 61796352,
      "serial_router_seconds_exact": "173853/6103515625",
      "router_selection_work_per_rank": {
        "softmax_scalar_flops": 287264,
        "exp_ops": 96256,
        "max_comparisons": 94752,
        "topk_rows": 1504,
        "topk_candidates": 96256,
        "renormalize_scalar_flops": 10528
      },
      "router_selection_seconds": null,
      "router_matrix_flops_all_replicas": 6308233216,
      "full_runtime_seconds": null,
      "quality": null,
      "declared_remaining_seconds_exact": "0",
      "conditional_extended_seconds_exact": "2013480329/97656250000"
    },
    {
      "variant": "fine256-k16",
      "ranks": [
        {
          "rank": 0,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56935809024,
          "necessary_capacity_bytes": 67855997952
        },
        {
          "rank": 1,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56935809024,
          "necessary_capacity_bytes": 67855997952
        },
        {
          "rank": 2,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56935809024,
          "necessary_capacity_bytes": 67855997952
        },
        {
          "rank": 3,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56935809024,
          "necessary_capacity_bytes": 67855997952
        },
        {
          "rank": 4,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56935809024,
          "necessary_capacity_bytes": 67855997952
        },
        {
          "rank": 5,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56935809024,
          "necessary_capacity_bytes": 67855997952
        },
        {
          "rank": 6,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56935809024,
          "necessary_capacity_bytes": 67855997952
        },
        {
          "rank": 7,
          "expert_matrix_flops": 56774098944,
          "expert_gemm_operand_bytes": 56935809024,
          "necessary_capacity_bytes": 67855997952
        }
      ],
      "peak_necessary_capacity_bytes": 67855997952,
      "necessary_capacity_fits": true,
      "max_rank_expert_flops": 56774098944,
      "max_rank_operand_bytes": 56935809024,
      "total_wire_bytes": 108017280,
      "serial_compute_seconds_exact": "2310144/6103515625",
      "serial_operand_seconds_exact": "4633448/244140625",
      "serial_wire_seconds_exact": "168777/156250000",
      "conditional_subaccount_seconds_exact": "2005750521/97656250000",
      "router_gemm_flops_per_rank": 3154116608,
      "router_gemm_operand_bytes_per_rank": 210223104,
      "serial_router_seconds_exact": "620212/6103515625",
      "router_selection_work_per_rank": {
        "softmax_scalar_flops": 1153568,
        "exp_ops": 385024,
        "max_comparisons": 383520,
        "topk_rows": 1504,
        "topk_candidates": 385024,
        "renormalize_scalar_flops": 46624
      },
      "router_selection_seconds": null,
      "router_matrix_flops_all_replicas": 25232932864,
      "full_runtime_seconds": null,
      "quality": null,
      "declared_remaining_seconds_exact": "1/1000000",
      "conditional_extended_seconds_exact": "8023392709/390625000000"
    }
  ],
  "fine_strictly_faster_rate_threshold_exact": "7372800000000000000/59431",
  "fine_can_win_with_finite_compute_rate": true,
  "same_wire_bytes": true,
  "fine_remaining_minus_coarse_must_be_less_than_seconds_exact": "483113/6103515625",
  "conditional_capacity_eligible_fastest_variants": [
    "fine256-k16"
  ],
  "extended_condition": "T_fine < T_coarse iff U_fine - U_coarse < reported slack; equality is a tie. Both require necessary capacity admission.",
  "scope": [
    "Fixed 16-token balanced TP2/EP4 cohort and 8192 retained positions; two untrained E/F/top-k alternatives from actual Qwen235 configuration. Full parameters differ because routers differ.",
    "Necessary capacity includes all stored weights, KV and declared workspace. It does not prove executable runtime feasibility.",
    "Expert GEMM operand bytes count each visited matrix call input/weight/output in BF16. These are logical interfaces, not measured HBM; gate/up rereads are explicit.",
    "Service model serially adds max-rank expert compute, max-rank logical operand service and total message wire over one shared fabric server. Effective rates are declared inputs, not official peaks or observed execution.",
    "Router GEMM is replicated on every TP/EP rank under an explicit policy, with BF16 interface bytes and a separately supplied effective rate. FP32 softmax/top-k/renormalization work is retained but its runtime is unknown. Attention/shared framework operations, nonlinearities, launch costs, queueing, real caches and topology remain outside this conditional subaccount. This is not a full-request ranking.",
    "Equal wire demand cannot create a bandwidth-driven ordering reversal at common wire rate. A different result requires changed routing/placement or an explicitly different service model.",
    "U_i is a caller-declared elapsed remainder under this serial service model, including unmodeled selection/nonlinearities and any other included stage costs. It is not measured here. Supplying only one remainder never enables a complete conditional choice; explicit zero is allowed but never inferred.",
    "No quality-equivalence assertion; conditional speed comparison only applies to the named partial resource account."
  ]
}
```
