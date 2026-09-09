# DeepSeek V4 optimizer reference

Explicit grouping and factored ten-step hybrid Newton–Schulz; full runtime remains unknown.

| Pattern | Family | Tensor shape | Count | Independent shape | Matrices/tensor | Parameters | Matrix FLOPs | Scalar operations |
|---|---|---|---:|---|---:|---:|---:|---:|
| embed.weight | adamw | [129280, 7168] | 1 | [129280, 7168] | 1 | 926679040 | 0 | 12973506560 |
| layers.{i}.attn.attn_sink | muon | [128] | 61 | [1, 128] | 1 | 7808 | 313540 | 243878 |
| layers.{i}.attn.compressor.ape | muon | [128, 512] | 31 | [128, 512] | 1 | 2031616 | 11702108160 | 78217216 |
| layers.{i}.hc_attn_base | adamw | [24] | 61 | [24] | 1 | 1464 | 0 | 20496 |
| layers.{i}.hc_attn_fn | muon | [24, 28672] | 61 | [24, 28672] | 1 | 41975808 | 40313640960 | 1302304128 |
| layers.{i}.hc_attn_scale | adamw | [3] | 61 | [3] | 1 | 183 | 0 | 2562 |
| layers.{i}.hc_ffn_base | adamw | [24] | 61 | [24] | 1 | 1464 | 0 | 20496 |
| layers.{i}.hc_ffn_fn | muon | [24, 28672] | 61 | [24, 28672] | 1 | 41975808 | 40313640960 | 1302304128 |
| layers.{i}.hc_ffn_scale | adamw | [3] | 61 | [3] | 1 | 183 | 0 | 2562 |
| layers.{i}.attn.compressor.norm.weight | adamw | [512] | 61 | [512] | 1 | 31232 | 0 | 437248 |
| layers.{i}.attn.compressor.wgate.weight | muon | [512, 7168] | 31 | [512, 7168] | 1 | 113770496 | 2413234749440 | 3770679296 |
| layers.{i}.attn.compressor.wkv.weight | muon | [512, 7168] | 31 | [512, 7168] | 1 | 113770496 | 2413234749440 | 3770679296 |
| layers.{i}.attn.kv_norm.weight | adamw | [512] | 61 | [512] | 1 | 31232 | 0 | 437248 |
| layers.{i}.attn.q_norm.weight | adamw | [1536] | 61 | [1536] | 1 | 93696 | 0 | 1311744 |
| layers.{i}.attn_norm.weight | adamw | [7168] | 61 | [7168] | 1 | 437248 | 0 | 6121472 |
| layers.{i}.ffn.gate.weight | muon | [384, 7168] | 61 | [384, 7168] | 1 | 167903232 | 2648073830400 | 5474844672 |
| layers.{i}.ffn_norm.weight | adamw | [7168] | 61 | [7168] | 1 | 437248 | 0 | 6121472 |
| layers.{i}.attn.wkv.weight | muon | [512, 7168] | 61 | [512, 7168] | 1 | 223870976 | 4748623216640 | 7419723776 |
| layers.{i}.attn.wo_a.weight | muon | [16384, 4096] | 61 | [1024, 4096] | 16 | 4093640704 | 188634963640320 | 157605167104 |
| layers.{i}.attn.wo_b.weight | muon | [7168, 16384] | 61 | [7168, 16384] | 1 | 7163871232 | 2503343163310080 | 316105818112 |
| layers.{i}.attn.wq_a.weight | muon | [1536, 7168] | 61 | [1536, 7168] | 1 | 671612928 | 45685030256640 | 25137512448 |
| layers.{i}.attn.wq_b.weight | muon | [65536, 1536] | 61 | [65536, 1536] | 1 | 6140461056 | 381691059240960 | 194671804416 |
| layers.{i}.ffn.shared_experts.w1.weight | muon | [3072, 7168] | 61 | [3072, 7168] | 1 | 1343225856 | 200424648867840 | 58910048256 |
| layers.{i}.ffn.shared_experts.w2.weight | muon | [7168, 3072] | 61 | [7168, 3072] | 1 | 1343225856 | 200424648867840 | 58910048256 |
| layers.{i}.ffn.shared_experts.w3.weight | muon | [3072, 7168] | 61 | [3072, 7168] | 1 | 1343225856 | 200424648867840 | 58910048256 |
| layers.{i}.ffn.experts.{i}.w1.weight | muon | [3072, 7168] | 23424 | [3072, 7168] | 1 | 515798728704 | 76963065165250560 | 22621458530304 |
| layers.{i}.ffn.experts.{i}.w2.weight | muon | [7168, 3072] | 23424 | [7168, 3072] | 1 | 515798728704 | 76963065165250560 | 22621458530304 |
| layers.{i}.ffn.experts.{i}.w3.weight | muon | [3072, 7168] | 23424 | [3072, 7168] | 1 | 515798728704 | 76963065165250560 | 22621458530304 |
| layers.{i}.attn.compressor.ape | muon | [4, 1024] | 30 | [4, 1024] | 1 | 122880 | 19699200 | 3823680 |
| layers.{i}.attn.indexer.compressor.ape | muon | [4, 256] | 30 | [4, 256] | 1 | 30720 | 4953600 | 966720 |
| layers.{i}.attn.compressor.wgate.weight | muon | [1024, 7168] | 30 | [1024, 7168] | 1 | 220200960 | 9663676416000 | 7769948160 |
| layers.{i}.attn.compressor.wkv.weight | muon | [1024, 7168] | 30 | [1024, 7168] | 1 | 220200960 | 9663676416000 | 7769948160 |
| layers.{i}.attn.indexer.compressor.norm.weight | adamw | [128] | 30 | [128] | 1 | 3840 | 0 | 53760 |
| layers.{i}.attn.indexer.compressor.wgate.weight | muon | [256, 7168] | 30 | [256, 7168] | 1 | 55050240 | 573780787200 | 1765539840 |
| layers.{i}.attn.indexer.compressor.wkv.weight | muon | [256, 7168] | 30 | [256, 7168] | 1 | 55050240 | 573780787200 | 1765539840 |
| layers.{i}.attn.indexer.weights_proj.weight | muon | [64, 7168] | 30 | [64, 7168] | 1 | 13762560 | 35389440000 | 430325760 |
| layers.{i}.attn.indexer.wq_b.weight | muon | [8192, 1536] | 30 | [8192, 1536] | 1 | 377487360 | 25367150592000 | 13825474560 |
| layers.{i}.ffn.gate.bias | external_router_bias | [384] | 58 | [384] | 1 | 22272 | 0 | unknown |
| hc_head_base | adamw | [4] | 1 | [4] | 1 | 4 | 0 | 56 |
| hc_head_fn | adamw | [4, 28672] | 1 | [4, 28672] | 1 | 114688 | 0 | 1605632 |
| hc_head_scale | adamw | [1] | 1 | [1] | 1 | 1 | 0 | 14 |
| head.weight | adamw | [129280, 7168] | 1 | [129280, 7168] | 1 | 926679040 | 0 | 12973506560 |
| norm.weight | adamw | [7168] | 1 | [7168] | 1 | 7168 | 0 | 100352 |

Complete per-matrix operations, state, interface bytes, assumptions and source hashes:

```json
{
  "schema": "v4-optimizer-reference-v1",
  "scenario": {
    "model": "deepseek-v4-pro",
    "include_mtp": false,
    "orientation": "smaller_gram",
    "wo_a_partition": "source_groups",
    "sink_policy": "row_muon",
    "head_mixer_policy": "adamw",
    "learning_rate": 0.0002,
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
        7168
      ],
      "independent_matrix_shape": [
        129280,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 1,
      "parameters": 926679040,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "embed.weight",
      "ordinary_scalar_operations": 12973506560,
      "special_operations": {
        "sqrt": 926679040
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.attn_sink",
      "optimizer": "muon",
      "logical_tensor_shape": [
        128
      ],
      "independent_matrix_shape": [
        1,
        128
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 7808,
      "reason": "report omits vector matrixization; row_muon is explicit assumption",
      "example_tensor": "layers.0.attn.attn_sink",
      "per_matrix_reference": {
        "oriented_shape": [
          1,
          128
        ],
        "parameters": 128,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1,
              1,
              128
            ],
            "flops": 256
          },
          {
            "name": "B=A@A",
            "mnk": [
              1,
              1,
              1
            ],
            "flops": 2
          },
          {
            "name": "C@X",
            "mnk": [
              1,
              128,
              1
            ],
            "flops": 256
          }
        ],
        "matrix_flops": 5140,
        "ordinary_scalar_operations": 3998,
        "scalar_detail": {
          "momentum_and_nesterov": 512,
          "frobenius_square_sum_epsilon_divide": 384,
          "polynomial_combine": 2590,
          "rescale_decay_update": 512
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 512,
          "momentum": 512
        },
        "fp32_gradient_input_bytes": 512,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 1548,
          "gemm_outputs": 520,
          "scalar_combine_reads": 1032,
          "scalar_combine_writes": 516
        },
        "individual_temporary_bytes": {
          "X": 512,
          "A": 4,
          "B": 4,
          "C": 4,
          "CX": 512
        }
      },
      "matrix_count": 61,
      "matrix_flops": 313540,
      "ordinary_scalar_operations": 243878
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
      "tensor_count": 31,
      "parameters": 2031616,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.compressor.ape",
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
      "matrix_count": 31,
      "matrix_flops": 11702108160,
      "ordinary_scalar_operations": 78217216
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
      "tensor_count": 61,
      "parameters": 1464,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.hc_attn_base",
      "ordinary_scalar_operations": 20496,
      "special_operations": {
        "sqrt": 1464
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.hc_attn_fn",
      "optimizer": "muon",
      "logical_tensor_shape": [
        24,
        28672
      ],
      "independent_matrix_shape": [
        24,
        28672
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 41975808,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.hc_attn_fn",
      "per_matrix_reference": {
        "oriented_shape": [
          24,
          28672
        ],
        "parameters": 688128,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              24,
              24,
              28672
            ],
            "flops": 33030144
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
              28672,
              24
            ],
            "flops": 33030144
          }
        ],
        "matrix_flops": 660879360,
        "ordinary_scalar_operations": 21349248,
        "scalar_detail": {
          "momentum_and_nesterov": 2752512,
          "frobenius_square_sum_epsilon_divide": 2064384,
          "polynomial_combine": 13779840,
          "rescale_decay_update": 2752512
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 2752512,
          "momentum": 2752512
        },
        "fp32_gradient_input_bytes": 2752512,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 8264448,
          "gemm_outputs": 2757120,
          "scalar_combine_reads": 5509632,
          "scalar_combine_writes": 2754816
        },
        "individual_temporary_bytes": {
          "X": 2752512,
          "A": 2304,
          "B": 2304,
          "C": 2304,
          "CX": 2752512
        }
      },
      "matrix_count": 61,
      "matrix_flops": 40313640960,
      "ordinary_scalar_operations": 1302304128
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
      "tensor_count": 61,
      "parameters": 183,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.hc_attn_scale",
      "ordinary_scalar_operations": 2562,
      "special_operations": {
        "sqrt": 183
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
      "tensor_count": 61,
      "parameters": 1464,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.hc_ffn_base",
      "ordinary_scalar_operations": 20496,
      "special_operations": {
        "sqrt": 1464
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.hc_ffn_fn",
      "optimizer": "muon",
      "logical_tensor_shape": [
        24,
        28672
      ],
      "independent_matrix_shape": [
        24,
        28672
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 41975808,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.hc_ffn_fn",
      "per_matrix_reference": {
        "oriented_shape": [
          24,
          28672
        ],
        "parameters": 688128,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              24,
              24,
              28672
            ],
            "flops": 33030144
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
              28672,
              24
            ],
            "flops": 33030144
          }
        ],
        "matrix_flops": 660879360,
        "ordinary_scalar_operations": 21349248,
        "scalar_detail": {
          "momentum_and_nesterov": 2752512,
          "frobenius_square_sum_epsilon_divide": 2064384,
          "polynomial_combine": 13779840,
          "rescale_decay_update": 2752512
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 2752512,
          "momentum": 2752512
        },
        "fp32_gradient_input_bytes": 2752512,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 8264448,
          "gemm_outputs": 2757120,
          "scalar_combine_reads": 5509632,
          "scalar_combine_writes": 2754816
        },
        "individual_temporary_bytes": {
          "X": 2752512,
          "A": 2304,
          "B": 2304,
          "C": 2304,
          "CX": 2752512
        }
      },
      "matrix_count": 61,
      "matrix_flops": 40313640960,
      "ordinary_scalar_operations": 1302304128
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
      "tensor_count": 61,
      "parameters": 183,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.hc_ffn_scale",
      "ordinary_scalar_operations": 2562,
      "special_operations": {
        "sqrt": 183
      }
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
      "tensor_count": 61,
      "parameters": 31232,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.attn.compressor.norm.weight",
      "ordinary_scalar_operations": 437248,
      "special_operations": {
        "sqrt": 31232
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.compressor.wgate.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        512,
        7168
      ],
      "independent_matrix_shape": [
        512,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 31,
      "parameters": 113770496,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.compressor.wgate.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          512,
          7168
        ],
        "parameters": 3670016,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              512,
              512,
              7168
            ],
            "flops": 3758096384
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
              7168,
              512
            ],
            "flops": 3758096384
          }
        ],
        "matrix_flops": 77846282240,
        "ordinary_scalar_operations": 121634816,
        "scalar_detail": {
          "momentum_and_nesterov": 14680064,
          "frobenius_square_sum_epsilon_divide": 11010048,
          "polynomial_combine": 81264640,
          "rescale_decay_update": 14680064
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 14680064,
          "momentum": 14680064
        },
        "fp32_gradient_input_bytes": 14680064,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 47185920,
          "gemm_outputs": 16777216,
          "scalar_combine_reads": 31457280,
          "scalar_combine_writes": 15728640
        },
        "individual_temporary_bytes": {
          "X": 14680064,
          "A": 1048576,
          "B": 1048576,
          "C": 1048576,
          "CX": 14680064
        }
      },
      "matrix_count": 31,
      "matrix_flops": 2413234749440,
      "ordinary_scalar_operations": 3770679296
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.compressor.wkv.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        512,
        7168
      ],
      "independent_matrix_shape": [
        512,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 31,
      "parameters": 113770496,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.compressor.wkv.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          512,
          7168
        ],
        "parameters": 3670016,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              512,
              512,
              7168
            ],
            "flops": 3758096384
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
              7168,
              512
            ],
            "flops": 3758096384
          }
        ],
        "matrix_flops": 77846282240,
        "ordinary_scalar_operations": 121634816,
        "scalar_detail": {
          "momentum_and_nesterov": 14680064,
          "frobenius_square_sum_epsilon_divide": 11010048,
          "polynomial_combine": 81264640,
          "rescale_decay_update": 14680064
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 14680064,
          "momentum": 14680064
        },
        "fp32_gradient_input_bytes": 14680064,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 47185920,
          "gemm_outputs": 16777216,
          "scalar_combine_reads": 31457280,
          "scalar_combine_writes": 15728640
        },
        "individual_temporary_bytes": {
          "X": 14680064,
          "A": 1048576,
          "B": 1048576,
          "C": 1048576,
          "CX": 14680064
        }
      },
      "matrix_count": 31,
      "matrix_flops": 2413234749440,
      "ordinary_scalar_operations": 3770679296
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
      "tensor_count": 61,
      "parameters": 31232,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.attn.kv_norm.weight",
      "ordinary_scalar_operations": 437248,
      "special_operations": {
        "sqrt": 31232
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.q_norm.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        1536
      ],
      "independent_matrix_shape": [
        1536
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 93696,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.attn.q_norm.weight",
      "ordinary_scalar_operations": 1311744,
      "special_operations": {
        "sqrt": 93696
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn_norm.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        7168
      ],
      "independent_matrix_shape": [
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 437248,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.attn_norm.weight",
      "ordinary_scalar_operations": 6121472,
      "special_operations": {
        "sqrt": 437248
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.gate.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        384,
        7168
      ],
      "independent_matrix_shape": [
        384,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 167903232,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.gate.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          384,
          7168
        ],
        "parameters": 2752512,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              384,
              384,
              7168
            ],
            "flops": 2113929216
          },
          {
            "name": "B=A@A",
            "mnk": [
              384,
              384,
              384
            ],
            "flops": 113246208
          },
          {
            "name": "C@X",
            "mnk": [
              384,
              7168,
              384
            ],
            "flops": 2113929216
          }
        ],
        "matrix_flops": 43411046400,
        "ordinary_scalar_operations": 89751552,
        "scalar_detail": {
          "momentum_and_nesterov": 11010048,
          "frobenius_square_sum_epsilon_divide": 8257536,
          "polynomial_combine": 59473920,
          "rescale_decay_update": 11010048
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 11010048,
          "momentum": 11010048
        },
        "fp32_gradient_input_bytes": 11010048,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 34799616,
          "gemm_outputs": 12189696,
          "scalar_combine_reads": 23199744,
          "scalar_combine_writes": 11599872
        },
        "individual_temporary_bytes": {
          "X": 11010048,
          "A": 589824,
          "B": 589824,
          "C": 589824,
          "CX": 11010048
        }
      },
      "matrix_count": 61,
      "matrix_flops": 2648073830400,
      "ordinary_scalar_operations": 5474844672
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn_norm.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        7168
      ],
      "independent_matrix_shape": [
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 437248,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.0.ffn_norm.weight",
      "ordinary_scalar_operations": 6121472,
      "special_operations": {
        "sqrt": 437248
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.wkv.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        512,
        7168
      ],
      "independent_matrix_shape": [
        512,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 223870976,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.wkv.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          512,
          7168
        ],
        "parameters": 3670016,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              512,
              512,
              7168
            ],
            "flops": 3758096384
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
              7168,
              512
            ],
            "flops": 3758096384
          }
        ],
        "matrix_flops": 77846282240,
        "ordinary_scalar_operations": 121634816,
        "scalar_detail": {
          "momentum_and_nesterov": 14680064,
          "frobenius_square_sum_epsilon_divide": 11010048,
          "polynomial_combine": 81264640,
          "rescale_decay_update": 14680064
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 14680064,
          "momentum": 14680064
        },
        "fp32_gradient_input_bytes": 14680064,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 47185920,
          "gemm_outputs": 16777216,
          "scalar_combine_reads": 31457280,
          "scalar_combine_writes": 15728640
        },
        "individual_temporary_bytes": {
          "X": 14680064,
          "A": 1048576,
          "B": 1048576,
          "C": 1048576,
          "CX": 14680064
        }
      },
      "matrix_count": 61,
      "matrix_flops": 4748623216640,
      "ordinary_scalar_operations": 7419723776
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.wo_a.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        16384,
        4096
      ],
      "independent_matrix_shape": [
        1024,
        4096
      ],
      "independent_matrices_per_tensor": 16,
      "tensor_count": 61,
      "parameters": 4093640704,
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
      "matrix_count": 976,
      "matrix_flops": 188634963640320,
      "ordinary_scalar_operations": 157605167104
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.wo_b.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        7168,
        16384
      ],
      "independent_matrix_shape": [
        7168,
        16384
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 7163871232,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.wo_b.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          7168,
          16384
        ],
        "parameters": 117440512,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              7168,
              7168,
              16384
            ],
            "flops": 1683627180032
          },
          {
            "name": "B=A@A",
            "mnk": [
              7168,
              7168,
              7168
            ],
            "flops": 736586891264
          },
          {
            "name": "C@X",
            "mnk": [
              7168,
              16384,
              7168
            ],
            "flops": 1683627180032
          }
        ],
        "matrix_flops": 41038412513280,
        "ordinary_scalar_operations": 5182062592,
        "scalar_detail": {
          "momentum_and_nesterov": 469762048,
          "frobenius_square_sum_epsilon_divide": 352321536,
          "polynomial_combine": 3890216960,
          "rescale_decay_update": 469762048
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 469762048,
          "momentum": 469762048
        },
        "fp32_gradient_input_bytes": 469762048,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 2025848832,
          "gemm_outputs": 880803840,
          "scalar_combine_reads": 1350565888,
          "scalar_combine_writes": 675282944
        },
        "individual_temporary_bytes": {
          "X": 469762048,
          "A": 205520896,
          "B": 205520896,
          "C": 205520896,
          "CX": 469762048
        }
      },
      "matrix_count": 61,
      "matrix_flops": 2503343163310080,
      "ordinary_scalar_operations": 316105818112
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.wq_a.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        1536,
        7168
      ],
      "independent_matrix_shape": [
        1536,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 671612928,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.wq_a.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          1536,
          7168
        ],
        "parameters": 11010048,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1536,
              1536,
              7168
            ],
            "flops": 33822867456
          },
          {
            "name": "B=A@A",
            "mnk": [
              1536,
              1536,
              1536
            ],
            "flops": 7247757312
          },
          {
            "name": "C@X",
            "mnk": [
              1536,
              7168,
              1536
            ],
            "flops": 33822867456
          }
        ],
        "matrix_flops": 748934922240,
        "ordinary_scalar_operations": 412090368,
        "scalar_detail": {
          "momentum_and_nesterov": 44040192,
          "frobenius_square_sum_epsilon_divide": 33030144,
          "polynomial_combine": 290979840,
          "rescale_decay_update": 44040192
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 44040192,
          "momentum": 44040192
        },
        "fp32_gradient_input_bytes": 44040192,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 160432128,
          "gemm_outputs": 62914560,
          "scalar_combine_reads": 106954752,
          "scalar_combine_writes": 53477376
        },
        "individual_temporary_bytes": {
          "X": 44040192,
          "A": 9437184,
          "B": 9437184,
          "C": 9437184,
          "CX": 44040192
        }
      },
      "matrix_count": 61,
      "matrix_flops": 45685030256640,
      "ordinary_scalar_operations": 25137512448
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.wq_b.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        65536,
        1536
      ],
      "independent_matrix_shape": [
        65536,
        1536
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 6140461056,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.attn.wq_b.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          1536,
          65536
        ],
        "parameters": 100663296,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1536,
              1536,
              65536
            ],
            "flops": 309237645312
          },
          {
            "name": "B=A@A",
            "mnk": [
              1536,
              1536,
              1536
            ],
            "flops": 7247757312
          },
          {
            "name": "C@X",
            "mnk": [
              1536,
              65536,
              1536
            ],
            "flops": 309237645312
          }
        ],
        "matrix_flops": 6257230479360,
        "ordinary_scalar_operations": 3191341056,
        "scalar_detail": {
          "momentum_and_nesterov": 402653184,
          "frobenius_square_sum_epsilon_divide": 301989888,
          "polynomial_combine": 2084044800,
          "rescale_decay_update": 402653184
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 402653184,
          "momentum": 402653184
        },
        "fp32_gradient_input_bytes": 402653184,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 1236271104,
          "gemm_outputs": 421527552,
          "scalar_combine_reads": 824180736,
          "scalar_combine_writes": 412090368
        },
        "individual_temporary_bytes": {
          "X": 402653184,
          "A": 9437184,
          "B": 9437184,
          "C": 9437184,
          "CX": 402653184
        }
      },
      "matrix_count": 61,
      "matrix_flops": 381691059240960,
      "ordinary_scalar_operations": 194671804416
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.shared_experts.w1.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        3072,
        7168
      ],
      "independent_matrix_shape": [
        3072,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 1343225856,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.shared_experts.w1.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          3072,
          7168
        ],
        "parameters": 22020096,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              3072,
              3072,
              7168
            ],
            "flops": 135291469824
          },
          {
            "name": "B=A@A",
            "mnk": [
              3072,
              3072,
              3072
            ],
            "flops": 57982058496
          },
          {
            "name": "C@X",
            "mnk": [
              3072,
              7168,
              3072
            ],
            "flops": 135291469824
          }
        ],
        "matrix_flops": 3285649981440,
        "ordinary_scalar_operations": 965738496,
        "scalar_detail": {
          "momentum_and_nesterov": 88080384,
          "frobenius_square_sum_epsilon_divide": 66060288,
          "polynomial_combine": 723517440,
          "rescale_decay_update": 88080384
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 88080384,
          "momentum": 88080384
        },
        "fp32_gradient_input_bytes": 88080384,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 377487360,
          "gemm_outputs": 163577856,
          "scalar_combine_reads": 251658240,
          "scalar_combine_writes": 125829120
        },
        "individual_temporary_bytes": {
          "X": 88080384,
          "A": 37748736,
          "B": 37748736,
          "C": 37748736,
          "CX": 88080384
        }
      },
      "matrix_count": 61,
      "matrix_flops": 200424648867840,
      "ordinary_scalar_operations": 58910048256
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.shared_experts.w2.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        7168,
        3072
      ],
      "independent_matrix_shape": [
        7168,
        3072
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 1343225856,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.shared_experts.w2.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          3072,
          7168
        ],
        "parameters": 22020096,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              3072,
              3072,
              7168
            ],
            "flops": 135291469824
          },
          {
            "name": "B=A@A",
            "mnk": [
              3072,
              3072,
              3072
            ],
            "flops": 57982058496
          },
          {
            "name": "C@X",
            "mnk": [
              3072,
              7168,
              3072
            ],
            "flops": 135291469824
          }
        ],
        "matrix_flops": 3285649981440,
        "ordinary_scalar_operations": 965738496,
        "scalar_detail": {
          "momentum_and_nesterov": 88080384,
          "frobenius_square_sum_epsilon_divide": 66060288,
          "polynomial_combine": 723517440,
          "rescale_decay_update": 88080384
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 88080384,
          "momentum": 88080384
        },
        "fp32_gradient_input_bytes": 88080384,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 377487360,
          "gemm_outputs": 163577856,
          "scalar_combine_reads": 251658240,
          "scalar_combine_writes": 125829120
        },
        "individual_temporary_bytes": {
          "X": 88080384,
          "A": 37748736,
          "B": 37748736,
          "C": 37748736,
          "CX": 88080384
        }
      },
      "matrix_count": 61,
      "matrix_flops": 200424648867840,
      "ordinary_scalar_operations": 58910048256
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.shared_experts.w3.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        3072,
        7168
      ],
      "independent_matrix_shape": [
        3072,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 61,
      "parameters": 1343225856,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.shared_experts.w3.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          3072,
          7168
        ],
        "parameters": 22020096,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              3072,
              3072,
              7168
            ],
            "flops": 135291469824
          },
          {
            "name": "B=A@A",
            "mnk": [
              3072,
              3072,
              3072
            ],
            "flops": 57982058496
          },
          {
            "name": "C@X",
            "mnk": [
              3072,
              7168,
              3072
            ],
            "flops": 135291469824
          }
        ],
        "matrix_flops": 3285649981440,
        "ordinary_scalar_operations": 965738496,
        "scalar_detail": {
          "momentum_and_nesterov": 88080384,
          "frobenius_square_sum_epsilon_divide": 66060288,
          "polynomial_combine": 723517440,
          "rescale_decay_update": 88080384
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 88080384,
          "momentum": 88080384
        },
        "fp32_gradient_input_bytes": 88080384,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 377487360,
          "gemm_outputs": 163577856,
          "scalar_combine_reads": 251658240,
          "scalar_combine_writes": 125829120
        },
        "individual_temporary_bytes": {
          "X": 88080384,
          "A": 37748736,
          "B": 37748736,
          "C": 37748736,
          "CX": 88080384
        }
      },
      "matrix_count": 61,
      "matrix_flops": 200424648867840,
      "ordinary_scalar_operations": 58910048256
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.experts.{i}.w1.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        3072,
        7168
      ],
      "independent_matrix_shape": [
        3072,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 23424,
      "parameters": 515798728704,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.experts.0.w1.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          3072,
          7168
        ],
        "parameters": 22020096,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              3072,
              3072,
              7168
            ],
            "flops": 135291469824
          },
          {
            "name": "B=A@A",
            "mnk": [
              3072,
              3072,
              3072
            ],
            "flops": 57982058496
          },
          {
            "name": "C@X",
            "mnk": [
              3072,
              7168,
              3072
            ],
            "flops": 135291469824
          }
        ],
        "matrix_flops": 3285649981440,
        "ordinary_scalar_operations": 965738496,
        "scalar_detail": {
          "momentum_and_nesterov": 88080384,
          "frobenius_square_sum_epsilon_divide": 66060288,
          "polynomial_combine": 723517440,
          "rescale_decay_update": 88080384
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 88080384,
          "momentum": 88080384
        },
        "fp32_gradient_input_bytes": 88080384,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 377487360,
          "gemm_outputs": 163577856,
          "scalar_combine_reads": 251658240,
          "scalar_combine_writes": 125829120
        },
        "individual_temporary_bytes": {
          "X": 88080384,
          "A": 37748736,
          "B": 37748736,
          "C": 37748736,
          "CX": 88080384
        }
      },
      "matrix_count": 23424,
      "matrix_flops": 76963065165250560,
      "ordinary_scalar_operations": 22621458530304
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.experts.{i}.w2.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        7168,
        3072
      ],
      "independent_matrix_shape": [
        7168,
        3072
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 23424,
      "parameters": 515798728704,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.experts.0.w2.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          3072,
          7168
        ],
        "parameters": 22020096,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              3072,
              3072,
              7168
            ],
            "flops": 135291469824
          },
          {
            "name": "B=A@A",
            "mnk": [
              3072,
              3072,
              3072
            ],
            "flops": 57982058496
          },
          {
            "name": "C@X",
            "mnk": [
              3072,
              7168,
              3072
            ],
            "flops": 135291469824
          }
        ],
        "matrix_flops": 3285649981440,
        "ordinary_scalar_operations": 965738496,
        "scalar_detail": {
          "momentum_and_nesterov": 88080384,
          "frobenius_square_sum_epsilon_divide": 66060288,
          "polynomial_combine": 723517440,
          "rescale_decay_update": 88080384
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 88080384,
          "momentum": 88080384
        },
        "fp32_gradient_input_bytes": 88080384,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 377487360,
          "gemm_outputs": 163577856,
          "scalar_combine_reads": 251658240,
          "scalar_combine_writes": 125829120
        },
        "individual_temporary_bytes": {
          "X": 88080384,
          "A": 37748736,
          "B": 37748736,
          "C": 37748736,
          "CX": 88080384
        }
      },
      "matrix_count": 23424,
      "matrix_flops": 76963065165250560,
      "ordinary_scalar_operations": 22621458530304
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.experts.{i}.w3.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        3072,
        7168
      ],
      "independent_matrix_shape": [
        3072,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 23424,
      "parameters": 515798728704,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.0.ffn.experts.0.w3.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          3072,
          7168
        ],
        "parameters": 22020096,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              3072,
              3072,
              7168
            ],
            "flops": 135291469824
          },
          {
            "name": "B=A@A",
            "mnk": [
              3072,
              3072,
              3072
            ],
            "flops": 57982058496
          },
          {
            "name": "C@X",
            "mnk": [
              3072,
              7168,
              3072
            ],
            "flops": 135291469824
          }
        ],
        "matrix_flops": 3285649981440,
        "ordinary_scalar_operations": 965738496,
        "scalar_detail": {
          "momentum_and_nesterov": 88080384,
          "frobenius_square_sum_epsilon_divide": 66060288,
          "polynomial_combine": 723517440,
          "rescale_decay_update": 88080384
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 88080384,
          "momentum": 88080384
        },
        "fp32_gradient_input_bytes": 88080384,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 377487360,
          "gemm_outputs": 163577856,
          "scalar_combine_reads": 251658240,
          "scalar_combine_writes": 125829120
        },
        "individual_temporary_bytes": {
          "X": 88080384,
          "A": 37748736,
          "B": 37748736,
          "C": 37748736,
          "CX": 88080384
        }
      },
      "matrix_count": 23424,
      "matrix_flops": 76963065165250560,
      "ordinary_scalar_operations": 22621458530304
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
      "tensor_count": 30,
      "parameters": 122880,
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
      "matrix_count": 30,
      "matrix_flops": 19699200,
      "ordinary_scalar_operations": 3823680
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
      "tensor_count": 30,
      "parameters": 30720,
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
      "matrix_count": 30,
      "matrix_flops": 4953600,
      "ordinary_scalar_operations": 966720
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.compressor.wgate.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        1024,
        7168
      ],
      "independent_matrix_shape": [
        1024,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 30,
      "parameters": 220200960,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.compressor.wgate.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          1024,
          7168
        ],
        "parameters": 7340032,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1024,
              1024,
              7168
            ],
            "flops": 15032385536
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
              7168,
              1024
            ],
            "flops": 15032385536
          }
        ],
        "matrix_flops": 322122547200,
        "ordinary_scalar_operations": 258998272,
        "scalar_detail": {
          "momentum_and_nesterov": 29360128,
          "frobenius_square_sum_epsilon_divide": 22020096,
          "polynomial_combine": 178257920,
          "rescale_decay_update": 29360128
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 29360128,
          "momentum": 29360128
        },
        "fp32_gradient_input_bytes": 29360128,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 100663296,
          "gemm_outputs": 37748736,
          "scalar_combine_reads": 67108864,
          "scalar_combine_writes": 33554432
        },
        "individual_temporary_bytes": {
          "X": 29360128,
          "A": 4194304,
          "B": 4194304,
          "C": 4194304,
          "CX": 29360128
        }
      },
      "matrix_count": 30,
      "matrix_flops": 9663676416000,
      "ordinary_scalar_operations": 7769948160
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.compressor.wkv.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        1024,
        7168
      ],
      "independent_matrix_shape": [
        1024,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 30,
      "parameters": 220200960,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.compressor.wkv.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          1024,
          7168
        ],
        "parameters": 7340032,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1024,
              1024,
              7168
            ],
            "flops": 15032385536
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
              7168,
              1024
            ],
            "flops": 15032385536
          }
        ],
        "matrix_flops": 322122547200,
        "ordinary_scalar_operations": 258998272,
        "scalar_detail": {
          "momentum_and_nesterov": 29360128,
          "frobenius_square_sum_epsilon_divide": 22020096,
          "polynomial_combine": 178257920,
          "rescale_decay_update": 29360128
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 29360128,
          "momentum": 29360128
        },
        "fp32_gradient_input_bytes": 29360128,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 100663296,
          "gemm_outputs": 37748736,
          "scalar_combine_reads": 67108864,
          "scalar_combine_writes": 33554432
        },
        "individual_temporary_bytes": {
          "X": 29360128,
          "A": 4194304,
          "B": 4194304,
          "C": 4194304,
          "CX": 29360128
        }
      },
      "matrix_count": 30,
      "matrix_flops": 9663676416000,
      "ordinary_scalar_operations": 7769948160
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
      "tensor_count": 30,
      "parameters": 3840,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "layers.2.attn.indexer.compressor.norm.weight",
      "ordinary_scalar_operations": 53760,
      "special_operations": {
        "sqrt": 3840
      }
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.indexer.compressor.wgate.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        256,
        7168
      ],
      "independent_matrix_shape": [
        256,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 30,
      "parameters": 55050240,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.indexer.compressor.wgate.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          256,
          7168
        ],
        "parameters": 1835008,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              256,
              256,
              7168
            ],
            "flops": 939524096
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
              7168,
              256
            ],
            "flops": 939524096
          }
        ],
        "matrix_flops": 19126026240,
        "ordinary_scalar_operations": 58851328,
        "scalar_detail": {
          "momentum_and_nesterov": 7340032,
          "frobenius_square_sum_epsilon_divide": 5505024,
          "polynomial_combine": 38666240,
          "rescale_decay_update": 7340032
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 7340032,
          "momentum": 7340032
        },
        "fp32_gradient_input_bytes": 7340032,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 22806528,
          "gemm_outputs": 7864320,
          "scalar_combine_reads": 15204352,
          "scalar_combine_writes": 7602176
        },
        "individual_temporary_bytes": {
          "X": 7340032,
          "A": 262144,
          "B": 262144,
          "C": 262144,
          "CX": 7340032
        }
      },
      "matrix_count": 30,
      "matrix_flops": 573780787200,
      "ordinary_scalar_operations": 1765539840
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.indexer.compressor.wkv.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        256,
        7168
      ],
      "independent_matrix_shape": [
        256,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 30,
      "parameters": 55050240,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.indexer.compressor.wkv.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          256,
          7168
        ],
        "parameters": 1835008,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              256,
              256,
              7168
            ],
            "flops": 939524096
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
              7168,
              256
            ],
            "flops": 939524096
          }
        ],
        "matrix_flops": 19126026240,
        "ordinary_scalar_operations": 58851328,
        "scalar_detail": {
          "momentum_and_nesterov": 7340032,
          "frobenius_square_sum_epsilon_divide": 5505024,
          "polynomial_combine": 38666240,
          "rescale_decay_update": 7340032
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 7340032,
          "momentum": 7340032
        },
        "fp32_gradient_input_bytes": 7340032,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 22806528,
          "gemm_outputs": 7864320,
          "scalar_combine_reads": 15204352,
          "scalar_combine_writes": 7602176
        },
        "individual_temporary_bytes": {
          "X": 7340032,
          "A": 262144,
          "B": 262144,
          "C": 262144,
          "CX": 7340032
        }
      },
      "matrix_count": 30,
      "matrix_flops": 573780787200,
      "ordinary_scalar_operations": 1765539840
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.indexer.weights_proj.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        64,
        7168
      ],
      "independent_matrix_shape": [
        64,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 30,
      "parameters": 13762560,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.indexer.weights_proj.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          64,
          7168
        ],
        "parameters": 458752,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              64,
              64,
              7168
            ],
            "flops": 58720256
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
              7168,
              64
            ],
            "flops": 58720256
          }
        ],
        "matrix_flops": 1179648000,
        "ordinary_scalar_operations": 14344192,
        "scalar_detail": {
          "momentum_and_nesterov": 1835008,
          "frobenius_square_sum_epsilon_divide": 1376256,
          "polynomial_combine": 9297920,
          "rescale_decay_update": 1835008
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 1835008,
          "momentum": 1835008
        },
        "fp32_gradient_input_bytes": 1835008,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 5554176,
          "gemm_outputs": 1867776,
          "scalar_combine_reads": 3702784,
          "scalar_combine_writes": 1851392
        },
        "individual_temporary_bytes": {
          "X": 1835008,
          "A": 16384,
          "B": 16384,
          "C": 16384,
          "CX": 1835008
        }
      },
      "matrix_count": 30,
      "matrix_flops": 35389440000,
      "ordinary_scalar_operations": 430325760
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.attn.indexer.wq_b.weight",
      "optimizer": "muon",
      "logical_tensor_shape": [
        8192,
        1536
      ],
      "independent_matrix_shape": [
        8192,
        1536
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 30,
      "parameters": 377487360,
      "reason": "report all other modules; stored matrix is independent unless explicitly partitioned",
      "example_tensor": "layers.2.attn.indexer.wq_b.weight",
      "per_matrix_reference": {
        "oriented_shape": [
          1536,
          8192
        ],
        "parameters": 12582912,
        "iterations": 10,
        "gemms_per_iteration": [
          {
            "name": "A=X@X.T",
            "mnk": [
              1536,
              1536,
              8192
            ],
            "flops": 38654705664
          },
          {
            "name": "B=A@A",
            "mnk": [
              1536,
              1536,
              1536
            ],
            "flops": 7247757312
          },
          {
            "name": "C@X",
            "mnk": [
              1536,
              8192,
              1536
            ],
            "flops": 38654705664
          }
        ],
        "matrix_flops": 845571686400,
        "ordinary_scalar_operations": 460849152,
        "scalar_detail": {
          "momentum_and_nesterov": 50331648,
          "frobenius_square_sum_epsilon_divide": 37748736,
          "polynomial_combine": 322437120,
          "rescale_decay_update": 50331648
        },
        "special_operations": {
          "sqrt": 1
        },
        "fp32_persistent_state_bytes": {
          "master_weight": 50331648,
          "momentum": 50331648
        },
        "fp32_gradient_input_bytes": 50331648,
        "tensor_interfaces_per_iteration_bytes": {
          "gemm_operand_reads": 179306496,
          "gemm_outputs": 69206016,
          "scalar_combine_reads": 119537664,
          "scalar_combine_writes": 59768832
        },
        "individual_temporary_bytes": {
          "X": 50331648,
          "A": 9437184,
          "B": 9437184,
          "C": 9437184,
          "CX": 50331648
        }
      },
      "matrix_count": 30,
      "matrix_flops": 25367150592000,
      "ordinary_scalar_operations": 13825474560
    },
    {
      "owner": "base",
      "name_pattern": "layers.{i}.ffn.gate.bias",
      "optimizer": "external_router_bias",
      "logical_tensor_shape": [
        384
      ],
      "independent_matrix_shape": [
        384
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 58,
      "parameters": 22272,
      "reason": "auxiliary-loss-free load balancing update, not differentiable route selection",
      "example_tensor": "layers.3.ffn.gate.bias"
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
      "optimizer": "adamw",
      "logical_tensor_shape": [
        4,
        28672
      ],
      "independent_matrix_shape": [
        4,
        28672
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 1,
      "parameters": 114688,
      "reason": "head module versus mHC projection boundary explicitly selected",
      "example_tensor": "hc_head_fn",
      "ordinary_scalar_operations": 1605632,
      "special_operations": {
        "sqrt": 114688
      }
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
        7168
      ],
      "independent_matrix_shape": [
        129280,
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 1,
      "parameters": 926679040,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "head.weight",
      "ordinary_scalar_operations": 12973506560,
      "special_operations": {
        "sqrt": 926679040
      }
    },
    {
      "owner": "base",
      "name_pattern": "norm.weight",
      "optimizer": "adamw",
      "logical_tensor_shape": [
        7168
      ],
      "independent_matrix_shape": [
        7168
      ],
      "independent_matrices_per_tensor": 1,
      "tensor_count": 1,
      "parameters": 7168,
      "reason": "report embedding/head/RMSNorm/mHC static bias and gate exception",
      "example_tensor": "norm.weight",
      "ordinary_scalar_operations": 100352,
      "special_operations": {
        "sqrt": 7168
      }
    }
  ],
  "summary": {
    "muon_parameters": 1571142661760,
    "adamw_parameters": 1854517731,
    "unresolved_parameters": 0,
    "external_router_bias_parameters": 22272,
    "ordinary_scalar_operations": 68817039849112,
    "adam_sqrt": 1854517731,
    "matrix_flops": 234668016634143940,
    "normalization_sqrt": 72252,
    "shared_step_scalar_operations": 8,
    "shape_setup_scalar_multiply": 17,
    "shape_setup_sqrt": 17
  },
  "inventory": {
    "base_logical_parameters": 1572997201763,
    "mtp_logical_parameters": 25840145979
  },
  "excluded_inventory": {
    "base_hash_elements": 2327040,
    "base_quant_scale_elements": 48357516352,
    "mtp_logical_parameters": 25840145979,
    "mtp_quant_scale_elements": 792752064
  },
  "checkpoint_verification": {
    "verified_tensors": 145116,
    "verified_shards": 64,
    "checkpoint_tensor_payload_bytes": 864704792696,
    "byte_groups": {
      "base_parameters_bytes": 802372072332,
      "base_total_bytes": 850748205004,
      "base_hash_table_bytes": 18616320,
      "base_quant_scales_bytes": 48357516352,
      "mtp_parameters_bytes": 13163835628,
      "mtp_total_bytes": 13956587692,
      "mtp_quant_scales_bytes": 792752064
    },
    "tensor_count_by_storage_dtype": {
      "BF16": 619,
      "I64": 3,
      "F32": 590,
      "F8_E8M0": 71952,
      "F8_E4M3": 528,
      "I8": 71424
    },
    "base_logical_parameters_excluding_scales_and_hash": 1572997201763,
    "scope": "Official checkpoint tensor payload, excluding file headers and filesystem overhead. Includes separate MTP; runtime dtype conversion, aliasing and allocated model copies may differ. Payload values were not downloaded or numerically validated."
  },
  "state_interfaces": {
    "declared_fp32_master_weights_bytes": 6291988717964,
    "declared_fp32_muon_momentum_bytes": 6284570647040,
    "declared_fp32_adam_m_v_bytes": 14836141848,
    "declared_fp32_gradient_input_bytes": 6291988717964,
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
    "conditional_selected_parameter_updates_covered": true,
    "router_bias_update_count_unknown": 22272,
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
      "file": "configs/models/deepseek-v4-pro/config.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/config.json",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "5fe4568daee51c208cb8a79538eaeda090ae011ade1dee2c386aa95f569c810e"
    },
    {
      "file": "configs/models/deepseek-v4-pro/inference/config.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/config.json",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "a6aded1806a2dbacbbab89bae2380d0422a6d0dcc55c946b421c7f5e06ef6094"
    },
    {
      "file": "sources/deepseek-v4-pro/inference/model.py",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/model.py",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "ce962f1face79d4f633d36436576214057a7e11443c9789935e1deb5c6cd1d71"
    },
    {
      "file": "sources/deepseek-v4-pro/inference/kernel.py",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/kernel.py",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
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
      "file": "sources/deepseek-v4-pro/model.safetensors.index.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model.safetensors.index.json",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "a3a39b9ccb4e729851922fc9c770f5c5755e7b9d7e96cd02c23f0e12b5e25cb9"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00001-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00001-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "f62844ce4c4d47bc40696a831380bb1464ae9717480bb30251ad05fe87b12fbd"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00002-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00002-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "09c84dc7e7d800b1b7eda5f950488a4edde5058dece58842155a2d2c19d38dfa"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00003-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00003-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "a0f61998df192ab90954d0a00a1ccf5166153a66899d6849741d09e38ab4f7a9"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00004-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00004-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "5ad3452b1f4668d7917a18b085a8c5f2767100fd3f36ff7686061eaa810321a0"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00005-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00005-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "9817aa67c797eb172e6c0ae9e84823ea54b04afb41e2e189c3cc7bedd547fff9"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00006-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00006-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "f012bb8296655c4449c76cfb0c78b2e367c0706f5548a64c180a47f9e8835db1"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00007-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00007-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "c48667932097f3843857a56a36870c2ba5a44149c47a8df7c76a4d0a9a7c0409"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00008-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00008-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "366ab679ecbe8e4dcc8809e7caf6432f11329c84363da64eca6459073142226e"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00009-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00009-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "972018fc9cfab2cefa9db1738e7dc52da0220d16552d944e8de9ff57b2f52e0a"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00010-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00010-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "764ed6d21313964fe00dae095c6afe2d75565bf9fe3ecbf87e09e6d83d093e1f"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00011-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00011-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "01db80934aa5584438318e4fdca952fb91afe58ad05d5332026d637cdc8db877"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00012-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00012-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "773af1e79c9f0ec3d1505fa049e80b4ffb670796b4e024951a4f64fb1342bef7"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00013-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00013-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "1c0343aa40c2392238fca1831246f13562779ddfde10d2ccf9a3a22ad701ddf6"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00014-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00014-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "5eb8c0502dc4385719778971d965cca146f76b9348177b6207e8d252c353f171"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00015-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00015-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "94a9511cae977b5916462e10f46fa6cdd7470414b407e6a9fc7f654d2da4e9d0"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00016-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00016-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "893a168b5ff71d4dff9c88f6ba0a6419b2c4cfca1327faa8f475deb9b6c7784b"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00017-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00017-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "c9368805fe734f1654f7e74f22070c19d13e5c3ce0d61d7563960252898725fc"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00018-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00018-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "42b4f2cf60eebbbc77e9765e5f034bf4dacd83f7fcd81edaab18935123ec0aaa"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00019-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00019-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "6c1ba9cd1ffd09fbbec7283b0b5830721eab9fb3048a56f70451cf4089fa6691"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00020-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00020-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "00d744b2ef8dcf64083fbd4c1fa57d88a8beed492d2ad9feb0abb084c324514d"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00021-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00021-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "08005b0a277f86b5d379be73d6c044e61e73a1cb748364487bd83eeae1f19b24"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00022-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00022-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "2096dd2862f84ed281004ede6d700f8c422ac9f5f6708fa4e622e78c089a3360"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00023-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00023-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "46a697dc52e865034ed8d910ede0f222900b3ea8c944a5cb500f72e939b04da3"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00024-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00024-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "e2b9c7a6e404a9d741f6f134c5453b556ba2a1d7a7c24a2ac7d3ed89e1aa2d22"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00025-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00025-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "5b301d2e50951f2cac98ffdcba8f251cd21ee06f9ee9b06c3a10281749b4a8e1"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00026-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00026-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "8d971ac61f41bbb56bae9300470f8fd6a0353125b3408b287ead3b17677fce3b"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00027-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00027-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "65ee01c2da71bd59d980cb77281ef274e7e28f39d5c3c6000355ed5d9f2d901d"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00028-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00028-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "32873d82bb2169171ada203db4fb6e156baa38e43ee4dec54b2135f45bb46372"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00029-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00029-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "6d896e9661a66563808d89ab2d175ca42ae4f454d12240fce5d01d6639f3b830"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00030-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00030-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "7d37c8cb35b4491a885dd93f5af70ab7207cbab58a6395a1ec0e3acda6070245"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00031-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00031-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "af3aa1bc6590a624d28dea59ff01851124e611b1f75d2bf93c82a533b999f063"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00032-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00032-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "111af8344c0da52f7086873f06977dadf4f0a93f2d5a6ba694373dcf0bacb497"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00033-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00033-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "2e27cd1549eb4cce96dd7a2d3c4326bc9b8369bf8ff3f0c0f502c1fd5981a751"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00034-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00034-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "fde9380f0ac661c616d4ca856591ecf953f384d004c5e3e725b4acf098c09c39"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00035-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00035-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "b444ab6670871e112d2f925a4037aec0fb48c236616b9861bde6da1b076b62a8"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00036-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00036-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "260f19fd3091cf5f1e1e02627b21d0ed3699c815ac7645d0bc7f6878b2ec85a9"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00037-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00037-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "ada278d9a5d040f4198791954d2120fa1234736a90082a5694ec920e638733c7"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00038-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00038-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "20636aa9b7a63fbf8bc48536c668720ca283cd6fbef63a94b912ff0a93e683a9"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00039-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00039-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "cdffc26189719dabd1301e040f1158a2d69ab5e88a7eb2247aa89c949f6f8437"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00040-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00040-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "ae12150988f04ff7a3c64ad20742c0b2039eb2003d271833b9ecce22872e9d98"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00041-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00041-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "4d1f15d8c4588f0735028cb6d2b9d308b9a8baf80e4a65d2565e53e71272decf"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00042-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00042-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "78245a3e3a163146cb8640ee7249e43baacbd6b0c1294f7f0b86f2c3a2ee262a"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00043-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00043-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "bcf24f2bd0eb8d597e3b3cca50941e34cc317b0a0aafeaa809941ba55ae65de4"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00044-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00044-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "9a0112e1ab9bd7cc7989e71e65b33b541180697794cd8aa328694d94f9b5fa5c"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00045-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00045-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "5024100086c9989a18c0d867643cb2058d954266686b979b0c1ca98132927830"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00046-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00046-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "123e4096f27146b8d7209e1f78b808025ec238ee719147eb5c375914f199b1de"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00047-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00047-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "f78fb5091fa057f1b09e034d0a66e5ca6c4ec444c0689d0928ff86247e7b3845"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00048-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00048-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "ff75f7a6cbe6b0558a94a304d4470c840db4e9b69de4143d555c28a85dafc1ef"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00049-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00049-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "f745de46aaea647f5b966cc61e6bf9f26643f7780b547f1206afa6b88b527cfd"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00050-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00050-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "d4b43bcc44eccceebb30a8d07ba7ec1bf626771a49007bc7ac4407f4d9a82b3b"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00051-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00051-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "d01cf662b54ab837ec7de7399d182f372d30bad1a1cf20a0e922918e662fc34c"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00052-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00052-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "8fd10a263f7d795c5fdae4cef849153ab1f4fc5cbe08c4f6f46fb57592fcb557"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00053-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00053-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "530bd227b6a95c4998bfe4539e32bbb68ca927487b2de154ff1d55f121402984"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00054-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00054-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "377c88b1ddd5ed0d29dd5fc0e1dc801c003773dbb6ff4cee594ec5c3572a3cf8"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00055-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00055-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "7f4fbfd6bd08895ae4f4f553af562e0977eb1ded070bb6fff6b585e54a5dced4"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00056-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00056-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "ce3736415591d513968768ab86dd164333b4d0a1a6491b846c8af0fbc1573ede"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00057-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00057-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "804da0c9349206088b99f94ea81b57845cca54d1eaeb30603675906d326f0e4b"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00058-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00058-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "7ccc9e5f5419659d4baa12760c05fa1fb3da4fe9d581060b219b4124c84d509f"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00059-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00059-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "e88377ef55fa69722cc08e7fc4720ce21e6c39000104bc7d05ce9e915391b87b"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00060-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00060-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "1af641c19db47af20c62850890c45ed4daaeb2035d311c4866b253a4cf20d3d9"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00061-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00061-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "e5e13b5c696c3f3c6306fde2be41f45111635ddb5f51bff597826f02ac59a78a"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00062-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00062-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "7258653c3c98ca6615f76c0eda6d6283222424370e9dd58758d6b1e80e19d8e3"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00063-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00063-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "711b38904bc397fca30cddf887b2c6581a48ffcf868fe258c3369af68147366f"
    },
    {
      "file": "sources/deepseek-v4-pro/headers/model-00064-of-00064.safetensors.json",
      "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00064-of-00064.safetensors?header=1",
      "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1",
      "sha256": "14a863bf950f74e19fdcaa16ebbdc192e125e9a7972fbc3f6a9985d100a3a6bb"
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
