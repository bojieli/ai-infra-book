# Qwen3-8B 训练非矩阵参考账

## 输入

| 字段 | 值 |
| --- | --- |
| batch | 1 |
| tokens | 128 |
| supervised_tokens | unknown |
| head_strategy | dense |
| activation_policy | save_nonlinear |
| adam_step | 1 |
| learning_rate | 0.001 |
| beta1 | 0.9 |
| beta2 | 0.999 |
| epsilon | 1e-08 |
| weight_decay | 0.01 |

## 汇总

普通算术与矩阵FLOPs可加为已计子账；special、cast、integer和bytes分别列出。完整训练与峰值保留unknown。

| 字段 | 值 |
| --- | --- |
| original_training_matrix_flops | 5826907471872 |
| forward_scalar_flops | 565679488 |
| backward_scalar_flops | 1095199872 |
| optimizer_scalar_flops | 114670295046 |
| accounted_special_ops | {"cos": 16384, "exp": 28958720, "log": 128, "max_compare": 28811136, "pow": 2, "rsqrt": 193664, "sigmoid": 56623104, "sin": 16384, "sqrt": 8190735360} |
| accounted_matrix_plus_scalar_flops | 5943238646278 |
| nonlinear_saved_at_forward_end_bytes | 1043550720 |
| declared_saved_and_recomputed_subset_peak_bytes | 1043550720 |
| original_parameter_state_bytes | 147433236480 |
| complete_training_step_flops | unknown |
| complete_activation_peak_bytes | unknown |
| complete_hbm_traffic_bytes | unknown |
| predicted_step_seconds | unknown |

## 非矩阵前向与反向

| 算子 | 形状 | 前向scalar | 反向scalar | 前向special | 反向special | 算法说明 |
| --- | --- | --- | --- | --- | --- | --- |
| input_rmsnorm | [36, 128, 4096] | 75502080 | 150847488 | {"rsqrt": 4608} | {} | dx=6RD; shared dgamma=(2R-1)D per parameter copy. FP32 saved z/r; no cross-layer gamma merge. |
| post_attention_rmsnorm | [36, 128, 4096] | 75502080 | 150847488 | {"rsqrt": 4608} | {} | dx=6RD; shared dgamma=(2R-1)D per parameter copy. FP32 saved z/r; no cross-layer gamma merge. |
| query_rmsnorm | [36, 4096, 128] | 75644928 | 150990336 | {"rsqrt": 147456} | {} | dx=6RD; shared dgamma=(2R-1)D per parameter copy. FP32 saved z/r; no cross-layer gamma merge. |
| key_rmsnorm | [36, 1024, 128] | 18911232 | 37744128 | {"rsqrt": 36864} | {} | dx=6RD; shared dgamma=(2R-1)D per parameter copy. FP32 saved z/r; no cross-layer gamma merge. |
| final_rmsnorm | [1, 128, 4096] | 2097280 | 4190208 | {"rsqrt": 128} | {} | dx=6RD; shared dgamma=(2R-1)D per parameter copy. FP32 saved z/r; no cross-layer gamma merge. |
| swiglu | [36, 128, 12288] | 113246208 | 339738624 | {"sigmoid": 56623104} | {} | Save a/s/u; or save g/u and recompute sigmoid plus a=g*s immediately before backward. |
| attention_scale_softmax | [36, 1, 32, 128, "causal_row_width=1..T"] | 37896192 | 47407104 | {"exp": 9510912, "max_compare": 9363456} | {} | Backward softmax=4K-1; backward score scale adds K. No gradient through stabilizing max selection. |
| rotary_apply | [36, 128, 40, 128] | 70778880 | 70778880 | {} | {} | Fixed rotation and transpose; no learned position parameter. |
| rotary_table_per_step | [128, 128] | 8192 | 0 | {"cos": 16384, "sin": 16384} | {} | Shared across batch and layers; fixed inv_freq initialization excluded. |
| residual_and_branch_gradient_merges | [36, 128, 4096] | 37748736 | 94371840 | {} | {} | Backward: two residual joins, one gate/up input join, two Q/K/V input joins; fork/alias itself is no arithmetic. |
| gqa_head_gradient_reduce | [36, 128, 8, 4, 128] | 0 | 28311552 | {} | {} | Declared independent per-query-head dK/dV outputs are summed into each KV group; fused grouped contraction may absorb this reduction into its own matrix convention. |
| embedding_scatter_add | [128, 4096] | 0 | 524288 | {} | {} | One additive contribution per token component into a zeroed dense embedding gradient; IDs/collisions/atomics unknown. |
| mean_cross_entropy | [128, 151936] | 58343680 | 19447936 | {"exp": 19447808, "log": 128, "max_compare": 19447680} | {} | Stable logsumexp plus saved probabilities; mean reduction S operations. Backward only target subtract then V scales per row. |

## AdamW

| 字段 | 值 |
| --- | --- |
| algorithm | unfused dense AdamW declared scalar formula |
| parameters | 8190735360 |
| parameter_scalar_flops | 114670295040 |
| shared_coefficient_scalar_flops | 6 |
| special_ops | {"pow": 2, "sqrt": 8190735360} |
| integer_ops | {"step_index_increment": 1} |
| typed_conversions | {"fp32_master_to_bf16_weights": 8190735360} |
| interfaces | {"bf16_parameter_write_bytes": 16381470720, "fp32_gradient_master_m_v_read_bytes": 131051765760, "fp32_master_m_v_write_bytes": 98288824320} |
| constants | {"beta1": 0.9, "beta2": 0.999, "epsilon": 1e-08, "learning_rate": 0.001, "step": 1, "weight_decay": 0.01} |

## Typed与数据操作

| 字段（名称标单位） | 值 |
| --- | --- |
| embedding_gradient_zero_fp32_bytes | 2489319424 |
| embedding_index_reads_int64_bytes | 1024 |
| loss_gradient_zero_fp32_bytes | 77791232 |
| loss_label_reads_int64_bytes | 1024 |
| loss_selected_logits_bf16_read_bytes | 38895616 |
| loss_gradient_scatter_fp32_write_bytes | 77791232 |
| bf16_to_fp32_nonlinear_input_elements | 194560000 |
| fp32_to_bf16_norm_swiglu_output_elements | 118489088 |
| compact_hidden_gather_bf16_read_write_bytes | 0 |
| compact_hidden_gradient_zero_fp32_bytes | 0 |
| compact_hidden_gradient_scatter_fp32_read_write_bytes | 0 |

## 声明保存对象

只列本非线性反向算法对象；不包含全部矩阵保存输入、梯度或allocator。

| ID | 对象 | 层 | 元素 | dtype | bytes |
| --- | --- | --- | --- | --- | --- |
| saved-0 | input_norm_z_r | 0 | 524416 | fp32 | 2097664 |
| saved-1 | query_norm_z_r | 0 | 528384 | fp32 | 2113536 |
| saved-2 | key_norm_z_r | 0 | 132096 | fp32 | 528384 |
| saved-3 | attention_probabilities | 0 | 264192 | fp32 | 1056768 |
| saved-4 | post_norm_z_r | 0 | 524416 | fp32 | 2097664 |
| saved-5 | swiglu_a_s_u | 0 | 4718592 | fp32 | 18874368 |
| saved-6 | input_norm_z_r | 1 | 524416 | fp32 | 2097664 |
| saved-7 | query_norm_z_r | 1 | 528384 | fp32 | 2113536 |
| saved-8 | key_norm_z_r | 1 | 132096 | fp32 | 528384 |
| saved-9 | attention_probabilities | 1 | 264192 | fp32 | 1056768 |
| saved-10 | post_norm_z_r | 1 | 524416 | fp32 | 2097664 |
| saved-11 | swiglu_a_s_u | 1 | 4718592 | fp32 | 18874368 |
| saved-12 | input_norm_z_r | 2 | 524416 | fp32 | 2097664 |
| saved-13 | query_norm_z_r | 2 | 528384 | fp32 | 2113536 |
| saved-14 | key_norm_z_r | 2 | 132096 | fp32 | 528384 |
| saved-15 | attention_probabilities | 2 | 264192 | fp32 | 1056768 |
| saved-16 | post_norm_z_r | 2 | 524416 | fp32 | 2097664 |
| saved-17 | swiglu_a_s_u | 2 | 4718592 | fp32 | 18874368 |
| saved-18 | input_norm_z_r | 3 | 524416 | fp32 | 2097664 |
| saved-19 | query_norm_z_r | 3 | 528384 | fp32 | 2113536 |
| saved-20 | key_norm_z_r | 3 | 132096 | fp32 | 528384 |
| saved-21 | attention_probabilities | 3 | 264192 | fp32 | 1056768 |
| saved-22 | post_norm_z_r | 3 | 524416 | fp32 | 2097664 |
| saved-23 | swiglu_a_s_u | 3 | 4718592 | fp32 | 18874368 |
| saved-24 | input_norm_z_r | 4 | 524416 | fp32 | 2097664 |
| saved-25 | query_norm_z_r | 4 | 528384 | fp32 | 2113536 |
| saved-26 | key_norm_z_r | 4 | 132096 | fp32 | 528384 |
| saved-27 | attention_probabilities | 4 | 264192 | fp32 | 1056768 |
| saved-28 | post_norm_z_r | 4 | 524416 | fp32 | 2097664 |
| saved-29 | swiglu_a_s_u | 4 | 4718592 | fp32 | 18874368 |
| saved-30 | input_norm_z_r | 5 | 524416 | fp32 | 2097664 |
| saved-31 | query_norm_z_r | 5 | 528384 | fp32 | 2113536 |
| saved-32 | key_norm_z_r | 5 | 132096 | fp32 | 528384 |
| saved-33 | attention_probabilities | 5 | 264192 | fp32 | 1056768 |
| saved-34 | post_norm_z_r | 5 | 524416 | fp32 | 2097664 |
| saved-35 | swiglu_a_s_u | 5 | 4718592 | fp32 | 18874368 |
| saved-36 | input_norm_z_r | 6 | 524416 | fp32 | 2097664 |
| saved-37 | query_norm_z_r | 6 | 528384 | fp32 | 2113536 |
| saved-38 | key_norm_z_r | 6 | 132096 | fp32 | 528384 |
| saved-39 | attention_probabilities | 6 | 264192 | fp32 | 1056768 |
| saved-40 | post_norm_z_r | 6 | 524416 | fp32 | 2097664 |
| saved-41 | swiglu_a_s_u | 6 | 4718592 | fp32 | 18874368 |
| saved-42 | input_norm_z_r | 7 | 524416 | fp32 | 2097664 |
| saved-43 | query_norm_z_r | 7 | 528384 | fp32 | 2113536 |
| saved-44 | key_norm_z_r | 7 | 132096 | fp32 | 528384 |
| saved-45 | attention_probabilities | 7 | 264192 | fp32 | 1056768 |
| saved-46 | post_norm_z_r | 7 | 524416 | fp32 | 2097664 |
| saved-47 | swiglu_a_s_u | 7 | 4718592 | fp32 | 18874368 |
| saved-48 | input_norm_z_r | 8 | 524416 | fp32 | 2097664 |
| saved-49 | query_norm_z_r | 8 | 528384 | fp32 | 2113536 |
| saved-50 | key_norm_z_r | 8 | 132096 | fp32 | 528384 |
| saved-51 | attention_probabilities | 8 | 264192 | fp32 | 1056768 |
| saved-52 | post_norm_z_r | 8 | 524416 | fp32 | 2097664 |
| saved-53 | swiglu_a_s_u | 8 | 4718592 | fp32 | 18874368 |
| saved-54 | input_norm_z_r | 9 | 524416 | fp32 | 2097664 |
| saved-55 | query_norm_z_r | 9 | 528384 | fp32 | 2113536 |
| saved-56 | key_norm_z_r | 9 | 132096 | fp32 | 528384 |
| saved-57 | attention_probabilities | 9 | 264192 | fp32 | 1056768 |
| saved-58 | post_norm_z_r | 9 | 524416 | fp32 | 2097664 |
| saved-59 | swiglu_a_s_u | 9 | 4718592 | fp32 | 18874368 |
| saved-60 | input_norm_z_r | 10 | 524416 | fp32 | 2097664 |
| saved-61 | query_norm_z_r | 10 | 528384 | fp32 | 2113536 |
| saved-62 | key_norm_z_r | 10 | 132096 | fp32 | 528384 |
| saved-63 | attention_probabilities | 10 | 264192 | fp32 | 1056768 |
| saved-64 | post_norm_z_r | 10 | 524416 | fp32 | 2097664 |
| saved-65 | swiglu_a_s_u | 10 | 4718592 | fp32 | 18874368 |
| saved-66 | input_norm_z_r | 11 | 524416 | fp32 | 2097664 |
| saved-67 | query_norm_z_r | 11 | 528384 | fp32 | 2113536 |
| saved-68 | key_norm_z_r | 11 | 132096 | fp32 | 528384 |
| saved-69 | attention_probabilities | 11 | 264192 | fp32 | 1056768 |
| saved-70 | post_norm_z_r | 11 | 524416 | fp32 | 2097664 |
| saved-71 | swiglu_a_s_u | 11 | 4718592 | fp32 | 18874368 |
| saved-72 | input_norm_z_r | 12 | 524416 | fp32 | 2097664 |
| saved-73 | query_norm_z_r | 12 | 528384 | fp32 | 2113536 |
| saved-74 | key_norm_z_r | 12 | 132096 | fp32 | 528384 |
| saved-75 | attention_probabilities | 12 | 264192 | fp32 | 1056768 |
| saved-76 | post_norm_z_r | 12 | 524416 | fp32 | 2097664 |
| saved-77 | swiglu_a_s_u | 12 | 4718592 | fp32 | 18874368 |
| saved-78 | input_norm_z_r | 13 | 524416 | fp32 | 2097664 |
| saved-79 | query_norm_z_r | 13 | 528384 | fp32 | 2113536 |
| saved-80 | key_norm_z_r | 13 | 132096 | fp32 | 528384 |
| saved-81 | attention_probabilities | 13 | 264192 | fp32 | 1056768 |
| saved-82 | post_norm_z_r | 13 | 524416 | fp32 | 2097664 |
| saved-83 | swiglu_a_s_u | 13 | 4718592 | fp32 | 18874368 |
| saved-84 | input_norm_z_r | 14 | 524416 | fp32 | 2097664 |
| saved-85 | query_norm_z_r | 14 | 528384 | fp32 | 2113536 |
| saved-86 | key_norm_z_r | 14 | 132096 | fp32 | 528384 |
| saved-87 | attention_probabilities | 14 | 264192 | fp32 | 1056768 |
| saved-88 | post_norm_z_r | 14 | 524416 | fp32 | 2097664 |
| saved-89 | swiglu_a_s_u | 14 | 4718592 | fp32 | 18874368 |
| saved-90 | input_norm_z_r | 15 | 524416 | fp32 | 2097664 |
| saved-91 | query_norm_z_r | 15 | 528384 | fp32 | 2113536 |
| saved-92 | key_norm_z_r | 15 | 132096 | fp32 | 528384 |
| saved-93 | attention_probabilities | 15 | 264192 | fp32 | 1056768 |
| saved-94 | post_norm_z_r | 15 | 524416 | fp32 | 2097664 |
| saved-95 | swiglu_a_s_u | 15 | 4718592 | fp32 | 18874368 |
| saved-96 | input_norm_z_r | 16 | 524416 | fp32 | 2097664 |
| saved-97 | query_norm_z_r | 16 | 528384 | fp32 | 2113536 |
| saved-98 | key_norm_z_r | 16 | 132096 | fp32 | 528384 |
| saved-99 | attention_probabilities | 16 | 264192 | fp32 | 1056768 |
| saved-100 | post_norm_z_r | 16 | 524416 | fp32 | 2097664 |
| saved-101 | swiglu_a_s_u | 16 | 4718592 | fp32 | 18874368 |
| saved-102 | input_norm_z_r | 17 | 524416 | fp32 | 2097664 |
| saved-103 | query_norm_z_r | 17 | 528384 | fp32 | 2113536 |
| saved-104 | key_norm_z_r | 17 | 132096 | fp32 | 528384 |
| saved-105 | attention_probabilities | 17 | 264192 | fp32 | 1056768 |
| saved-106 | post_norm_z_r | 17 | 524416 | fp32 | 2097664 |
| saved-107 | swiglu_a_s_u | 17 | 4718592 | fp32 | 18874368 |
| saved-108 | input_norm_z_r | 18 | 524416 | fp32 | 2097664 |
| saved-109 | query_norm_z_r | 18 | 528384 | fp32 | 2113536 |
| saved-110 | key_norm_z_r | 18 | 132096 | fp32 | 528384 |
| saved-111 | attention_probabilities | 18 | 264192 | fp32 | 1056768 |
| saved-112 | post_norm_z_r | 18 | 524416 | fp32 | 2097664 |
| saved-113 | swiglu_a_s_u | 18 | 4718592 | fp32 | 18874368 |
| saved-114 | input_norm_z_r | 19 | 524416 | fp32 | 2097664 |
| saved-115 | query_norm_z_r | 19 | 528384 | fp32 | 2113536 |
| saved-116 | key_norm_z_r | 19 | 132096 | fp32 | 528384 |
| saved-117 | attention_probabilities | 19 | 264192 | fp32 | 1056768 |
| saved-118 | post_norm_z_r | 19 | 524416 | fp32 | 2097664 |
| saved-119 | swiglu_a_s_u | 19 | 4718592 | fp32 | 18874368 |
| saved-120 | input_norm_z_r | 20 | 524416 | fp32 | 2097664 |
| saved-121 | query_norm_z_r | 20 | 528384 | fp32 | 2113536 |
| saved-122 | key_norm_z_r | 20 | 132096 | fp32 | 528384 |
| saved-123 | attention_probabilities | 20 | 264192 | fp32 | 1056768 |
| saved-124 | post_norm_z_r | 20 | 524416 | fp32 | 2097664 |
| saved-125 | swiglu_a_s_u | 20 | 4718592 | fp32 | 18874368 |
| saved-126 | input_norm_z_r | 21 | 524416 | fp32 | 2097664 |
| saved-127 | query_norm_z_r | 21 | 528384 | fp32 | 2113536 |
| saved-128 | key_norm_z_r | 21 | 132096 | fp32 | 528384 |
| saved-129 | attention_probabilities | 21 | 264192 | fp32 | 1056768 |
| saved-130 | post_norm_z_r | 21 | 524416 | fp32 | 2097664 |
| saved-131 | swiglu_a_s_u | 21 | 4718592 | fp32 | 18874368 |
| saved-132 | input_norm_z_r | 22 | 524416 | fp32 | 2097664 |
| saved-133 | query_norm_z_r | 22 | 528384 | fp32 | 2113536 |
| saved-134 | key_norm_z_r | 22 | 132096 | fp32 | 528384 |
| saved-135 | attention_probabilities | 22 | 264192 | fp32 | 1056768 |
| saved-136 | post_norm_z_r | 22 | 524416 | fp32 | 2097664 |
| saved-137 | swiglu_a_s_u | 22 | 4718592 | fp32 | 18874368 |
| saved-138 | input_norm_z_r | 23 | 524416 | fp32 | 2097664 |
| saved-139 | query_norm_z_r | 23 | 528384 | fp32 | 2113536 |
| saved-140 | key_norm_z_r | 23 | 132096 | fp32 | 528384 |
| saved-141 | attention_probabilities | 23 | 264192 | fp32 | 1056768 |
| saved-142 | post_norm_z_r | 23 | 524416 | fp32 | 2097664 |
| saved-143 | swiglu_a_s_u | 23 | 4718592 | fp32 | 18874368 |
| saved-144 | input_norm_z_r | 24 | 524416 | fp32 | 2097664 |
| saved-145 | query_norm_z_r | 24 | 528384 | fp32 | 2113536 |
| saved-146 | key_norm_z_r | 24 | 132096 | fp32 | 528384 |
| saved-147 | attention_probabilities | 24 | 264192 | fp32 | 1056768 |
| saved-148 | post_norm_z_r | 24 | 524416 | fp32 | 2097664 |
| saved-149 | swiglu_a_s_u | 24 | 4718592 | fp32 | 18874368 |
| saved-150 | input_norm_z_r | 25 | 524416 | fp32 | 2097664 |
| saved-151 | query_norm_z_r | 25 | 528384 | fp32 | 2113536 |
| saved-152 | key_norm_z_r | 25 | 132096 | fp32 | 528384 |
| saved-153 | attention_probabilities | 25 | 264192 | fp32 | 1056768 |
| saved-154 | post_norm_z_r | 25 | 524416 | fp32 | 2097664 |
| saved-155 | swiglu_a_s_u | 25 | 4718592 | fp32 | 18874368 |
| saved-156 | input_norm_z_r | 26 | 524416 | fp32 | 2097664 |
| saved-157 | query_norm_z_r | 26 | 528384 | fp32 | 2113536 |
| saved-158 | key_norm_z_r | 26 | 132096 | fp32 | 528384 |
| saved-159 | attention_probabilities | 26 | 264192 | fp32 | 1056768 |
| saved-160 | post_norm_z_r | 26 | 524416 | fp32 | 2097664 |
| saved-161 | swiglu_a_s_u | 26 | 4718592 | fp32 | 18874368 |
| saved-162 | input_norm_z_r | 27 | 524416 | fp32 | 2097664 |
| saved-163 | query_norm_z_r | 27 | 528384 | fp32 | 2113536 |
| saved-164 | key_norm_z_r | 27 | 132096 | fp32 | 528384 |
| saved-165 | attention_probabilities | 27 | 264192 | fp32 | 1056768 |
| saved-166 | post_norm_z_r | 27 | 524416 | fp32 | 2097664 |
| saved-167 | swiglu_a_s_u | 27 | 4718592 | fp32 | 18874368 |
| saved-168 | input_norm_z_r | 28 | 524416 | fp32 | 2097664 |
| saved-169 | query_norm_z_r | 28 | 528384 | fp32 | 2113536 |
| saved-170 | key_norm_z_r | 28 | 132096 | fp32 | 528384 |
| saved-171 | attention_probabilities | 28 | 264192 | fp32 | 1056768 |
| saved-172 | post_norm_z_r | 28 | 524416 | fp32 | 2097664 |
| saved-173 | swiglu_a_s_u | 28 | 4718592 | fp32 | 18874368 |
| saved-174 | input_norm_z_r | 29 | 524416 | fp32 | 2097664 |
| saved-175 | query_norm_z_r | 29 | 528384 | fp32 | 2113536 |
| saved-176 | key_norm_z_r | 29 | 132096 | fp32 | 528384 |
| saved-177 | attention_probabilities | 29 | 264192 | fp32 | 1056768 |
| saved-178 | post_norm_z_r | 29 | 524416 | fp32 | 2097664 |
| saved-179 | swiglu_a_s_u | 29 | 4718592 | fp32 | 18874368 |
| saved-180 | input_norm_z_r | 30 | 524416 | fp32 | 2097664 |
| saved-181 | query_norm_z_r | 30 | 528384 | fp32 | 2113536 |
| saved-182 | key_norm_z_r | 30 | 132096 | fp32 | 528384 |
| saved-183 | attention_probabilities | 30 | 264192 | fp32 | 1056768 |
| saved-184 | post_norm_z_r | 30 | 524416 | fp32 | 2097664 |
| saved-185 | swiglu_a_s_u | 30 | 4718592 | fp32 | 18874368 |
| saved-186 | input_norm_z_r | 31 | 524416 | fp32 | 2097664 |
| saved-187 | query_norm_z_r | 31 | 528384 | fp32 | 2113536 |
| saved-188 | key_norm_z_r | 31 | 132096 | fp32 | 528384 |
| saved-189 | attention_probabilities | 31 | 264192 | fp32 | 1056768 |
| saved-190 | post_norm_z_r | 31 | 524416 | fp32 | 2097664 |
| saved-191 | swiglu_a_s_u | 31 | 4718592 | fp32 | 18874368 |
| saved-192 | input_norm_z_r | 32 | 524416 | fp32 | 2097664 |
| saved-193 | query_norm_z_r | 32 | 528384 | fp32 | 2113536 |
| saved-194 | key_norm_z_r | 32 | 132096 | fp32 | 528384 |
| saved-195 | attention_probabilities | 32 | 264192 | fp32 | 1056768 |
| saved-196 | post_norm_z_r | 32 | 524416 | fp32 | 2097664 |
| saved-197 | swiglu_a_s_u | 32 | 4718592 | fp32 | 18874368 |
| saved-198 | input_norm_z_r | 33 | 524416 | fp32 | 2097664 |
| saved-199 | query_norm_z_r | 33 | 528384 | fp32 | 2113536 |
| saved-200 | key_norm_z_r | 33 | 132096 | fp32 | 528384 |
| saved-201 | attention_probabilities | 33 | 264192 | fp32 | 1056768 |
| saved-202 | post_norm_z_r | 33 | 524416 | fp32 | 2097664 |
| saved-203 | swiglu_a_s_u | 33 | 4718592 | fp32 | 18874368 |
| saved-204 | input_norm_z_r | 34 | 524416 | fp32 | 2097664 |
| saved-205 | query_norm_z_r | 34 | 528384 | fp32 | 2113536 |
| saved-206 | key_norm_z_r | 34 | 132096 | fp32 | 528384 |
| saved-207 | attention_probabilities | 34 | 264192 | fp32 | 1056768 |
| saved-208 | post_norm_z_r | 34 | 524416 | fp32 | 2097664 |
| saved-209 | swiglu_a_s_u | 34 | 4718592 | fp32 | 18874368 |
| saved-210 | input_norm_z_r | 35 | 524416 | fp32 | 2097664 |
| saved-211 | query_norm_z_r | 35 | 528384 | fp32 | 2113536 |
| saved-212 | key_norm_z_r | 35 | 132096 | fp32 | 528384 |
| saved-213 | attention_probabilities | 35 | 264192 | fp32 | 1056768 |
| saved-214 | post_norm_z_r | 35 | 524416 | fp32 | 2097664 |
| saved-215 | swiglu_a_s_u | 35 | 4718592 | fp32 | 18874368 |
| saved-216 | final_norm_z_r | unknown | 524416 | fp32 | 2097664 |
| saved-217 | loss_probabilities | unknown | 19447808 | fp32 | 77791232 |

## 保存与重算事件

| 事件 | 动作 | 对象 | 变化bytes | 子集合存活bytes |
| --- | --- | --- | --- | --- |
| 0 | save | saved-0 | 2097664 | 2097664 |
| 1 | save | saved-1 | 2113536 | 4211200 |
| 2 | save | saved-2 | 528384 | 4739584 |
| 3 | save | saved-3 | 1056768 | 5796352 |
| 4 | save | saved-4 | 2097664 | 7894016 |
| 5 | save | saved-5 | 18874368 | 26768384 |
| 6 | save | saved-6 | 2097664 | 28866048 |
| 7 | save | saved-7 | 2113536 | 30979584 |
| 8 | save | saved-8 | 528384 | 31507968 |
| 9 | save | saved-9 | 1056768 | 32564736 |
| 10 | save | saved-10 | 2097664 | 34662400 |
| 11 | save | saved-11 | 18874368 | 53536768 |
| 12 | save | saved-12 | 2097664 | 55634432 |
| 13 | save | saved-13 | 2113536 | 57747968 |
| 14 | save | saved-14 | 528384 | 58276352 |
| 15 | save | saved-15 | 1056768 | 59333120 |
| 16 | save | saved-16 | 2097664 | 61430784 |
| 17 | save | saved-17 | 18874368 | 80305152 |
| 18 | save | saved-18 | 2097664 | 82402816 |
| 19 | save | saved-19 | 2113536 | 84516352 |
| 20 | save | saved-20 | 528384 | 85044736 |
| 21 | save | saved-21 | 1056768 | 86101504 |
| 22 | save | saved-22 | 2097664 | 88199168 |
| 23 | save | saved-23 | 18874368 | 107073536 |
| 24 | save | saved-24 | 2097664 | 109171200 |
| 25 | save | saved-25 | 2113536 | 111284736 |
| 26 | save | saved-26 | 528384 | 111813120 |
| 27 | save | saved-27 | 1056768 | 112869888 |
| 28 | save | saved-28 | 2097664 | 114967552 |
| 29 | save | saved-29 | 18874368 | 133841920 |
| 30 | save | saved-30 | 2097664 | 135939584 |
| 31 | save | saved-31 | 2113536 | 138053120 |
| 32 | save | saved-32 | 528384 | 138581504 |
| 33 | save | saved-33 | 1056768 | 139638272 |
| 34 | save | saved-34 | 2097664 | 141735936 |
| 35 | save | saved-35 | 18874368 | 160610304 |
| 36 | save | saved-36 | 2097664 | 162707968 |
| 37 | save | saved-37 | 2113536 | 164821504 |
| 38 | save | saved-38 | 528384 | 165349888 |
| 39 | save | saved-39 | 1056768 | 166406656 |
| 40 | save | saved-40 | 2097664 | 168504320 |
| 41 | save | saved-41 | 18874368 | 187378688 |
| 42 | save | saved-42 | 2097664 | 189476352 |
| 43 | save | saved-43 | 2113536 | 191589888 |
| 44 | save | saved-44 | 528384 | 192118272 |
| 45 | save | saved-45 | 1056768 | 193175040 |
| 46 | save | saved-46 | 2097664 | 195272704 |
| 47 | save | saved-47 | 18874368 | 214147072 |
| 48 | save | saved-48 | 2097664 | 216244736 |
| 49 | save | saved-49 | 2113536 | 218358272 |
| 50 | save | saved-50 | 528384 | 218886656 |
| 51 | save | saved-51 | 1056768 | 219943424 |
| 52 | save | saved-52 | 2097664 | 222041088 |
| 53 | save | saved-53 | 18874368 | 240915456 |
| 54 | save | saved-54 | 2097664 | 243013120 |
| 55 | save | saved-55 | 2113536 | 245126656 |
| 56 | save | saved-56 | 528384 | 245655040 |
| 57 | save | saved-57 | 1056768 | 246711808 |
| 58 | save | saved-58 | 2097664 | 248809472 |
| 59 | save | saved-59 | 18874368 | 267683840 |
| 60 | save | saved-60 | 2097664 | 269781504 |
| 61 | save | saved-61 | 2113536 | 271895040 |
| 62 | save | saved-62 | 528384 | 272423424 |
| 63 | save | saved-63 | 1056768 | 273480192 |
| 64 | save | saved-64 | 2097664 | 275577856 |
| 65 | save | saved-65 | 18874368 | 294452224 |
| 66 | save | saved-66 | 2097664 | 296549888 |
| 67 | save | saved-67 | 2113536 | 298663424 |
| 68 | save | saved-68 | 528384 | 299191808 |
| 69 | save | saved-69 | 1056768 | 300248576 |
| 70 | save | saved-70 | 2097664 | 302346240 |
| 71 | save | saved-71 | 18874368 | 321220608 |
| 72 | save | saved-72 | 2097664 | 323318272 |
| 73 | save | saved-73 | 2113536 | 325431808 |
| 74 | save | saved-74 | 528384 | 325960192 |
| 75 | save | saved-75 | 1056768 | 327016960 |
| 76 | save | saved-76 | 2097664 | 329114624 |
| 77 | save | saved-77 | 18874368 | 347988992 |
| 78 | save | saved-78 | 2097664 | 350086656 |
| 79 | save | saved-79 | 2113536 | 352200192 |
| 80 | save | saved-80 | 528384 | 352728576 |
| 81 | save | saved-81 | 1056768 | 353785344 |
| 82 | save | saved-82 | 2097664 | 355883008 |
| 83 | save | saved-83 | 18874368 | 374757376 |
| 84 | save | saved-84 | 2097664 | 376855040 |
| 85 | save | saved-85 | 2113536 | 378968576 |
| 86 | save | saved-86 | 528384 | 379496960 |
| 87 | save | saved-87 | 1056768 | 380553728 |
| 88 | save | saved-88 | 2097664 | 382651392 |
| 89 | save | saved-89 | 18874368 | 401525760 |
| 90 | save | saved-90 | 2097664 | 403623424 |
| 91 | save | saved-91 | 2113536 | 405736960 |
| 92 | save | saved-92 | 528384 | 406265344 |
| 93 | save | saved-93 | 1056768 | 407322112 |
| 94 | save | saved-94 | 2097664 | 409419776 |
| 95 | save | saved-95 | 18874368 | 428294144 |
| 96 | save | saved-96 | 2097664 | 430391808 |
| 97 | save | saved-97 | 2113536 | 432505344 |
| 98 | save | saved-98 | 528384 | 433033728 |
| 99 | save | saved-99 | 1056768 | 434090496 |
| 100 | save | saved-100 | 2097664 | 436188160 |
| 101 | save | saved-101 | 18874368 | 455062528 |
| 102 | save | saved-102 | 2097664 | 457160192 |
| 103 | save | saved-103 | 2113536 | 459273728 |
| 104 | save | saved-104 | 528384 | 459802112 |
| 105 | save | saved-105 | 1056768 | 460858880 |
| 106 | save | saved-106 | 2097664 | 462956544 |
| 107 | save | saved-107 | 18874368 | 481830912 |
| 108 | save | saved-108 | 2097664 | 483928576 |
| 109 | save | saved-109 | 2113536 | 486042112 |
| 110 | save | saved-110 | 528384 | 486570496 |
| 111 | save | saved-111 | 1056768 | 487627264 |
| 112 | save | saved-112 | 2097664 | 489724928 |
| 113 | save | saved-113 | 18874368 | 508599296 |
| 114 | save | saved-114 | 2097664 | 510696960 |
| 115 | save | saved-115 | 2113536 | 512810496 |
| 116 | save | saved-116 | 528384 | 513338880 |
| 117 | save | saved-117 | 1056768 | 514395648 |
| 118 | save | saved-118 | 2097664 | 516493312 |
| 119 | save | saved-119 | 18874368 | 535367680 |
| 120 | save | saved-120 | 2097664 | 537465344 |
| 121 | save | saved-121 | 2113536 | 539578880 |
| 122 | save | saved-122 | 528384 | 540107264 |
| 123 | save | saved-123 | 1056768 | 541164032 |
| 124 | save | saved-124 | 2097664 | 543261696 |
| 125 | save | saved-125 | 18874368 | 562136064 |
| 126 | save | saved-126 | 2097664 | 564233728 |
| 127 | save | saved-127 | 2113536 | 566347264 |
| 128 | save | saved-128 | 528384 | 566875648 |
| 129 | save | saved-129 | 1056768 | 567932416 |
| 130 | save | saved-130 | 2097664 | 570030080 |
| 131 | save | saved-131 | 18874368 | 588904448 |
| 132 | save | saved-132 | 2097664 | 591002112 |
| 133 | save | saved-133 | 2113536 | 593115648 |
| 134 | save | saved-134 | 528384 | 593644032 |
| 135 | save | saved-135 | 1056768 | 594700800 |
| 136 | save | saved-136 | 2097664 | 596798464 |
| 137 | save | saved-137 | 18874368 | 615672832 |
| 138 | save | saved-138 | 2097664 | 617770496 |
| 139 | save | saved-139 | 2113536 | 619884032 |
| 140 | save | saved-140 | 528384 | 620412416 |
| 141 | save | saved-141 | 1056768 | 621469184 |
| 142 | save | saved-142 | 2097664 | 623566848 |
| 143 | save | saved-143 | 18874368 | 642441216 |
| 144 | save | saved-144 | 2097664 | 644538880 |
| 145 | save | saved-145 | 2113536 | 646652416 |
| 146 | save | saved-146 | 528384 | 647180800 |
| 147 | save | saved-147 | 1056768 | 648237568 |
| 148 | save | saved-148 | 2097664 | 650335232 |
| 149 | save | saved-149 | 18874368 | 669209600 |
| 150 | save | saved-150 | 2097664 | 671307264 |
| 151 | save | saved-151 | 2113536 | 673420800 |
| 152 | save | saved-152 | 528384 | 673949184 |
| 153 | save | saved-153 | 1056768 | 675005952 |
| 154 | save | saved-154 | 2097664 | 677103616 |
| 155 | save | saved-155 | 18874368 | 695977984 |
| 156 | save | saved-156 | 2097664 | 698075648 |
| 157 | save | saved-157 | 2113536 | 700189184 |
| 158 | save | saved-158 | 528384 | 700717568 |
| 159 | save | saved-159 | 1056768 | 701774336 |
| 160 | save | saved-160 | 2097664 | 703872000 |
| 161 | save | saved-161 | 18874368 | 722746368 |
| 162 | save | saved-162 | 2097664 | 724844032 |
| 163 | save | saved-163 | 2113536 | 726957568 |
| 164 | save | saved-164 | 528384 | 727485952 |
| 165 | save | saved-165 | 1056768 | 728542720 |
| 166 | save | saved-166 | 2097664 | 730640384 |
| 167 | save | saved-167 | 18874368 | 749514752 |
| 168 | save | saved-168 | 2097664 | 751612416 |
| 169 | save | saved-169 | 2113536 | 753725952 |
| 170 | save | saved-170 | 528384 | 754254336 |
| 171 | save | saved-171 | 1056768 | 755311104 |
| 172 | save | saved-172 | 2097664 | 757408768 |
| 173 | save | saved-173 | 18874368 | 776283136 |
| 174 | save | saved-174 | 2097664 | 778380800 |
| 175 | save | saved-175 | 2113536 | 780494336 |
| 176 | save | saved-176 | 528384 | 781022720 |
| 177 | save | saved-177 | 1056768 | 782079488 |
| 178 | save | saved-178 | 2097664 | 784177152 |
| 179 | save | saved-179 | 18874368 | 803051520 |
| 180 | save | saved-180 | 2097664 | 805149184 |
| 181 | save | saved-181 | 2113536 | 807262720 |
| 182 | save | saved-182 | 528384 | 807791104 |
| 183 | save | saved-183 | 1056768 | 808847872 |
| 184 | save | saved-184 | 2097664 | 810945536 |
| 185 | save | saved-185 | 18874368 | 829819904 |
| 186 | save | saved-186 | 2097664 | 831917568 |
| 187 | save | saved-187 | 2113536 | 834031104 |
| 188 | save | saved-188 | 528384 | 834559488 |
| 189 | save | saved-189 | 1056768 | 835616256 |
| 190 | save | saved-190 | 2097664 | 837713920 |
| 191 | save | saved-191 | 18874368 | 856588288 |
| 192 | save | saved-192 | 2097664 | 858685952 |
| 193 | save | saved-193 | 2113536 | 860799488 |
| 194 | save | saved-194 | 528384 | 861327872 |
| 195 | save | saved-195 | 1056768 | 862384640 |
| 196 | save | saved-196 | 2097664 | 864482304 |
| 197 | save | saved-197 | 18874368 | 883356672 |
| 198 | save | saved-198 | 2097664 | 885454336 |
| 199 | save | saved-199 | 2113536 | 887567872 |
| 200 | save | saved-200 | 528384 | 888096256 |
| 201 | save | saved-201 | 1056768 | 889153024 |
| 202 | save | saved-202 | 2097664 | 891250688 |
| 203 | save | saved-203 | 18874368 | 910125056 |
| 204 | save | saved-204 | 2097664 | 912222720 |
| 205 | save | saved-205 | 2113536 | 914336256 |
| 206 | save | saved-206 | 528384 | 914864640 |
| 207 | save | saved-207 | 1056768 | 915921408 |
| 208 | save | saved-208 | 2097664 | 918019072 |
| 209 | save | saved-209 | 18874368 | 936893440 |
| 210 | save | saved-210 | 2097664 | 938991104 |
| 211 | save | saved-211 | 2113536 | 941104640 |
| 212 | save | saved-212 | 528384 | 941633024 |
| 213 | save | saved-213 | 1056768 | 942689792 |
| 214 | save | saved-214 | 2097664 | 944787456 |
| 215 | save | saved-215 | 18874368 | 963661824 |
| 216 | save | saved-216 | 2097664 | 965759488 |
| 217 | save | saved-217 | 77791232 | 1043550720 |
| 218 | backward_last_use_release | saved-217 | -77791232 | 965759488 |
| 219 | backward_last_use_release | saved-216 | -2097664 | 963661824 |
| 220 | backward_last_use_release | saved-215 | -18874368 | 944787456 |
| 221 | backward_last_use_release | saved-214 | -2097664 | 942689792 |
| 222 | backward_last_use_release | saved-213 | -1056768 | 941633024 |
| 223 | backward_last_use_release | saved-212 | -528384 | 941104640 |
| 224 | backward_last_use_release | saved-211 | -2113536 | 938991104 |
| 225 | backward_last_use_release | saved-210 | -2097664 | 936893440 |
| 226 | backward_last_use_release | saved-209 | -18874368 | 918019072 |
| 227 | backward_last_use_release | saved-208 | -2097664 | 915921408 |
| 228 | backward_last_use_release | saved-207 | -1056768 | 914864640 |
| 229 | backward_last_use_release | saved-206 | -528384 | 914336256 |
| 230 | backward_last_use_release | saved-205 | -2113536 | 912222720 |
| 231 | backward_last_use_release | saved-204 | -2097664 | 910125056 |
| 232 | backward_last_use_release | saved-203 | -18874368 | 891250688 |
| 233 | backward_last_use_release | saved-202 | -2097664 | 889153024 |
| 234 | backward_last_use_release | saved-201 | -1056768 | 888096256 |
| 235 | backward_last_use_release | saved-200 | -528384 | 887567872 |
| 236 | backward_last_use_release | saved-199 | -2113536 | 885454336 |
| 237 | backward_last_use_release | saved-198 | -2097664 | 883356672 |
| 238 | backward_last_use_release | saved-197 | -18874368 | 864482304 |
| 239 | backward_last_use_release | saved-196 | -2097664 | 862384640 |
| 240 | backward_last_use_release | saved-195 | -1056768 | 861327872 |
| 241 | backward_last_use_release | saved-194 | -528384 | 860799488 |
| 242 | backward_last_use_release | saved-193 | -2113536 | 858685952 |
| 243 | backward_last_use_release | saved-192 | -2097664 | 856588288 |
| 244 | backward_last_use_release | saved-191 | -18874368 | 837713920 |
| 245 | backward_last_use_release | saved-190 | -2097664 | 835616256 |
| 246 | backward_last_use_release | saved-189 | -1056768 | 834559488 |
| 247 | backward_last_use_release | saved-188 | -528384 | 834031104 |
| 248 | backward_last_use_release | saved-187 | -2113536 | 831917568 |
| 249 | backward_last_use_release | saved-186 | -2097664 | 829819904 |
| 250 | backward_last_use_release | saved-185 | -18874368 | 810945536 |
| 251 | backward_last_use_release | saved-184 | -2097664 | 808847872 |
| 252 | backward_last_use_release | saved-183 | -1056768 | 807791104 |
| 253 | backward_last_use_release | saved-182 | -528384 | 807262720 |
| 254 | backward_last_use_release | saved-181 | -2113536 | 805149184 |
| 255 | backward_last_use_release | saved-180 | -2097664 | 803051520 |
| 256 | backward_last_use_release | saved-179 | -18874368 | 784177152 |
| 257 | backward_last_use_release | saved-178 | -2097664 | 782079488 |
| 258 | backward_last_use_release | saved-177 | -1056768 | 781022720 |
| 259 | backward_last_use_release | saved-176 | -528384 | 780494336 |
| 260 | backward_last_use_release | saved-175 | -2113536 | 778380800 |
| 261 | backward_last_use_release | saved-174 | -2097664 | 776283136 |
| 262 | backward_last_use_release | saved-173 | -18874368 | 757408768 |
| 263 | backward_last_use_release | saved-172 | -2097664 | 755311104 |
| 264 | backward_last_use_release | saved-171 | -1056768 | 754254336 |
| 265 | backward_last_use_release | saved-170 | -528384 | 753725952 |
| 266 | backward_last_use_release | saved-169 | -2113536 | 751612416 |
| 267 | backward_last_use_release | saved-168 | -2097664 | 749514752 |
| 268 | backward_last_use_release | saved-167 | -18874368 | 730640384 |
| 269 | backward_last_use_release | saved-166 | -2097664 | 728542720 |
| 270 | backward_last_use_release | saved-165 | -1056768 | 727485952 |
| 271 | backward_last_use_release | saved-164 | -528384 | 726957568 |
| 272 | backward_last_use_release | saved-163 | -2113536 | 724844032 |
| 273 | backward_last_use_release | saved-162 | -2097664 | 722746368 |
| 274 | backward_last_use_release | saved-161 | -18874368 | 703872000 |
| 275 | backward_last_use_release | saved-160 | -2097664 | 701774336 |
| 276 | backward_last_use_release | saved-159 | -1056768 | 700717568 |
| 277 | backward_last_use_release | saved-158 | -528384 | 700189184 |
| 278 | backward_last_use_release | saved-157 | -2113536 | 698075648 |
| 279 | backward_last_use_release | saved-156 | -2097664 | 695977984 |
| 280 | backward_last_use_release | saved-155 | -18874368 | 677103616 |
| 281 | backward_last_use_release | saved-154 | -2097664 | 675005952 |
| 282 | backward_last_use_release | saved-153 | -1056768 | 673949184 |
| 283 | backward_last_use_release | saved-152 | -528384 | 673420800 |
| 284 | backward_last_use_release | saved-151 | -2113536 | 671307264 |
| 285 | backward_last_use_release | saved-150 | -2097664 | 669209600 |
| 286 | backward_last_use_release | saved-149 | -18874368 | 650335232 |
| 287 | backward_last_use_release | saved-148 | -2097664 | 648237568 |
| 288 | backward_last_use_release | saved-147 | -1056768 | 647180800 |
| 289 | backward_last_use_release | saved-146 | -528384 | 646652416 |
| 290 | backward_last_use_release | saved-145 | -2113536 | 644538880 |
| 291 | backward_last_use_release | saved-144 | -2097664 | 642441216 |
| 292 | backward_last_use_release | saved-143 | -18874368 | 623566848 |
| 293 | backward_last_use_release | saved-142 | -2097664 | 621469184 |
| 294 | backward_last_use_release | saved-141 | -1056768 | 620412416 |
| 295 | backward_last_use_release | saved-140 | -528384 | 619884032 |
| 296 | backward_last_use_release | saved-139 | -2113536 | 617770496 |
| 297 | backward_last_use_release | saved-138 | -2097664 | 615672832 |
| 298 | backward_last_use_release | saved-137 | -18874368 | 596798464 |
| 299 | backward_last_use_release | saved-136 | -2097664 | 594700800 |
| 300 | backward_last_use_release | saved-135 | -1056768 | 593644032 |
| 301 | backward_last_use_release | saved-134 | -528384 | 593115648 |
| 302 | backward_last_use_release | saved-133 | -2113536 | 591002112 |
| 303 | backward_last_use_release | saved-132 | -2097664 | 588904448 |
| 304 | backward_last_use_release | saved-131 | -18874368 | 570030080 |
| 305 | backward_last_use_release | saved-130 | -2097664 | 567932416 |
| 306 | backward_last_use_release | saved-129 | -1056768 | 566875648 |
| 307 | backward_last_use_release | saved-128 | -528384 | 566347264 |
| 308 | backward_last_use_release | saved-127 | -2113536 | 564233728 |
| 309 | backward_last_use_release | saved-126 | -2097664 | 562136064 |
| 310 | backward_last_use_release | saved-125 | -18874368 | 543261696 |
| 311 | backward_last_use_release | saved-124 | -2097664 | 541164032 |
| 312 | backward_last_use_release | saved-123 | -1056768 | 540107264 |
| 313 | backward_last_use_release | saved-122 | -528384 | 539578880 |
| 314 | backward_last_use_release | saved-121 | -2113536 | 537465344 |
| 315 | backward_last_use_release | saved-120 | -2097664 | 535367680 |
| 316 | backward_last_use_release | saved-119 | -18874368 | 516493312 |
| 317 | backward_last_use_release | saved-118 | -2097664 | 514395648 |
| 318 | backward_last_use_release | saved-117 | -1056768 | 513338880 |
| 319 | backward_last_use_release | saved-116 | -528384 | 512810496 |
| 320 | backward_last_use_release | saved-115 | -2113536 | 510696960 |
| 321 | backward_last_use_release | saved-114 | -2097664 | 508599296 |
| 322 | backward_last_use_release | saved-113 | -18874368 | 489724928 |
| 323 | backward_last_use_release | saved-112 | -2097664 | 487627264 |
| 324 | backward_last_use_release | saved-111 | -1056768 | 486570496 |
| 325 | backward_last_use_release | saved-110 | -528384 | 486042112 |
| 326 | backward_last_use_release | saved-109 | -2113536 | 483928576 |
| 327 | backward_last_use_release | saved-108 | -2097664 | 481830912 |
| 328 | backward_last_use_release | saved-107 | -18874368 | 462956544 |
| 329 | backward_last_use_release | saved-106 | -2097664 | 460858880 |
| 330 | backward_last_use_release | saved-105 | -1056768 | 459802112 |
| 331 | backward_last_use_release | saved-104 | -528384 | 459273728 |
| 332 | backward_last_use_release | saved-103 | -2113536 | 457160192 |
| 333 | backward_last_use_release | saved-102 | -2097664 | 455062528 |
| 334 | backward_last_use_release | saved-101 | -18874368 | 436188160 |
| 335 | backward_last_use_release | saved-100 | -2097664 | 434090496 |
| 336 | backward_last_use_release | saved-99 | -1056768 | 433033728 |
| 337 | backward_last_use_release | saved-98 | -528384 | 432505344 |
| 338 | backward_last_use_release | saved-97 | -2113536 | 430391808 |
| 339 | backward_last_use_release | saved-96 | -2097664 | 428294144 |
| 340 | backward_last_use_release | saved-95 | -18874368 | 409419776 |
| 341 | backward_last_use_release | saved-94 | -2097664 | 407322112 |
| 342 | backward_last_use_release | saved-93 | -1056768 | 406265344 |
| 343 | backward_last_use_release | saved-92 | -528384 | 405736960 |
| 344 | backward_last_use_release | saved-91 | -2113536 | 403623424 |
| 345 | backward_last_use_release | saved-90 | -2097664 | 401525760 |
| 346 | backward_last_use_release | saved-89 | -18874368 | 382651392 |
| 347 | backward_last_use_release | saved-88 | -2097664 | 380553728 |
| 348 | backward_last_use_release | saved-87 | -1056768 | 379496960 |
| 349 | backward_last_use_release | saved-86 | -528384 | 378968576 |
| 350 | backward_last_use_release | saved-85 | -2113536 | 376855040 |
| 351 | backward_last_use_release | saved-84 | -2097664 | 374757376 |
| 352 | backward_last_use_release | saved-83 | -18874368 | 355883008 |
| 353 | backward_last_use_release | saved-82 | -2097664 | 353785344 |
| 354 | backward_last_use_release | saved-81 | -1056768 | 352728576 |
| 355 | backward_last_use_release | saved-80 | -528384 | 352200192 |
| 356 | backward_last_use_release | saved-79 | -2113536 | 350086656 |
| 357 | backward_last_use_release | saved-78 | -2097664 | 347988992 |
| 358 | backward_last_use_release | saved-77 | -18874368 | 329114624 |
| 359 | backward_last_use_release | saved-76 | -2097664 | 327016960 |
| 360 | backward_last_use_release | saved-75 | -1056768 | 325960192 |
| 361 | backward_last_use_release | saved-74 | -528384 | 325431808 |
| 362 | backward_last_use_release | saved-73 | -2113536 | 323318272 |
| 363 | backward_last_use_release | saved-72 | -2097664 | 321220608 |
| 364 | backward_last_use_release | saved-71 | -18874368 | 302346240 |
| 365 | backward_last_use_release | saved-70 | -2097664 | 300248576 |
| 366 | backward_last_use_release | saved-69 | -1056768 | 299191808 |
| 367 | backward_last_use_release | saved-68 | -528384 | 298663424 |
| 368 | backward_last_use_release | saved-67 | -2113536 | 296549888 |
| 369 | backward_last_use_release | saved-66 | -2097664 | 294452224 |
| 370 | backward_last_use_release | saved-65 | -18874368 | 275577856 |
| 371 | backward_last_use_release | saved-64 | -2097664 | 273480192 |
| 372 | backward_last_use_release | saved-63 | -1056768 | 272423424 |
| 373 | backward_last_use_release | saved-62 | -528384 | 271895040 |
| 374 | backward_last_use_release | saved-61 | -2113536 | 269781504 |
| 375 | backward_last_use_release | saved-60 | -2097664 | 267683840 |
| 376 | backward_last_use_release | saved-59 | -18874368 | 248809472 |
| 377 | backward_last_use_release | saved-58 | -2097664 | 246711808 |
| 378 | backward_last_use_release | saved-57 | -1056768 | 245655040 |
| 379 | backward_last_use_release | saved-56 | -528384 | 245126656 |
| 380 | backward_last_use_release | saved-55 | -2113536 | 243013120 |
| 381 | backward_last_use_release | saved-54 | -2097664 | 240915456 |
| 382 | backward_last_use_release | saved-53 | -18874368 | 222041088 |
| 383 | backward_last_use_release | saved-52 | -2097664 | 219943424 |
| 384 | backward_last_use_release | saved-51 | -1056768 | 218886656 |
| 385 | backward_last_use_release | saved-50 | -528384 | 218358272 |
| 386 | backward_last_use_release | saved-49 | -2113536 | 216244736 |
| 387 | backward_last_use_release | saved-48 | -2097664 | 214147072 |
| 388 | backward_last_use_release | saved-47 | -18874368 | 195272704 |
| 389 | backward_last_use_release | saved-46 | -2097664 | 193175040 |
| 390 | backward_last_use_release | saved-45 | -1056768 | 192118272 |
| 391 | backward_last_use_release | saved-44 | -528384 | 191589888 |
| 392 | backward_last_use_release | saved-43 | -2113536 | 189476352 |
| 393 | backward_last_use_release | saved-42 | -2097664 | 187378688 |
| 394 | backward_last_use_release | saved-41 | -18874368 | 168504320 |
| 395 | backward_last_use_release | saved-40 | -2097664 | 166406656 |
| 396 | backward_last_use_release | saved-39 | -1056768 | 165349888 |
| 397 | backward_last_use_release | saved-38 | -528384 | 164821504 |
| 398 | backward_last_use_release | saved-37 | -2113536 | 162707968 |
| 399 | backward_last_use_release | saved-36 | -2097664 | 160610304 |
| 400 | backward_last_use_release | saved-35 | -18874368 | 141735936 |
| 401 | backward_last_use_release | saved-34 | -2097664 | 139638272 |
| 402 | backward_last_use_release | saved-33 | -1056768 | 138581504 |
| 403 | backward_last_use_release | saved-32 | -528384 | 138053120 |
| 404 | backward_last_use_release | saved-31 | -2113536 | 135939584 |
| 405 | backward_last_use_release | saved-30 | -2097664 | 133841920 |
| 406 | backward_last_use_release | saved-29 | -18874368 | 114967552 |
| 407 | backward_last_use_release | saved-28 | -2097664 | 112869888 |
| 408 | backward_last_use_release | saved-27 | -1056768 | 111813120 |
| 409 | backward_last_use_release | saved-26 | -528384 | 111284736 |
| 410 | backward_last_use_release | saved-25 | -2113536 | 109171200 |
| 411 | backward_last_use_release | saved-24 | -2097664 | 107073536 |
| 412 | backward_last_use_release | saved-23 | -18874368 | 88199168 |
| 413 | backward_last_use_release | saved-22 | -2097664 | 86101504 |
| 414 | backward_last_use_release | saved-21 | -1056768 | 85044736 |
| 415 | backward_last_use_release | saved-20 | -528384 | 84516352 |
| 416 | backward_last_use_release | saved-19 | -2113536 | 82402816 |
| 417 | backward_last_use_release | saved-18 | -2097664 | 80305152 |
| 418 | backward_last_use_release | saved-17 | -18874368 | 61430784 |
| 419 | backward_last_use_release | saved-16 | -2097664 | 59333120 |
| 420 | backward_last_use_release | saved-15 | -1056768 | 58276352 |
| 421 | backward_last_use_release | saved-14 | -528384 | 57747968 |
| 422 | backward_last_use_release | saved-13 | -2113536 | 55634432 |
| 423 | backward_last_use_release | saved-12 | -2097664 | 53536768 |
| 424 | backward_last_use_release | saved-11 | -18874368 | 34662400 |
| 425 | backward_last_use_release | saved-10 | -2097664 | 32564736 |
| 426 | backward_last_use_release | saved-9 | -1056768 | 31507968 |
| 427 | backward_last_use_release | saved-8 | -528384 | 30979584 |
| 428 | backward_last_use_release | saved-7 | -2113536 | 28866048 |
| 429 | backward_last_use_release | saved-6 | -2097664 | 26768384 |
| 430 | backward_last_use_release | saved-5 | -18874368 | 7894016 |
| 431 | backward_last_use_release | saved-4 | -2097664 | 5796352 |
| 432 | backward_last_use_release | saved-3 | -1056768 | 4739584 |
| 433 | backward_last_use_release | saved-2 | -528384 | 4211200 |
| 434 | backward_last_use_release | saved-1 | -2113536 | 2097664 |
| 435 | backward_last_use_release | saved-0 | -2097664 | 0 |

## 原矩阵与参数状态（不变）

| 原summary | 值 |
| --- | --- |
| parameters | 8190735360 |
| input_tokens | 128 |
| loss_tokens | 128 |
| expert_assignments_per_layer | 0 |
| active_experts_per_layer | 0 |
| executed_head_rows | 128 |
| forward_matrix_flops | 1942302490624 |
| backward_matrix_flops | 3884604981248 |
| training_matrix_flops | 5826907471872 |
| attention_training_matrix_flops | 14608760832 |
| six_nd_flops | 6290484756480 |
| matrix_minus_six_nd_flops | -463577284608 |
| matrix_to_six_nd_ratio | 0.9263049983341178 |
| unsharded_parameter_state_bytes | 147433236480 |
| activation_peak_bytes | unknown |
| complete_training_step_flops | unknown |
| predicted_step_seconds | unknown |

| 矩阵 | 形状 | repeats | forward | gradient_each | training_total |
| --- | --- | --- | --- | --- | --- |
| q_proj | {"d_input_matmul": [[128, 4096], [4096, 4096]], "d_weight_matmul": [[4096, 128], [128, 4096]], "input": [128, 4096], "output": [128, 4096], "weight_storage": [4096, 4096]} | 36 | 4294967296 | 4294967296 | 463856467968 |
| k_proj | {"d_input_matmul": [[128, 1024], [1024, 4096]], "d_weight_matmul": [[1024, 128], [128, 4096]], "input": [128, 4096], "output": [128, 1024], "weight_storage": [1024, 4096]} | 36 | 1073741824 | 1073741824 | 115964116992 |
| v_proj | {"d_input_matmul": [[128, 1024], [1024, 4096]], "d_weight_matmul": [[1024, 128], [128, 4096]], "input": [128, 4096], "output": [128, 1024], "weight_storage": [1024, 4096]} | 36 | 1073741824 | 1073741824 | 115964116992 |
| qk | {"K_shared": [1, 8, 128, 128], "Q": [1, 32, 128, 128], "scores_rectangular": [1, 32, 128, 128]} | 36 | 67633152 | 67633152 | 7304380416 |
| pv | {"P": [1, 32, 128, 128], "V_shared": [1, 8, 128, 128], "output": [1, 32, 128, 128]} | 36 | 67633152 | 67633152 | 7304380416 |
| o_proj | {"d_input_matmul": [[128, 4096], [4096, 4096]], "d_weight_matmul": [[4096, 128], [128, 4096]], "input": [128, 4096], "output": [128, 4096], "weight_storage": [4096, 4096]} | 36 | 4294967296 | 4294967296 | 463856467968 |
| gate_proj | {"d_input_matmul": [[128, 12288], [12288, 4096]], "d_weight_matmul": [[12288, 128], [128, 4096]], "input": [128, 4096], "output": [128, 12288], "weight_storage": [12288, 4096]} | 36 | 12884901888 | 12884901888 | 1391569403904 |
| up_proj | {"d_input_matmul": [[128, 12288], [12288, 4096]], "d_weight_matmul": [[12288, 128], [128, 4096]], "input": [128, 4096], "output": [128, 12288], "weight_storage": [12288, 4096]} | 36 | 12884901888 | 12884901888 | 1391569403904 |
| down_proj | {"d_input_matmul": [[128, 4096], [4096, 12288]], "d_weight_matmul": [[4096, 128], [128, 12288]], "input": [128, 12288], "output": [128, 4096], "weight_storage": [4096, 12288]} | 36 | 12884901888 | 12884901888 | 1391569403904 |
| lm_head | {"d_input_matmul": [[128, 151936], [151936, 4096]], "d_weight_matmul": [[151936, 128], [128, 4096]], "input": [128, 4096], "output": [128, 151936], "weight_storage": [151936, 4096]} | 1 | 159316443136 | 159316443136 | 477949329408 |

## 假设与原题剩余

- Official Qwen3-8B dimensions with declared mathematical backward algorithms; not an assertion about a specific autograd saved-tensor choice, fused optimizer, or kernel instruction sequence.
- Original training_matrix record and parameter-state budget are preserved unchanged. New ordinary scalar operations never multiply or recount its GEMM gradients.
- Nonlinear reference arithmetic and saved tensors are FP32; numerical derivative checks use FP64. BF16 interfaces/master copy are typed operations, not proof of identical BF16 backend rounding or Tensor hardware feasibility.
- Attention counts valid causal cells and a ragged saved-probability reference. Dense masked buffers or FlashAttention recomputation would require a different explicitly expanded execution policy.
- Compact head gradient scatters S selected rows into a newly zeroed full B*T by H FP32 buffer before final-norm backward. Its full-buffer zero write and selected read/write payload are separate; no existing initialized buffer is assumed.
- S valid shifted/masked labels are caller input. Their identities are not fabricated; loss selects S rows, while dense vocabulary head still executes all B*T rows. Gather/scatter are logical contribution counts, not coalescing/atomic traces.
- Every listed saved nonlinear object remains until its explicit backward event. This subset omits GEMM saved inputs/outputs, live gradients, full temporary buffers and allocator workspace; its peak is not model peak or a measured lower bound for every other algorithm.
- Recompute_silu changes only this declared nonlinear subgraph: save g/u, recompute sigmoid and a, retain its two temporaries through that local backward and then release. No full-layer checkpoint is implied.
- Unfused AdamW uses dense FP32 gradient/master/m/v for all parameters, including zero-gradient embedding rows. Bias correction two pow calls and six shared arithmetic operations execute once per step; no foreach/fused backend equivalence claimed.
- Residual/backbone branch merges are declared additive accumulation into already available gradients. Embedding scatter explicitly accumulates into zeroed dense storage; collisions and exact zero-gating behavior require token identities.
- Not included: V4 training, loss-specific branches beyond mean CE, clipping/loss-scaling, gradient accumulation, distributed communication, all casts/copies, scheduler/allocator and complete optimizer initialization. Chapter3 experiment3-6 remains partial.

## 固定来源

| 记录 | 值 |
| --- | --- |
| 0 | {"file": "configs/models/qwen3-8b/config.json", "revision": "b968826d9c46dd6066d109eabc6255188de91218", "sha256": "f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30", "url": "https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json"} |
| 1 | {"file": "sources/qwen3-8b/model.safetensors.index.json", "revision": "b968826d9c46dd6066d109eabc6255188de91218", "sha256": "f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc", "url": "https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json"} |
| 2 | {"file": "sources/qwen3/modeling_qwen3.py", "revision": "0720e206c6ba28887e4d60ef60a6a089f6c1cc76", "sha256": "704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2", "url": "https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py"} |
| 3 | {"file": "sources/qwen3/modeling_qwen3_moe.py", "revision": "0720e206c6ba28887e4d60ef60a6a089f6c1cc76", "sha256": "3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8", "url": "https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py"} |
