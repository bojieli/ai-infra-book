# Qwen3-8B 训练非矩阵参考账

## 输入

| 字段 | 值 |
| --- | --- |
| batch | 1 |
| tokens | 128 |
| supervised_tokens | unknown |
| head_strategy | dense |
| activation_policy | recompute_silu |
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
| backward_scalar_flops | 1151822976 |
| optimizer_scalar_flops | 114670295046 |
| accounted_special_ops | {"cos": 16384, "exp": 28958720, "log": 128, "max_compare": 28811136, "pow": 2, "rsqrt": 193664, "sigmoid": 113246208, "sin": 16384, "sqrt": 8190735360} |
| accounted_matrix_plus_scalar_flops | 5943295269382 |
| nonlinear_saved_at_forward_end_bytes | 817058304 |
| declared_saved_and_recomputed_subset_peak_bytes | 817058304 |
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
| swiglu | [36, 128, 12288] | 113246208 | 396361728 | {"sigmoid": 56623104} | {"sigmoid": 56623104} | Save a/s/u; or save g/u and recompute sigmoid plus a=g*s immediately before backward. |
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
| saved-5 | swiglu_g_u | 0 | 3145728 | fp32 | 12582912 |
| saved-6 | input_norm_z_r | 1 | 524416 | fp32 | 2097664 |
| saved-7 | query_norm_z_r | 1 | 528384 | fp32 | 2113536 |
| saved-8 | key_norm_z_r | 1 | 132096 | fp32 | 528384 |
| saved-9 | attention_probabilities | 1 | 264192 | fp32 | 1056768 |
| saved-10 | post_norm_z_r | 1 | 524416 | fp32 | 2097664 |
| saved-11 | swiglu_g_u | 1 | 3145728 | fp32 | 12582912 |
| saved-12 | input_norm_z_r | 2 | 524416 | fp32 | 2097664 |
| saved-13 | query_norm_z_r | 2 | 528384 | fp32 | 2113536 |
| saved-14 | key_norm_z_r | 2 | 132096 | fp32 | 528384 |
| saved-15 | attention_probabilities | 2 | 264192 | fp32 | 1056768 |
| saved-16 | post_norm_z_r | 2 | 524416 | fp32 | 2097664 |
| saved-17 | swiglu_g_u | 2 | 3145728 | fp32 | 12582912 |
| saved-18 | input_norm_z_r | 3 | 524416 | fp32 | 2097664 |
| saved-19 | query_norm_z_r | 3 | 528384 | fp32 | 2113536 |
| saved-20 | key_norm_z_r | 3 | 132096 | fp32 | 528384 |
| saved-21 | attention_probabilities | 3 | 264192 | fp32 | 1056768 |
| saved-22 | post_norm_z_r | 3 | 524416 | fp32 | 2097664 |
| saved-23 | swiglu_g_u | 3 | 3145728 | fp32 | 12582912 |
| saved-24 | input_norm_z_r | 4 | 524416 | fp32 | 2097664 |
| saved-25 | query_norm_z_r | 4 | 528384 | fp32 | 2113536 |
| saved-26 | key_norm_z_r | 4 | 132096 | fp32 | 528384 |
| saved-27 | attention_probabilities | 4 | 264192 | fp32 | 1056768 |
| saved-28 | post_norm_z_r | 4 | 524416 | fp32 | 2097664 |
| saved-29 | swiglu_g_u | 4 | 3145728 | fp32 | 12582912 |
| saved-30 | input_norm_z_r | 5 | 524416 | fp32 | 2097664 |
| saved-31 | query_norm_z_r | 5 | 528384 | fp32 | 2113536 |
| saved-32 | key_norm_z_r | 5 | 132096 | fp32 | 528384 |
| saved-33 | attention_probabilities | 5 | 264192 | fp32 | 1056768 |
| saved-34 | post_norm_z_r | 5 | 524416 | fp32 | 2097664 |
| saved-35 | swiglu_g_u | 5 | 3145728 | fp32 | 12582912 |
| saved-36 | input_norm_z_r | 6 | 524416 | fp32 | 2097664 |
| saved-37 | query_norm_z_r | 6 | 528384 | fp32 | 2113536 |
| saved-38 | key_norm_z_r | 6 | 132096 | fp32 | 528384 |
| saved-39 | attention_probabilities | 6 | 264192 | fp32 | 1056768 |
| saved-40 | post_norm_z_r | 6 | 524416 | fp32 | 2097664 |
| saved-41 | swiglu_g_u | 6 | 3145728 | fp32 | 12582912 |
| saved-42 | input_norm_z_r | 7 | 524416 | fp32 | 2097664 |
| saved-43 | query_norm_z_r | 7 | 528384 | fp32 | 2113536 |
| saved-44 | key_norm_z_r | 7 | 132096 | fp32 | 528384 |
| saved-45 | attention_probabilities | 7 | 264192 | fp32 | 1056768 |
| saved-46 | post_norm_z_r | 7 | 524416 | fp32 | 2097664 |
| saved-47 | swiglu_g_u | 7 | 3145728 | fp32 | 12582912 |
| saved-48 | input_norm_z_r | 8 | 524416 | fp32 | 2097664 |
| saved-49 | query_norm_z_r | 8 | 528384 | fp32 | 2113536 |
| saved-50 | key_norm_z_r | 8 | 132096 | fp32 | 528384 |
| saved-51 | attention_probabilities | 8 | 264192 | fp32 | 1056768 |
| saved-52 | post_norm_z_r | 8 | 524416 | fp32 | 2097664 |
| saved-53 | swiglu_g_u | 8 | 3145728 | fp32 | 12582912 |
| saved-54 | input_norm_z_r | 9 | 524416 | fp32 | 2097664 |
| saved-55 | query_norm_z_r | 9 | 528384 | fp32 | 2113536 |
| saved-56 | key_norm_z_r | 9 | 132096 | fp32 | 528384 |
| saved-57 | attention_probabilities | 9 | 264192 | fp32 | 1056768 |
| saved-58 | post_norm_z_r | 9 | 524416 | fp32 | 2097664 |
| saved-59 | swiglu_g_u | 9 | 3145728 | fp32 | 12582912 |
| saved-60 | input_norm_z_r | 10 | 524416 | fp32 | 2097664 |
| saved-61 | query_norm_z_r | 10 | 528384 | fp32 | 2113536 |
| saved-62 | key_norm_z_r | 10 | 132096 | fp32 | 528384 |
| saved-63 | attention_probabilities | 10 | 264192 | fp32 | 1056768 |
| saved-64 | post_norm_z_r | 10 | 524416 | fp32 | 2097664 |
| saved-65 | swiglu_g_u | 10 | 3145728 | fp32 | 12582912 |
| saved-66 | input_norm_z_r | 11 | 524416 | fp32 | 2097664 |
| saved-67 | query_norm_z_r | 11 | 528384 | fp32 | 2113536 |
| saved-68 | key_norm_z_r | 11 | 132096 | fp32 | 528384 |
| saved-69 | attention_probabilities | 11 | 264192 | fp32 | 1056768 |
| saved-70 | post_norm_z_r | 11 | 524416 | fp32 | 2097664 |
| saved-71 | swiglu_g_u | 11 | 3145728 | fp32 | 12582912 |
| saved-72 | input_norm_z_r | 12 | 524416 | fp32 | 2097664 |
| saved-73 | query_norm_z_r | 12 | 528384 | fp32 | 2113536 |
| saved-74 | key_norm_z_r | 12 | 132096 | fp32 | 528384 |
| saved-75 | attention_probabilities | 12 | 264192 | fp32 | 1056768 |
| saved-76 | post_norm_z_r | 12 | 524416 | fp32 | 2097664 |
| saved-77 | swiglu_g_u | 12 | 3145728 | fp32 | 12582912 |
| saved-78 | input_norm_z_r | 13 | 524416 | fp32 | 2097664 |
| saved-79 | query_norm_z_r | 13 | 528384 | fp32 | 2113536 |
| saved-80 | key_norm_z_r | 13 | 132096 | fp32 | 528384 |
| saved-81 | attention_probabilities | 13 | 264192 | fp32 | 1056768 |
| saved-82 | post_norm_z_r | 13 | 524416 | fp32 | 2097664 |
| saved-83 | swiglu_g_u | 13 | 3145728 | fp32 | 12582912 |
| saved-84 | input_norm_z_r | 14 | 524416 | fp32 | 2097664 |
| saved-85 | query_norm_z_r | 14 | 528384 | fp32 | 2113536 |
| saved-86 | key_norm_z_r | 14 | 132096 | fp32 | 528384 |
| saved-87 | attention_probabilities | 14 | 264192 | fp32 | 1056768 |
| saved-88 | post_norm_z_r | 14 | 524416 | fp32 | 2097664 |
| saved-89 | swiglu_g_u | 14 | 3145728 | fp32 | 12582912 |
| saved-90 | input_norm_z_r | 15 | 524416 | fp32 | 2097664 |
| saved-91 | query_norm_z_r | 15 | 528384 | fp32 | 2113536 |
| saved-92 | key_norm_z_r | 15 | 132096 | fp32 | 528384 |
| saved-93 | attention_probabilities | 15 | 264192 | fp32 | 1056768 |
| saved-94 | post_norm_z_r | 15 | 524416 | fp32 | 2097664 |
| saved-95 | swiglu_g_u | 15 | 3145728 | fp32 | 12582912 |
| saved-96 | input_norm_z_r | 16 | 524416 | fp32 | 2097664 |
| saved-97 | query_norm_z_r | 16 | 528384 | fp32 | 2113536 |
| saved-98 | key_norm_z_r | 16 | 132096 | fp32 | 528384 |
| saved-99 | attention_probabilities | 16 | 264192 | fp32 | 1056768 |
| saved-100 | post_norm_z_r | 16 | 524416 | fp32 | 2097664 |
| saved-101 | swiglu_g_u | 16 | 3145728 | fp32 | 12582912 |
| saved-102 | input_norm_z_r | 17 | 524416 | fp32 | 2097664 |
| saved-103 | query_norm_z_r | 17 | 528384 | fp32 | 2113536 |
| saved-104 | key_norm_z_r | 17 | 132096 | fp32 | 528384 |
| saved-105 | attention_probabilities | 17 | 264192 | fp32 | 1056768 |
| saved-106 | post_norm_z_r | 17 | 524416 | fp32 | 2097664 |
| saved-107 | swiglu_g_u | 17 | 3145728 | fp32 | 12582912 |
| saved-108 | input_norm_z_r | 18 | 524416 | fp32 | 2097664 |
| saved-109 | query_norm_z_r | 18 | 528384 | fp32 | 2113536 |
| saved-110 | key_norm_z_r | 18 | 132096 | fp32 | 528384 |
| saved-111 | attention_probabilities | 18 | 264192 | fp32 | 1056768 |
| saved-112 | post_norm_z_r | 18 | 524416 | fp32 | 2097664 |
| saved-113 | swiglu_g_u | 18 | 3145728 | fp32 | 12582912 |
| saved-114 | input_norm_z_r | 19 | 524416 | fp32 | 2097664 |
| saved-115 | query_norm_z_r | 19 | 528384 | fp32 | 2113536 |
| saved-116 | key_norm_z_r | 19 | 132096 | fp32 | 528384 |
| saved-117 | attention_probabilities | 19 | 264192 | fp32 | 1056768 |
| saved-118 | post_norm_z_r | 19 | 524416 | fp32 | 2097664 |
| saved-119 | swiglu_g_u | 19 | 3145728 | fp32 | 12582912 |
| saved-120 | input_norm_z_r | 20 | 524416 | fp32 | 2097664 |
| saved-121 | query_norm_z_r | 20 | 528384 | fp32 | 2113536 |
| saved-122 | key_norm_z_r | 20 | 132096 | fp32 | 528384 |
| saved-123 | attention_probabilities | 20 | 264192 | fp32 | 1056768 |
| saved-124 | post_norm_z_r | 20 | 524416 | fp32 | 2097664 |
| saved-125 | swiglu_g_u | 20 | 3145728 | fp32 | 12582912 |
| saved-126 | input_norm_z_r | 21 | 524416 | fp32 | 2097664 |
| saved-127 | query_norm_z_r | 21 | 528384 | fp32 | 2113536 |
| saved-128 | key_norm_z_r | 21 | 132096 | fp32 | 528384 |
| saved-129 | attention_probabilities | 21 | 264192 | fp32 | 1056768 |
| saved-130 | post_norm_z_r | 21 | 524416 | fp32 | 2097664 |
| saved-131 | swiglu_g_u | 21 | 3145728 | fp32 | 12582912 |
| saved-132 | input_norm_z_r | 22 | 524416 | fp32 | 2097664 |
| saved-133 | query_norm_z_r | 22 | 528384 | fp32 | 2113536 |
| saved-134 | key_norm_z_r | 22 | 132096 | fp32 | 528384 |
| saved-135 | attention_probabilities | 22 | 264192 | fp32 | 1056768 |
| saved-136 | post_norm_z_r | 22 | 524416 | fp32 | 2097664 |
| saved-137 | swiglu_g_u | 22 | 3145728 | fp32 | 12582912 |
| saved-138 | input_norm_z_r | 23 | 524416 | fp32 | 2097664 |
| saved-139 | query_norm_z_r | 23 | 528384 | fp32 | 2113536 |
| saved-140 | key_norm_z_r | 23 | 132096 | fp32 | 528384 |
| saved-141 | attention_probabilities | 23 | 264192 | fp32 | 1056768 |
| saved-142 | post_norm_z_r | 23 | 524416 | fp32 | 2097664 |
| saved-143 | swiglu_g_u | 23 | 3145728 | fp32 | 12582912 |
| saved-144 | input_norm_z_r | 24 | 524416 | fp32 | 2097664 |
| saved-145 | query_norm_z_r | 24 | 528384 | fp32 | 2113536 |
| saved-146 | key_norm_z_r | 24 | 132096 | fp32 | 528384 |
| saved-147 | attention_probabilities | 24 | 264192 | fp32 | 1056768 |
| saved-148 | post_norm_z_r | 24 | 524416 | fp32 | 2097664 |
| saved-149 | swiglu_g_u | 24 | 3145728 | fp32 | 12582912 |
| saved-150 | input_norm_z_r | 25 | 524416 | fp32 | 2097664 |
| saved-151 | query_norm_z_r | 25 | 528384 | fp32 | 2113536 |
| saved-152 | key_norm_z_r | 25 | 132096 | fp32 | 528384 |
| saved-153 | attention_probabilities | 25 | 264192 | fp32 | 1056768 |
| saved-154 | post_norm_z_r | 25 | 524416 | fp32 | 2097664 |
| saved-155 | swiglu_g_u | 25 | 3145728 | fp32 | 12582912 |
| saved-156 | input_norm_z_r | 26 | 524416 | fp32 | 2097664 |
| saved-157 | query_norm_z_r | 26 | 528384 | fp32 | 2113536 |
| saved-158 | key_norm_z_r | 26 | 132096 | fp32 | 528384 |
| saved-159 | attention_probabilities | 26 | 264192 | fp32 | 1056768 |
| saved-160 | post_norm_z_r | 26 | 524416 | fp32 | 2097664 |
| saved-161 | swiglu_g_u | 26 | 3145728 | fp32 | 12582912 |
| saved-162 | input_norm_z_r | 27 | 524416 | fp32 | 2097664 |
| saved-163 | query_norm_z_r | 27 | 528384 | fp32 | 2113536 |
| saved-164 | key_norm_z_r | 27 | 132096 | fp32 | 528384 |
| saved-165 | attention_probabilities | 27 | 264192 | fp32 | 1056768 |
| saved-166 | post_norm_z_r | 27 | 524416 | fp32 | 2097664 |
| saved-167 | swiglu_g_u | 27 | 3145728 | fp32 | 12582912 |
| saved-168 | input_norm_z_r | 28 | 524416 | fp32 | 2097664 |
| saved-169 | query_norm_z_r | 28 | 528384 | fp32 | 2113536 |
| saved-170 | key_norm_z_r | 28 | 132096 | fp32 | 528384 |
| saved-171 | attention_probabilities | 28 | 264192 | fp32 | 1056768 |
| saved-172 | post_norm_z_r | 28 | 524416 | fp32 | 2097664 |
| saved-173 | swiglu_g_u | 28 | 3145728 | fp32 | 12582912 |
| saved-174 | input_norm_z_r | 29 | 524416 | fp32 | 2097664 |
| saved-175 | query_norm_z_r | 29 | 528384 | fp32 | 2113536 |
| saved-176 | key_norm_z_r | 29 | 132096 | fp32 | 528384 |
| saved-177 | attention_probabilities | 29 | 264192 | fp32 | 1056768 |
| saved-178 | post_norm_z_r | 29 | 524416 | fp32 | 2097664 |
| saved-179 | swiglu_g_u | 29 | 3145728 | fp32 | 12582912 |
| saved-180 | input_norm_z_r | 30 | 524416 | fp32 | 2097664 |
| saved-181 | query_norm_z_r | 30 | 528384 | fp32 | 2113536 |
| saved-182 | key_norm_z_r | 30 | 132096 | fp32 | 528384 |
| saved-183 | attention_probabilities | 30 | 264192 | fp32 | 1056768 |
| saved-184 | post_norm_z_r | 30 | 524416 | fp32 | 2097664 |
| saved-185 | swiglu_g_u | 30 | 3145728 | fp32 | 12582912 |
| saved-186 | input_norm_z_r | 31 | 524416 | fp32 | 2097664 |
| saved-187 | query_norm_z_r | 31 | 528384 | fp32 | 2113536 |
| saved-188 | key_norm_z_r | 31 | 132096 | fp32 | 528384 |
| saved-189 | attention_probabilities | 31 | 264192 | fp32 | 1056768 |
| saved-190 | post_norm_z_r | 31 | 524416 | fp32 | 2097664 |
| saved-191 | swiglu_g_u | 31 | 3145728 | fp32 | 12582912 |
| saved-192 | input_norm_z_r | 32 | 524416 | fp32 | 2097664 |
| saved-193 | query_norm_z_r | 32 | 528384 | fp32 | 2113536 |
| saved-194 | key_norm_z_r | 32 | 132096 | fp32 | 528384 |
| saved-195 | attention_probabilities | 32 | 264192 | fp32 | 1056768 |
| saved-196 | post_norm_z_r | 32 | 524416 | fp32 | 2097664 |
| saved-197 | swiglu_g_u | 32 | 3145728 | fp32 | 12582912 |
| saved-198 | input_norm_z_r | 33 | 524416 | fp32 | 2097664 |
| saved-199 | query_norm_z_r | 33 | 528384 | fp32 | 2113536 |
| saved-200 | key_norm_z_r | 33 | 132096 | fp32 | 528384 |
| saved-201 | attention_probabilities | 33 | 264192 | fp32 | 1056768 |
| saved-202 | post_norm_z_r | 33 | 524416 | fp32 | 2097664 |
| saved-203 | swiglu_g_u | 33 | 3145728 | fp32 | 12582912 |
| saved-204 | input_norm_z_r | 34 | 524416 | fp32 | 2097664 |
| saved-205 | query_norm_z_r | 34 | 528384 | fp32 | 2113536 |
| saved-206 | key_norm_z_r | 34 | 132096 | fp32 | 528384 |
| saved-207 | attention_probabilities | 34 | 264192 | fp32 | 1056768 |
| saved-208 | post_norm_z_r | 34 | 524416 | fp32 | 2097664 |
| saved-209 | swiglu_g_u | 34 | 3145728 | fp32 | 12582912 |
| saved-210 | input_norm_z_r | 35 | 524416 | fp32 | 2097664 |
| saved-211 | query_norm_z_r | 35 | 528384 | fp32 | 2113536 |
| saved-212 | key_norm_z_r | 35 | 132096 | fp32 | 528384 |
| saved-213 | attention_probabilities | 35 | 264192 | fp32 | 1056768 |
| saved-214 | post_norm_z_r | 35 | 524416 | fp32 | 2097664 |
| saved-215 | swiglu_g_u | 35 | 3145728 | fp32 | 12582912 |
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
| 5 | save | saved-5 | 12582912 | 20476928 |
| 6 | save | saved-6 | 2097664 | 22574592 |
| 7 | save | saved-7 | 2113536 | 24688128 |
| 8 | save | saved-8 | 528384 | 25216512 |
| 9 | save | saved-9 | 1056768 | 26273280 |
| 10 | save | saved-10 | 2097664 | 28370944 |
| 11 | save | saved-11 | 12582912 | 40953856 |
| 12 | save | saved-12 | 2097664 | 43051520 |
| 13 | save | saved-13 | 2113536 | 45165056 |
| 14 | save | saved-14 | 528384 | 45693440 |
| 15 | save | saved-15 | 1056768 | 46750208 |
| 16 | save | saved-16 | 2097664 | 48847872 |
| 17 | save | saved-17 | 12582912 | 61430784 |
| 18 | save | saved-18 | 2097664 | 63528448 |
| 19 | save | saved-19 | 2113536 | 65641984 |
| 20 | save | saved-20 | 528384 | 66170368 |
| 21 | save | saved-21 | 1056768 | 67227136 |
| 22 | save | saved-22 | 2097664 | 69324800 |
| 23 | save | saved-23 | 12582912 | 81907712 |
| 24 | save | saved-24 | 2097664 | 84005376 |
| 25 | save | saved-25 | 2113536 | 86118912 |
| 26 | save | saved-26 | 528384 | 86647296 |
| 27 | save | saved-27 | 1056768 | 87704064 |
| 28 | save | saved-28 | 2097664 | 89801728 |
| 29 | save | saved-29 | 12582912 | 102384640 |
| 30 | save | saved-30 | 2097664 | 104482304 |
| 31 | save | saved-31 | 2113536 | 106595840 |
| 32 | save | saved-32 | 528384 | 107124224 |
| 33 | save | saved-33 | 1056768 | 108180992 |
| 34 | save | saved-34 | 2097664 | 110278656 |
| 35 | save | saved-35 | 12582912 | 122861568 |
| 36 | save | saved-36 | 2097664 | 124959232 |
| 37 | save | saved-37 | 2113536 | 127072768 |
| 38 | save | saved-38 | 528384 | 127601152 |
| 39 | save | saved-39 | 1056768 | 128657920 |
| 40 | save | saved-40 | 2097664 | 130755584 |
| 41 | save | saved-41 | 12582912 | 143338496 |
| 42 | save | saved-42 | 2097664 | 145436160 |
| 43 | save | saved-43 | 2113536 | 147549696 |
| 44 | save | saved-44 | 528384 | 148078080 |
| 45 | save | saved-45 | 1056768 | 149134848 |
| 46 | save | saved-46 | 2097664 | 151232512 |
| 47 | save | saved-47 | 12582912 | 163815424 |
| 48 | save | saved-48 | 2097664 | 165913088 |
| 49 | save | saved-49 | 2113536 | 168026624 |
| 50 | save | saved-50 | 528384 | 168555008 |
| 51 | save | saved-51 | 1056768 | 169611776 |
| 52 | save | saved-52 | 2097664 | 171709440 |
| 53 | save | saved-53 | 12582912 | 184292352 |
| 54 | save | saved-54 | 2097664 | 186390016 |
| 55 | save | saved-55 | 2113536 | 188503552 |
| 56 | save | saved-56 | 528384 | 189031936 |
| 57 | save | saved-57 | 1056768 | 190088704 |
| 58 | save | saved-58 | 2097664 | 192186368 |
| 59 | save | saved-59 | 12582912 | 204769280 |
| 60 | save | saved-60 | 2097664 | 206866944 |
| 61 | save | saved-61 | 2113536 | 208980480 |
| 62 | save | saved-62 | 528384 | 209508864 |
| 63 | save | saved-63 | 1056768 | 210565632 |
| 64 | save | saved-64 | 2097664 | 212663296 |
| 65 | save | saved-65 | 12582912 | 225246208 |
| 66 | save | saved-66 | 2097664 | 227343872 |
| 67 | save | saved-67 | 2113536 | 229457408 |
| 68 | save | saved-68 | 528384 | 229985792 |
| 69 | save | saved-69 | 1056768 | 231042560 |
| 70 | save | saved-70 | 2097664 | 233140224 |
| 71 | save | saved-71 | 12582912 | 245723136 |
| 72 | save | saved-72 | 2097664 | 247820800 |
| 73 | save | saved-73 | 2113536 | 249934336 |
| 74 | save | saved-74 | 528384 | 250462720 |
| 75 | save | saved-75 | 1056768 | 251519488 |
| 76 | save | saved-76 | 2097664 | 253617152 |
| 77 | save | saved-77 | 12582912 | 266200064 |
| 78 | save | saved-78 | 2097664 | 268297728 |
| 79 | save | saved-79 | 2113536 | 270411264 |
| 80 | save | saved-80 | 528384 | 270939648 |
| 81 | save | saved-81 | 1056768 | 271996416 |
| 82 | save | saved-82 | 2097664 | 274094080 |
| 83 | save | saved-83 | 12582912 | 286676992 |
| 84 | save | saved-84 | 2097664 | 288774656 |
| 85 | save | saved-85 | 2113536 | 290888192 |
| 86 | save | saved-86 | 528384 | 291416576 |
| 87 | save | saved-87 | 1056768 | 292473344 |
| 88 | save | saved-88 | 2097664 | 294571008 |
| 89 | save | saved-89 | 12582912 | 307153920 |
| 90 | save | saved-90 | 2097664 | 309251584 |
| 91 | save | saved-91 | 2113536 | 311365120 |
| 92 | save | saved-92 | 528384 | 311893504 |
| 93 | save | saved-93 | 1056768 | 312950272 |
| 94 | save | saved-94 | 2097664 | 315047936 |
| 95 | save | saved-95 | 12582912 | 327630848 |
| 96 | save | saved-96 | 2097664 | 329728512 |
| 97 | save | saved-97 | 2113536 | 331842048 |
| 98 | save | saved-98 | 528384 | 332370432 |
| 99 | save | saved-99 | 1056768 | 333427200 |
| 100 | save | saved-100 | 2097664 | 335524864 |
| 101 | save | saved-101 | 12582912 | 348107776 |
| 102 | save | saved-102 | 2097664 | 350205440 |
| 103 | save | saved-103 | 2113536 | 352318976 |
| 104 | save | saved-104 | 528384 | 352847360 |
| 105 | save | saved-105 | 1056768 | 353904128 |
| 106 | save | saved-106 | 2097664 | 356001792 |
| 107 | save | saved-107 | 12582912 | 368584704 |
| 108 | save | saved-108 | 2097664 | 370682368 |
| 109 | save | saved-109 | 2113536 | 372795904 |
| 110 | save | saved-110 | 528384 | 373324288 |
| 111 | save | saved-111 | 1056768 | 374381056 |
| 112 | save | saved-112 | 2097664 | 376478720 |
| 113 | save | saved-113 | 12582912 | 389061632 |
| 114 | save | saved-114 | 2097664 | 391159296 |
| 115 | save | saved-115 | 2113536 | 393272832 |
| 116 | save | saved-116 | 528384 | 393801216 |
| 117 | save | saved-117 | 1056768 | 394857984 |
| 118 | save | saved-118 | 2097664 | 396955648 |
| 119 | save | saved-119 | 12582912 | 409538560 |
| 120 | save | saved-120 | 2097664 | 411636224 |
| 121 | save | saved-121 | 2113536 | 413749760 |
| 122 | save | saved-122 | 528384 | 414278144 |
| 123 | save | saved-123 | 1056768 | 415334912 |
| 124 | save | saved-124 | 2097664 | 417432576 |
| 125 | save | saved-125 | 12582912 | 430015488 |
| 126 | save | saved-126 | 2097664 | 432113152 |
| 127 | save | saved-127 | 2113536 | 434226688 |
| 128 | save | saved-128 | 528384 | 434755072 |
| 129 | save | saved-129 | 1056768 | 435811840 |
| 130 | save | saved-130 | 2097664 | 437909504 |
| 131 | save | saved-131 | 12582912 | 450492416 |
| 132 | save | saved-132 | 2097664 | 452590080 |
| 133 | save | saved-133 | 2113536 | 454703616 |
| 134 | save | saved-134 | 528384 | 455232000 |
| 135 | save | saved-135 | 1056768 | 456288768 |
| 136 | save | saved-136 | 2097664 | 458386432 |
| 137 | save | saved-137 | 12582912 | 470969344 |
| 138 | save | saved-138 | 2097664 | 473067008 |
| 139 | save | saved-139 | 2113536 | 475180544 |
| 140 | save | saved-140 | 528384 | 475708928 |
| 141 | save | saved-141 | 1056768 | 476765696 |
| 142 | save | saved-142 | 2097664 | 478863360 |
| 143 | save | saved-143 | 12582912 | 491446272 |
| 144 | save | saved-144 | 2097664 | 493543936 |
| 145 | save | saved-145 | 2113536 | 495657472 |
| 146 | save | saved-146 | 528384 | 496185856 |
| 147 | save | saved-147 | 1056768 | 497242624 |
| 148 | save | saved-148 | 2097664 | 499340288 |
| 149 | save | saved-149 | 12582912 | 511923200 |
| 150 | save | saved-150 | 2097664 | 514020864 |
| 151 | save | saved-151 | 2113536 | 516134400 |
| 152 | save | saved-152 | 528384 | 516662784 |
| 153 | save | saved-153 | 1056768 | 517719552 |
| 154 | save | saved-154 | 2097664 | 519817216 |
| 155 | save | saved-155 | 12582912 | 532400128 |
| 156 | save | saved-156 | 2097664 | 534497792 |
| 157 | save | saved-157 | 2113536 | 536611328 |
| 158 | save | saved-158 | 528384 | 537139712 |
| 159 | save | saved-159 | 1056768 | 538196480 |
| 160 | save | saved-160 | 2097664 | 540294144 |
| 161 | save | saved-161 | 12582912 | 552877056 |
| 162 | save | saved-162 | 2097664 | 554974720 |
| 163 | save | saved-163 | 2113536 | 557088256 |
| 164 | save | saved-164 | 528384 | 557616640 |
| 165 | save | saved-165 | 1056768 | 558673408 |
| 166 | save | saved-166 | 2097664 | 560771072 |
| 167 | save | saved-167 | 12582912 | 573353984 |
| 168 | save | saved-168 | 2097664 | 575451648 |
| 169 | save | saved-169 | 2113536 | 577565184 |
| 170 | save | saved-170 | 528384 | 578093568 |
| 171 | save | saved-171 | 1056768 | 579150336 |
| 172 | save | saved-172 | 2097664 | 581248000 |
| 173 | save | saved-173 | 12582912 | 593830912 |
| 174 | save | saved-174 | 2097664 | 595928576 |
| 175 | save | saved-175 | 2113536 | 598042112 |
| 176 | save | saved-176 | 528384 | 598570496 |
| 177 | save | saved-177 | 1056768 | 599627264 |
| 178 | save | saved-178 | 2097664 | 601724928 |
| 179 | save | saved-179 | 12582912 | 614307840 |
| 180 | save | saved-180 | 2097664 | 616405504 |
| 181 | save | saved-181 | 2113536 | 618519040 |
| 182 | save | saved-182 | 528384 | 619047424 |
| 183 | save | saved-183 | 1056768 | 620104192 |
| 184 | save | saved-184 | 2097664 | 622201856 |
| 185 | save | saved-185 | 12582912 | 634784768 |
| 186 | save | saved-186 | 2097664 | 636882432 |
| 187 | save | saved-187 | 2113536 | 638995968 |
| 188 | save | saved-188 | 528384 | 639524352 |
| 189 | save | saved-189 | 1056768 | 640581120 |
| 190 | save | saved-190 | 2097664 | 642678784 |
| 191 | save | saved-191 | 12582912 | 655261696 |
| 192 | save | saved-192 | 2097664 | 657359360 |
| 193 | save | saved-193 | 2113536 | 659472896 |
| 194 | save | saved-194 | 528384 | 660001280 |
| 195 | save | saved-195 | 1056768 | 661058048 |
| 196 | save | saved-196 | 2097664 | 663155712 |
| 197 | save | saved-197 | 12582912 | 675738624 |
| 198 | save | saved-198 | 2097664 | 677836288 |
| 199 | save | saved-199 | 2113536 | 679949824 |
| 200 | save | saved-200 | 528384 | 680478208 |
| 201 | save | saved-201 | 1056768 | 681534976 |
| 202 | save | saved-202 | 2097664 | 683632640 |
| 203 | save | saved-203 | 12582912 | 696215552 |
| 204 | save | saved-204 | 2097664 | 698313216 |
| 205 | save | saved-205 | 2113536 | 700426752 |
| 206 | save | saved-206 | 528384 | 700955136 |
| 207 | save | saved-207 | 1056768 | 702011904 |
| 208 | save | saved-208 | 2097664 | 704109568 |
| 209 | save | saved-209 | 12582912 | 716692480 |
| 210 | save | saved-210 | 2097664 | 718790144 |
| 211 | save | saved-211 | 2113536 | 720903680 |
| 212 | save | saved-212 | 528384 | 721432064 |
| 213 | save | saved-213 | 1056768 | 722488832 |
| 214 | save | saved-214 | 2097664 | 724586496 |
| 215 | save | saved-215 | 12582912 | 737169408 |
| 216 | save | saved-216 | 2097664 | 739267072 |
| 217 | save | saved-217 | 77791232 | 817058304 |
| 218 | backward_last_use_release | saved-217 | -77791232 | 739267072 |
| 219 | backward_last_use_release | saved-216 | -2097664 | 737169408 |
| 220 | backward_recompute_allocate | saved-215-s-a | 12582912 | 749752320 |
| 221 | backward_recompute_release | saved-215-s-a | -12582912 | 737169408 |
| 222 | backward_last_use_release | saved-215 | -12582912 | 724586496 |
| 223 | backward_last_use_release | saved-214 | -2097664 | 722488832 |
| 224 | backward_last_use_release | saved-213 | -1056768 | 721432064 |
| 225 | backward_last_use_release | saved-212 | -528384 | 720903680 |
| 226 | backward_last_use_release | saved-211 | -2113536 | 718790144 |
| 227 | backward_last_use_release | saved-210 | -2097664 | 716692480 |
| 228 | backward_recompute_allocate | saved-209-s-a | 12582912 | 729275392 |
| 229 | backward_recompute_release | saved-209-s-a | -12582912 | 716692480 |
| 230 | backward_last_use_release | saved-209 | -12582912 | 704109568 |
| 231 | backward_last_use_release | saved-208 | -2097664 | 702011904 |
| 232 | backward_last_use_release | saved-207 | -1056768 | 700955136 |
| 233 | backward_last_use_release | saved-206 | -528384 | 700426752 |
| 234 | backward_last_use_release | saved-205 | -2113536 | 698313216 |
| 235 | backward_last_use_release | saved-204 | -2097664 | 696215552 |
| 236 | backward_recompute_allocate | saved-203-s-a | 12582912 | 708798464 |
| 237 | backward_recompute_release | saved-203-s-a | -12582912 | 696215552 |
| 238 | backward_last_use_release | saved-203 | -12582912 | 683632640 |
| 239 | backward_last_use_release | saved-202 | -2097664 | 681534976 |
| 240 | backward_last_use_release | saved-201 | -1056768 | 680478208 |
| 241 | backward_last_use_release | saved-200 | -528384 | 679949824 |
| 242 | backward_last_use_release | saved-199 | -2113536 | 677836288 |
| 243 | backward_last_use_release | saved-198 | -2097664 | 675738624 |
| 244 | backward_recompute_allocate | saved-197-s-a | 12582912 | 688321536 |
| 245 | backward_recompute_release | saved-197-s-a | -12582912 | 675738624 |
| 246 | backward_last_use_release | saved-197 | -12582912 | 663155712 |
| 247 | backward_last_use_release | saved-196 | -2097664 | 661058048 |
| 248 | backward_last_use_release | saved-195 | -1056768 | 660001280 |
| 249 | backward_last_use_release | saved-194 | -528384 | 659472896 |
| 250 | backward_last_use_release | saved-193 | -2113536 | 657359360 |
| 251 | backward_last_use_release | saved-192 | -2097664 | 655261696 |
| 252 | backward_recompute_allocate | saved-191-s-a | 12582912 | 667844608 |
| 253 | backward_recompute_release | saved-191-s-a | -12582912 | 655261696 |
| 254 | backward_last_use_release | saved-191 | -12582912 | 642678784 |
| 255 | backward_last_use_release | saved-190 | -2097664 | 640581120 |
| 256 | backward_last_use_release | saved-189 | -1056768 | 639524352 |
| 257 | backward_last_use_release | saved-188 | -528384 | 638995968 |
| 258 | backward_last_use_release | saved-187 | -2113536 | 636882432 |
| 259 | backward_last_use_release | saved-186 | -2097664 | 634784768 |
| 260 | backward_recompute_allocate | saved-185-s-a | 12582912 | 647367680 |
| 261 | backward_recompute_release | saved-185-s-a | -12582912 | 634784768 |
| 262 | backward_last_use_release | saved-185 | -12582912 | 622201856 |
| 263 | backward_last_use_release | saved-184 | -2097664 | 620104192 |
| 264 | backward_last_use_release | saved-183 | -1056768 | 619047424 |
| 265 | backward_last_use_release | saved-182 | -528384 | 618519040 |
| 266 | backward_last_use_release | saved-181 | -2113536 | 616405504 |
| 267 | backward_last_use_release | saved-180 | -2097664 | 614307840 |
| 268 | backward_recompute_allocate | saved-179-s-a | 12582912 | 626890752 |
| 269 | backward_recompute_release | saved-179-s-a | -12582912 | 614307840 |
| 270 | backward_last_use_release | saved-179 | -12582912 | 601724928 |
| 271 | backward_last_use_release | saved-178 | -2097664 | 599627264 |
| 272 | backward_last_use_release | saved-177 | -1056768 | 598570496 |
| 273 | backward_last_use_release | saved-176 | -528384 | 598042112 |
| 274 | backward_last_use_release | saved-175 | -2113536 | 595928576 |
| 275 | backward_last_use_release | saved-174 | -2097664 | 593830912 |
| 276 | backward_recompute_allocate | saved-173-s-a | 12582912 | 606413824 |
| 277 | backward_recompute_release | saved-173-s-a | -12582912 | 593830912 |
| 278 | backward_last_use_release | saved-173 | -12582912 | 581248000 |
| 279 | backward_last_use_release | saved-172 | -2097664 | 579150336 |
| 280 | backward_last_use_release | saved-171 | -1056768 | 578093568 |
| 281 | backward_last_use_release | saved-170 | -528384 | 577565184 |
| 282 | backward_last_use_release | saved-169 | -2113536 | 575451648 |
| 283 | backward_last_use_release | saved-168 | -2097664 | 573353984 |
| 284 | backward_recompute_allocate | saved-167-s-a | 12582912 | 585936896 |
| 285 | backward_recompute_release | saved-167-s-a | -12582912 | 573353984 |
| 286 | backward_last_use_release | saved-167 | -12582912 | 560771072 |
| 287 | backward_last_use_release | saved-166 | -2097664 | 558673408 |
| 288 | backward_last_use_release | saved-165 | -1056768 | 557616640 |
| 289 | backward_last_use_release | saved-164 | -528384 | 557088256 |
| 290 | backward_last_use_release | saved-163 | -2113536 | 554974720 |
| 291 | backward_last_use_release | saved-162 | -2097664 | 552877056 |
| 292 | backward_recompute_allocate | saved-161-s-a | 12582912 | 565459968 |
| 293 | backward_recompute_release | saved-161-s-a | -12582912 | 552877056 |
| 294 | backward_last_use_release | saved-161 | -12582912 | 540294144 |
| 295 | backward_last_use_release | saved-160 | -2097664 | 538196480 |
| 296 | backward_last_use_release | saved-159 | -1056768 | 537139712 |
| 297 | backward_last_use_release | saved-158 | -528384 | 536611328 |
| 298 | backward_last_use_release | saved-157 | -2113536 | 534497792 |
| 299 | backward_last_use_release | saved-156 | -2097664 | 532400128 |
| 300 | backward_recompute_allocate | saved-155-s-a | 12582912 | 544983040 |
| 301 | backward_recompute_release | saved-155-s-a | -12582912 | 532400128 |
| 302 | backward_last_use_release | saved-155 | -12582912 | 519817216 |
| 303 | backward_last_use_release | saved-154 | -2097664 | 517719552 |
| 304 | backward_last_use_release | saved-153 | -1056768 | 516662784 |
| 305 | backward_last_use_release | saved-152 | -528384 | 516134400 |
| 306 | backward_last_use_release | saved-151 | -2113536 | 514020864 |
| 307 | backward_last_use_release | saved-150 | -2097664 | 511923200 |
| 308 | backward_recompute_allocate | saved-149-s-a | 12582912 | 524506112 |
| 309 | backward_recompute_release | saved-149-s-a | -12582912 | 511923200 |
| 310 | backward_last_use_release | saved-149 | -12582912 | 499340288 |
| 311 | backward_last_use_release | saved-148 | -2097664 | 497242624 |
| 312 | backward_last_use_release | saved-147 | -1056768 | 496185856 |
| 313 | backward_last_use_release | saved-146 | -528384 | 495657472 |
| 314 | backward_last_use_release | saved-145 | -2113536 | 493543936 |
| 315 | backward_last_use_release | saved-144 | -2097664 | 491446272 |
| 316 | backward_recompute_allocate | saved-143-s-a | 12582912 | 504029184 |
| 317 | backward_recompute_release | saved-143-s-a | -12582912 | 491446272 |
| 318 | backward_last_use_release | saved-143 | -12582912 | 478863360 |
| 319 | backward_last_use_release | saved-142 | -2097664 | 476765696 |
| 320 | backward_last_use_release | saved-141 | -1056768 | 475708928 |
| 321 | backward_last_use_release | saved-140 | -528384 | 475180544 |
| 322 | backward_last_use_release | saved-139 | -2113536 | 473067008 |
| 323 | backward_last_use_release | saved-138 | -2097664 | 470969344 |
| 324 | backward_recompute_allocate | saved-137-s-a | 12582912 | 483552256 |
| 325 | backward_recompute_release | saved-137-s-a | -12582912 | 470969344 |
| 326 | backward_last_use_release | saved-137 | -12582912 | 458386432 |
| 327 | backward_last_use_release | saved-136 | -2097664 | 456288768 |
| 328 | backward_last_use_release | saved-135 | -1056768 | 455232000 |
| 329 | backward_last_use_release | saved-134 | -528384 | 454703616 |
| 330 | backward_last_use_release | saved-133 | -2113536 | 452590080 |
| 331 | backward_last_use_release | saved-132 | -2097664 | 450492416 |
| 332 | backward_recompute_allocate | saved-131-s-a | 12582912 | 463075328 |
| 333 | backward_recompute_release | saved-131-s-a | -12582912 | 450492416 |
| 334 | backward_last_use_release | saved-131 | -12582912 | 437909504 |
| 335 | backward_last_use_release | saved-130 | -2097664 | 435811840 |
| 336 | backward_last_use_release | saved-129 | -1056768 | 434755072 |
| 337 | backward_last_use_release | saved-128 | -528384 | 434226688 |
| 338 | backward_last_use_release | saved-127 | -2113536 | 432113152 |
| 339 | backward_last_use_release | saved-126 | -2097664 | 430015488 |
| 340 | backward_recompute_allocate | saved-125-s-a | 12582912 | 442598400 |
| 341 | backward_recompute_release | saved-125-s-a | -12582912 | 430015488 |
| 342 | backward_last_use_release | saved-125 | -12582912 | 417432576 |
| 343 | backward_last_use_release | saved-124 | -2097664 | 415334912 |
| 344 | backward_last_use_release | saved-123 | -1056768 | 414278144 |
| 345 | backward_last_use_release | saved-122 | -528384 | 413749760 |
| 346 | backward_last_use_release | saved-121 | -2113536 | 411636224 |
| 347 | backward_last_use_release | saved-120 | -2097664 | 409538560 |
| 348 | backward_recompute_allocate | saved-119-s-a | 12582912 | 422121472 |
| 349 | backward_recompute_release | saved-119-s-a | -12582912 | 409538560 |
| 350 | backward_last_use_release | saved-119 | -12582912 | 396955648 |
| 351 | backward_last_use_release | saved-118 | -2097664 | 394857984 |
| 352 | backward_last_use_release | saved-117 | -1056768 | 393801216 |
| 353 | backward_last_use_release | saved-116 | -528384 | 393272832 |
| 354 | backward_last_use_release | saved-115 | -2113536 | 391159296 |
| 355 | backward_last_use_release | saved-114 | -2097664 | 389061632 |
| 356 | backward_recompute_allocate | saved-113-s-a | 12582912 | 401644544 |
| 357 | backward_recompute_release | saved-113-s-a | -12582912 | 389061632 |
| 358 | backward_last_use_release | saved-113 | -12582912 | 376478720 |
| 359 | backward_last_use_release | saved-112 | -2097664 | 374381056 |
| 360 | backward_last_use_release | saved-111 | -1056768 | 373324288 |
| 361 | backward_last_use_release | saved-110 | -528384 | 372795904 |
| 362 | backward_last_use_release | saved-109 | -2113536 | 370682368 |
| 363 | backward_last_use_release | saved-108 | -2097664 | 368584704 |
| 364 | backward_recompute_allocate | saved-107-s-a | 12582912 | 381167616 |
| 365 | backward_recompute_release | saved-107-s-a | -12582912 | 368584704 |
| 366 | backward_last_use_release | saved-107 | -12582912 | 356001792 |
| 367 | backward_last_use_release | saved-106 | -2097664 | 353904128 |
| 368 | backward_last_use_release | saved-105 | -1056768 | 352847360 |
| 369 | backward_last_use_release | saved-104 | -528384 | 352318976 |
| 370 | backward_last_use_release | saved-103 | -2113536 | 350205440 |
| 371 | backward_last_use_release | saved-102 | -2097664 | 348107776 |
| 372 | backward_recompute_allocate | saved-101-s-a | 12582912 | 360690688 |
| 373 | backward_recompute_release | saved-101-s-a | -12582912 | 348107776 |
| 374 | backward_last_use_release | saved-101 | -12582912 | 335524864 |
| 375 | backward_last_use_release | saved-100 | -2097664 | 333427200 |
| 376 | backward_last_use_release | saved-99 | -1056768 | 332370432 |
| 377 | backward_last_use_release | saved-98 | -528384 | 331842048 |
| 378 | backward_last_use_release | saved-97 | -2113536 | 329728512 |
| 379 | backward_last_use_release | saved-96 | -2097664 | 327630848 |
| 380 | backward_recompute_allocate | saved-95-s-a | 12582912 | 340213760 |
| 381 | backward_recompute_release | saved-95-s-a | -12582912 | 327630848 |
| 382 | backward_last_use_release | saved-95 | -12582912 | 315047936 |
| 383 | backward_last_use_release | saved-94 | -2097664 | 312950272 |
| 384 | backward_last_use_release | saved-93 | -1056768 | 311893504 |
| 385 | backward_last_use_release | saved-92 | -528384 | 311365120 |
| 386 | backward_last_use_release | saved-91 | -2113536 | 309251584 |
| 387 | backward_last_use_release | saved-90 | -2097664 | 307153920 |
| 388 | backward_recompute_allocate | saved-89-s-a | 12582912 | 319736832 |
| 389 | backward_recompute_release | saved-89-s-a | -12582912 | 307153920 |
| 390 | backward_last_use_release | saved-89 | -12582912 | 294571008 |
| 391 | backward_last_use_release | saved-88 | -2097664 | 292473344 |
| 392 | backward_last_use_release | saved-87 | -1056768 | 291416576 |
| 393 | backward_last_use_release | saved-86 | -528384 | 290888192 |
| 394 | backward_last_use_release | saved-85 | -2113536 | 288774656 |
| 395 | backward_last_use_release | saved-84 | -2097664 | 286676992 |
| 396 | backward_recompute_allocate | saved-83-s-a | 12582912 | 299259904 |
| 397 | backward_recompute_release | saved-83-s-a | -12582912 | 286676992 |
| 398 | backward_last_use_release | saved-83 | -12582912 | 274094080 |
| 399 | backward_last_use_release | saved-82 | -2097664 | 271996416 |
| 400 | backward_last_use_release | saved-81 | -1056768 | 270939648 |
| 401 | backward_last_use_release | saved-80 | -528384 | 270411264 |
| 402 | backward_last_use_release | saved-79 | -2113536 | 268297728 |
| 403 | backward_last_use_release | saved-78 | -2097664 | 266200064 |
| 404 | backward_recompute_allocate | saved-77-s-a | 12582912 | 278782976 |
| 405 | backward_recompute_release | saved-77-s-a | -12582912 | 266200064 |
| 406 | backward_last_use_release | saved-77 | -12582912 | 253617152 |
| 407 | backward_last_use_release | saved-76 | -2097664 | 251519488 |
| 408 | backward_last_use_release | saved-75 | -1056768 | 250462720 |
| 409 | backward_last_use_release | saved-74 | -528384 | 249934336 |
| 410 | backward_last_use_release | saved-73 | -2113536 | 247820800 |
| 411 | backward_last_use_release | saved-72 | -2097664 | 245723136 |
| 412 | backward_recompute_allocate | saved-71-s-a | 12582912 | 258306048 |
| 413 | backward_recompute_release | saved-71-s-a | -12582912 | 245723136 |
| 414 | backward_last_use_release | saved-71 | -12582912 | 233140224 |
| 415 | backward_last_use_release | saved-70 | -2097664 | 231042560 |
| 416 | backward_last_use_release | saved-69 | -1056768 | 229985792 |
| 417 | backward_last_use_release | saved-68 | -528384 | 229457408 |
| 418 | backward_last_use_release | saved-67 | -2113536 | 227343872 |
| 419 | backward_last_use_release | saved-66 | -2097664 | 225246208 |
| 420 | backward_recompute_allocate | saved-65-s-a | 12582912 | 237829120 |
| 421 | backward_recompute_release | saved-65-s-a | -12582912 | 225246208 |
| 422 | backward_last_use_release | saved-65 | -12582912 | 212663296 |
| 423 | backward_last_use_release | saved-64 | -2097664 | 210565632 |
| 424 | backward_last_use_release | saved-63 | -1056768 | 209508864 |
| 425 | backward_last_use_release | saved-62 | -528384 | 208980480 |
| 426 | backward_last_use_release | saved-61 | -2113536 | 206866944 |
| 427 | backward_last_use_release | saved-60 | -2097664 | 204769280 |
| 428 | backward_recompute_allocate | saved-59-s-a | 12582912 | 217352192 |
| 429 | backward_recompute_release | saved-59-s-a | -12582912 | 204769280 |
| 430 | backward_last_use_release | saved-59 | -12582912 | 192186368 |
| 431 | backward_last_use_release | saved-58 | -2097664 | 190088704 |
| 432 | backward_last_use_release | saved-57 | -1056768 | 189031936 |
| 433 | backward_last_use_release | saved-56 | -528384 | 188503552 |
| 434 | backward_last_use_release | saved-55 | -2113536 | 186390016 |
| 435 | backward_last_use_release | saved-54 | -2097664 | 184292352 |
| 436 | backward_recompute_allocate | saved-53-s-a | 12582912 | 196875264 |
| 437 | backward_recompute_release | saved-53-s-a | -12582912 | 184292352 |
| 438 | backward_last_use_release | saved-53 | -12582912 | 171709440 |
| 439 | backward_last_use_release | saved-52 | -2097664 | 169611776 |
| 440 | backward_last_use_release | saved-51 | -1056768 | 168555008 |
| 441 | backward_last_use_release | saved-50 | -528384 | 168026624 |
| 442 | backward_last_use_release | saved-49 | -2113536 | 165913088 |
| 443 | backward_last_use_release | saved-48 | -2097664 | 163815424 |
| 444 | backward_recompute_allocate | saved-47-s-a | 12582912 | 176398336 |
| 445 | backward_recompute_release | saved-47-s-a | -12582912 | 163815424 |
| 446 | backward_last_use_release | saved-47 | -12582912 | 151232512 |
| 447 | backward_last_use_release | saved-46 | -2097664 | 149134848 |
| 448 | backward_last_use_release | saved-45 | -1056768 | 148078080 |
| 449 | backward_last_use_release | saved-44 | -528384 | 147549696 |
| 450 | backward_last_use_release | saved-43 | -2113536 | 145436160 |
| 451 | backward_last_use_release | saved-42 | -2097664 | 143338496 |
| 452 | backward_recompute_allocate | saved-41-s-a | 12582912 | 155921408 |
| 453 | backward_recompute_release | saved-41-s-a | -12582912 | 143338496 |
| 454 | backward_last_use_release | saved-41 | -12582912 | 130755584 |
| 455 | backward_last_use_release | saved-40 | -2097664 | 128657920 |
| 456 | backward_last_use_release | saved-39 | -1056768 | 127601152 |
| 457 | backward_last_use_release | saved-38 | -528384 | 127072768 |
| 458 | backward_last_use_release | saved-37 | -2113536 | 124959232 |
| 459 | backward_last_use_release | saved-36 | -2097664 | 122861568 |
| 460 | backward_recompute_allocate | saved-35-s-a | 12582912 | 135444480 |
| 461 | backward_recompute_release | saved-35-s-a | -12582912 | 122861568 |
| 462 | backward_last_use_release | saved-35 | -12582912 | 110278656 |
| 463 | backward_last_use_release | saved-34 | -2097664 | 108180992 |
| 464 | backward_last_use_release | saved-33 | -1056768 | 107124224 |
| 465 | backward_last_use_release | saved-32 | -528384 | 106595840 |
| 466 | backward_last_use_release | saved-31 | -2113536 | 104482304 |
| 467 | backward_last_use_release | saved-30 | -2097664 | 102384640 |
| 468 | backward_recompute_allocate | saved-29-s-a | 12582912 | 114967552 |
| 469 | backward_recompute_release | saved-29-s-a | -12582912 | 102384640 |
| 470 | backward_last_use_release | saved-29 | -12582912 | 89801728 |
| 471 | backward_last_use_release | saved-28 | -2097664 | 87704064 |
| 472 | backward_last_use_release | saved-27 | -1056768 | 86647296 |
| 473 | backward_last_use_release | saved-26 | -528384 | 86118912 |
| 474 | backward_last_use_release | saved-25 | -2113536 | 84005376 |
| 475 | backward_last_use_release | saved-24 | -2097664 | 81907712 |
| 476 | backward_recompute_allocate | saved-23-s-a | 12582912 | 94490624 |
| 477 | backward_recompute_release | saved-23-s-a | -12582912 | 81907712 |
| 478 | backward_last_use_release | saved-23 | -12582912 | 69324800 |
| 479 | backward_last_use_release | saved-22 | -2097664 | 67227136 |
| 480 | backward_last_use_release | saved-21 | -1056768 | 66170368 |
| 481 | backward_last_use_release | saved-20 | -528384 | 65641984 |
| 482 | backward_last_use_release | saved-19 | -2113536 | 63528448 |
| 483 | backward_last_use_release | saved-18 | -2097664 | 61430784 |
| 484 | backward_recompute_allocate | saved-17-s-a | 12582912 | 74013696 |
| 485 | backward_recompute_release | saved-17-s-a | -12582912 | 61430784 |
| 486 | backward_last_use_release | saved-17 | -12582912 | 48847872 |
| 487 | backward_last_use_release | saved-16 | -2097664 | 46750208 |
| 488 | backward_last_use_release | saved-15 | -1056768 | 45693440 |
| 489 | backward_last_use_release | saved-14 | -528384 | 45165056 |
| 490 | backward_last_use_release | saved-13 | -2113536 | 43051520 |
| 491 | backward_last_use_release | saved-12 | -2097664 | 40953856 |
| 492 | backward_recompute_allocate | saved-11-s-a | 12582912 | 53536768 |
| 493 | backward_recompute_release | saved-11-s-a | -12582912 | 40953856 |
| 494 | backward_last_use_release | saved-11 | -12582912 | 28370944 |
| 495 | backward_last_use_release | saved-10 | -2097664 | 26273280 |
| 496 | backward_last_use_release | saved-9 | -1056768 | 25216512 |
| 497 | backward_last_use_release | saved-8 | -528384 | 24688128 |
| 498 | backward_last_use_release | saved-7 | -2113536 | 22574592 |
| 499 | backward_last_use_release | saved-6 | -2097664 | 20476928 |
| 500 | backward_recompute_allocate | saved-5-s-a | 12582912 | 33059840 |
| 501 | backward_recompute_release | saved-5-s-a | -12582912 | 20476928 |
| 502 | backward_last_use_release | saved-5 | -12582912 | 7894016 |
| 503 | backward_last_use_release | saved-4 | -2097664 | 5796352 |
| 504 | backward_last_use_release | saved-3 | -1056768 | 4739584 |
| 505 | backward_last_use_release | saved-2 | -528384 | 4211200 |
| 506 | backward_last_use_release | saved-1 | -2113536 | 2097664 |
| 507 | backward_last_use_release | saved-0 | -2097664 | 0 |

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
