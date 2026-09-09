# Qwen3-8B 训练非矩阵参考账

## 输入

| 字段 | 值 |
| --- | --- |
| batch | 1 |
| tokens | 8192 |
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
| original_training_matrix_flops | 431367993163776 |
| forward_scalar_flops | 188406390784 |
| backward_scalar_flops | 260365839360 |
| optimizer_scalar_flops | 114670295046 |
| accounted_special_ops | {"cos": 1048576, "exp": 39904083968, "log": 8192, "max_compare": 39894638592, "pow": 2, "rsqrt": 12394496, "sigmoid": 3623878656, "sin": 1048576, "sqrt": 8190735360} |
| accounted_matrix_plus_scalar_flops | 431931435688966 |
| nonlinear_saved_at_forward_end_bytes | 218990149632 |
| declared_saved_and_recomputed_subset_peak_bytes | 218990149632 |
| original_parameter_state_bytes | 147433236480 |
| complete_training_step_flops | unknown |
| complete_activation_peak_bytes | unknown |
| complete_hbm_traffic_bytes | unknown |
| predicted_step_seconds | unknown |

## 非矩阵前向与反向

| 算子 | 形状 | 前向scalar | 反向scalar | 前向special | 反向special | 算法说明 |
| --- | --- | --- | --- | --- | --- | --- |
| input_rmsnorm | [36, 8192, 4096] | 4832133120 | 9663528960 | {"rsqrt": 294912} | {} | dx=6RD; shared dgamma=(2R-1)D per parameter copy. FP32 saved z/r; no cross-layer gamma merge. |
| post_attention_rmsnorm | [36, 8192, 4096] | 4832133120 | 9663528960 | {"rsqrt": 294912} | {} | dx=6RD; shared dgamma=(2R-1)D per parameter copy. FP32 saved z/r; no cross-layer gamma merge. |
| query_rmsnorm | [36, 262144, 128] | 4841275392 | 9663671808 | {"rsqrt": 9437184} | {} | dx=6RD; shared dgamma=(2R-1)D per parameter copy. FP32 saved z/r; no cross-layer gamma merge. |
| key_rmsnorm | [36, 65536, 128] | 1210318848 | 2415914496 | {"rsqrt": 2359296} | {} | dx=6RD; shared dgamma=(2R-1)D per parameter copy. FP32 saved z/r; no cross-layer gamma merge. |
| final_rmsnorm | [1, 8192, 4096] | 134225920 | 268431360 | {"rsqrt": 8192} | {} | dx=6RD; shared dgamma=(2R-1)D per parameter copy. FP32 saved z/r; no cross-layer gamma merge. |
| swiglu | [36, 8192, 12288] | 7247757312 | 21743271936 | {"sigmoid": 3623878656} | {} | Save a/s/u; or save g/u and recompute sigmoid plus a=g*s immediately before backward. |
| attention_scale_softmax | [36, 1, 32, 8192, "causal_row_width=1..T"] | 154628259840 | 193287684096 | {"exp": 38659424256, "max_compare": 38649987072} | {} | Backward softmax=4K-1; backward score scale adds K. No gradient through stabilizing max selection. |
| rotary_apply | [36, 8192, 40, 128] | 4529848320 | 4529848320 | {} | {} | Fixed rotation and transpose; no learned position parameter. |
| rotary_table_per_step | [8192, 128] | 524288 | 0 | {"cos": 1048576, "sin": 1048576} | {} | Shared across batch and layers; fixed inv_freq initialization excluded. |
| residual_and_branch_gradient_merges | [36, 8192, 4096] | 2415919104 | 6039797760 | {} | {} | Backward: two residual joins, one gate/up input join, two Q/K/V input joins; fork/alias itself is no arithmetic. |
| gqa_head_gradient_reduce | [36, 8192, 8, 4, 128] | 0 | 1811939328 | {} | {} | Declared independent per-query-head dK/dV outputs are summed into each KV group; fused grouped contraction may absorb this reduction into its own matrix convention. |
| embedding_scatter_add | [8192, 4096] | 0 | 33554432 | {} | {} | One additive contribution per token component into a zeroed dense embedding gradient; IDs/collisions/atomics unknown. |
| mean_cross_entropy | [8192, 151936] | 3733995520 | 1244667904 | {"exp": 1244659712, "log": 8192, "max_compare": 1244651520} | {} | Stable logsumexp plus saved probabilities; mean reduction S operations. Backward only target subtract then V scales per row. |

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
| embedding_index_reads_int64_bytes | 65536 |
| loss_gradient_zero_fp32_bytes | 4978638848 |
| loss_label_reads_int64_bytes | 65536 |
| loss_selected_logits_bf16_read_bytes | 2489319424 |
| loss_gradient_scatter_fp32_write_bytes | 4978638848 |
| bf16_to_fp32_nonlinear_input_elements | 12451840000 |
| fp32_to_bf16_norm_swiglu_output_elements | 7583301632 |
| compact_hidden_gather_bf16_read_write_bytes | 0 |
| compact_hidden_gradient_zero_fp32_bytes | 0 |
| compact_hidden_gradient_scatter_fp32_read_write_bytes | 0 |

## 声明保存对象

只列本非线性反向算法对象；不包含全部矩阵保存输入、梯度或allocator。

| ID | 对象 | 层 | 元素 | dtype | bytes |
| --- | --- | --- | --- | --- | --- |
| saved-0 | input_norm_z_r | 0 | 33562624 | fp32 | 134250496 |
| saved-1 | query_norm_z_r | 0 | 33816576 | fp32 | 135266304 |
| saved-2 | key_norm_z_r | 0 | 8454144 | fp32 | 33816576 |
| saved-3 | attention_probabilities | 0 | 1073872896 | fp32 | 4295491584 |
| saved-4 | post_norm_z_r | 0 | 33562624 | fp32 | 134250496 |
| saved-5 | swiglu_a_s_u | 0 | 301989888 | fp32 | 1207959552 |
| saved-6 | input_norm_z_r | 1 | 33562624 | fp32 | 134250496 |
| saved-7 | query_norm_z_r | 1 | 33816576 | fp32 | 135266304 |
| saved-8 | key_norm_z_r | 1 | 8454144 | fp32 | 33816576 |
| saved-9 | attention_probabilities | 1 | 1073872896 | fp32 | 4295491584 |
| saved-10 | post_norm_z_r | 1 | 33562624 | fp32 | 134250496 |
| saved-11 | swiglu_a_s_u | 1 | 301989888 | fp32 | 1207959552 |
| saved-12 | input_norm_z_r | 2 | 33562624 | fp32 | 134250496 |
| saved-13 | query_norm_z_r | 2 | 33816576 | fp32 | 135266304 |
| saved-14 | key_norm_z_r | 2 | 8454144 | fp32 | 33816576 |
| saved-15 | attention_probabilities | 2 | 1073872896 | fp32 | 4295491584 |
| saved-16 | post_norm_z_r | 2 | 33562624 | fp32 | 134250496 |
| saved-17 | swiglu_a_s_u | 2 | 301989888 | fp32 | 1207959552 |
| saved-18 | input_norm_z_r | 3 | 33562624 | fp32 | 134250496 |
| saved-19 | query_norm_z_r | 3 | 33816576 | fp32 | 135266304 |
| saved-20 | key_norm_z_r | 3 | 8454144 | fp32 | 33816576 |
| saved-21 | attention_probabilities | 3 | 1073872896 | fp32 | 4295491584 |
| saved-22 | post_norm_z_r | 3 | 33562624 | fp32 | 134250496 |
| saved-23 | swiglu_a_s_u | 3 | 301989888 | fp32 | 1207959552 |
| saved-24 | input_norm_z_r | 4 | 33562624 | fp32 | 134250496 |
| saved-25 | query_norm_z_r | 4 | 33816576 | fp32 | 135266304 |
| saved-26 | key_norm_z_r | 4 | 8454144 | fp32 | 33816576 |
| saved-27 | attention_probabilities | 4 | 1073872896 | fp32 | 4295491584 |
| saved-28 | post_norm_z_r | 4 | 33562624 | fp32 | 134250496 |
| saved-29 | swiglu_a_s_u | 4 | 301989888 | fp32 | 1207959552 |
| saved-30 | input_norm_z_r | 5 | 33562624 | fp32 | 134250496 |
| saved-31 | query_norm_z_r | 5 | 33816576 | fp32 | 135266304 |
| saved-32 | key_norm_z_r | 5 | 8454144 | fp32 | 33816576 |
| saved-33 | attention_probabilities | 5 | 1073872896 | fp32 | 4295491584 |
| saved-34 | post_norm_z_r | 5 | 33562624 | fp32 | 134250496 |
| saved-35 | swiglu_a_s_u | 5 | 301989888 | fp32 | 1207959552 |
| saved-36 | input_norm_z_r | 6 | 33562624 | fp32 | 134250496 |
| saved-37 | query_norm_z_r | 6 | 33816576 | fp32 | 135266304 |
| saved-38 | key_norm_z_r | 6 | 8454144 | fp32 | 33816576 |
| saved-39 | attention_probabilities | 6 | 1073872896 | fp32 | 4295491584 |
| saved-40 | post_norm_z_r | 6 | 33562624 | fp32 | 134250496 |
| saved-41 | swiglu_a_s_u | 6 | 301989888 | fp32 | 1207959552 |
| saved-42 | input_norm_z_r | 7 | 33562624 | fp32 | 134250496 |
| saved-43 | query_norm_z_r | 7 | 33816576 | fp32 | 135266304 |
| saved-44 | key_norm_z_r | 7 | 8454144 | fp32 | 33816576 |
| saved-45 | attention_probabilities | 7 | 1073872896 | fp32 | 4295491584 |
| saved-46 | post_norm_z_r | 7 | 33562624 | fp32 | 134250496 |
| saved-47 | swiglu_a_s_u | 7 | 301989888 | fp32 | 1207959552 |
| saved-48 | input_norm_z_r | 8 | 33562624 | fp32 | 134250496 |
| saved-49 | query_norm_z_r | 8 | 33816576 | fp32 | 135266304 |
| saved-50 | key_norm_z_r | 8 | 8454144 | fp32 | 33816576 |
| saved-51 | attention_probabilities | 8 | 1073872896 | fp32 | 4295491584 |
| saved-52 | post_norm_z_r | 8 | 33562624 | fp32 | 134250496 |
| saved-53 | swiglu_a_s_u | 8 | 301989888 | fp32 | 1207959552 |
| saved-54 | input_norm_z_r | 9 | 33562624 | fp32 | 134250496 |
| saved-55 | query_norm_z_r | 9 | 33816576 | fp32 | 135266304 |
| saved-56 | key_norm_z_r | 9 | 8454144 | fp32 | 33816576 |
| saved-57 | attention_probabilities | 9 | 1073872896 | fp32 | 4295491584 |
| saved-58 | post_norm_z_r | 9 | 33562624 | fp32 | 134250496 |
| saved-59 | swiglu_a_s_u | 9 | 301989888 | fp32 | 1207959552 |
| saved-60 | input_norm_z_r | 10 | 33562624 | fp32 | 134250496 |
| saved-61 | query_norm_z_r | 10 | 33816576 | fp32 | 135266304 |
| saved-62 | key_norm_z_r | 10 | 8454144 | fp32 | 33816576 |
| saved-63 | attention_probabilities | 10 | 1073872896 | fp32 | 4295491584 |
| saved-64 | post_norm_z_r | 10 | 33562624 | fp32 | 134250496 |
| saved-65 | swiglu_a_s_u | 10 | 301989888 | fp32 | 1207959552 |
| saved-66 | input_norm_z_r | 11 | 33562624 | fp32 | 134250496 |
| saved-67 | query_norm_z_r | 11 | 33816576 | fp32 | 135266304 |
| saved-68 | key_norm_z_r | 11 | 8454144 | fp32 | 33816576 |
| saved-69 | attention_probabilities | 11 | 1073872896 | fp32 | 4295491584 |
| saved-70 | post_norm_z_r | 11 | 33562624 | fp32 | 134250496 |
| saved-71 | swiglu_a_s_u | 11 | 301989888 | fp32 | 1207959552 |
| saved-72 | input_norm_z_r | 12 | 33562624 | fp32 | 134250496 |
| saved-73 | query_norm_z_r | 12 | 33816576 | fp32 | 135266304 |
| saved-74 | key_norm_z_r | 12 | 8454144 | fp32 | 33816576 |
| saved-75 | attention_probabilities | 12 | 1073872896 | fp32 | 4295491584 |
| saved-76 | post_norm_z_r | 12 | 33562624 | fp32 | 134250496 |
| saved-77 | swiglu_a_s_u | 12 | 301989888 | fp32 | 1207959552 |
| saved-78 | input_norm_z_r | 13 | 33562624 | fp32 | 134250496 |
| saved-79 | query_norm_z_r | 13 | 33816576 | fp32 | 135266304 |
| saved-80 | key_norm_z_r | 13 | 8454144 | fp32 | 33816576 |
| saved-81 | attention_probabilities | 13 | 1073872896 | fp32 | 4295491584 |
| saved-82 | post_norm_z_r | 13 | 33562624 | fp32 | 134250496 |
| saved-83 | swiglu_a_s_u | 13 | 301989888 | fp32 | 1207959552 |
| saved-84 | input_norm_z_r | 14 | 33562624 | fp32 | 134250496 |
| saved-85 | query_norm_z_r | 14 | 33816576 | fp32 | 135266304 |
| saved-86 | key_norm_z_r | 14 | 8454144 | fp32 | 33816576 |
| saved-87 | attention_probabilities | 14 | 1073872896 | fp32 | 4295491584 |
| saved-88 | post_norm_z_r | 14 | 33562624 | fp32 | 134250496 |
| saved-89 | swiglu_a_s_u | 14 | 301989888 | fp32 | 1207959552 |
| saved-90 | input_norm_z_r | 15 | 33562624 | fp32 | 134250496 |
| saved-91 | query_norm_z_r | 15 | 33816576 | fp32 | 135266304 |
| saved-92 | key_norm_z_r | 15 | 8454144 | fp32 | 33816576 |
| saved-93 | attention_probabilities | 15 | 1073872896 | fp32 | 4295491584 |
| saved-94 | post_norm_z_r | 15 | 33562624 | fp32 | 134250496 |
| saved-95 | swiglu_a_s_u | 15 | 301989888 | fp32 | 1207959552 |
| saved-96 | input_norm_z_r | 16 | 33562624 | fp32 | 134250496 |
| saved-97 | query_norm_z_r | 16 | 33816576 | fp32 | 135266304 |
| saved-98 | key_norm_z_r | 16 | 8454144 | fp32 | 33816576 |
| saved-99 | attention_probabilities | 16 | 1073872896 | fp32 | 4295491584 |
| saved-100 | post_norm_z_r | 16 | 33562624 | fp32 | 134250496 |
| saved-101 | swiglu_a_s_u | 16 | 301989888 | fp32 | 1207959552 |
| saved-102 | input_norm_z_r | 17 | 33562624 | fp32 | 134250496 |
| saved-103 | query_norm_z_r | 17 | 33816576 | fp32 | 135266304 |
| saved-104 | key_norm_z_r | 17 | 8454144 | fp32 | 33816576 |
| saved-105 | attention_probabilities | 17 | 1073872896 | fp32 | 4295491584 |
| saved-106 | post_norm_z_r | 17 | 33562624 | fp32 | 134250496 |
| saved-107 | swiglu_a_s_u | 17 | 301989888 | fp32 | 1207959552 |
| saved-108 | input_norm_z_r | 18 | 33562624 | fp32 | 134250496 |
| saved-109 | query_norm_z_r | 18 | 33816576 | fp32 | 135266304 |
| saved-110 | key_norm_z_r | 18 | 8454144 | fp32 | 33816576 |
| saved-111 | attention_probabilities | 18 | 1073872896 | fp32 | 4295491584 |
| saved-112 | post_norm_z_r | 18 | 33562624 | fp32 | 134250496 |
| saved-113 | swiglu_a_s_u | 18 | 301989888 | fp32 | 1207959552 |
| saved-114 | input_norm_z_r | 19 | 33562624 | fp32 | 134250496 |
| saved-115 | query_norm_z_r | 19 | 33816576 | fp32 | 135266304 |
| saved-116 | key_norm_z_r | 19 | 8454144 | fp32 | 33816576 |
| saved-117 | attention_probabilities | 19 | 1073872896 | fp32 | 4295491584 |
| saved-118 | post_norm_z_r | 19 | 33562624 | fp32 | 134250496 |
| saved-119 | swiglu_a_s_u | 19 | 301989888 | fp32 | 1207959552 |
| saved-120 | input_norm_z_r | 20 | 33562624 | fp32 | 134250496 |
| saved-121 | query_norm_z_r | 20 | 33816576 | fp32 | 135266304 |
| saved-122 | key_norm_z_r | 20 | 8454144 | fp32 | 33816576 |
| saved-123 | attention_probabilities | 20 | 1073872896 | fp32 | 4295491584 |
| saved-124 | post_norm_z_r | 20 | 33562624 | fp32 | 134250496 |
| saved-125 | swiglu_a_s_u | 20 | 301989888 | fp32 | 1207959552 |
| saved-126 | input_norm_z_r | 21 | 33562624 | fp32 | 134250496 |
| saved-127 | query_norm_z_r | 21 | 33816576 | fp32 | 135266304 |
| saved-128 | key_norm_z_r | 21 | 8454144 | fp32 | 33816576 |
| saved-129 | attention_probabilities | 21 | 1073872896 | fp32 | 4295491584 |
| saved-130 | post_norm_z_r | 21 | 33562624 | fp32 | 134250496 |
| saved-131 | swiglu_a_s_u | 21 | 301989888 | fp32 | 1207959552 |
| saved-132 | input_norm_z_r | 22 | 33562624 | fp32 | 134250496 |
| saved-133 | query_norm_z_r | 22 | 33816576 | fp32 | 135266304 |
| saved-134 | key_norm_z_r | 22 | 8454144 | fp32 | 33816576 |
| saved-135 | attention_probabilities | 22 | 1073872896 | fp32 | 4295491584 |
| saved-136 | post_norm_z_r | 22 | 33562624 | fp32 | 134250496 |
| saved-137 | swiglu_a_s_u | 22 | 301989888 | fp32 | 1207959552 |
| saved-138 | input_norm_z_r | 23 | 33562624 | fp32 | 134250496 |
| saved-139 | query_norm_z_r | 23 | 33816576 | fp32 | 135266304 |
| saved-140 | key_norm_z_r | 23 | 8454144 | fp32 | 33816576 |
| saved-141 | attention_probabilities | 23 | 1073872896 | fp32 | 4295491584 |
| saved-142 | post_norm_z_r | 23 | 33562624 | fp32 | 134250496 |
| saved-143 | swiglu_a_s_u | 23 | 301989888 | fp32 | 1207959552 |
| saved-144 | input_norm_z_r | 24 | 33562624 | fp32 | 134250496 |
| saved-145 | query_norm_z_r | 24 | 33816576 | fp32 | 135266304 |
| saved-146 | key_norm_z_r | 24 | 8454144 | fp32 | 33816576 |
| saved-147 | attention_probabilities | 24 | 1073872896 | fp32 | 4295491584 |
| saved-148 | post_norm_z_r | 24 | 33562624 | fp32 | 134250496 |
| saved-149 | swiglu_a_s_u | 24 | 301989888 | fp32 | 1207959552 |
| saved-150 | input_norm_z_r | 25 | 33562624 | fp32 | 134250496 |
| saved-151 | query_norm_z_r | 25 | 33816576 | fp32 | 135266304 |
| saved-152 | key_norm_z_r | 25 | 8454144 | fp32 | 33816576 |
| saved-153 | attention_probabilities | 25 | 1073872896 | fp32 | 4295491584 |
| saved-154 | post_norm_z_r | 25 | 33562624 | fp32 | 134250496 |
| saved-155 | swiglu_a_s_u | 25 | 301989888 | fp32 | 1207959552 |
| saved-156 | input_norm_z_r | 26 | 33562624 | fp32 | 134250496 |
| saved-157 | query_norm_z_r | 26 | 33816576 | fp32 | 135266304 |
| saved-158 | key_norm_z_r | 26 | 8454144 | fp32 | 33816576 |
| saved-159 | attention_probabilities | 26 | 1073872896 | fp32 | 4295491584 |
| saved-160 | post_norm_z_r | 26 | 33562624 | fp32 | 134250496 |
| saved-161 | swiglu_a_s_u | 26 | 301989888 | fp32 | 1207959552 |
| saved-162 | input_norm_z_r | 27 | 33562624 | fp32 | 134250496 |
| saved-163 | query_norm_z_r | 27 | 33816576 | fp32 | 135266304 |
| saved-164 | key_norm_z_r | 27 | 8454144 | fp32 | 33816576 |
| saved-165 | attention_probabilities | 27 | 1073872896 | fp32 | 4295491584 |
| saved-166 | post_norm_z_r | 27 | 33562624 | fp32 | 134250496 |
| saved-167 | swiglu_a_s_u | 27 | 301989888 | fp32 | 1207959552 |
| saved-168 | input_norm_z_r | 28 | 33562624 | fp32 | 134250496 |
| saved-169 | query_norm_z_r | 28 | 33816576 | fp32 | 135266304 |
| saved-170 | key_norm_z_r | 28 | 8454144 | fp32 | 33816576 |
| saved-171 | attention_probabilities | 28 | 1073872896 | fp32 | 4295491584 |
| saved-172 | post_norm_z_r | 28 | 33562624 | fp32 | 134250496 |
| saved-173 | swiglu_a_s_u | 28 | 301989888 | fp32 | 1207959552 |
| saved-174 | input_norm_z_r | 29 | 33562624 | fp32 | 134250496 |
| saved-175 | query_norm_z_r | 29 | 33816576 | fp32 | 135266304 |
| saved-176 | key_norm_z_r | 29 | 8454144 | fp32 | 33816576 |
| saved-177 | attention_probabilities | 29 | 1073872896 | fp32 | 4295491584 |
| saved-178 | post_norm_z_r | 29 | 33562624 | fp32 | 134250496 |
| saved-179 | swiglu_a_s_u | 29 | 301989888 | fp32 | 1207959552 |
| saved-180 | input_norm_z_r | 30 | 33562624 | fp32 | 134250496 |
| saved-181 | query_norm_z_r | 30 | 33816576 | fp32 | 135266304 |
| saved-182 | key_norm_z_r | 30 | 8454144 | fp32 | 33816576 |
| saved-183 | attention_probabilities | 30 | 1073872896 | fp32 | 4295491584 |
| saved-184 | post_norm_z_r | 30 | 33562624 | fp32 | 134250496 |
| saved-185 | swiglu_a_s_u | 30 | 301989888 | fp32 | 1207959552 |
| saved-186 | input_norm_z_r | 31 | 33562624 | fp32 | 134250496 |
| saved-187 | query_norm_z_r | 31 | 33816576 | fp32 | 135266304 |
| saved-188 | key_norm_z_r | 31 | 8454144 | fp32 | 33816576 |
| saved-189 | attention_probabilities | 31 | 1073872896 | fp32 | 4295491584 |
| saved-190 | post_norm_z_r | 31 | 33562624 | fp32 | 134250496 |
| saved-191 | swiglu_a_s_u | 31 | 301989888 | fp32 | 1207959552 |
| saved-192 | input_norm_z_r | 32 | 33562624 | fp32 | 134250496 |
| saved-193 | query_norm_z_r | 32 | 33816576 | fp32 | 135266304 |
| saved-194 | key_norm_z_r | 32 | 8454144 | fp32 | 33816576 |
| saved-195 | attention_probabilities | 32 | 1073872896 | fp32 | 4295491584 |
| saved-196 | post_norm_z_r | 32 | 33562624 | fp32 | 134250496 |
| saved-197 | swiglu_a_s_u | 32 | 301989888 | fp32 | 1207959552 |
| saved-198 | input_norm_z_r | 33 | 33562624 | fp32 | 134250496 |
| saved-199 | query_norm_z_r | 33 | 33816576 | fp32 | 135266304 |
| saved-200 | key_norm_z_r | 33 | 8454144 | fp32 | 33816576 |
| saved-201 | attention_probabilities | 33 | 1073872896 | fp32 | 4295491584 |
| saved-202 | post_norm_z_r | 33 | 33562624 | fp32 | 134250496 |
| saved-203 | swiglu_a_s_u | 33 | 301989888 | fp32 | 1207959552 |
| saved-204 | input_norm_z_r | 34 | 33562624 | fp32 | 134250496 |
| saved-205 | query_norm_z_r | 34 | 33816576 | fp32 | 135266304 |
| saved-206 | key_norm_z_r | 34 | 8454144 | fp32 | 33816576 |
| saved-207 | attention_probabilities | 34 | 1073872896 | fp32 | 4295491584 |
| saved-208 | post_norm_z_r | 34 | 33562624 | fp32 | 134250496 |
| saved-209 | swiglu_a_s_u | 34 | 301989888 | fp32 | 1207959552 |
| saved-210 | input_norm_z_r | 35 | 33562624 | fp32 | 134250496 |
| saved-211 | query_norm_z_r | 35 | 33816576 | fp32 | 135266304 |
| saved-212 | key_norm_z_r | 35 | 8454144 | fp32 | 33816576 |
| saved-213 | attention_probabilities | 35 | 1073872896 | fp32 | 4295491584 |
| saved-214 | post_norm_z_r | 35 | 33562624 | fp32 | 134250496 |
| saved-215 | swiglu_a_s_u | 35 | 301989888 | fp32 | 1207959552 |
| saved-216 | final_norm_z_r | unknown | 33562624 | fp32 | 134250496 |
| saved-217 | loss_probabilities | unknown | 1244659712 | fp32 | 4978638848 |

## 保存与重算事件

| 事件 | 动作 | 对象 | 变化bytes | 子集合存活bytes |
| --- | --- | --- | --- | --- |
| 0 | save | saved-0 | 134250496 | 134250496 |
| 1 | save | saved-1 | 135266304 | 269516800 |
| 2 | save | saved-2 | 33816576 | 303333376 |
| 3 | save | saved-3 | 4295491584 | 4598824960 |
| 4 | save | saved-4 | 134250496 | 4733075456 |
| 5 | save | saved-5 | 1207959552 | 5941035008 |
| 6 | save | saved-6 | 134250496 | 6075285504 |
| 7 | save | saved-7 | 135266304 | 6210551808 |
| 8 | save | saved-8 | 33816576 | 6244368384 |
| 9 | save | saved-9 | 4295491584 | 10539859968 |
| 10 | save | saved-10 | 134250496 | 10674110464 |
| 11 | save | saved-11 | 1207959552 | 11882070016 |
| 12 | save | saved-12 | 134250496 | 12016320512 |
| 13 | save | saved-13 | 135266304 | 12151586816 |
| 14 | save | saved-14 | 33816576 | 12185403392 |
| 15 | save | saved-15 | 4295491584 | 16480894976 |
| 16 | save | saved-16 | 134250496 | 16615145472 |
| 17 | save | saved-17 | 1207959552 | 17823105024 |
| 18 | save | saved-18 | 134250496 | 17957355520 |
| 19 | save | saved-19 | 135266304 | 18092621824 |
| 20 | save | saved-20 | 33816576 | 18126438400 |
| 21 | save | saved-21 | 4295491584 | 22421929984 |
| 22 | save | saved-22 | 134250496 | 22556180480 |
| 23 | save | saved-23 | 1207959552 | 23764140032 |
| 24 | save | saved-24 | 134250496 | 23898390528 |
| 25 | save | saved-25 | 135266304 | 24033656832 |
| 26 | save | saved-26 | 33816576 | 24067473408 |
| 27 | save | saved-27 | 4295491584 | 28362964992 |
| 28 | save | saved-28 | 134250496 | 28497215488 |
| 29 | save | saved-29 | 1207959552 | 29705175040 |
| 30 | save | saved-30 | 134250496 | 29839425536 |
| 31 | save | saved-31 | 135266304 | 29974691840 |
| 32 | save | saved-32 | 33816576 | 30008508416 |
| 33 | save | saved-33 | 4295491584 | 34304000000 |
| 34 | save | saved-34 | 134250496 | 34438250496 |
| 35 | save | saved-35 | 1207959552 | 35646210048 |
| 36 | save | saved-36 | 134250496 | 35780460544 |
| 37 | save | saved-37 | 135266304 | 35915726848 |
| 38 | save | saved-38 | 33816576 | 35949543424 |
| 39 | save | saved-39 | 4295491584 | 40245035008 |
| 40 | save | saved-40 | 134250496 | 40379285504 |
| 41 | save | saved-41 | 1207959552 | 41587245056 |
| 42 | save | saved-42 | 134250496 | 41721495552 |
| 43 | save | saved-43 | 135266304 | 41856761856 |
| 44 | save | saved-44 | 33816576 | 41890578432 |
| 45 | save | saved-45 | 4295491584 | 46186070016 |
| 46 | save | saved-46 | 134250496 | 46320320512 |
| 47 | save | saved-47 | 1207959552 | 47528280064 |
| 48 | save | saved-48 | 134250496 | 47662530560 |
| 49 | save | saved-49 | 135266304 | 47797796864 |
| 50 | save | saved-50 | 33816576 | 47831613440 |
| 51 | save | saved-51 | 4295491584 | 52127105024 |
| 52 | save | saved-52 | 134250496 | 52261355520 |
| 53 | save | saved-53 | 1207959552 | 53469315072 |
| 54 | save | saved-54 | 134250496 | 53603565568 |
| 55 | save | saved-55 | 135266304 | 53738831872 |
| 56 | save | saved-56 | 33816576 | 53772648448 |
| 57 | save | saved-57 | 4295491584 | 58068140032 |
| 58 | save | saved-58 | 134250496 | 58202390528 |
| 59 | save | saved-59 | 1207959552 | 59410350080 |
| 60 | save | saved-60 | 134250496 | 59544600576 |
| 61 | save | saved-61 | 135266304 | 59679866880 |
| 62 | save | saved-62 | 33816576 | 59713683456 |
| 63 | save | saved-63 | 4295491584 | 64009175040 |
| 64 | save | saved-64 | 134250496 | 64143425536 |
| 65 | save | saved-65 | 1207959552 | 65351385088 |
| 66 | save | saved-66 | 134250496 | 65485635584 |
| 67 | save | saved-67 | 135266304 | 65620901888 |
| 68 | save | saved-68 | 33816576 | 65654718464 |
| 69 | save | saved-69 | 4295491584 | 69950210048 |
| 70 | save | saved-70 | 134250496 | 70084460544 |
| 71 | save | saved-71 | 1207959552 | 71292420096 |
| 72 | save | saved-72 | 134250496 | 71426670592 |
| 73 | save | saved-73 | 135266304 | 71561936896 |
| 74 | save | saved-74 | 33816576 | 71595753472 |
| 75 | save | saved-75 | 4295491584 | 75891245056 |
| 76 | save | saved-76 | 134250496 | 76025495552 |
| 77 | save | saved-77 | 1207959552 | 77233455104 |
| 78 | save | saved-78 | 134250496 | 77367705600 |
| 79 | save | saved-79 | 135266304 | 77502971904 |
| 80 | save | saved-80 | 33816576 | 77536788480 |
| 81 | save | saved-81 | 4295491584 | 81832280064 |
| 82 | save | saved-82 | 134250496 | 81966530560 |
| 83 | save | saved-83 | 1207959552 | 83174490112 |
| 84 | save | saved-84 | 134250496 | 83308740608 |
| 85 | save | saved-85 | 135266304 | 83444006912 |
| 86 | save | saved-86 | 33816576 | 83477823488 |
| 87 | save | saved-87 | 4295491584 | 87773315072 |
| 88 | save | saved-88 | 134250496 | 87907565568 |
| 89 | save | saved-89 | 1207959552 | 89115525120 |
| 90 | save | saved-90 | 134250496 | 89249775616 |
| 91 | save | saved-91 | 135266304 | 89385041920 |
| 92 | save | saved-92 | 33816576 | 89418858496 |
| 93 | save | saved-93 | 4295491584 | 93714350080 |
| 94 | save | saved-94 | 134250496 | 93848600576 |
| 95 | save | saved-95 | 1207959552 | 95056560128 |
| 96 | save | saved-96 | 134250496 | 95190810624 |
| 97 | save | saved-97 | 135266304 | 95326076928 |
| 98 | save | saved-98 | 33816576 | 95359893504 |
| 99 | save | saved-99 | 4295491584 | 99655385088 |
| 100 | save | saved-100 | 134250496 | 99789635584 |
| 101 | save | saved-101 | 1207959552 | 100997595136 |
| 102 | save | saved-102 | 134250496 | 101131845632 |
| 103 | save | saved-103 | 135266304 | 101267111936 |
| 104 | save | saved-104 | 33816576 | 101300928512 |
| 105 | save | saved-105 | 4295491584 | 105596420096 |
| 106 | save | saved-106 | 134250496 | 105730670592 |
| 107 | save | saved-107 | 1207959552 | 106938630144 |
| 108 | save | saved-108 | 134250496 | 107072880640 |
| 109 | save | saved-109 | 135266304 | 107208146944 |
| 110 | save | saved-110 | 33816576 | 107241963520 |
| 111 | save | saved-111 | 4295491584 | 111537455104 |
| 112 | save | saved-112 | 134250496 | 111671705600 |
| 113 | save | saved-113 | 1207959552 | 112879665152 |
| 114 | save | saved-114 | 134250496 | 113013915648 |
| 115 | save | saved-115 | 135266304 | 113149181952 |
| 116 | save | saved-116 | 33816576 | 113182998528 |
| 117 | save | saved-117 | 4295491584 | 117478490112 |
| 118 | save | saved-118 | 134250496 | 117612740608 |
| 119 | save | saved-119 | 1207959552 | 118820700160 |
| 120 | save | saved-120 | 134250496 | 118954950656 |
| 121 | save | saved-121 | 135266304 | 119090216960 |
| 122 | save | saved-122 | 33816576 | 119124033536 |
| 123 | save | saved-123 | 4295491584 | 123419525120 |
| 124 | save | saved-124 | 134250496 | 123553775616 |
| 125 | save | saved-125 | 1207959552 | 124761735168 |
| 126 | save | saved-126 | 134250496 | 124895985664 |
| 127 | save | saved-127 | 135266304 | 125031251968 |
| 128 | save | saved-128 | 33816576 | 125065068544 |
| 129 | save | saved-129 | 4295491584 | 129360560128 |
| 130 | save | saved-130 | 134250496 | 129494810624 |
| 131 | save | saved-131 | 1207959552 | 130702770176 |
| 132 | save | saved-132 | 134250496 | 130837020672 |
| 133 | save | saved-133 | 135266304 | 130972286976 |
| 134 | save | saved-134 | 33816576 | 131006103552 |
| 135 | save | saved-135 | 4295491584 | 135301595136 |
| 136 | save | saved-136 | 134250496 | 135435845632 |
| 137 | save | saved-137 | 1207959552 | 136643805184 |
| 138 | save | saved-138 | 134250496 | 136778055680 |
| 139 | save | saved-139 | 135266304 | 136913321984 |
| 140 | save | saved-140 | 33816576 | 136947138560 |
| 141 | save | saved-141 | 4295491584 | 141242630144 |
| 142 | save | saved-142 | 134250496 | 141376880640 |
| 143 | save | saved-143 | 1207959552 | 142584840192 |
| 144 | save | saved-144 | 134250496 | 142719090688 |
| 145 | save | saved-145 | 135266304 | 142854356992 |
| 146 | save | saved-146 | 33816576 | 142888173568 |
| 147 | save | saved-147 | 4295491584 | 147183665152 |
| 148 | save | saved-148 | 134250496 | 147317915648 |
| 149 | save | saved-149 | 1207959552 | 148525875200 |
| 150 | save | saved-150 | 134250496 | 148660125696 |
| 151 | save | saved-151 | 135266304 | 148795392000 |
| 152 | save | saved-152 | 33816576 | 148829208576 |
| 153 | save | saved-153 | 4295491584 | 153124700160 |
| 154 | save | saved-154 | 134250496 | 153258950656 |
| 155 | save | saved-155 | 1207959552 | 154466910208 |
| 156 | save | saved-156 | 134250496 | 154601160704 |
| 157 | save | saved-157 | 135266304 | 154736427008 |
| 158 | save | saved-158 | 33816576 | 154770243584 |
| 159 | save | saved-159 | 4295491584 | 159065735168 |
| 160 | save | saved-160 | 134250496 | 159199985664 |
| 161 | save | saved-161 | 1207959552 | 160407945216 |
| 162 | save | saved-162 | 134250496 | 160542195712 |
| 163 | save | saved-163 | 135266304 | 160677462016 |
| 164 | save | saved-164 | 33816576 | 160711278592 |
| 165 | save | saved-165 | 4295491584 | 165006770176 |
| 166 | save | saved-166 | 134250496 | 165141020672 |
| 167 | save | saved-167 | 1207959552 | 166348980224 |
| 168 | save | saved-168 | 134250496 | 166483230720 |
| 169 | save | saved-169 | 135266304 | 166618497024 |
| 170 | save | saved-170 | 33816576 | 166652313600 |
| 171 | save | saved-171 | 4295491584 | 170947805184 |
| 172 | save | saved-172 | 134250496 | 171082055680 |
| 173 | save | saved-173 | 1207959552 | 172290015232 |
| 174 | save | saved-174 | 134250496 | 172424265728 |
| 175 | save | saved-175 | 135266304 | 172559532032 |
| 176 | save | saved-176 | 33816576 | 172593348608 |
| 177 | save | saved-177 | 4295491584 | 176888840192 |
| 178 | save | saved-178 | 134250496 | 177023090688 |
| 179 | save | saved-179 | 1207959552 | 178231050240 |
| 180 | save | saved-180 | 134250496 | 178365300736 |
| 181 | save | saved-181 | 135266304 | 178500567040 |
| 182 | save | saved-182 | 33816576 | 178534383616 |
| 183 | save | saved-183 | 4295491584 | 182829875200 |
| 184 | save | saved-184 | 134250496 | 182964125696 |
| 185 | save | saved-185 | 1207959552 | 184172085248 |
| 186 | save | saved-186 | 134250496 | 184306335744 |
| 187 | save | saved-187 | 135266304 | 184441602048 |
| 188 | save | saved-188 | 33816576 | 184475418624 |
| 189 | save | saved-189 | 4295491584 | 188770910208 |
| 190 | save | saved-190 | 134250496 | 188905160704 |
| 191 | save | saved-191 | 1207959552 | 190113120256 |
| 192 | save | saved-192 | 134250496 | 190247370752 |
| 193 | save | saved-193 | 135266304 | 190382637056 |
| 194 | save | saved-194 | 33816576 | 190416453632 |
| 195 | save | saved-195 | 4295491584 | 194711945216 |
| 196 | save | saved-196 | 134250496 | 194846195712 |
| 197 | save | saved-197 | 1207959552 | 196054155264 |
| 198 | save | saved-198 | 134250496 | 196188405760 |
| 199 | save | saved-199 | 135266304 | 196323672064 |
| 200 | save | saved-200 | 33816576 | 196357488640 |
| 201 | save | saved-201 | 4295491584 | 200652980224 |
| 202 | save | saved-202 | 134250496 | 200787230720 |
| 203 | save | saved-203 | 1207959552 | 201995190272 |
| 204 | save | saved-204 | 134250496 | 202129440768 |
| 205 | save | saved-205 | 135266304 | 202264707072 |
| 206 | save | saved-206 | 33816576 | 202298523648 |
| 207 | save | saved-207 | 4295491584 | 206594015232 |
| 208 | save | saved-208 | 134250496 | 206728265728 |
| 209 | save | saved-209 | 1207959552 | 207936225280 |
| 210 | save | saved-210 | 134250496 | 208070475776 |
| 211 | save | saved-211 | 135266304 | 208205742080 |
| 212 | save | saved-212 | 33816576 | 208239558656 |
| 213 | save | saved-213 | 4295491584 | 212535050240 |
| 214 | save | saved-214 | 134250496 | 212669300736 |
| 215 | save | saved-215 | 1207959552 | 213877260288 |
| 216 | save | saved-216 | 134250496 | 214011510784 |
| 217 | save | saved-217 | 4978638848 | 218990149632 |
| 218 | backward_last_use_release | saved-217 | -4978638848 | 214011510784 |
| 219 | backward_last_use_release | saved-216 | -134250496 | 213877260288 |
| 220 | backward_last_use_release | saved-215 | -1207959552 | 212669300736 |
| 221 | backward_last_use_release | saved-214 | -134250496 | 212535050240 |
| 222 | backward_last_use_release | saved-213 | -4295491584 | 208239558656 |
| 223 | backward_last_use_release | saved-212 | -33816576 | 208205742080 |
| 224 | backward_last_use_release | saved-211 | -135266304 | 208070475776 |
| 225 | backward_last_use_release | saved-210 | -134250496 | 207936225280 |
| 226 | backward_last_use_release | saved-209 | -1207959552 | 206728265728 |
| 227 | backward_last_use_release | saved-208 | -134250496 | 206594015232 |
| 228 | backward_last_use_release | saved-207 | -4295491584 | 202298523648 |
| 229 | backward_last_use_release | saved-206 | -33816576 | 202264707072 |
| 230 | backward_last_use_release | saved-205 | -135266304 | 202129440768 |
| 231 | backward_last_use_release | saved-204 | -134250496 | 201995190272 |
| 232 | backward_last_use_release | saved-203 | -1207959552 | 200787230720 |
| 233 | backward_last_use_release | saved-202 | -134250496 | 200652980224 |
| 234 | backward_last_use_release | saved-201 | -4295491584 | 196357488640 |
| 235 | backward_last_use_release | saved-200 | -33816576 | 196323672064 |
| 236 | backward_last_use_release | saved-199 | -135266304 | 196188405760 |
| 237 | backward_last_use_release | saved-198 | -134250496 | 196054155264 |
| 238 | backward_last_use_release | saved-197 | -1207959552 | 194846195712 |
| 239 | backward_last_use_release | saved-196 | -134250496 | 194711945216 |
| 240 | backward_last_use_release | saved-195 | -4295491584 | 190416453632 |
| 241 | backward_last_use_release | saved-194 | -33816576 | 190382637056 |
| 242 | backward_last_use_release | saved-193 | -135266304 | 190247370752 |
| 243 | backward_last_use_release | saved-192 | -134250496 | 190113120256 |
| 244 | backward_last_use_release | saved-191 | -1207959552 | 188905160704 |
| 245 | backward_last_use_release | saved-190 | -134250496 | 188770910208 |
| 246 | backward_last_use_release | saved-189 | -4295491584 | 184475418624 |
| 247 | backward_last_use_release | saved-188 | -33816576 | 184441602048 |
| 248 | backward_last_use_release | saved-187 | -135266304 | 184306335744 |
| 249 | backward_last_use_release | saved-186 | -134250496 | 184172085248 |
| 250 | backward_last_use_release | saved-185 | -1207959552 | 182964125696 |
| 251 | backward_last_use_release | saved-184 | -134250496 | 182829875200 |
| 252 | backward_last_use_release | saved-183 | -4295491584 | 178534383616 |
| 253 | backward_last_use_release | saved-182 | -33816576 | 178500567040 |
| 254 | backward_last_use_release | saved-181 | -135266304 | 178365300736 |
| 255 | backward_last_use_release | saved-180 | -134250496 | 178231050240 |
| 256 | backward_last_use_release | saved-179 | -1207959552 | 177023090688 |
| 257 | backward_last_use_release | saved-178 | -134250496 | 176888840192 |
| 258 | backward_last_use_release | saved-177 | -4295491584 | 172593348608 |
| 259 | backward_last_use_release | saved-176 | -33816576 | 172559532032 |
| 260 | backward_last_use_release | saved-175 | -135266304 | 172424265728 |
| 261 | backward_last_use_release | saved-174 | -134250496 | 172290015232 |
| 262 | backward_last_use_release | saved-173 | -1207959552 | 171082055680 |
| 263 | backward_last_use_release | saved-172 | -134250496 | 170947805184 |
| 264 | backward_last_use_release | saved-171 | -4295491584 | 166652313600 |
| 265 | backward_last_use_release | saved-170 | -33816576 | 166618497024 |
| 266 | backward_last_use_release | saved-169 | -135266304 | 166483230720 |
| 267 | backward_last_use_release | saved-168 | -134250496 | 166348980224 |
| 268 | backward_last_use_release | saved-167 | -1207959552 | 165141020672 |
| 269 | backward_last_use_release | saved-166 | -134250496 | 165006770176 |
| 270 | backward_last_use_release | saved-165 | -4295491584 | 160711278592 |
| 271 | backward_last_use_release | saved-164 | -33816576 | 160677462016 |
| 272 | backward_last_use_release | saved-163 | -135266304 | 160542195712 |
| 273 | backward_last_use_release | saved-162 | -134250496 | 160407945216 |
| 274 | backward_last_use_release | saved-161 | -1207959552 | 159199985664 |
| 275 | backward_last_use_release | saved-160 | -134250496 | 159065735168 |
| 276 | backward_last_use_release | saved-159 | -4295491584 | 154770243584 |
| 277 | backward_last_use_release | saved-158 | -33816576 | 154736427008 |
| 278 | backward_last_use_release | saved-157 | -135266304 | 154601160704 |
| 279 | backward_last_use_release | saved-156 | -134250496 | 154466910208 |
| 280 | backward_last_use_release | saved-155 | -1207959552 | 153258950656 |
| 281 | backward_last_use_release | saved-154 | -134250496 | 153124700160 |
| 282 | backward_last_use_release | saved-153 | -4295491584 | 148829208576 |
| 283 | backward_last_use_release | saved-152 | -33816576 | 148795392000 |
| 284 | backward_last_use_release | saved-151 | -135266304 | 148660125696 |
| 285 | backward_last_use_release | saved-150 | -134250496 | 148525875200 |
| 286 | backward_last_use_release | saved-149 | -1207959552 | 147317915648 |
| 287 | backward_last_use_release | saved-148 | -134250496 | 147183665152 |
| 288 | backward_last_use_release | saved-147 | -4295491584 | 142888173568 |
| 289 | backward_last_use_release | saved-146 | -33816576 | 142854356992 |
| 290 | backward_last_use_release | saved-145 | -135266304 | 142719090688 |
| 291 | backward_last_use_release | saved-144 | -134250496 | 142584840192 |
| 292 | backward_last_use_release | saved-143 | -1207959552 | 141376880640 |
| 293 | backward_last_use_release | saved-142 | -134250496 | 141242630144 |
| 294 | backward_last_use_release | saved-141 | -4295491584 | 136947138560 |
| 295 | backward_last_use_release | saved-140 | -33816576 | 136913321984 |
| 296 | backward_last_use_release | saved-139 | -135266304 | 136778055680 |
| 297 | backward_last_use_release | saved-138 | -134250496 | 136643805184 |
| 298 | backward_last_use_release | saved-137 | -1207959552 | 135435845632 |
| 299 | backward_last_use_release | saved-136 | -134250496 | 135301595136 |
| 300 | backward_last_use_release | saved-135 | -4295491584 | 131006103552 |
| 301 | backward_last_use_release | saved-134 | -33816576 | 130972286976 |
| 302 | backward_last_use_release | saved-133 | -135266304 | 130837020672 |
| 303 | backward_last_use_release | saved-132 | -134250496 | 130702770176 |
| 304 | backward_last_use_release | saved-131 | -1207959552 | 129494810624 |
| 305 | backward_last_use_release | saved-130 | -134250496 | 129360560128 |
| 306 | backward_last_use_release | saved-129 | -4295491584 | 125065068544 |
| 307 | backward_last_use_release | saved-128 | -33816576 | 125031251968 |
| 308 | backward_last_use_release | saved-127 | -135266304 | 124895985664 |
| 309 | backward_last_use_release | saved-126 | -134250496 | 124761735168 |
| 310 | backward_last_use_release | saved-125 | -1207959552 | 123553775616 |
| 311 | backward_last_use_release | saved-124 | -134250496 | 123419525120 |
| 312 | backward_last_use_release | saved-123 | -4295491584 | 119124033536 |
| 313 | backward_last_use_release | saved-122 | -33816576 | 119090216960 |
| 314 | backward_last_use_release | saved-121 | -135266304 | 118954950656 |
| 315 | backward_last_use_release | saved-120 | -134250496 | 118820700160 |
| 316 | backward_last_use_release | saved-119 | -1207959552 | 117612740608 |
| 317 | backward_last_use_release | saved-118 | -134250496 | 117478490112 |
| 318 | backward_last_use_release | saved-117 | -4295491584 | 113182998528 |
| 319 | backward_last_use_release | saved-116 | -33816576 | 113149181952 |
| 320 | backward_last_use_release | saved-115 | -135266304 | 113013915648 |
| 321 | backward_last_use_release | saved-114 | -134250496 | 112879665152 |
| 322 | backward_last_use_release | saved-113 | -1207959552 | 111671705600 |
| 323 | backward_last_use_release | saved-112 | -134250496 | 111537455104 |
| 324 | backward_last_use_release | saved-111 | -4295491584 | 107241963520 |
| 325 | backward_last_use_release | saved-110 | -33816576 | 107208146944 |
| 326 | backward_last_use_release | saved-109 | -135266304 | 107072880640 |
| 327 | backward_last_use_release | saved-108 | -134250496 | 106938630144 |
| 328 | backward_last_use_release | saved-107 | -1207959552 | 105730670592 |
| 329 | backward_last_use_release | saved-106 | -134250496 | 105596420096 |
| 330 | backward_last_use_release | saved-105 | -4295491584 | 101300928512 |
| 331 | backward_last_use_release | saved-104 | -33816576 | 101267111936 |
| 332 | backward_last_use_release | saved-103 | -135266304 | 101131845632 |
| 333 | backward_last_use_release | saved-102 | -134250496 | 100997595136 |
| 334 | backward_last_use_release | saved-101 | -1207959552 | 99789635584 |
| 335 | backward_last_use_release | saved-100 | -134250496 | 99655385088 |
| 336 | backward_last_use_release | saved-99 | -4295491584 | 95359893504 |
| 337 | backward_last_use_release | saved-98 | -33816576 | 95326076928 |
| 338 | backward_last_use_release | saved-97 | -135266304 | 95190810624 |
| 339 | backward_last_use_release | saved-96 | -134250496 | 95056560128 |
| 340 | backward_last_use_release | saved-95 | -1207959552 | 93848600576 |
| 341 | backward_last_use_release | saved-94 | -134250496 | 93714350080 |
| 342 | backward_last_use_release | saved-93 | -4295491584 | 89418858496 |
| 343 | backward_last_use_release | saved-92 | -33816576 | 89385041920 |
| 344 | backward_last_use_release | saved-91 | -135266304 | 89249775616 |
| 345 | backward_last_use_release | saved-90 | -134250496 | 89115525120 |
| 346 | backward_last_use_release | saved-89 | -1207959552 | 87907565568 |
| 347 | backward_last_use_release | saved-88 | -134250496 | 87773315072 |
| 348 | backward_last_use_release | saved-87 | -4295491584 | 83477823488 |
| 349 | backward_last_use_release | saved-86 | -33816576 | 83444006912 |
| 350 | backward_last_use_release | saved-85 | -135266304 | 83308740608 |
| 351 | backward_last_use_release | saved-84 | -134250496 | 83174490112 |
| 352 | backward_last_use_release | saved-83 | -1207959552 | 81966530560 |
| 353 | backward_last_use_release | saved-82 | -134250496 | 81832280064 |
| 354 | backward_last_use_release | saved-81 | -4295491584 | 77536788480 |
| 355 | backward_last_use_release | saved-80 | -33816576 | 77502971904 |
| 356 | backward_last_use_release | saved-79 | -135266304 | 77367705600 |
| 357 | backward_last_use_release | saved-78 | -134250496 | 77233455104 |
| 358 | backward_last_use_release | saved-77 | -1207959552 | 76025495552 |
| 359 | backward_last_use_release | saved-76 | -134250496 | 75891245056 |
| 360 | backward_last_use_release | saved-75 | -4295491584 | 71595753472 |
| 361 | backward_last_use_release | saved-74 | -33816576 | 71561936896 |
| 362 | backward_last_use_release | saved-73 | -135266304 | 71426670592 |
| 363 | backward_last_use_release | saved-72 | -134250496 | 71292420096 |
| 364 | backward_last_use_release | saved-71 | -1207959552 | 70084460544 |
| 365 | backward_last_use_release | saved-70 | -134250496 | 69950210048 |
| 366 | backward_last_use_release | saved-69 | -4295491584 | 65654718464 |
| 367 | backward_last_use_release | saved-68 | -33816576 | 65620901888 |
| 368 | backward_last_use_release | saved-67 | -135266304 | 65485635584 |
| 369 | backward_last_use_release | saved-66 | -134250496 | 65351385088 |
| 370 | backward_last_use_release | saved-65 | -1207959552 | 64143425536 |
| 371 | backward_last_use_release | saved-64 | -134250496 | 64009175040 |
| 372 | backward_last_use_release | saved-63 | -4295491584 | 59713683456 |
| 373 | backward_last_use_release | saved-62 | -33816576 | 59679866880 |
| 374 | backward_last_use_release | saved-61 | -135266304 | 59544600576 |
| 375 | backward_last_use_release | saved-60 | -134250496 | 59410350080 |
| 376 | backward_last_use_release | saved-59 | -1207959552 | 58202390528 |
| 377 | backward_last_use_release | saved-58 | -134250496 | 58068140032 |
| 378 | backward_last_use_release | saved-57 | -4295491584 | 53772648448 |
| 379 | backward_last_use_release | saved-56 | -33816576 | 53738831872 |
| 380 | backward_last_use_release | saved-55 | -135266304 | 53603565568 |
| 381 | backward_last_use_release | saved-54 | -134250496 | 53469315072 |
| 382 | backward_last_use_release | saved-53 | -1207959552 | 52261355520 |
| 383 | backward_last_use_release | saved-52 | -134250496 | 52127105024 |
| 384 | backward_last_use_release | saved-51 | -4295491584 | 47831613440 |
| 385 | backward_last_use_release | saved-50 | -33816576 | 47797796864 |
| 386 | backward_last_use_release | saved-49 | -135266304 | 47662530560 |
| 387 | backward_last_use_release | saved-48 | -134250496 | 47528280064 |
| 388 | backward_last_use_release | saved-47 | -1207959552 | 46320320512 |
| 389 | backward_last_use_release | saved-46 | -134250496 | 46186070016 |
| 390 | backward_last_use_release | saved-45 | -4295491584 | 41890578432 |
| 391 | backward_last_use_release | saved-44 | -33816576 | 41856761856 |
| 392 | backward_last_use_release | saved-43 | -135266304 | 41721495552 |
| 393 | backward_last_use_release | saved-42 | -134250496 | 41587245056 |
| 394 | backward_last_use_release | saved-41 | -1207959552 | 40379285504 |
| 395 | backward_last_use_release | saved-40 | -134250496 | 40245035008 |
| 396 | backward_last_use_release | saved-39 | -4295491584 | 35949543424 |
| 397 | backward_last_use_release | saved-38 | -33816576 | 35915726848 |
| 398 | backward_last_use_release | saved-37 | -135266304 | 35780460544 |
| 399 | backward_last_use_release | saved-36 | -134250496 | 35646210048 |
| 400 | backward_last_use_release | saved-35 | -1207959552 | 34438250496 |
| 401 | backward_last_use_release | saved-34 | -134250496 | 34304000000 |
| 402 | backward_last_use_release | saved-33 | -4295491584 | 30008508416 |
| 403 | backward_last_use_release | saved-32 | -33816576 | 29974691840 |
| 404 | backward_last_use_release | saved-31 | -135266304 | 29839425536 |
| 405 | backward_last_use_release | saved-30 | -134250496 | 29705175040 |
| 406 | backward_last_use_release | saved-29 | -1207959552 | 28497215488 |
| 407 | backward_last_use_release | saved-28 | -134250496 | 28362964992 |
| 408 | backward_last_use_release | saved-27 | -4295491584 | 24067473408 |
| 409 | backward_last_use_release | saved-26 | -33816576 | 24033656832 |
| 410 | backward_last_use_release | saved-25 | -135266304 | 23898390528 |
| 411 | backward_last_use_release | saved-24 | -134250496 | 23764140032 |
| 412 | backward_last_use_release | saved-23 | -1207959552 | 22556180480 |
| 413 | backward_last_use_release | saved-22 | -134250496 | 22421929984 |
| 414 | backward_last_use_release | saved-21 | -4295491584 | 18126438400 |
| 415 | backward_last_use_release | saved-20 | -33816576 | 18092621824 |
| 416 | backward_last_use_release | saved-19 | -135266304 | 17957355520 |
| 417 | backward_last_use_release | saved-18 | -134250496 | 17823105024 |
| 418 | backward_last_use_release | saved-17 | -1207959552 | 16615145472 |
| 419 | backward_last_use_release | saved-16 | -134250496 | 16480894976 |
| 420 | backward_last_use_release | saved-15 | -4295491584 | 12185403392 |
| 421 | backward_last_use_release | saved-14 | -33816576 | 12151586816 |
| 422 | backward_last_use_release | saved-13 | -135266304 | 12016320512 |
| 423 | backward_last_use_release | saved-12 | -134250496 | 11882070016 |
| 424 | backward_last_use_release | saved-11 | -1207959552 | 10674110464 |
| 425 | backward_last_use_release | saved-10 | -134250496 | 10539859968 |
| 426 | backward_last_use_release | saved-9 | -4295491584 | 6244368384 |
| 427 | backward_last_use_release | saved-8 | -33816576 | 6210551808 |
| 428 | backward_last_use_release | saved-7 | -135266304 | 6075285504 |
| 429 | backward_last_use_release | saved-6 | -134250496 | 5941035008 |
| 430 | backward_last_use_release | saved-5 | -1207959552 | 4733075456 |
| 431 | backward_last_use_release | saved-4 | -134250496 | 4598824960 |
| 432 | backward_last_use_release | saved-3 | -4295491584 | 303333376 |
| 433 | backward_last_use_release | saved-2 | -33816576 | 269516800 |
| 434 | backward_last_use_release | saved-1 | -135266304 | 134250496 |
| 435 | backward_last_use_release | saved-0 | -134250496 | 0 |

## 原矩阵与参数状态（不变）

| 原summary | 值 |
| --- | --- |
| parameters | 8190735360 |
| input_tokens | 8192 |
| loss_tokens | 8192 |
| expert_assignments_per_layer | 0 |
| active_experts_per_layer | 0 |
| executed_head_rows | 8192 |
| forward_matrix_flops | 143789331054592 |
| backward_matrix_flops | 287578662109184 |
| training_matrix_flops | 431367993163776 |
| attention_training_matrix_flops | 59380875657216 |
| six_nd_flops | 402591024414720 |
| matrix_minus_six_nd_flops | 28776968749056 |
| matrix_to_six_nd_ratio | 1.0714794096338622 |
| unsharded_parameter_state_bytes | 147433236480 |
| activation_peak_bytes | unknown |
| complete_training_step_flops | unknown |
| predicted_step_seconds | unknown |

| 矩阵 | 形状 | repeats | forward | gradient_each | training_total |
| --- | --- | --- | --- | --- | --- |
| q_proj | {"d_input_matmul": [[8192, 4096], [4096, 4096]], "d_weight_matmul": [[4096, 8192], [8192, 4096]], "input": [8192, 4096], "output": [8192, 4096], "weight_storage": [4096, 4096]} | 36 | 274877906944 | 274877906944 | 29686813949952 |
| k_proj | {"d_input_matmul": [[8192, 1024], [1024, 4096]], "d_weight_matmul": [[1024, 8192], [8192, 4096]], "input": [8192, 4096], "output": [8192, 1024], "weight_storage": [1024, 4096]} | 36 | 68719476736 | 68719476736 | 7421703487488 |
| v_proj | {"d_input_matmul": [[8192, 1024], [1024, 4096]], "d_weight_matmul": [[1024, 8192], [8192, 4096]], "input": [8192, 4096], "output": [8192, 1024], "weight_storage": [1024, 4096]} | 36 | 68719476736 | 68719476736 | 7421703487488 |
| qk | {"K_shared": [1, 8, 8192, 128], "Q": [1, 32, 8192, 128], "scores_rectangular": [1, 32, 8192, 8192]} | 36 | 274911461376 | 274911461376 | 29690437828608 |
| pv | {"P": [1, 32, 8192, 8192], "V_shared": [1, 8, 8192, 128], "output": [1, 32, 8192, 128]} | 36 | 274911461376 | 274911461376 | 29690437828608 |
| o_proj | {"d_input_matmul": [[8192, 4096], [4096, 4096]], "d_weight_matmul": [[4096, 8192], [8192, 4096]], "input": [8192, 4096], "output": [8192, 4096], "weight_storage": [4096, 4096]} | 36 | 274877906944 | 274877906944 | 29686813949952 |
| gate_proj | {"d_input_matmul": [[8192, 12288], [12288, 4096]], "d_weight_matmul": [[12288, 8192], [8192, 4096]], "input": [8192, 4096], "output": [8192, 12288], "weight_storage": [12288, 4096]} | 36 | 824633720832 | 824633720832 | 89060441849856 |
| up_proj | {"d_input_matmul": [[8192, 12288], [12288, 4096]], "d_weight_matmul": [[12288, 8192], [8192, 4096]], "input": [8192, 4096], "output": [8192, 12288], "weight_storage": [12288, 4096]} | 36 | 824633720832 | 824633720832 | 89060441849856 |
| down_proj | {"d_input_matmul": [[8192, 4096], [4096, 12288]], "d_weight_matmul": [[4096, 8192], [8192, 12288]], "input": [8192, 12288], "output": [8192, 4096], "weight_storage": [4096, 12288]} | 36 | 824633720832 | 824633720832 | 89060441849856 |
| lm_head | {"d_input_matmul": [[8192, 151936], [151936, 4096]], "d_weight_matmul": [[151936, 8192], [8192, 4096]], "input": [8192, 4096], "output": [8192, 151936], "weight_storage": [151936, 4096]} | 1 | 10196252360704 | 10196252360704 | 30588757082112 |

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
