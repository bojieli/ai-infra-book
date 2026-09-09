# deepseek-v3-base-forward — deepseek-v3

输入：`{"activation_bytes": 2, "attention_work": "valid", "batch": 1, "history": 8192, "kv_bytes": 2, "mla_path": "reference_expanded", "output_head": "all", "routing": "balanced", "score_bytes": 4, "tokens": 1, "tokens_per_expert_per_moe_layer": [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "training": false, "weight_bytes": 2}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| matrix_flops | 114,190,598,144 |
| scalar_flops | 271,205,237 |
| weight_read_bytes | 73,464,141,824 |
| activation_read_bytes | 41,247,100,032 |
| activation_write_bytes | 291,853,184 |
| special_ops | `{"rsqrt": 245, "sign_negation": 251808, "exp": 63970944, "compare_max": 63963136, "sigmoid": 1139200, "cast_elements": 129280}` |
| logical_base_parameters | 671,026,419,200 |
| uniform_bf16_parameter_bytes | 1,342,052,838,400 |
| logical_base_tensor_count | 45,395 |
| dense_layers | 3 |
| moe_layers | 58 |
| expert_union_per_layer | 8 |
| kv_bytes_per_token_per_request | 4,997,120 |
| kv_resident_after_bytes | 40,941,404,160 |
| kv_new_write_bytes | 4,997,120 |
| history_unique_payload_bytes | 40,936,407,040 |
| valid_attention_matrix_flops | 40,941,404,160 |
| eager_attention_matrix_flops | 40,941,404,160 |
| rectangular_score_fp32_bytes_per_layer | 4,194,816 |
| complete_runtime_bytes | `null` |
| complete_hbm_bytes | `null` |
| predicted_latency_seconds | `null` |

覆盖边界：`{"base_logical_weight_and_operator_graph": true, "checkpoint_header_validation": false, "missing": ["FP8 checkpoint scales and runtime quantization/conversion allocations", "backend tile work, topk/sort internal comparisons and traffic, dispatch copies", "YaRN table construction/growth, DynamicCache concatenation, allocator/workspace lifetimes", "MTP, training/backward, compact MLA alternative, measured runtime/HBM"]}`

每行是一次出现的成本，整模型需乘 repeats；层编号为 0 起。

| 算子 | 重复 | 输入／矩阵／输出 | 矩阵 FLOPs | 普通算术 | 权重读 bytes | 激活读 bytes | 激活写 bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| embedding_lookup | 1 | ids=[1, 1]；output=[1, 7168] | 0 | 0 | 14,336 | 0 | 14,336 |
| input_rmsnorm | 61 | input=[1, 7168]；weight=[7168]；output=[1, 7168] | 0 | 28,673 | 14,336 | 14,336 | 14,336 |
| post_attention_rmsnorm | 61 | input=[1, 7168]；weight=[7168]；output=[1, 7168] | 0 | 28,673 | 14,336 | 14,336 | 14,336 |
| q_a_proj | 61 | input=[1, 7168]；weight_math=[7168, 1536]；weight_storage=[1536, 7168]；output=[1, 1536] | 22,020,096 | 0 | 22,020,096 | 14,336 | 3,072 |
| q_b_proj | 61 | input=[1, 1536]；weight_math=[1536, 24576]；weight_storage=[24576, 1536]；output=[1, 24576] | 75,497,472 | 0 | 75,497,472 | 3,072 | 49,152 |
| kv_a_proj_with_mqa | 61 | input=[1, 7168]；weight_math=[7168, 576]；weight_storage=[576, 7168]；output=[1, 576] | 8,257,536 | 0 | 8,257,536 | 14,336 | 1,152 |
| kv_b_proj | 61 | input=[1, 512]；weight_math=[512, 32768]；weight_storage=[32768, 512]；output=[1, 32768] | 33,554,432 | 0 | 33,554,432 | 1,024 | 65,536 |
| o_proj | 61 | input=[1, 16384]；weight_math=[16384, 7168]；weight_storage=[7168, 16384]；output=[1, 7168] | 234,881,024 | 0 | 234,881,024 | 32,768 | 14,336 |
| q_a_layernorm | 61 | input=[1, 1536]；weight=[1536]；output=[1, 1536] | 0 | 6,145 | 3,072 | 3,072 | 3,072 |
| kv_a_layernorm | 61 | input=[1, 512]；weight=[512]；output=[1, 512] | 0 | 2,049 | 1,024 | 1,024 | 1,024 |
| rotary_q_and_shared_k | 61 | q_rotary=[1, 128, 1, 64]；k_rotary=[1, 1, 1, 64] | 0 | 24,768 | 0 | 16,768 | 16,512 |
| expanded_kv_append | 61 | key=[1, 128, 1, 192]；value=[1, 128, 1, 128] | 0 | 0 | 0 | 81,920 | 81,920 |
| qk_scores | 61 | query=[1, 128, 1, 192]；keys=[1, 128, 8193, 192]；scores_rectangle=[1, 128, 1, 8193] | 402,702,336 | 0 | 0 | 402,751,488 | 2,097,408 |
| score_scale_softmax | 61 | accounted_cells=1048704；query_rows=128 | 0 | 4,194,688 | 0 | 2,097,408 | 2,097,408 |
| pv_output | 61 | probability_rectangle=[1, 128, 1, 8193]；values=[1, 128, 8193, 128]；output=[1, 128, 1, 128] | 268,468,224 | 0 | 0 | 270,565,632 | 32,768 |
| router_fp32 | 58 | input=[1, 7168]；weight_math=[7168, 256]；weight_storage=[256, 7168]；output=[1, 256] | 3,670,016 | 0 | 7,340,032 | 28,672 | 1,024 |
| router_sigmoid_and_correction | 58 | scores=[1, 256] | 0 | 256 | 1,024 | 1,024 | 2,048 |
| router_group_sum_and_weight_normalization | 58 | group_top2=[1, 8, 2]；selected=[1, 8] | 0 | 32 | 0 | 96 | 64 |
| dense_gate | 3 | input=[1, 7168]；weight_math=[7168, 18432]；weight_storage=[18432, 7168]；output=[1, 18432] | 264,241,152 | 0 | 264,241,152 | 14,336 | 36,864 |
| dense_up | 3 | input=[1, 7168]；weight_math=[7168, 18432]；weight_storage=[18432, 7168]；output=[1, 18432] | 264,241,152 | 0 | 264,241,152 | 14,336 | 36,864 |
| dense_down | 3 | input=[1, 18432]；weight_math=[18432, 7168]；weight_storage=[7168, 18432]；output=[1, 7168] | 264,241,152 | 0 | 264,241,152 | 36,864 | 14,336 |
| dense_silu_and_product | 3 | gate_and_up=[1, 18432] | 0 | 36,864 | 0 | 73,728 | 36,864 |
| shared_gate | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| shared_up | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| shared_down | 58 | input=[1, 2048]；weight_math=[2048, 7168]；weight_storage=[7168, 2048]；output=[1, 7168] | 29,360,128 | 0 | 29,360,128 | 4,096 | 14,336 |
| shared_silu_and_product | 58 | gate_and_up=[1, 2048] | 0 | 4,096 | 0 | 8,192 | 4,096 |
| expert_0_gate | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_0_up | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_0_down | 58 | input=[1, 2048]；weight_math=[2048, 7168]；weight_storage=[7168, 2048]；output=[1, 7168] | 29,360,128 | 0 | 29,360,128 | 4,096 | 14,336 |
| expert_0_silu_and_product | 58 | gate_and_up=[1, 2048] | 0 | 4,096 | 0 | 8,192 | 4,096 |
| expert_1_gate | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_1_up | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_1_down | 58 | input=[1, 2048]；weight_math=[2048, 7168]；weight_storage=[7168, 2048]；output=[1, 7168] | 29,360,128 | 0 | 29,360,128 | 4,096 | 14,336 |
| expert_1_silu_and_product | 58 | gate_and_up=[1, 2048] | 0 | 4,096 | 0 | 8,192 | 4,096 |
| expert_2_gate | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_2_up | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_2_down | 58 | input=[1, 2048]；weight_math=[2048, 7168]；weight_storage=[7168, 2048]；output=[1, 7168] | 29,360,128 | 0 | 29,360,128 | 4,096 | 14,336 |
| expert_2_silu_and_product | 58 | gate_and_up=[1, 2048] | 0 | 4,096 | 0 | 8,192 | 4,096 |
| expert_3_gate | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_3_up | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_3_down | 58 | input=[1, 2048]；weight_math=[2048, 7168]；weight_storage=[7168, 2048]；output=[1, 7168] | 29,360,128 | 0 | 29,360,128 | 4,096 | 14,336 |
| expert_3_silu_and_product | 58 | gate_and_up=[1, 2048] | 0 | 4,096 | 0 | 8,192 | 4,096 |
| expert_4_gate | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_4_up | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_4_down | 58 | input=[1, 2048]；weight_math=[2048, 7168]；weight_storage=[7168, 2048]；output=[1, 7168] | 29,360,128 | 0 | 29,360,128 | 4,096 | 14,336 |
| expert_4_silu_and_product | 58 | gate_and_up=[1, 2048] | 0 | 4,096 | 0 | 8,192 | 4,096 |
| expert_5_gate | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_5_up | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_5_down | 58 | input=[1, 2048]；weight_math=[2048, 7168]；weight_storage=[7168, 2048]；output=[1, 7168] | 29,360,128 | 0 | 29,360,128 | 4,096 | 14,336 |
| expert_5_silu_and_product | 58 | gate_and_up=[1, 2048] | 0 | 4,096 | 0 | 8,192 | 4,096 |
| expert_6_gate | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_6_up | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_6_down | 58 | input=[1, 2048]；weight_math=[2048, 7168]；weight_storage=[7168, 2048]；output=[1, 7168] | 29,360,128 | 0 | 29,360,128 | 4,096 | 14,336 |
| expert_6_silu_and_product | 58 | gate_and_up=[1, 2048] | 0 | 4,096 | 0 | 8,192 | 4,096 |
| expert_7_gate | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_7_up | 58 | input=[1, 7168]；weight_math=[7168, 2048]；weight_storage=[2048, 7168]；output=[1, 2048] | 29,360,128 | 0 | 29,360,128 | 14,336 | 4,096 |
| expert_7_down | 58 | input=[1, 2048]；weight_math=[2048, 7168]；weight_storage=[7168, 2048]；output=[1, 7168] | 29,360,128 | 0 | 29,360,128 | 4,096 | 14,336 |
| expert_7_silu_and_product | 58 | gate_and_up=[1, 2048] | 0 | 4,096 | 0 | 8,192 | 4,096 |
| routed_weighted_reduce_and_shared_add | 58 | expert_outputs=[1, 8, 7168] | 0 | 114,688 | 0 | 129,056 | 14,336 |
| attention_and_ffn_residual_adds | 122 | input=[1, 7168] | 0 | 7,168 | 0 | 28,672 | 14,336 |
| final_rmsnorm | 1 | input=[1, 7168]；weight=[7168]；output=[1, 7168] | 0 | 28,673 | 14,336 | 14,336 | 14,336 |
| lm_head | 1 | input=[1, 7168]；weight_math=[7168, 129280]；weight_storage=[129280, 7168]；output=[1, 129280] | 1,853,358,080 | 0 | 1,853,358,080 | 14,336 | 258,560 |
| logits_float32_cast | 1 | logits=[1, 129280] | 0 | 0 | 0 | 258,560 | 517,120 |

计量条件：

- Pinned base model with 61 attention layers, 3 dense FFNs and 58 MoE FFNs; 256 routed top-8 plus one shared expert. Weights enumerate logical model tensors, excluding MTP and checkpoint quantization scales. No checkpoint index/header evidence is claimed.
- Official HF forward expands KV then cache.update, applies RoPE to Q and shared K extra branch, and projects all positions by default. last/none output heads are explicit workload alternatives, not a claim about this unmodified forward.
- Valid attention counts useful causal cells; eager counts full score rectangle plus additive mask, matching the source mathematical path. FP32 internal softmax and source conversion traffic are not inferred as fused backend HBM. No attention dropout in inference.
- YaRN cos/sin tables and softmax scale are prepared constants. Rotary application is counted; table preparation/growth is separate. Shared rotary K is expanded across heads in the reference cache.
- Balanced/concentrated histograms are conditional routing inputs repeated across MoE layers, not measured choices. Explicit histograms pass assignment conservation but do not prove realizability under four-group selection. Grouped routing uses biased scores only for selection; mixture weights use original sigmoid scores, normalized then multiplied by 2.5.
- Matrix FMA counts as two FLOPs. Scalar arithmetic and special functions stay separate. Weight and activation bytes are declared logical operator interfaces with one read per operand; expert weights read once per visited expert. They are not cache-aware HBM measurements or simultaneous allocation peaks.
- Uniform two-byte weight capacity is a comparison format only. Router executes FP32 operands; official FP8 block quantization requires separate physical storage and conversion accounting. Global state, runtime copies, dispatch/reshape traffic and unsupported paths stay explicit in coverage.

固定来源：

- [configs/models/deepseek-v3/config.json](https://huggingface.co/deepseek-ai/DeepSeek-V3/resolve/e815299b0bcbac849fa540c768ef21845365c9eb/config.json)，SHA256 `cbf0b95dc614de208a109bb5fd4e7eed11385e9c68411d2c17db5319443035d9`。
- [sources/deepseek-v3/modeling_deepseek.py](https://huggingface.co/deepseek-ai/DeepSeek-V3/resolve/e815299b0bcbac849fa540c768ef21845365c9eb/modeling_deepseek.py)，SHA256 `eb6d535742061cf9da7a4232ecfe2f089d5ce20080afc5d2181e9d70ec4af8a4`。
