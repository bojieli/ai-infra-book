# DeepSeek V4 optimizer reference

Explicit grouping and factored ten-step hybrid Newton–Schulz; full runtime remains unknown.

| Pattern | Family | Tensor shape | Count | Independent shape | Matrices/tensor | Parameters | Matrix FLOPs | Scalar operations |
|---|---|---|---:|---|---:|---:|---:|---:|
| embed.weight | adamw | [129280, 4096] | 1 | [129280, 4096] | 1 | 529530880 | 0 | 7413432320 |
| layers.{i}.attn.attn_sink | unresolved | [64] | 43 | [64] | 1 | 2752 | 0 | unknown |
| layers.{i}.hc_attn_base | adamw | [24] | 43 | [24] | 1 | 1032 | 0 | 14448 |
| layers.{i}.hc_attn_fn | muon | [24, 16384] | 43 | [24, 16384] | 1 | 16908288 | 16243845120 | 524899968 |
| layers.{i}.hc_attn_scale | adamw | [3] | 43 | [3] | 1 | 129 | 0 | 1806 |
| layers.{i}.hc_ffn_base | adamw | [24] | 43 | [24] | 1 | 1032 | 0 | 14448 |
| layers.{i}.hc_ffn_fn | muon | [24, 16384] | 43 | [24, 16384] | 1 | 16908288 | 16243845120 | 524899968 |
| layers.{i}.hc_ffn_scale | adamw | [3] | 43 | [3] | 1 | 129 | 0 | 1806 |
| layers.{i}.attn.kv_norm.weight | adamw | [512] | 43 | [512] | 1 | 22016 | 0 | 308224 |
| layers.{i}.attn.q_norm.weight | adamw | [1024] | 43 | [1024] | 1 | 44032 | 0 | 616448 |
| layers.{i}.attn_norm.weight | adamw | [4096] | 43 | [4096] | 1 | 176128 | 0 | 2465792 |
| layers.{i}.ffn.gate.weight | muon | [256, 4096] | 43 | [256, 4096] | 1 | 45088768 | 476137390080 | 1482293248 |
| layers.{i}.ffn_norm.weight | adamw | [4096] | 43 | [4096] | 1 | 176128 | 0 | 2465792 |
| layers.{i}.attn.wkv.weight | muon | [512, 4096] | 43 | [512, 4096] | 1 | 90177536 | 1962263183360 | 3133669376 |
| layers.{i}.attn.wo_a.weight | muon | [8192, 4096] | 43 | [1024, 4096] | 8 | 1442840576 | 66486093742080 | 55549362176 |
| layers.{i}.attn.wo_b.weight | muon | [4096, 8192] | 43 | [4096, 8192] | 1 | 1442840576 | 295493749964800 | 66370666496 |
| layers.{i}.attn.wq_a.weight | muon | [1024, 4096] | 43 | [1024, 4096] | 1 | 180355072 | 8310761717760 | 6943670272 |
| layers.{i}.attn.wq_b.weight | muon | [32768, 1024] | 43 | [32768, 1024] | 1 | 1442840576 | 60022167961600 | 46080720896 |
| layers.{i}.ffn.shared_experts.w1.weight | muon | [2048, 4096] | 43 | [2048, 4096] | 1 | 360710144 | 36936718745600 | 16592666624 |
| layers.{i}.ffn.shared_experts.w2.weight | muon | [4096, 2048] | 43 | [4096, 2048] | 1 | 360710144 | 36936718745600 | 16592666624 |
| layers.{i}.ffn.shared_experts.w3.weight | muon | [2048, 4096] | 43 | [2048, 4096] | 1 | 360710144 | 36936718745600 | 16592666624 |
| layers.{i}.ffn.experts.{i}.w1.weight | muon | [2048, 4096] | 11008 | [2048, 4096] | 1 | 92341796864 | 9455799998873600 | 4247722655744 |
| layers.{i}.ffn.experts.{i}.w2.weight | muon | [4096, 2048] | 11008 | [4096, 2048] | 1 | 92341796864 | 9455799998873600 | 4247722655744 |
| layers.{i}.ffn.experts.{i}.w3.weight | muon | [2048, 4096] | 11008 | [2048, 4096] | 1 | 92341796864 | 9455799998873600 | 4247722655744 |
| layers.{i}.attn.compressor.ape | muon | [4, 1024] | 21 | [4, 1024] | 1 | 86016 | 13789440 | 2676576 |
| layers.{i}.attn.indexer.compressor.ape | muon | [4, 256] | 21 | [4, 256] | 1 | 21504 | 3467520 | 676704 |
| layers.{i}.attn.compressor.norm.weight | adamw | [512] | 41 | [512] | 1 | 20992 | 0 | 293888 |
| layers.{i}.attn.compressor.wgate.weight | muon | [1024, 4096] | 21 | [1024, 4096] | 1 | 88080384 | 4058744094720 | 3391094784 |
| layers.{i}.attn.compressor.wkv.weight | muon | [1024, 4096] | 21 | [1024, 4096] | 1 | 88080384 | 4058744094720 | 3391094784 |
| layers.{i}.attn.indexer.compressor.norm.weight | adamw | [128] | 21 | [128] | 1 | 2688 | 0 | 37632 |
| layers.{i}.attn.indexer.compressor.wgate.weight | muon | [256, 4096] | 21 | [256, 4096] | 1 | 22020096 | 232532213760 | 723910656 |
| layers.{i}.attn.indexer.compressor.wkv.weight | muon | [256, 4096] | 21 | [256, 4096] | 1 | 22020096 | 232532213760 | 723910656 |
| layers.{i}.attn.indexer.weights_proj.weight | muon | [64, 4096] | 21 | [64, 4096] | 1 | 5505024 | 14202961920 | 173236224 |
| layers.{i}.attn.indexer.wq_b.weight | muon | [8192, 1024] | 21 | [8192, 1024] | 1 | 176160768 | 7666516623360 | 6121586688 |
| layers.{i}.attn.compressor.ape | muon | [128, 512] | 20 | [128, 512] | 1 | 1310720 | 7549747200 | 50462720 |
| layers.{i}.ffn.gate.bias | external_router_bias | [256] | 40 | [256] | 1 | 10240 | 0 | unknown |
| layers.{i}.attn.compressor.wgate.weight | muon | [512, 4096] | 20 | [512, 4096] | 1 | 41943040 | 912680550400 | 1457520640 |
| layers.{i}.attn.compressor.wkv.weight | muon | [512, 4096] | 20 | [512, 4096] | 1 | 41943040 | 912680550400 | 1457520640 |
| hc_head_base | adamw | [4] | 1 | [4] | 1 | 4 | 0 | 56 |
| hc_head_fn | unresolved | [4, 16384] | 1 | [4, 16384] | 1 | 65536 | 0 | unknown |
| hc_head_scale | adamw | [1] | 1 | [1] | 1 | 1 | 0 | 14 |
| head.weight | adamw | [129280, 4096] | 1 | [129280, 4096] | 1 | 529530880 | 0 | 7413432320 |
| norm.weight | adamw | [4096] | 1 | [4096] | 1 | 4096 | 0 | 57344 |

Complete per-matrix operations, state, interface bytes, assumptions and source hashes:

```json
{
  "schema": "v4-optimizer-reference-v1",
  "scenario": {
    "model": "deepseek-v4-flash",
    "include_mtp": false,
    "orientation": "smaller_gram",
    "wo_a_partition": "source_groups",
    "sink_policy": "unresolved",
    "head_mixer_policy": "unresolved",
    "learning_rate": 0.00027,
    "norm_epsilon": 0.0,
    "adam_step": 1
  },
  "groups": [
    {
      "owner": "base",
      "name_pattern": "embed.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        129280,
        4096
      ],
      "independent_matrix_shape": [
        129280,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 1,
      "parameters": 529530880,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "embed.weight",
      "ordinary_scalar_operations": 7413432320,
      "special_operations": {
        "sqrt": 529530880
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.attn_sink",
      "optimizer": "unresolved",
      "logical_tensor_shape": [
        64
      ],
      "independent_matrix_shape": [
        64
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 2752,
      "reason": "report omits vector matrixization; row_muon is explicit assumption",
      "example_tensor": "layers.0.attn.attn_sink"
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.hc_attn_base",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        24
      ],
      "independent_matrix_shape": [
        24
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 1032,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.hc_attn_base",
      "ordinary_scalar_operations": 14448,
      "special_operations": {
        "sqrt": 1032
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.hc_attn_fn",
      "optimizer": "muon",
      "logical_tensor_shape": [
        24,
        16384
      ],
      "independent_matrix_shape": [
        24,
        16384
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 16908288,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.hc_attn_fn",
      "per_matrix_reference": {
        "oriented_shape": [
          24,
          16384
        ],
        "parameters": 393216,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              24,
              24,
              16384
            ],
            "flops": 18874368
          },
          {
            "name": "B=A@A",
            "mnk": [
              24,
              24,
              24
            ],
            "flops": 27648
          },
          {
            "name": "C@X",
            "mnk": [
              24,
              16384,
              24
            ],
            "flops": 18874368
          }
        ],
        "matrix_flops": 377763840,
        "ordinary_scalar_operations": 12206976,
        "scalar_detail": {
          "momentum_and_nesterov": 1572864,
          "frobenius_square_sum_epsilon_divide": 1179648,
          "polynomial_combine": 7881600,
          "rescale_decay_update": 1572864
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 1572864,
          "momentum": 1572864
        },
        "fp32_gradient_input_bytes": 1572864,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 4725504,
          "gemm_outputs": 1577472,
          "scalar_combine_reads": 3150336,
          "scalar_combine_writes": 1575168
        },
        "individual_temporary_bytes": {
          "X": 1572864,
          "A": 2304,
          "B": 2304,
          "C": 2304,
          "CX": 1572864
        }
      },
      "matrix_count": 43,
      "matrix_flops": 16243845120,
      "ordinary_scalar_operations": 524899968
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.hc_attn_scale",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        3
      ],
      "independent_matrix_shape": [
        3
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 129,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.hc_attn_scale",
      "ordinary_scalar_operations": 1806,
      "special_operations": {
        "sqrt": 129
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.hc_ffn_base",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        24
      ],
      "independent_matrix_shape": [
        24
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 1032,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.hc_ffn_base",
      "ordinary_scalar_operations": 14448,
      "special_operations": {
        "sqrt": 1032
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.hc_ffn_fn",
      "optimizer": "muon",
      "logical_tensor_shape": [
        24,
        16384
      ],
      "independent_matrix_shape": [
        24,
        16384
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 16908288,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.hc_ffn_fn",
      "per_matrix_reference": {
        "oriented_shape": [
          24,
          16384
        ],
        "parameters": 393216,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              24,
              24,
              16384
            ],
            "flops": 18874368
          },
          {
            "name": "B=A@A",
            "mnk": [
              24,
              24,
              24
            ],
            "flops": 27648
          },
          {
            "name": "C@X",
            "mnk": [
              24,
              16384,
              24
            ],
            "flops": 18874368
          }
        ],
        "matrix_flops": 377763840,
        "ordinary_scalar_operations": 12206976,
        "scalar_detail": {
          "momentum_and_nesterov": 1572864,
          "frobenius_square_sum_epsilon_divide": 1179648,
          "polynomial_combine": 7881600,
          "rescale_decay_update": 1572864
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 1572864,
          "momentum": 1572864
        },
        "fp32_gradient_input_bytes": 1572864,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 4725504,
          "gemm_outputs": 1577472,
          "scalar_combine_reads": 3150336,
          "scalar_combine_writes": 1575168
        },
        "individual_temporary_bytes": {
          "X": 1572864,
          "A": 2304,
          "B": 2304,
          "C": 2304,
          "CX": 1572864
        }
      },
      "matrix_count": 43,
      "matrix_flops": 16243845120,
      "ordinary_scalar_operations": 524899968
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.hc_ffn_scale",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        3
      ],
      "independent_matrix_shape": [
        3
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 129,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.hc_ffn_scale",
      "ordinary_scalar_operations": 1806,
      "special_operations": {
        "sqrt": 129
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.kv_norm.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        512
      ],
      "independent_matrix_shape": [
        512
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 22016,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.attn.kv_norm.weight",
      "ordinary_scalar_operations": 308224,
      "special_operations": {
        "sqrt": 22016
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.q_norm.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        1024
      ],
      "independent_matrix_shape": [
        1024
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 44032,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.attn.q_norm.weight",
      "ordinary_scalar_operations": 616448,
      "special_operations": {
        "sqrt": 44032
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn_norm.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        4096
      ],
      "independent_matrix_shape": [
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 176128,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.attn_norm.weight",
      "ordinary_scalar_operations": 2465792,
      "special_operations": {
        "sqrt": 176128
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.gate.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        256,
        4096
      ],
      "independent_matrix_shape": [
        256,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 45088768,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.gate.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          256,
          4096
        ],
        "parameters": 1048576,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              256,
              256,
              4096
            ],
            "flops": 536870912
          },
          {
            "name": "B=A@A",
            "mnk": [
              256,
              256,
              256
            ],
            "flops": 33554432
          },
          {
            "name": "C@X",
            "mnk": [
              256,
              4096,
              256
            ],
            "flops": 536870912
          }
        ],
        "matrix_flops": 11072962560,
        "ordinary_scalar_operations": 34471936,
        "scalar_detail": {
          "momentum_and_nesterov": 4194304,
          "frobenius_square_sum_epsilon_divide": 3145728,
          "polynomial_combine": 22937600,
          "rescale_decay_update": 4194304
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 4194304,
          "momentum": 4194304
        },
        "fp32_gradient_input_bytes": 4194304,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 13369344,
          "gemm_outputs": 4718592,
          "scalar_combine_reads": 8912896,
          "scalar_combine_writes": 4456448
        },
        "individual_temporary_bytes": {
          "X": 4194304,
          "A": 262144,
          "B": 262144,
          "C": 262144,
          "CX": 4194304
        }
      },
      "matrix_count": 43,
      "matrix_flops": 476137390080,
      "ordinary_scalar_operations": 1482293248
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn_norm.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        4096
      ],
      "independent_matrix_shape": [
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 176128,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.ffn_norm.weight",
      "ordinary_scalar_operations": 2465792,
      "special_operations": {
        "sqrt": 176128
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.wkv.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        512,
        4096
      ],
      "independent_matrix_shape": [
        512,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 90177536,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.wkv.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          512,
          4096
        ],
        "parameters": 2097152,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              512,
              512,
              4096
            ],
            "flops": 2147483648
          },
          {
            "name": "B=A@A",
            "mnk": [
              512,
              512,
              512
            ],
            "flops": 268435456
          },
          {
            "name": "C@X",
            "mnk": [
              512,
              4096,
              512
            ],
            "flops": 2147483648
          }
        ],
        "matrix_flops": 45634027520,
        "ordinary_scalar_operations": 72876032,
        "scalar_detail": {
          "momentum_and_nesterov": 8388608,
          "frobenius_square_sum_epsilon_divide": 6291456,
          "polynomial_combine": 49807360,
          "rescale_decay_update": 8388608
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 8388608,
          "momentum": 8388608
        },
        "fp32_gradient_input_bytes": 8388608,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 28311552,
          "gemm_outputs": 10485760,
          "scalar_combine_reads": 18874368,
          "scalar_combine_writes": 9437184
        },
        "individual_temporary_bytes": {
          "X": 8388608,
          "A": 1048576,
          "B": 1048576,
          "C": 1048576,
          "CX": 8388608
        }
      },
      "matrix_count": 43,
      "matrix_flops": 1962263183360,
      "ordinary_scalar_operations": 3133669376
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.wo_a.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        8192,
        4096
      ],
      "independent_matrix_shape": [
        1024,
        4096
      ],
      "independent_matrices_per_tensor": 8,
      "tensor_count": 43,
      "parameters": 1442840576,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.wo_a.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          1024,
          4096
        ],
        "parameters": 4194304,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1024,
              1024,
              4096
            ],
            "flops": 8589934592
          },
          {
            "name": "B=A@A",
            "mnk": [
              1024,
              1024,
              1024
            ],
            "flops": 2147483648
          },
          {
            "name": "C@X",
            "mnk": [
              1024,
              4096,
              1024
            ],
            "flops": 8589934592
          }
        ],
        "matrix_flops": 193273528320,
        "ordinary_scalar_operations": 161480704,
        "scalar_detail": {
          "momentum_and_nesterov": 16777216,
          "frobenius_square_sum_epsilon_divide": 12582912,
          "polynomial_combine": 115343360,
          "rescale_decay_update": 16777216
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 16777216,
          "momentum": 16777216
        },
        "fp32_gradient_input_bytes": 16777216,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 62914560,
          "gemm_outputs": 25165824,
          "scalar_combine_reads": 41943040,
          "scalar_combine_writes": 20971520
        },
        "individual_temporary_bytes": {
          "X": 16777216,
          "A": 4194304,
          "B": 4194304,
          "C": 4194304,
          "CX": 16777216
        }
      },
      "matrix_count": 344,
      "matrix_flops": 66486093742080,
      "ordinary_scalar_operations": 55549362176
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.wo_b.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        4096,
        8192
      ],
      "independent_matrix_shape": [
        4096,
        8192
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 1442840576,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.wo_b.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          4096,
          8192
        ],
        "parameters": 33554432,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              4096,
              4096,
              8192
            ],
            "flops": 274877906944
          },
          {
            "name": "B=A@A",
            "mnk": [
              4096,
              4096,
              4096
            ],
            "flops": 137438953472
          },
          {
            "name": "C@X",
            "mnk": [
              4096,
              8192,
              4096
            ],
            "flops": 274877906944
          }
        ],
        "matrix_flops": 6871947673600,
        "ordinary_scalar_operations": 1543503872,
        "scalar_detail": {
          "momentum_and_nesterov": 134217728,
          "frobenius_square_sum_epsilon_divide": 100663296,
          "polynomial_combine": 1174405120,
          "rescale_decay_update": 134217728
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 134217728,
          "momentum": 134217728
        },
        "fp32_gradient_input_bytes": 134217728,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 603979776,
          "gemm_outputs": 268435456,
          "scalar_combine_reads": 402653184,
          "scalar_combine_writes": 201326592
        },
        "individual_temporary_bytes": {
          "X": 134217728,
          "A": 67108864,
          "B": 67108864,
          "C": 67108864,
          "CX": 134217728
        }
      },
      "matrix_count": 43,
      "matrix_flops": 295493749964800,
      "ordinary_scalar_operations": 66370666496
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.wq_a.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        1024,
        4096
      ],
      "independent_matrix_shape": [
        1024,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 180355072,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.wq_a.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          1024,
          4096
        ],
        "parameters": 4194304,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1024,
              1024,
              4096
            ],
            "flops": 8589934592
          },
          {
            "name": "B=A@A",
            "mnk": [
              1024,
              1024,
              1024
            ],
            "flops": 2147483648
          },
          {
            "name": "C@X",
            "mnk": [
              1024,
              4096,
              1024
            ],
            "flops": 8589934592
          }
        ],
        "matrix_flops": 193273528320,
        "ordinary_scalar_operations": 161480704,
        "scalar_detail": {
          "momentum_and_nesterov": 16777216,
          "frobenius_square_sum_epsilon_divide": 12582912,
          "polynomial_combine": 115343360,
          "rescale_decay_update": 16777216
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 16777216,
          "momentum": 16777216
        },
        "fp32_gradient_input_bytes": 16777216,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 62914560,
          "gemm_outputs": 25165824,
          "scalar_combine_reads": 41943040,
          "scalar_combine_writes": 20971520
        },
        "individual_temporary_bytes": {
          "X": 16777216,
          "A": 4194304,
          "B": 4194304,
          "C": 4194304,
          "CX": 16777216
        }
      },
      "matrix_count": 43,
      "matrix_flops": 8310761717760,
      "ordinary_scalar_operations": 6943670272
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.wq_b.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        32768,
        1024
      ],
      "independent_matrix_shape": [
        32768,
        1024
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 1442840576,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.wq_b.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          1024,
          32768
        ],
        "parameters": 33554432,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1024,
              1024,
              32768
            ],
            "flops": 68719476736
          },
          {
            "name": "B=A@A",
            "mnk": [
              1024,
              1024,
              1024
            ],
            "flops": 2147483648
          },
          {
            "name": "C@X",
            "mnk": [
              1024,
              32768,
              1024
            ],
            "flops": 68719476736
          }
        ],
        "matrix_flops": 1395864371200,
        "ordinary_scalar_operations": 1071644672,
        "scalar_detail": {
          "momentum_and_nesterov": 134217728,
          "frobenius_square_sum_epsilon_divide": 100663296,
          "polynomial_combine": 702545920,
          "rescale_decay_update": 134217728
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 134217728,
          "momentum": 134217728
        },
        "fp32_gradient_input_bytes": 134217728,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 415236096,
          "gemm_outputs": 142606336,
          "scalar_combine_reads": 276824064,
          "scalar_combine_writes": 138412032
        },
        "individual_temporary_bytes": {
          "X": 134217728,
          "A": 4194304,
          "B": 4194304,
          "C": 4194304,
          "CX": 134217728
        }
      },
      "matrix_count": 43,
      "matrix_flops": 60022167961600,
      "ordinary_scalar_operations": 46080720896
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.shared_experts.w1.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        2048,
        4096
      ],
      "independent_matrix_shape": [
        2048,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 360710144,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.shared_experts.w1.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          2048,
          4096
        ],
        "parameters": 8388608,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              2048,
              2048,
              4096
            ],
            "flops": 34359738368
          },
          {
            "name": "B=A@A",
            "mnk": [
              2048,
              2048,
              2048
            ],
            "flops": 17179869184
          },
          {
            "name": "C@X",
            "mnk": [
              2048,
              4096,
              2048
            ],
            "flops": 34359738368
          }
        ],
        "matrix_flops": 858993459200,
        "ordinary_scalar_operations": 385875968,
        "scalar_detail": {
          "momentum_and_nesterov": 33554432,
          "frobenius_square_sum_epsilon_divide": 25165824,
          "polynomial_combine": 293601280,
          "rescale_decay_update": 33554432
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 33554432,
          "momentum": 33554432
        },
        "fp32_gradient_input_bytes": 33554432,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 150994944,
          "gemm_outputs": 67108864,
          "scalar_combine_reads": 100663296,
          "scalar_combine_writes": 50331648
        },
        "individual_temporary_bytes": {
          "X": 33554432,
          "A": 16777216,
          "B": 16777216,
          "C": 16777216,
          "CX": 33554432
        }
      },
      "matrix_count": 43,
      "matrix_flops": 36936718745600,
      "ordinary_scalar_operations": 16592666624
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.shared_experts.w2.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        4096,
        2048
      ],
      "independent_matrix_shape": [
        4096,
        2048
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 360710144,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.shared_experts.w2.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          2048,
          4096
        ],
        "parameters": 8388608,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              2048,
              2048,
              4096
            ],
            "flops": 34359738368
          },
          {
            "name": "B=A@A",
            "mnk": [
              2048,
              2048,
              2048
            ],
            "flops": 17179869184
          },
          {
            "name": "C@X",
            "mnk": [
              2048,
              4096,
              2048
            ],
            "flops": 34359738368
          }
        ],
        "matrix_flops": 858993459200,
        "ordinary_scalar_operations": 385875968,
        "scalar_detail": {
          "momentum_and_nesterov": 33554432,
          "frobenius_square_sum_epsilon_divide": 25165824,
          "polynomial_combine": 293601280,
          "rescale_decay_update": 33554432
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 33554432,
          "momentum": 33554432
        },
        "fp32_gradient_input_bytes": 33554432,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 150994944,
          "gemm_outputs": 67108864,
          "scalar_combine_reads": 100663296,
          "scalar_combine_writes": 50331648
        },
        "individual_temporary_bytes": {
          "X": 33554432,
          "A": 16777216,
          "B": 16777216,
          "C": 16777216,
          "CX": 33554432
        }
      },
      "matrix_count": 43,
      "matrix_flops": 36936718745600,
      "ordinary_scalar_operations": 16592666624
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.shared_experts.w3.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        2048,
        4096
      ],
      "independent_matrix_shape": [
        2048,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 43,
      "parameters": 360710144,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.shared_experts.w3.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          2048,
          4096
        ],
        "parameters": 8388608,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              2048,
              2048,
              4096
            ],
            "flops": 34359738368
          },
          {
            "name": "B=A@A",
            "mnk": [
              2048,
              2048,
              2048
            ],
            "flops": 17179869184
          },
          {
            "name": "C@X",
            "mnk": [
              2048,
              4096,
              2048
            ],
            "flops": 34359738368
          }
        ],
        "matrix_flops": 858993459200,
        "ordinary_scalar_operations": 385875968,
        "scalar_detail": {
          "momentum_and_nesterov": 33554432,
          "frobenius_square_sum_epsilon_divide": 25165824,
          "polynomial_combine": 293601280,
          "rescale_decay_update": 33554432
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 33554432,
          "momentum": 33554432
        },
        "fp32_gradient_input_bytes": 33554432,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 150994944,
          "gemm_outputs": 67108864,
          "scalar_combine_reads": 100663296,
          "scalar_combine_writes": 50331648
        },
        "individual_temporary_bytes": {
          "X": 33554432,
          "A": 16777216,
          "B": 16777216,
          "C": 16777216,
          "CX": 33554432
        }
      },
      "matrix_count": 43,
      "matrix_flops": 36936718745600,
      "ordinary_scalar_operations": 16592666624
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.experts.{i}.w1.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        2048,
        4096
      ],
      "independent_matrix_shape": [
        2048,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 11008,
      "parameters": 92341796864,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.experts.0.w1.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          2048,
          4096
        ],
        "parameters": 8388608,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              2048,
              2048,
              4096
            ],
            "flops": 34359738368
          },
          {
            "name": "B=A@A",
            "mnk": [
              2048,
              2048,
              2048
            ],
            "flops": 17179869184
          },
          {
            "name": "C@X",
            "mnk": [
              2048,
              4096,
              2048
            ],
            "flops": 34359738368
          }
        ],
        "matrix_flops": 858993459200,
        "ordinary_scalar_operations": 385875968,
        "scalar_detail": {
          "momentum_and_nesterov": 33554432,
          "frobenius_square_sum_epsilon_divide": 25165824,
          "polynomial_combine": 293601280,
          "rescale_decay_update": 33554432
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 33554432,
          "momentum": 33554432
        },
        "fp32_gradient_input_bytes": 33554432,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 150994944,
          "gemm_outputs": 67108864,
          "scalar_combine_reads": 100663296,
          "scalar_combine_writes": 50331648
        },
        "individual_temporary_bytes": {
          "X": 33554432,
          "A": 16777216,
          "B": 16777216,
          "C": 16777216,
          "CX": 33554432
        }
      },
      "matrix_count": 11008,
      "matrix_flops": 9455799998873600,
      "ordinary_scalar_operations": 4247722655744
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.experts.{i}.w2.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        4096,
        2048
      ],
      "independent_matrix_shape": [
        4096,
        2048
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 11008,
      "parameters": 92341796864,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.experts.0.w2.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          2048,
          4096
        ],
        "parameters": 8388608,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              2048,
              2048,
              4096
            ],
            "flops": 34359738368
          },
          {
            "name": "B=A@A",
            "mnk": [
              2048,
              2048,
              2048
            ],
            "flops": 17179869184
          },
          {
            "name": "C@X",
            "mnk": [
              2048,
              4096,
              2048
            ],
            "flops": 34359738368
          }
        ],
        "matrix_flops": 858993459200,
        "ordinary_scalar_operations": 385875968,
        "scalar_detail": {
          "momentum_and_nesterov": 33554432,
          "frobenius_square_sum_epsilon_divide": 25165824,
          "polynomial_combine": 293601280,
          "rescale_decay_update": 33554432
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 33554432,
          "momentum": 33554432
        },
        "fp32_gradient_input_bytes": 33554432,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 150994944,
          "gemm_outputs": 67108864,
          "scalar_combine_reads": 100663296,
          "scalar_combine_writes": 50331648
        },
        "individual_temporary_bytes": {
          "X": 33554432,
          "A": 16777216,
          "B": 16777216,
          "C": 16777216,
          "CX": 33554432
        }
      },
      "matrix_count": 11008,
      "matrix_flops": 9455799998873600,
      "ordinary_scalar_operations": 4247722655744
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.experts.{i}.w3.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        2048,
        4096
      ],
      "independent_matrix_shape": [
        2048,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 11008,
      "parameters": 92341796864,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.experts.0.w3.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          2048,
          4096
        ],
        "parameters": 8388608,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              2048,
              2048,
              4096
            ],
            "flops": 34359738368
          },
          {
            "name": "B=A@A",
            "mnk": [
              2048,
              2048,
              2048
            ],
            "flops": 17179869184
          },
          {
            "name": "C@X",
            "mnk": [
              2048,
              4096,
              2048
            ],
            "flops": 34359738368
          }
        ],
        "matrix_flops": 858993459200,
        "ordinary_scalar_operations": 385875968,
        "scalar_detail": {
          "momentum_and_nesterov": 33554432,
          "frobenius_square_sum_epsilon_divide": 25165824,
          "polynomial_combine": 293601280,
          "rescale_decay_update": 33554432
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 33554432,
          "momentum": 33554432
        },
        "fp32_gradient_input_bytes": 33554432,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 150994944,
          "gemm_outputs": 67108864,
          "scalar_combine_reads": 100663296,
          "scalar_combine_writes": 50331648
        },
        "individual_temporary_bytes": {
          "X": 33554432,
          "A": 16777216,
          "B": 16777216,
          "C": 16777216,
          "CX": 33554432
        }
      },
      "matrix_count": 11008,
      "matrix_flops": 9455799998873600,
      "ordinary_scalar_operations": 4247722655744
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.compressor.ape",
      "optimizer": "muon",
      "logical_tensor_shape": [
        4,
        1024
      ],
      "independent_matrix_shape": [
        4,
        1024
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 21,
      "parameters": 86016,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.compressor.ape",
      "per_matrix_reference": {
        "oriented_shape": [
          4,
          1024
        ],
        "parameters": 4096,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              4,
              4,
              1024
            ],
            "flops": 32768
          },
          {
            "name": "B=A@A",
            "mnk": [
              4,
              4,
              4
            ],
            "flops": 128
          },
          {
            "name": "C@X",
            "mnk": [
              4,
              1024,
              4
            ],
            "flops": 32768
          }
        ],
        "matrix_flops": 656640,
        "ordinary_scalar_operations": 127456,
        "scalar_detail": {
          "momentum_and_nesterov": 16384,
          "frobenius_square_sum_epsilon_divide": 12288,
          "polynomial_combine": 82400,
          "rescale_decay_update": 16384
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 16384,
          "momentum": 16384
        },
        "fp32_gradient_input_bytes": 16384,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 49344,
          "gemm_outputs": 16512,
          "scalar_combine_reads": 32896,
          "scalar_combine_writes": 16448
        },
        "individual_temporary_bytes": {
          "X": 16384,
          "A": 64,
          "B": 64,
          "C": 64,
          "CX": 16384
        }
      },
      "matrix_count": 21,
      "matrix_flops": 13789440,
      "ordinary_scalar_operations": 2676576
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.indexer.compressor.ape",
      "optimizer": "muon",
      "logical_tensor_shape": [
        4,
        256
      ],
      "independent_matrix_shape": [
        4,
        256
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 21,
      "parameters": 21504,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.indexer.compressor.ape",
      "per_matrix_reference": {
        "oriented_shape": [
          4,
          256
        ],
        "parameters": 1024,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              4,
              4,
              256
            ],
            "flops": 8192
          },
          {
            "name": "B=A@A",
            "mnk": [
              4,
              4,
              4
            ],
            "flops": 128
          },
          {
            "name": "C@X",
            "mnk": [
              4,
              256,
              4
            ],
            "flops": 8192
          }
        ],
        "matrix_flops": 165120,
        "ordinary_scalar_operations": 32224,
        "scalar_detail": {
          "momentum_and_nesterov": 4096,
          "frobenius_square_sum_epsilon_divide": 3072,
          "polynomial_combine": 20960,
          "rescale_decay_update": 4096
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 4096,
          "momentum": 4096
        },
        "fp32_gradient_input_bytes": 4096,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 12480,
          "gemm_outputs": 4224,
          "scalar_combine_reads": 8320,
          "scalar_combine_writes": 4160
        },
        "individual_temporary_bytes": {
          "X": 4096,
          "A": 64,
          "B": 64,
          "C": 64,
          "CX": 4096
        }
      },
      "matrix_count": 21,
      "matrix_flops": 3467520,
      "ordinary_scalar_operations": 676704
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.compressor.norm.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        512
      ],
      "independent_matrix_shape": [
        512
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 41,
      "parameters": 20992,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.2.attn.compressor.norm.weight",
      "ordinary_scalar_operations": 293888,
      "special_operations": {
        "sqrt": 20992
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.compressor.wgate.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        1024,
        4096
      ],
      "independent_matrix_shape": [
        1024,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 21,
      "parameters": 88080384,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.compressor.wgate.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          1024,
          4096
        ],
        "parameters": 4194304,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1024,
              1024,
              4096
            ],
            "flops": 8589934592
          },
          {
            "name": "B=A@A",
            "mnk": [
              1024,
              1024,
              1024
            ],
            "flops": 2147483648
          },
          {
            "name": "C@X",
            "mnk": [
              1024,
              4096,
              1024
            ],
            "flops": 8589934592
          }
        ],
        "matrix_flops": 193273528320,
        "ordinary_scalar_operations": 161480704,
        "scalar_detail": {
          "momentum_and_nesterov": 16777216,
          "frobenius_square_sum_epsilon_divide": 12582912,
          "polynomial_combine": 115343360,
          "rescale_decay_update": 16777216
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 16777216,
          "momentum": 16777216
        },
        "fp32_gradient_input_bytes": 16777216,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 62914560,
          "gemm_outputs": 25165824,
          "scalar_combine_reads": 41943040,
          "scalar_combine_writes": 20971520
        },
        "individual_temporary_bytes": {
          "X": 16777216,
          "A": 4194304,
          "B": 4194304,
          "C": 4194304,
          "CX": 16777216
        }
      },
      "matrix_count": 21,
      "matrix_flops": 4058744094720,
      "ordinary_scalar_operations": 3391094784
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.compressor.wkv.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        1024,
        4096
      ],
      "independent_matrix_shape": [
        1024,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 21,
      "parameters": 88080384,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.compressor.wkv.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          1024,
          4096
        ],
        "parameters": 4194304,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1024,
              1024,
              4096
            ],
            "flops": 8589934592
          },
          {
            "name": "B=A@A",
            "mnk": [
              1024,
              1024,
              1024
            ],
            "flops": 2147483648
          },
          {
            "name": "C@X",
            "mnk": [
              1024,
              4096,
              1024
            ],
            "flops": 8589934592
          }
        ],
        "matrix_flops": 193273528320,
        "ordinary_scalar_operations": 161480704,
        "scalar_detail": {
          "momentum_and_nesterov": 16777216,
          "frobenius_square_sum_epsilon_divide": 12582912,
          "polynomial_combine": 115343360,
          "rescale_decay_update": 16777216
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 16777216,
          "momentum": 16777216
        },
        "fp32_gradient_input_bytes": 16777216,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 62914560,
          "gemm_outputs": 25165824,
          "scalar_combine_reads": 41943040,
          "scalar_combine_writes": 20971520
        },
        "individual_temporary_bytes": {
          "X": 16777216,
          "A": 4194304,
          "B": 4194304,
          "C": 4194304,
          "CX": 16777216
        }
      },
      "matrix_count": 21,
      "matrix_flops": 4058744094720,
      "ordinary_scalar_operations": 3391094784
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.indexer.compressor.norm.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        128
      ],
      "independent_matrix_shape": [
        128
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 21,
      "parameters": 2688,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.2.attn.indexer.compressor.norm.weight",
      "ordinary_scalar_operations": 37632,
      "special_operations": {
        "sqrt": 2688
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.indexer.compressor.wgate.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        256,
        4096
      ],
      "independent_matrix_shape": [
        256,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 21,
      "parameters": 22020096,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.indexer.compressor.wgate.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          256,
          4096
        ],
        "parameters": 1048576,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              256,
              256,
              4096
            ],
            "flops": 536870912
          },
          {
            "name": "B=A@A",
            "mnk": [
              256,
              256,
              256
            ],
            "flops": 33554432
          },
          {
            "name": "C@X",
            "mnk": [
              256,
              4096,
              256
            ],
            "flops": 536870912
          }
        ],
        "matrix_flops": 11072962560,
        "ordinary_scalar_operations": 34471936,
        "scalar_detail": {
          "momentum_and_nesterov": 4194304,
          "frobenius_square_sum_epsilon_divide": 3145728,
          "polynomial_combine": 22937600,
          "rescale_decay_update": 4194304
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 4194304,
          "momentum": 4194304
        },
        "fp32_gradient_input_bytes": 4194304,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 13369344,
          "gemm_outputs": 4718592,
          "scalar_combine_reads": 8912896,
          "scalar_combine_writes": 4456448
        },
        "individual_temporary_bytes": {
          "X": 4194304,
          "A": 262144,
          "B": 262144,
          "C": 262144,
          "CX": 4194304
        }
      },
      "matrix_count": 21,
      "matrix_flops": 232532213760,
      "ordinary_scalar_operations": 723910656
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.indexer.compressor.wkv.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        256,
        4096
      ],
      "independent_matrix_shape": [
        256,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 21,
      "parameters": 22020096,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.indexer.compressor.wkv.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          256,
          4096
        ],
        "parameters": 1048576,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              256,
              256,
              4096
            ],
            "flops": 536870912
          },
          {
            "name": "B=A@A",
            "mnk": [
              256,
              256,
              256
            ],
            "flops": 33554432
          },
          {
            "name": "C@X",
            "mnk": [
              256,
              4096,
              256
            ],
            "flops": 536870912
          }
        ],
        "matrix_flops": 11072962560,
        "ordinary_scalar_operations": 34471936,
        "scalar_detail": {
          "momentum_and_nesterov": 4194304,
          "frobenius_square_sum_epsilon_divide": 3145728,
          "polynomial_combine": 22937600,
          "rescale_decay_update": 4194304
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 4194304,
          "momentum": 4194304
        },
        "fp32_gradient_input_bytes": 4194304,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 13369344,
          "gemm_outputs": 4718592,
          "scalar_combine_reads": 8912896,
          "scalar_combine_writes": 4456448
        },
        "individual_temporary_bytes": {
          "X": 4194304,
          "A": 262144,
          "B": 262144,
          "C": 262144,
          "CX": 4194304
        }
      },
      "matrix_count": 21,
      "matrix_flops": 232532213760,
      "ordinary_scalar_operations": 723910656
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.indexer.weights_proj.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        64,
        4096
      ],
      "independent_matrix_shape": [
        64,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 21,
      "parameters": 5505024,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.indexer.weights_proj.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          64,
          4096
        ],
        "parameters": 262144,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              64,
              64,
              4096
            ],
            "flops": 33554432
          },
          {
            "name": "B=A@A",
            "mnk": [
              64,
              64,
              64
            ],
            "flops": 524288
          },
          {
            "name": "C@X",
            "mnk": [
              64,
              4096,
              64
            ],
            "flops": 33554432
          }
        ],
        "matrix_flops": 676331520,
        "ordinary_scalar_operations": 8249344,
        "scalar_detail": {
          "momentum_and_nesterov": 1048576,
          "frobenius_square_sum_epsilon_divide": 786432,
          "polynomial_combine": 5365760,
          "rescale_decay_update": 1048576
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 1048576,
          "momentum": 1048576
        },
        "fp32_gradient_input_bytes": 1048576,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 3194880,
          "gemm_outputs": 1081344,
          "scalar_combine_reads": 2129920,
          "scalar_combine_writes": 1064960
        },
        "individual_temporary_bytes": {
          "X": 1048576,
          "A": 16384,
          "B": 16384,
          "C": 16384,
          "CX": 1048576
        }
      },
      "matrix_count": 21,
      "matrix_flops": 14202961920,
      "ordinary_scalar_operations": 173236224
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.indexer.wq_b.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        8192,
        1024
      ],
      "independent_matrix_shape": [
        8192,
        1024
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 21,
      "parameters": 176160768,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.indexer.wq_b.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          1024,
          8192
        ],
        "parameters": 8388608,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1024,
              1024,
              8192
            ],
            "flops": 17179869184
          },
          {
            "name": "B=A@A",
            "mnk": [
              1024,
              1024,
              1024
            ],
            "flops": 2147483648
          },
          {
            "name": "C@X",
            "mnk": [
              1024,
              8192,
              1024
            ],
            "flops": 17179869184
          }
        ],
        "matrix_flops": 365072220160,
        "ordinary_scalar_operations": 291504128,
        "scalar_detail": {
          "momentum_and_nesterov": 33554432,
          "frobenius_square_sum_epsilon_divide": 25165824,
          "polynomial_combine": 199229440,
          "rescale_decay_update": 33554432
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 33554432,
          "momentum": 33554432
        },
        "fp32_gradient_input_bytes": 33554432,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 113246208,
          "gemm_outputs": 41943040,
          "scalar_combine_reads": 75497472,
          "scalar_combine_writes": 37748736
        },
        "individual_temporary_bytes": {
          "X": 33554432,
          "A": 4194304,
          "B": 4194304,
          "C": 4194304,
          "CX": 33554432
        }
      },
      "matrix_count": 21,
      "matrix_flops": 7666516623360,
      "ordinary_scalar_operations": 6121586688
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.compressor.ape",
      "optimizer": "muon",
      "logical_tensor_shape": [
        128,
        512
      ],
      "independent_matrix_shape": [
        128,
        512
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 20,
      "parameters": 1310720,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.3.attn.compressor.ape",
      "per_matrix_reference": {
        "oriented_shape": [
          128,
          512
        ],
        "parameters": 65536,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              128,
              128,
              512
            ],
            "flops": 16777216
          },
          {
            "name": "B=A@A",
            "mnk": [
              128,
              128,
              128
            ],
            "flops": 4194304
          },
          {
            "name": "C@X",
            "mnk": [
              128,
              512,
              128
            ],
            "flops": 16777216
          }
        ],
        "matrix_flops": 377487360,
        "ordinary_scalar_operations": 2523136,
        "scalar_detail": {
          "momentum_and_nesterov": 262144,
          "frobenius_square_sum_epsilon_divide": 196608,
          "polynomial_combine": 1802240,
          "rescale_decay_update": 262144
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 262144,
          "momentum": 262144
        },
        "fp32_gradient_input_bytes": 262144,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 983040,
          "gemm_outputs": 393216,
          "scalar_combine_reads": 655360,
          "scalar_combine_writes": 327680
        },
        "individual_temporary_bytes": {
          "X": 262144,
          "A": 65536,
          "B": 65536,
          "C": 65536,
          "CX": 262144
        }
      },
      "matrix_count": 20,
      "matrix_flops": 7549747200,
      "ordinary_scalar_operations": 50462720
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.gate.bias",
      "optimizer": "external_router_bias",
      "logical_tensor_shape": [
        256
      ],
      "independent_matrix_shape": [
        256
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 40,
      "parameters": 10240,
      "reason": "auxiliary-loss-free load balancing update, not differentiable route selection",
      "example_tensor": "layers.3.ffn.gate.bias"
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.compressor.wgate.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        512,
        4096
      ],
      "independent_matrix_shape": [
        512,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 20,
      "parameters": 41943040,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.3.attn.compressor.wgate.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          512,
          4096
        ],
        "parameters": 2097152,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              512,
              512,
              4096
            ],
            "flops": 2147483648
          },
          {
            "name": "B=A@A",
            "mnk": [
              512,
              512,
              512
            ],
            "flops": 268435456
          },
          {
            "name": "C@X",
            "mnk": [
              512,
              4096,
              512
            ],
            "flops": 2147483648
          }
        ],
        "matrix_flops": 45634027520,
        "ordinary_scalar_operations": 72876032,
        "scalar_detail": {
          "momentum_and_nesterov": 8388608,
          "frobenius_square_sum_epsilon_divide": 6291456,
          "polynomial_combine": 49807360,
          "rescale_decay_update": 8388608
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 8388608,
          "momentum": 8388608
        },
        "fp32_gradient_input_bytes": 8388608,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 28311552,
          "gemm_outputs": 10485760,
          "scalar_combine_reads": 18874368,
          "scalar_combine_writes": 9437184
        },
        "individual_temporary_bytes": {
          "X": 8388608,
          "A": 1048576,
          "B": 1048576,
          "C": 1048576,
          "CX": 8388608
        }
      },
      "matrix_count": 20,
      "matrix_flops": 912680550400,
      "ordinary_scalar_operations": 1457520640
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.compressor.wkv.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        512,
        4096
      ],
      "independent_matrix_shape": [
        512,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 20,
      "parameters": 41943040,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.3.attn.compressor.wkv.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          512,
          4096
        ],
        "parameters": 2097152,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              512,
              512,
              4096
            ],
            "flops": 2147483648
          },
          {
            "name": "B=A@A",
            "mnk": [
              512,
              512,
              512
            ],
            "flops": 268435456
          },
          {
            "name": "C@X",
            "mnk": [
              512,
              4096,
              512
            ],
            "flops": 2147483648
          }
        ],
        "matrix_flops": 45634027520,
        "ordinary_scalar_operations": 72876032,
        "scalar_detail": {
          "momentum_and_nesterov": 8388608,
          "frobenius_square_sum_epsilon_divide": 6291456,
          "polynomial_combine": 49807360,
          "rescale_decay_update": 8388608
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 8388608,
          "momentum": 8388608
        },
        "fp32_gradient_input_bytes": 8388608,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 28311552,
          "gemm_outputs": 10485760,
          "scalar_combine_reads": 18874368,
          "scalar_combine_writes": 9437184
        },
        "individual_temporary_bytes": {
          "X": 8388608,
          "A": 1048576,
          "B": 1048576,
          "C": 1048576,
          "CX": 8388608
        }
      },
      "matrix_count": 20,
      "matrix_flops": 912680550400,
      "ordinary_scalar_operations": 1457520640
    },
    {
      "owner": "base",
      "name_pattern": "hc_head_base",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        4
      ],
      "independent_matrix_shape": [
        4
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 1,
      "parameters": 4,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "hc_head_base",
      "ordinary_scalar_operations": 56,
      "special_operations": {
        "sqrt": 4
      }
    },
    {
      "owner": "base",
      "name_pattern": "hc_head_fn",
      "optimizer": "unresolved",
      "logical_tensor_shape": [
        4,
        16384
      ],
      "independent_matrix_shape": [
        4,
        16384
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 1,
      "parameters": 65536,
      "reason": "head module versus mHC projection boundary explicitly selected",
      "example_tensor": "hc_head_fn"
    },
    {
      "owner": "base",
      "name_pattern": "hc_head_scale",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        1
      ],
      "independent_matrix_shape": [
        1
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 1,
      "parameters": 1,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "hc_head_scale",
      "ordinary_scalar_operations": 14,
      "special_operations": {
        "sqrt": 1
      }
    },
    {
      "owner": "base",
      "name_pattern": "head.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        129280,
        4096
      ],
      "independent_matrix_shape": [
        129280,
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 1,
      "parameters": 529530880,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "head.weight",
      "ordinary_scalar_operations": 7413432320,
      "special_operations": {
        "sqrt": 529530880
      }
    },
    {
      "owner": "base",
      "name_pattern": "norm.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        4096
      ],
      "independent_matrix_shape": [
        4096
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 1,
      "parameters": 4096,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "norm.weight",
      "ordinary_scalar_operations": 57344,
      "special_operations": {
        "sqrt": 4096
      }
    }
  ],
  "summary": {
    "muon_parameters": 283272651776,
    "adamw_parameters": 1059510167,
    "unresolved_parameters": 68288,
    "external_router_bias_parameters": 10240,
    "ordinary_scalar_operations": 13005882982922,
    "adam_sqrt": 1059510167,
    "matrix_flops": 28929090014814720,
    "normalization_sqrt": 34026,
    "shared_step_scalar_operations": 8,
    "shape_setup_scalar_multiply": 13,
    "shape_setup_sqrt": 13
  },
  "inventory": {
    "base_logical_parameters": 284332240471,
    "mtp_logical_parameters": 6610048891
  },
  "excluded_inventory": {
    "base_hash_elements": 2327040,
    "base_quant_scale_elements": 8657400960,
    "mtp_logical_parameters": 6610048891,
    "mtp_quant_scale_elements": 201336704
  },
  "checkpoint_verification": {
    "verified_tensors": 69187,
    "verified_shards": 46,
    "checkpoint_tensor_payload_bytes": 159609485896,
    "byte_groups": {
      "base_parameters_bytes": 147339680860,
      "base_total_bytes": 156015698140,
      "base_hash_table_bytes": 18616320,
      "base_quant_scales_bytes": 8657400960,
      "mtp_parameters_bytes": 3392451052,
      "mtp_total_bytes": 3593787756,
      "mtp_quant_scales_bytes": 201336704
    },
    "tensor_count_by_storage_dtype": {
      "BF16": 433,
      "I64": 3,
      "F32": 417,
      "F8_E8M0": 34167,
      "F8_E4M3": 375,
      "I8": 33792
    },
    "base_logical_parameters_excluding_scales_and_hash": 284332240471,
    "scope": "Official checkpoint tensor payload, excluding file headers and filesystem overhead. Includes separate MTP; runtime dtype conversion, aliasing and allocated model copies may differ. Payload values were not downloaded or numerically validated."
  },
  "state_interfaces": {
    "declared_fp32_master_weights_bytes": 1137328647772,
    "declared_fp32_muon_momentum_bytes": 1133090607104,
    "declared_fp32_adam_m_v_bytes": 8476081336,
    "declared_fp32_gradient_input_bytes": 1137328647772,
    "runtime_training_weight_copies_bytes": null,
    "distributed_padding_and_replication_bytes": null,
    "actual_peak_bytes": null,
    "actual_hbm_bytes": null
  },
  "algorithm": {
    "mu": 0.95,
    "weight_decay": 0.1,
    "gamma": 0.18,
    "adam_beta1": 0.9,
    "adam_beta2": 0.95,
    "adam_epsilon": 1e-20,
    "ns_coefficients": [
      [
        3.4445,
        -4.775,
        2.0315
      ],
      [
        3.4445,
        -4.775,
        2.0315
      ],
      [
        3.4445,
        -4.775,
        2.0315
      ],
      [
        3.4445,
        -4.775,
        2.0315
      ],
      [
        3.4445,
        -4.775,
        2.0315
      ],
      [
        3.4445,
        -4.775,
        2.0315
      ],
      [
        3.4445,
        -4.775,
        2.0315
      ],
      [
        3.4445,
        -4.775,
        2.0315
      ],
      [
        2.0,
        -1.5,
        0.5
      ],
      [
        2.0,
        -1.5,
        0.5
      ]
    ],
    "adam_pow_per_step": 2
  },
  "scope": {
    "full_optimizer_exact": false,
    "conditional_selected_parameter_updates_covered": false,
    "router_bias_update_count_unknown": 10240,
    "reference_precision": "real arithmetic; declared FP32 state/interfaces, report BF16 NS matmuls not emulated",
    "normalization": "Frobenius sqrt(sum squares)+explicit epsilon; epsilon=0 excludes zero Nesterov matrices",
    "source_algorithm_vs_kernel": "three-GEMM factored polynomial per iteration; transpose is explicit algebraic assumption, not disclosed kernel",
    "distributed": "full independent matrices required; dense capped ZeRO and MoE per-expert ownership; no rank layout or padding ratio assumed",
    "lifetimes": "master and momentum/moments persist across steps; gradient consumed this step; NS X/A/B/C/CX are per-matrix temporaries; views/transposes not charged as physical copies",
    "interfaces": "logical FP32 tensor accesses, not measured HBM; GEMM input duplicate operands counted per role; scalar fusion/alias and casts unknown",
    "excluded": "gradient production, load balancing bias rule, distributed synchronization, cast/quantization, optimizer implementation instruction count, actual peak/runtime"
  },
  "sources": [
    {
      "file": "configs/models/deepseek-v4-flash/config.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/config.json",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "b628e63398a645abc711d92207f8737dd8140f7a4ef1e0a5b3616019e0ddd818"
    },
    {
      "file": "configs/models/deepseek-v4-flash/inference/config.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/inference/config.json",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "6cc6f816ca73a8d38750194e330398e4f6955b4b45f674f7d29c96da14ccb733"
    },
    {
      "file": "sources/deepseek-v4-flash/inference/model.py",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/inference/model.py",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "ce962f1face79d4f633d36436576214057a7e11443c9789935e1deb5c6cd1d71"
    },
    {
      "file": "sources/deepseek-v4-flash/inference/kernel.py",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/inference/kernel.py",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "59b325083d7103975cba025bd0d60ea343bb82d8fff53088afb7c04bd380c0c2"
    },
    {
      "file": "sources/fast-hadamard-transform/README.md",
      "url": "https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/README.md",
      "revision": "e7706faf8d1c3b9f241e36860640ad1dac644ede",
      "sha256": "e9d1a782e751104628590c481ba325bc436292254aaefe4cfa39ee3c0b1eb00e"
    },
    {
      "file": "sources/fast-hadamard-transform/csrc/fast_hadamard_transform_common.h",
      "url": "https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/csrc/fast_hadamard_transform_common.h",
      "revision": "e7706faf8d1c3b9f241e36860640ad1dac644ede",
      "sha256": "e51345eb6be7b43cb657d73b8db9b2debcb4060de2266c7b42fc45bb3b86b473"
    },
    {
      "file": "sources/fast-hadamard-transform/fast_hadamard_transform/fast_hadamard_transform_interface.py",
      "url": "https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/fast_hadamard_transform/fast_hadamard_transform_interface.py",
      "revision": "e7706faf8d1c3b9f241e36860640ad1dac644ede",
      "sha256": "a2f32a615b03c83d075fd49eba266c9f6c13df790cbe549db3bf8c0c1f3e8877"
    },
    {
      "file": "sources/deepseek-v4-flash/model.safetensors.index.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model.safetensors.index.json",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "7e975ba3bef8947a94e7da0abd60888375b232b4dfad883d59653e65c6ba522a"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00001-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00001-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "7bdd252c75d1e8975a69b8399b226f0129ce119b23da7bd68deac4ba4b1a4a40"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00002-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00002-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "adbe0338649aec4a8099bd12e7f99b18b3497f73b38345f84ecb1c46eca9d992"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00003-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00003-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "066ac29abaa9071fd8af1166d76c411844336d778eea985781354b0a651bfd5f"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00004-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00004-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "739266275c9abeafe21fcf8def381588c2a556bae0206d42659789ab603c997e"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00005-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00005-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "00bf95ba015a6cb4f02c3bd6bab53b2bf12def11ed1201ac8e6b4e8e380299bb"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00006-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00006-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "c3fdf86122ab5d53a8c4d08eba13aaf8063e87cc475dc67072cb7a88106c6eac"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00007-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00007-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "2bb96fe9673587075839f4f38a6758a00c655d1386d93937ecb31a8fae7aa4e4"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00008-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00008-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "0f2cd169dd987424c04f4c04090b72f8ad780e1069fb9a49fd29340434bc0db7"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00009-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00009-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "c42b8df2eb4810f731edf8a646f61ba54226f66de484faa12df306e2bfbc18df"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00010-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00010-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "4ddfce5b94da6cf104f0c569357107d75466f57896eea5913f14bf2d9d669df8"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00011-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00011-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "a166d9008aebc86ffa5292305b5cd47b0ebfab13e59d2e9727bdff64f2273cf6"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00012-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00012-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "817002743a975c90a12ba1305d7a1cb31e2c1e3aee54fe7ecb1c01f052ace3c8"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00013-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00013-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "d2ca46ad597b90fbf32413a3f722a20d965500556d18c1a8c3d7fd362e7162d0"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00014-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00014-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "96a3457df88bcb76bd021b88abc4affa414a7337959ba53483474a8dc3c87325"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00015-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00015-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "cf8bce7b372e692d908185249a2f2405432b21f7e7d209fa701d13934e599ad0"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00016-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00016-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "758a06cf96357bcc35172bb569673cf3da9a49a7b7c0196d700734fe3ed6ceef"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00017-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00017-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "bef71dd20ade402de29a55026e7ca4239286c1e17767a5a06a6985888ad00b77"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00018-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00018-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "d752870f40b3db91c87e95dd9e4264ea1df5cad65d48365d1559d62bf6074b57"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00019-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00019-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "9c59b39cf7e4411fd6be6cef6be84d9505479e7c74cd6a6aed31e4acbbbfe4db"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00020-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00020-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "b78c94a19d78e815a59e381c070f9bb71c80afca32fb65b8cf3ddd4869f76a40"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00021-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00021-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "f4eae632cce4ebb4c7d6604a26b4404bbe0ed780b85309d370789901773f8865"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00022-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00022-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "e51e7f6ee11a7398e16082d2c821302cafb272a0f6760b848eba4457ed33091e"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00023-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00023-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "c834cc39b1bfab2222a6e61d61cd897012694f46b395cbb8c5dcee273667e875"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00024-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00024-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "bce06d093a55e7549d1c7828dde524d0274e08fd2b0906459b5df8311a728344"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00025-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00025-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "bcd896440e657458ffc1a03748c740c8da52d6a8792279d96a1aa30785ee0211"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00026-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00026-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "a8ccf8bfe0299db51fe7ba2a372be4e8b216b8e757e1f28376aeabe520f79b71"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00027-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00027-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "9761e7cdccbac4388df634eeb6135335742fb57c0a2291b49545d5846dc5d59c"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00028-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00028-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "ed35c3458805563571cc084014f95b1b520ddb2f720dc7be313fb36e85c2b631"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00029-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00029-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "df0037d7d7b0c8c3533ba7d8017b080ba628141ceb432046c18b7b80c7641ee8"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00030-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00030-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "f10b48bae9465a0ecf009b78e2602988dcce8f11efcb8ecf39be8eb60c3de41c"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00031-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00031-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "5b9ba12c0356d38bb4be66ef38feed3f7dd5ae558e39e8da6190396bba2bb129"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00032-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00032-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "03874e0e912e3639adea07b51aeafe9ab3eb84d5715defbace83a6ed0a002a95"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00033-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00033-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "13ef931a9fcd6bca4ffabdbbeccefbb7b4fa014facde32eeaeeb6e3bed6453ce"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00034-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00034-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "61c718832c85e4673c46a50b910e0c9ea0aeadd9f12a7131f1f40157d020c6de"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00035-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00035-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "22a3adf08b435595c3862f5289bf2797ff7157258c7cfa24ff1b0313aeae8bd0"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00036-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00036-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "359e010953a51169166f7140842b149e9f236c942cb99b2dc6082d7961011e16"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00037-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00037-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "8b228cfe5f5f6d5f5834046d5f7cd0045410b6f20048adf533170e3d23071b9a"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00038-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00038-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "deff29eb762eae6765766f6f2b1888cd7f627effd297bc4675d150d55171c425"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00039-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00039-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "44b9d5cec4550fd656c9da02bd51fde182812350601b9415e05210efe16b23bd"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00040-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00040-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "9f4e9b51b358e7f49827305e1b2e8fd1bffcb27567aebee96b5382a58a5a76a8"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00041-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00041-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "3cbe8dd9615eb0f1579a0bf83ab8885859348eaab555ce1fa43453fe78a9d3da"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00042-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00042-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "590483059c64c03a3c140b8a4c692441bda09e1c8d3c8a50e0f3b9e5bdb6569d"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00043-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00043-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "da9f9b7994e40f1b7e34416856e3f0927884cc5adf6ded630a4ce1cfb576fb82"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00044-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00044-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "a95f8067ab7db45ecb0118b4207aa68ed1b270c41e23849b48244c1d78799396"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00045-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00045-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "76d10bb3b022bad26446539ebaf16c9245fdcf835b28fd55a75052e0b0bb60b8"
    },
    {
      "file": "sources/deepseek-v4-flash/headers/model-00046-of-00046.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00046-of-00046.safetensors?header=1",
      "revision": "60d8d70770c6776ff598c94bb586a859a38244f1",
      "sha256": "10f90b036e608fabcf2c781dd5274a0fbc262f7aeaf959218ff1ccb829903981"
    },
    {
      "file": "references/text/deepseek-v4.txt",
      "url": "https://arxiv.org/pdf/2606.19348",
      "revision": "2606.19348v1",
      "sha256": "3fa26fbc1ca9fdbfee428100894e467e0c1c967945c6f4a1a19203a71730e5d7",
      "locators": [
        "section 2.4 Algorithm 1 and Eq.28",
        "section 3.4.1",
        "section 4.2.2"
      ],
      "kind": "archived report text, bound by source-evidence.json"
    }
  ]
}
```
