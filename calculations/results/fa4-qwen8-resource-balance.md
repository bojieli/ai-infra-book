# FA4单SM注意力资源配比

固定Qwen3-8B head_dim=128，采用论文B200分析输入。周期是三项稳态资源下界，不是完整kernel时延。

| 场景 | 矩阵周期 | SMEM周期 | 指数周期 | 下界周期 | 限制资源 |
|---|---:|---:|---:|---:|---|
| m128-n128-paper-baseline | 1024 | 768 | 1024 | 1024 | matrix, exp |
| m128-n128-matrix-double | 512 | 768 | 1024 | 1024 | exp |
| m128-n128-matrix-exp-double | 512 | 768 | 512 | 768 | smem |
| m128-n128-all-three-double | 512 | 384 | 512 | 512 | matrix, exp |
| m256-n128-paper-baseline | 2048 | 1536 | 2048 | 2048 | matrix, exp |
| m256-n128-matrix-double | 1024 | 1536 | 2048 | 2048 | exp |
| m256-n128-matrix-exp-double | 1024 | 1536 | 1024 | 1536 | smem |
| m256-n128-all-three-double | 1024 | 768 | 1024 | 1024 | matrix, exp |
| m128-n256-paper-baseline | 2048 | 1536 | 2048 | 2048 | matrix, exp |
| m128-n256-matrix-double | 1024 | 1536 | 2048 | 2048 | exp |
| m128-n256-matrix-exp-double | 1024 | 1536 | 1024 | 1536 | smem |
| m128-n256-all-three-double | 1024 | 768 | 1024 | 1024 | matrix, exp |
| m256-n256-paper-baseline | 4096 | 3072 | 4096 | 4096 | matrix, exp |
| m256-n256-matrix-double | 2048 | 3072 | 4096 | 4096 | exp |
| m256-n256-matrix-exp-double | 2048 | 3072 | 2048 | 3072 | smem |
| m256-n256-all-three-double | 2048 | 1536 | 2048 | 2048 | matrix, exp |

共享内存按MMA输出分块重复读取Q/K/V；PV的P由TMEM提供。唯一QKV输入载荷不能替代SMEM访问计数。

## 口径与限制

- BF16 dense rectangular QK/PV tiles; no projections or causal masking/padding claim.
- Matrix rate is a paper analytical input, not an independently selected whole-device precision peak.
- SMEM reads count repeated MMA operands; unique Q/K/V bytes cannot replace them. P is consumed from TMEM.
- max(resource work/rate) assumes ideal overlap for a steady-state resource bound; not the serial QK-softmax-PV latency.
- Exp is only part of softmax. Reductions, scaling, TMEM traffic, correction, scheduling and synchronization are not assigned zero cost.
- Multipliers are hypothetical supply changes, not other GPU specifications. No measured throughput or kernel speedup is inferred.

## 完整形状、字节与来源

```json
{
  "calculation": "fa4-single-sm-resource-balance",
  "sources": {
    "scope": "FA4 paper section 2.2 and 3.1.1, equations 1-3, Table 1; pinned Qwen3-8B head_dim",
    "sources": [
      {
        "file": "sources/fa4-resource-balance/paper.pdf",
        "sha256": "3aae64f2f4879545ae31ccb856614d5638d61d321a9fce7a8dc2122a8cf5bc27",
        "url": "https://proceedings.mlsys.org/paper_files/paper/2026/file/ae8b0b5838ba510daff1198474e7b984-Paper-Conference.pdf",
        "kind": "official_pdf"
      },
      {
        "file": "sources/fa4-resource-balance/paper.txt",
        "sha256": "959bb50bea6250360b8125b07f3a2e40543ed3bc91287bb4ad26f6df9b37c03a",
        "url": "https://proceedings.mlsys.org/paper_files/paper/2026/file/ae8b0b5838ba510daff1198474e7b984-Paper-Conference.pdf",
        "kind": "local_extracted_text"
      },
      {
        "file": "configs/models/qwen3-8b/config.json",
        "sha256": "f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30"
      }
    ],
    "rates": {
      "bf16_matrix_flops_per_sm_cycle": 8192,
      "exponential_results_per_sm_cycle": 16,
      "smem_read_bytes_per_sm_cycle": 128
    },
    "rate_scope": "Paper B200 single-SM resource analysis; SMEM measured input attributed by authors, not HBM or full-card rates",
    "inputs": {
      "mma_m": 128,
      "mma_n": 128,
      "element_bytes": 2
    }
  },
  "scenarios": [
    {
      "shape": {
        "M": 128,
        "N": 128,
        "d": 128
      },
      "multipliers": {
        "matrix": 1,
        "exp": 1,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 4194304
        },
        {
          "name": "PV",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 4194304
        }
      ],
      "mma_output_tiles": {
        "QK": 1,
        "PV": 1
      },
      "interface_bytes": {
        "qk_smem_read": 65536,
        "pv_smem_read": 32768,
        "unique_qkv_input_payload": 98304,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 8388608,
        "smem_read_bytes": 98304,
        "exp_results": 16384
      },
      "cycles": {
        "matrix": {
          "numerator": 1024,
          "denominator": 1
        },
        "smem": {
          "numerator": 768,
          "denominator": 1
        },
        "exp": {
          "numerator": 1024,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 1024,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "matrix",
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m128-n128-paper-baseline",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 1
      }
    },
    {
      "shape": {
        "M": 128,
        "N": 128,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 1,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 4194304
        },
        {
          "name": "PV",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 4194304
        }
      ],
      "mma_output_tiles": {
        "QK": 1,
        "PV": 1
      },
      "interface_bytes": {
        "qk_smem_read": 65536,
        "pv_smem_read": 32768,
        "unique_qkv_input_payload": 98304,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 8388608,
        "smem_read_bytes": 98304,
        "exp_results": 16384
      },
      "cycles": {
        "matrix": {
          "numerator": 512,
          "denominator": 1
        },
        "smem": {
          "numerator": 768,
          "denominator": 1
        },
        "exp": {
          "numerator": 1024,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 1024,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m128-n128-matrix-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 1
      }
    },
    {
      "shape": {
        "M": 128,
        "N": 128,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 2,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 4194304
        },
        {
          "name": "PV",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 4194304
        }
      ],
      "mma_output_tiles": {
        "QK": 1,
        "PV": 1
      },
      "interface_bytes": {
        "qk_smem_read": 65536,
        "pv_smem_read": 32768,
        "unique_qkv_input_payload": 98304,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 8388608,
        "smem_read_bytes": 98304,
        "exp_results": 16384
      },
      "cycles": {
        "matrix": {
          "numerator": 512,
          "denominator": 1
        },
        "smem": {
          "numerator": 768,
          "denominator": 1
        },
        "exp": {
          "numerator": 512,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 768,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "smem"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m128-n128-matrix-exp-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 3,
        "denominator": 4
      }
    },
    {
      "shape": {
        "M": 128,
        "N": 128,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 2,
        "smem": 2
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 4194304
        },
        {
          "name": "PV",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 4194304
        }
      ],
      "mma_output_tiles": {
        "QK": 1,
        "PV": 1
      },
      "interface_bytes": {
        "qk_smem_read": 65536,
        "pv_smem_read": 32768,
        "unique_qkv_input_payload": 98304,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 8388608,
        "smem_read_bytes": 98304,
        "exp_results": 16384
      },
      "cycles": {
        "matrix": {
          "numerator": 512,
          "denominator": 1
        },
        "smem": {
          "numerator": 384,
          "denominator": 1
        },
        "exp": {
          "numerator": 512,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 512,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "matrix",
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m128-n128-all-three-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 2
      }
    },
    {
      "shape": {
        "M": 256,
        "N": 128,
        "d": 128
      },
      "multipliers": {
        "matrix": 1,
        "exp": 1,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 8388608
        },
        {
          "name": "PV",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 8388608
        }
      ],
      "mma_output_tiles": {
        "QK": 2,
        "PV": 2
      },
      "interface_bytes": {
        "qk_smem_read": 131072,
        "pv_smem_read": 65536,
        "unique_qkv_input_payload": 131072,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 16777216,
        "smem_read_bytes": 196608,
        "exp_results": 32768
      },
      "cycles": {
        "matrix": {
          "numerator": 2048,
          "denominator": 1
        },
        "smem": {
          "numerator": 1536,
          "denominator": 1
        },
        "exp": {
          "numerator": 2048,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 2048,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "matrix",
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m256-n128-paper-baseline",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 1
      }
    },
    {
      "shape": {
        "M": 256,
        "N": 128,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 1,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 8388608
        },
        {
          "name": "PV",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 8388608
        }
      ],
      "mma_output_tiles": {
        "QK": 2,
        "PV": 2
      },
      "interface_bytes": {
        "qk_smem_read": 131072,
        "pv_smem_read": 65536,
        "unique_qkv_input_payload": 131072,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 16777216,
        "smem_read_bytes": 196608,
        "exp_results": 32768
      },
      "cycles": {
        "matrix": {
          "numerator": 1024,
          "denominator": 1
        },
        "smem": {
          "numerator": 1536,
          "denominator": 1
        },
        "exp": {
          "numerator": 2048,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 2048,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m256-n128-matrix-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 1
      }
    },
    {
      "shape": {
        "M": 256,
        "N": 128,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 2,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 8388608
        },
        {
          "name": "PV",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 8388608
        }
      ],
      "mma_output_tiles": {
        "QK": 2,
        "PV": 2
      },
      "interface_bytes": {
        "qk_smem_read": 131072,
        "pv_smem_read": 65536,
        "unique_qkv_input_payload": 131072,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 16777216,
        "smem_read_bytes": 196608,
        "exp_results": 32768
      },
      "cycles": {
        "matrix": {
          "numerator": 1024,
          "denominator": 1
        },
        "smem": {
          "numerator": 1536,
          "denominator": 1
        },
        "exp": {
          "numerator": 1024,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 1536,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "smem"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m256-n128-matrix-exp-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 3,
        "denominator": 4
      }
    },
    {
      "shape": {
        "M": 256,
        "N": 128,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 2,
        "smem": 2
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 8388608
        },
        {
          "name": "PV",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 8388608
        }
      ],
      "mma_output_tiles": {
        "QK": 2,
        "PV": 2
      },
      "interface_bytes": {
        "qk_smem_read": 131072,
        "pv_smem_read": 65536,
        "unique_qkv_input_payload": 131072,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 16777216,
        "smem_read_bytes": 196608,
        "exp_results": 32768
      },
      "cycles": {
        "matrix": {
          "numerator": 1024,
          "denominator": 1
        },
        "smem": {
          "numerator": 768,
          "denominator": 1
        },
        "exp": {
          "numerator": 1024,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 1024,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "matrix",
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m256-n128-all-three-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 2
      }
    },
    {
      "shape": {
        "M": 128,
        "N": 256,
        "d": 128
      },
      "multipliers": {
        "matrix": 1,
        "exp": 1,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            256
          ],
          "output": [
            128,
            256
          ],
          "flops": 8388608
        },
        {
          "name": "PV",
          "left": [
            128,
            256
          ],
          "right": [
            256,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 8388608
        }
      ],
      "mma_output_tiles": {
        "QK": 2,
        "PV": 1
      },
      "interface_bytes": {
        "qk_smem_read": 131072,
        "pv_smem_read": 65536,
        "unique_qkv_input_payload": 163840,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 16777216,
        "smem_read_bytes": 196608,
        "exp_results": 32768
      },
      "cycles": {
        "matrix": {
          "numerator": 2048,
          "denominator": 1
        },
        "smem": {
          "numerator": 1536,
          "denominator": 1
        },
        "exp": {
          "numerator": 2048,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 2048,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "matrix",
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m128-n256-paper-baseline",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 1
      }
    },
    {
      "shape": {
        "M": 128,
        "N": 256,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 1,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            256
          ],
          "output": [
            128,
            256
          ],
          "flops": 8388608
        },
        {
          "name": "PV",
          "left": [
            128,
            256
          ],
          "right": [
            256,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 8388608
        }
      ],
      "mma_output_tiles": {
        "QK": 2,
        "PV": 1
      },
      "interface_bytes": {
        "qk_smem_read": 131072,
        "pv_smem_read": 65536,
        "unique_qkv_input_payload": 163840,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 16777216,
        "smem_read_bytes": 196608,
        "exp_results": 32768
      },
      "cycles": {
        "matrix": {
          "numerator": 1024,
          "denominator": 1
        },
        "smem": {
          "numerator": 1536,
          "denominator": 1
        },
        "exp": {
          "numerator": 2048,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 2048,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m128-n256-matrix-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 1
      }
    },
    {
      "shape": {
        "M": 128,
        "N": 256,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 2,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            256
          ],
          "output": [
            128,
            256
          ],
          "flops": 8388608
        },
        {
          "name": "PV",
          "left": [
            128,
            256
          ],
          "right": [
            256,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 8388608
        }
      ],
      "mma_output_tiles": {
        "QK": 2,
        "PV": 1
      },
      "interface_bytes": {
        "qk_smem_read": 131072,
        "pv_smem_read": 65536,
        "unique_qkv_input_payload": 163840,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 16777216,
        "smem_read_bytes": 196608,
        "exp_results": 32768
      },
      "cycles": {
        "matrix": {
          "numerator": 1024,
          "denominator": 1
        },
        "smem": {
          "numerator": 1536,
          "denominator": 1
        },
        "exp": {
          "numerator": 1024,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 1536,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "smem"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m128-n256-matrix-exp-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 3,
        "denominator": 4
      }
    },
    {
      "shape": {
        "M": 128,
        "N": 256,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 2,
        "smem": 2
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            128,
            128
          ],
          "right": [
            128,
            256
          ],
          "output": [
            128,
            256
          ],
          "flops": 8388608
        },
        {
          "name": "PV",
          "left": [
            128,
            256
          ],
          "right": [
            256,
            128
          ],
          "output": [
            128,
            128
          ],
          "flops": 8388608
        }
      ],
      "mma_output_tiles": {
        "QK": 2,
        "PV": 1
      },
      "interface_bytes": {
        "qk_smem_read": 131072,
        "pv_smem_read": 65536,
        "unique_qkv_input_payload": 163840,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 16777216,
        "smem_read_bytes": 196608,
        "exp_results": 32768
      },
      "cycles": {
        "matrix": {
          "numerator": 1024,
          "denominator": 1
        },
        "smem": {
          "numerator": 768,
          "denominator": 1
        },
        "exp": {
          "numerator": 1024,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 1024,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "matrix",
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m128-n256-all-three-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 2
      }
    },
    {
      "shape": {
        "M": 256,
        "N": 256,
        "d": 128
      },
      "multipliers": {
        "matrix": 1,
        "exp": 1,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            256
          ],
          "output": [
            256,
            256
          ],
          "flops": 16777216
        },
        {
          "name": "PV",
          "left": [
            256,
            256
          ],
          "right": [
            256,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 16777216
        }
      ],
      "mma_output_tiles": {
        "QK": 4,
        "PV": 2
      },
      "interface_bytes": {
        "qk_smem_read": 262144,
        "pv_smem_read": 131072,
        "unique_qkv_input_payload": 196608,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 33554432,
        "smem_read_bytes": 393216,
        "exp_results": 65536
      },
      "cycles": {
        "matrix": {
          "numerator": 4096,
          "denominator": 1
        },
        "smem": {
          "numerator": 3072,
          "denominator": 1
        },
        "exp": {
          "numerator": 4096,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 4096,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "matrix",
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m256-n256-paper-baseline",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 1
      }
    },
    {
      "shape": {
        "M": 256,
        "N": 256,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 1,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            256
          ],
          "output": [
            256,
            256
          ],
          "flops": 16777216
        },
        {
          "name": "PV",
          "left": [
            256,
            256
          ],
          "right": [
            256,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 16777216
        }
      ],
      "mma_output_tiles": {
        "QK": 4,
        "PV": 2
      },
      "interface_bytes": {
        "qk_smem_read": 262144,
        "pv_smem_read": 131072,
        "unique_qkv_input_payload": 196608,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 33554432,
        "smem_read_bytes": 393216,
        "exp_results": 65536
      },
      "cycles": {
        "matrix": {
          "numerator": 2048,
          "denominator": 1
        },
        "smem": {
          "numerator": 3072,
          "denominator": 1
        },
        "exp": {
          "numerator": 4096,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 4096,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m256-n256-matrix-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 1
      }
    },
    {
      "shape": {
        "M": 256,
        "N": 256,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 2,
        "smem": 1
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            256
          ],
          "output": [
            256,
            256
          ],
          "flops": 16777216
        },
        {
          "name": "PV",
          "left": [
            256,
            256
          ],
          "right": [
            256,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 16777216
        }
      ],
      "mma_output_tiles": {
        "QK": 4,
        "PV": 2
      },
      "interface_bytes": {
        "qk_smem_read": 262144,
        "pv_smem_read": 131072,
        "unique_qkv_input_payload": 196608,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 33554432,
        "smem_read_bytes": 393216,
        "exp_results": 65536
      },
      "cycles": {
        "matrix": {
          "numerator": 2048,
          "denominator": 1
        },
        "smem": {
          "numerator": 3072,
          "denominator": 1
        },
        "exp": {
          "numerator": 2048,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 3072,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "smem"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m256-n256-matrix-exp-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 3,
        "denominator": 4
      }
    },
    {
      "shape": {
        "M": 256,
        "N": 256,
        "d": 128
      },
      "multipliers": {
        "matrix": 2,
        "exp": 2,
        "smem": 2
      },
      "matrices": [
        {
          "name": "QK",
          "left": [
            256,
            128
          ],
          "right": [
            128,
            256
          ],
          "output": [
            256,
            256
          ],
          "flops": 16777216
        },
        {
          "name": "PV",
          "left": [
            256,
            256
          ],
          "right": [
            256,
            128
          ],
          "output": [
            256,
            128
          ],
          "flops": 16777216
        }
      ],
      "mma_output_tiles": {
        "QK": 4,
        "PV": 2
      },
      "interface_bytes": {
        "qk_smem_read": 262144,
        "pv_smem_read": 131072,
        "unique_qkv_input_payload": 196608,
        "measured_hbm": null
      },
      "work": {
        "matrix_flops": 33554432,
        "smem_read_bytes": 393216,
        "exp_results": 65536
      },
      "cycles": {
        "matrix": {
          "numerator": 2048,
          "denominator": 1
        },
        "smem": {
          "numerator": 1536,
          "denominator": 1
        },
        "exp": {
          "numerator": 2048,
          "denominator": 1
        }
      },
      "accounted_steady_state_bound_cycles": {
        "numerator": 2048,
        "denominator": 1
      },
      "tied_limiting_resources": [
        "matrix",
        "exp"
      ],
      "complete_softmax_cycles": null,
      "measured_kernel_cycles": null,
      "id": "m256-n256-all-three-double",
      "accounted_bound_ratio_to_baseline": {
        "numerator": 1,
        "denominator": 2
      }
    }
  ],
  "assumptions": [
    "BF16 dense rectangular QK/PV tiles; no projections or causal masking/padding claim.",
    "Matrix rate is a paper analytical input, not an independently selected whole-device precision peak.",
    "SMEM reads count repeated MMA operands; unique Q/K/V bytes cannot replace them. P is consumed from TMEM.",
    "max(resource work/rate) assumes ideal overlap for a steady-state resource bound; not the serial QK-softmax-PV latency.",
    "Exp is only part of softmax. Reductions, scaling, TMEM traffic, correction, scheduling and synchronization are not assigned zero cost.",
    "Multipliers are hypothetical supply changes, not other GPU specifications. No measured throughput or kernel speedup is inferred."
  ]
}
```
