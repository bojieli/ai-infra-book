# deepseek-v4-flash：顺序前缀延续

已知后缀逐 token 执行完整基础 forward；不是并行 cached chunk。所有数值沿 JSON 的声明口径，无实际 HBM 或延迟推断。

## 请求与源分配条件

| 输入 | 值 |
| --- | --- |
| model | deepseek-v4-flash |
| prefix_tokens | 127 |
| new_tokens | 2 |
| batch | 3 |
| routing | balanced |
| counts | unknown |
| allocated_max_seq_len | 129 |
| allocated_max_batch_size | 3 |

源 ModelArgs 默认 max_seq_len=4096/max_batch_size=4；此场景明确覆盖分配参数。完整前缀快照必须包含 window 环形布局、压缩/index cache、FP32 kv/score 槽和重叠 carry。

| 源分配字段 | 值 |
| --- | --- |
| max_seq_len | 129 |
| max_batch_size | 3 |
| bf16_history_and_fp32_compressor_bytes | 56168448 |
| scope | Full reference cache/compressor buffers only; frequency tables, weights and other temporaries excluded |

| 固定执行方式 | 值 |
| --- | --- |
| output_head | each sequential call |
| parallel_cached_chunk | False |

## 汇总

| 指标 | 值 |
| --- | --- |
| matrix_flops_effective_attention | 164157456384 |
| matrix_flops_with_reference_sparse_and_expert_tiles | 2580991967232 |
| accounted_scalar_flops | 3910961979 |
| vocabulary_head_matrix_flops | 6354370560 |
| forward_calls | 2 |
| vocabulary_head_calls | 2 |
| useful_final_vocabulary_heads | 1 |
| discarded_intermediate_vocabulary_heads | 1 |
| initial_state_resident_bytes | 55894272 |
| final_state_resident_bytes | 56168448 |
| state_growth_bytes | 274176 |
| complete_hbm_traffic_bytes | unknown |
| complete_runtime_resident_bytes | unknown |
| complete_scalar_flops | unknown |
| predicted_latency_seconds | unknown |

## 全段特殊调用与非 FLOPs 操作

名称表示各自运算/候选/编码/比较次数，不能作为统一 Tensor FLOPs 相加。

| 操作 | 次数 |
| --- | --- |
| rsqrt | 18258 |
| abs | 1210944 |
| amax_compare | 1175769 |
| scale_floor_compare | 35175 |
| clamp_bound_compare | 2421888 |
| power_of_two_scale_bit_round | 35175 |
| fp8_encode | 170688 |
| fp8_decode | 170688 |
| exp | 7449408 |
| compare_max | 7311024 |
| fp4_encode | 1040256 |
| fp4_decode | 1040256 |
| relu_compare | 258048 |
| topk_rows | 366 |
| topk_candidates | 65472 |
| softplus | 66048 |
| sqrt | 66048 |
| integer_lookup_entries | 108 |
| silu | 3698688 |
| clamp_bound_comparisons | 11096064 |
| sigmoid | 4152 |

## 已知接口总量

各字段单位为 bytes。uniform BF16 专家列与 routed actual packed+scale 是替代口径，不得相加。gather 包含当前可见记录；FP32 slot/roll、状态增长和最终驻留均是不同量。

| 接口字段 | bytes |
| --- | --- |
| gathered_kv_bytes | 38068224 |
| query_read_bytes | 16908288 |
| output_write_bytes | 16908288 |
| index_read_bytes | 148704 |
| sink_read_bytes | 66048 |
| embedding_lookup_payload_bytes | 49152 |
| attention_uniform_bf16_matrix_weight_payload_bytes | 20339228672 |
| expert_uniform_bf16_matrix_weight_payload_bytes | 82422267904 |
| routed_expert_actual_packed_and_scale_payload_bytes | 20695744512 |
| hc_fp32_parameter_payload_bytes | 271075512 |
| vocabulary_head_uniform_bf16_weight_payload_bytes | 2118123520 |
| window_slot_write_bytes | 264192 |
| completed_cache_entry_write_bytes | 142080 |
| index_scan_payload_bytes | 1032192 |
| compressor_fp32_slot_write_bytes | 1781760 |
| overlap_roll_fp32_read_bytes | 2580480 |
| overlap_roll_fp32_write_bytes | 2580480 |

## 静态每调用分区与基础权重

| 分区 | 值 |
| --- | --- |
| matrix_flops_per_call | 49100488704 |
| matrix_flops_with_known_tiles_per_call | 1256758050816 |
| scalar_flops_per_call | 1900084011 |
| special_ops_per_call | {"abs": 0, "amax_compare": 0, "clamp_bound_compare": 0, "clamp_bound_comparisons": 5548032, "compare_max": 3096, "exp": 4128, "fp4_decode": 0, "fp4_encode": 0, "fp8_decode": 0, "fp8_encode": 0, "integer_lookup_entries": 54, "power_of_two_scale_bit_round": 0, "relu_compare": 0, "rsqrt": 522, "scale_floor_compare": 0, "sigmoid": 2076, "silu": 1849344, "softplus": 33024, "sqrt": 33024, "topk_candidates": 30720, "topk_rows": 120} |

静态分区每一步都执行，checkpoint 只解析一次。以下保留完整基础参数分项，未把基础 checkpoint 载荷当运行时实际常驻。

| 基础参数分项 | 参数数 |
| --- | --- |
| attention_matrices | 5084807168 |
| expert_matrices_including_router_shared | 278152609792 |
| hyper_connections | 33884439 |
| embedding | 529530880 |
| vocabulary_head | 529530880 |
| external_norms | 356352 |
| attention_q_lowrank_and_kv_norm | 66048 |
| attention_sinks | 2752 |
| compressor_norms | 23680 |
| compressor_ape | 1418240 |
| router_bias | 10240 |

## 压缩完成边界

位置均为处理后的 end_position=input_position+1。列表完整，无省略。

| ratio | 完成次数 | 全部结束位置 |
| --- | --- | --- |
| 4 | 1 | [128] |
| 128 | 1 | [128] |

## 初始与最终有效状态


### 初始

| summary 字段 | 值 |
| --- | --- |
| history_resident_bytes | 19276032 |
| compressor_buffer_bytes | 36618240 |
| resident_bytes | 55894272 |
| selected_history_payload_bytes | 19276032 |

| component 字段 | 值 |
| --- | --- |
| window_history_bytes | 16776192 |
| compressed_history_bytes | 1999872 |
| index_history_bytes | 499968 |
| main_compressor_buffer_bytes | 35586048 |
| index_compressor_buffer_bytes | 1032192 |
| main_selected_payload_bytes | 18776064 |
| index_scan_payload_bytes | 499968 |
| last_query_main_qk_pv_flops | 2403336192 |
| last_query_index_dot_flops | 31997952 |
| next_token_window_write_bytes | 132096 |
| next_token_completed_entry_write_bytes | 142080 |

| layer | kind | ratio | window_history_bytes | compressed_history_bytes | index_history_bytes | main_compressor_buffer_bytes | index_compressor_buffer_bytes | main_selected_payload_bytes | index_scan_payload_bytes | last_query_main_qk_pv_flops | last_query_index_dot_flops | next_token_window_write_bytes | next_token_completed_entry_write_bytes | next_token_completes_compression |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | window | 0 | 390144 | 0 | 0 | 0 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 0 | False |
| 1 | window | 0 | 390144 | 0 | 0 | 0 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 0 | False |
| 2 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 3 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 4 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 5 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 6 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 7 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 8 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 9 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 10 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 11 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 12 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 13 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 14 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 15 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 16 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 17 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 18 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 19 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 20 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 21 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 22 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 23 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 24 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 25 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 26 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 27 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 28 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 29 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 30 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 31 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 32 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 33 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 34 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 35 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 36 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 37 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 38 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 39 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 40 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |
| 41 | HCA | 128 | 390144 | 0 | 0 | 1572864 | 0 | 390144 | 0 | 49938432 | 0 | 3072 | 3072 | True |
| 42 | CSA | 4 | 390144 | 95232 | 23808 | 196608 | 49152 | 485376 | 23808 | 62128128 | 1523712 | 3072 | 3840 | True |

### 最终

| summary 字段 | 值 |
| --- | --- |
| history_resident_bytes | 19550208 |
| compressor_buffer_bytes | 36618240 |
| resident_bytes | 56168448 |
| selected_history_payload_bytes | 19550208 |

| component 字段 | 值 |
| --- | --- |
| window_history_bytes | 16908288 |
| compressed_history_bytes | 2125824 |
| index_history_bytes | 516096 |
| main_compressor_buffer_bytes | 35586048 |
| index_compressor_buffer_bytes | 1032192 |
| main_selected_payload_bytes | 19034112 |
| index_scan_payload_bytes | 516096 |
| last_query_main_qk_pv_flops | 2436366336 |
| last_query_index_dot_flops | 33030144 |
| next_token_window_write_bytes | 132096 |
| next_token_completed_entry_write_bytes | 0 |

| layer | kind | ratio | window_history_bytes | compressed_history_bytes | index_history_bytes | main_compressor_buffer_bytes | index_compressor_buffer_bytes | main_selected_payload_bytes | index_scan_payload_bytes | last_query_main_qk_pv_flops | last_query_index_dot_flops | next_token_window_write_bytes | next_token_completed_entry_write_bytes | next_token_completes_compression |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | window | 0 | 393216 | 0 | 0 | 0 | 0 | 393216 | 0 | 50331648 | 0 | 3072 | 0 | False |
| 1 | window | 0 | 393216 | 0 | 0 | 0 | 0 | 393216 | 0 | 50331648 | 0 | 3072 | 0 | False |
| 2 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 3 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 4 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 5 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 6 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 7 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 8 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 9 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 10 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 11 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 12 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 13 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 14 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 15 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 16 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 17 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 18 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 19 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 20 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 21 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 22 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 23 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 24 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 25 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 26 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 27 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 28 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 29 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 30 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 31 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 32 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 33 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 34 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 35 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 36 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 37 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 38 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 39 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 40 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |
| 41 | HCA | 128 | 393216 | 3072 | 0 | 1572864 | 0 | 396288 | 0 | 50724864 | 0 | 3072 | 0 | False |
| 42 | CSA | 4 | 393216 | 98304 | 24576 | 196608 | 49152 | 491520 | 24576 | 62914560 | 1572864 | 3072 | 0 | False |

## 每一步工作与状态

special/interface ID 指向下方完整字典；相同向量复用 ID，逐步映射和所有字段保留。矩阵/scalar 单位 FLOPs，状态单位 bytes。

| step | 输入位置 | 结束位置 | 完成ratio | 有效矩阵 | 已知tile矩阵 | 已计scalar | 末状态bytes | 特殊操作ID | 接口ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 127 | 128 | [4, 128] | 82078728192 | 1290495983616 | 1966302759 | 56168448 | special-0 | interface-0 |
| 1 | 128 | 129 | [] | 82078728192 | 1290495983616 | 1944659220 | 56168448 | special-1 | interface-1 |

## special 完整向量定义

| ID | 操作/字段 | 次数 |
| --- | --- | --- |
| special-0 | rsqrt | 9222 |
| special-0 | abs | 637056 |
| special-0 | amax_compare | 618912 |
| special-0 | scale_floor_compare | 18144 |
| special-0 | clamp_bound_compare | 1274112 |
| special-0 | power_of_two_scale_bit_round | 18144 |
| special-0 | fp8_encode | 112896 |
| special-0 | fp8_decode | 112896 |
| special-0 | exp | 5852064 |
| special-0 | compare_max | 5747352 |
| special-0 | fp4_encode | 524160 |
| special-0 | fp4_decode | 524160 |
| special-0 | relu_compare | 129024 |
| special-0 | topk_rows | 183 |
| special-0 | topk_candidates | 32736 |
| special-0 | softplus | 33024 |
| special-0 | sqrt | 33024 |
| special-0 | integer_lookup_entries | 54 |
| special-0 | silu | 1849344 |
| special-0 | clamp_bound_comparisons | 5548032 |
| special-0 | sigmoid | 2076 |
| special-1 | rsqrt | 9036 |
| special-1 | abs | 573888 |
| special-1 | amax_compare | 556857 |
| special-1 | scale_floor_compare | 17031 |
| special-1 | clamp_bound_compare | 1147776 |
| special-1 | power_of_two_scale_bit_round | 17031 |
| special-1 | fp8_encode | 57792 |
| special-1 | fp8_decode | 57792 |
| special-1 | exp | 1597344 |
| special-1 | compare_max | 1563672 |
| special-1 | fp4_encode | 516096 |
| special-1 | fp4_decode | 516096 |
| special-1 | relu_compare | 129024 |
| special-1 | topk_rows | 183 |
| special-1 | topk_candidates | 32736 |
| special-1 | softplus | 33024 |
| special-1 | sqrt | 33024 |
| special-1 | integer_lookup_entries | 54 |
| special-1 | silu | 1849344 |
| special-1 | clamp_bound_comparisons | 5548032 |
| special-1 | sigmoid | 2076 |

## interface 完整向量定义

| ID | 操作/字段 | bytes |
| --- | --- | --- |
| interface-0 | gathered_kv_bytes | 19034112 |
| interface-0 | query_read_bytes | 8454144 |
| interface-0 | output_write_bytes | 8454144 |
| interface-0 | index_read_bytes | 74352 |
| interface-0 | sink_read_bytes | 33024 |
| interface-0 | embedding_lookup_payload_bytes | 24576 |
| interface-0 | attention_uniform_bf16_matrix_weight_payload_bytes | 10169614336 |
| interface-0 | expert_uniform_bf16_matrix_weight_payload_bytes | 41211133952 |
| interface-0 | routed_expert_actual_packed_and_scale_payload_bytes | 10347872256 |
| interface-0 | hc_fp32_parameter_payload_bytes | 135537756 |
| interface-0 | vocabulary_head_uniform_bf16_weight_payload_bytes | 1059061760 |
| interface-0 | window_slot_write_bytes | 132096 |
| interface-0 | completed_cache_entry_write_bytes | 142080 |
| interface-0 | index_scan_payload_bytes | 516096 |
| interface-0 | compressor_fp32_slot_write_bytes | 890880 |
| interface-0 | overlap_roll_fp32_read_bytes | 2580480 |
| interface-0 | overlap_roll_fp32_write_bytes | 2580480 |
| interface-1 | gathered_kv_bytes | 19034112 |
| interface-1 | query_read_bytes | 8454144 |
| interface-1 | output_write_bytes | 8454144 |
| interface-1 | index_read_bytes | 74352 |
| interface-1 | sink_read_bytes | 33024 |
| interface-1 | embedding_lookup_payload_bytes | 24576 |
| interface-1 | attention_uniform_bf16_matrix_weight_payload_bytes | 10169614336 |
| interface-1 | expert_uniform_bf16_matrix_weight_payload_bytes | 41211133952 |
| interface-1 | routed_expert_actual_packed_and_scale_payload_bytes | 10347872256 |
| interface-1 | hc_fp32_parameter_payload_bytes | 135537756 |
| interface-1 | vocabulary_head_uniform_bf16_weight_payload_bytes | 1059061760 |
| interface-1 | window_slot_write_bytes | 132096 |
| interface-1 | completed_cache_entry_write_bytes | 0 |
| interface-1 | index_scan_payload_bytes | 516096 |
| interface-1 | compressor_fp32_slot_write_bytes | 890880 |
| interface-1 | overlap_roll_fp32_read_bytes | 0 |
| interface-1 | overlap_roll_fp32_write_bytes | 0 |

## 覆盖范围与 unknown

| 字段 | 值 |
| --- | --- |
| full_base_matrix_graph | True |
| parallel_cached_chunk | False |

- FP8 projection/shared-expert activation quantization and scale application
- runtime conversions/aliases and resident allocations beyond checkpoint storage
- all remaining source copies/casts, frequency precomputation and allocator/backend bookkeeping
- compiled tile work for projection GEMMs, device feasibility and measured traffic
- MTP separate forward; parallel multi-token cached-prefix execution remains unsupported
- prefix snapshot creation/lookup/transfer/restoration work
- actual token-dependent expert histogram: declared per-step fixture only
- complete source data movement, transient allocation and physical runtime traffic

## 假设

- Declared max_seq_len/max_batch_size override ModelArgs defaults (4096/4) as needed; the default book request explicitly budgets allocation to 8192/1. Sufficient allocation and device capacity must be established before source execution.
- Prefix state must already be materialized at the exact boundary, including window ring layout, compressed/index caches, FP32 compressor kv/score slots and overlap carry. Prefix length alone cannot reconstruct it.
- Known suffix input tokens run one at a time at positions prefix..prefix+new_tokens-1; no generated-token sampling or parallel chunk claim. All layers and head execute each call as in the pinned base Transformer.forward.
- Each intermediate vocabulary head is real reference work even though its logits are discarded. The final head can supply the first future output token; that subsequent output generation is not included.
- Routing histogram and dtype/tile assumptions are identical on every step, expressly a workload fixture. Real hash/scoring routing can differ across input tokens and requires recorded per-step counts for exact expert reuse.
- Dynamic attention includes compressor boundaries and changing scan lengths; expert/mHC/external norm/head work is reused as a per-call static budget, not treated as zero. Checkpoint parsing occurs once.
- Uniform BF16 matrix weight columns are comparison-format reads; routed actual packed+scale is an alternative subset, not additive with the uniform expert column. Norm-vector and all runtime conversions are not a complete weight-read ledger.
- Known interface columns belong to distinct semantic operations; gathered KV includes currently visible entries, not only prior history. Do not call their sum HBM or subtract it from final state.
- FP32 compressor slots and BF16 reference cache are retained-state accounting, not actual FP8/FP4 resident cache, maximum preallocation or allocator peak. State growth excludes overwrite writes.
- Existing base-forward partial scalar/format coverage is preserved; this continuation schedule does not magically close its unknown fields.

## 固定来源

| 来源记录 | 值 |
| --- | --- |
| 0 | {"file": "configs/models/deepseek-v4-flash/config.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "b628e63398a645abc711d92207f8737dd8140f7a4ef1e0a5b3616019e0ddd818", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/config.json"} |
| 1 | {"file": "configs/models/deepseek-v4-flash/inference/config.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "6cc6f816ca73a8d38750194e330398e4f6955b4b45f674f7d29c96da14ccb733", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/inference/config.json"} |
| 2 | {"file": "sources/deepseek-v4-flash/inference/model.py", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "ce962f1face79d4f633d36436576214057a7e11443c9789935e1deb5c6cd1d71", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/inference/model.py"} |
| 3 | {"file": "sources/deepseek-v4-flash/inference/kernel.py", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "59b325083d7103975cba025bd0d60ea343bb82d8fff53088afb7c04bd380c0c2", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/inference/kernel.py"} |
| 4 | {"file": "sources/fast-hadamard-transform/README.md", "revision": "e7706faf8d1c3b9f241e36860640ad1dac644ede", "sha256": "e9d1a782e751104628590c481ba325bc436292254aaefe4cfa39ee3c0b1eb00e", "url": "https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/README.md"} |
| 5 | {"file": "sources/fast-hadamard-transform/csrc/fast_hadamard_transform_common.h", "revision": "e7706faf8d1c3b9f241e36860640ad1dac644ede", "sha256": "e51345eb6be7b43cb657d73b8db9b2debcb4060de2266c7b42fc45bb3b86b473", "url": "https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/csrc/fast_hadamard_transform_common.h"} |
| 6 | {"file": "sources/fast-hadamard-transform/fast_hadamard_transform/fast_hadamard_transform_interface.py", "revision": "e7706faf8d1c3b9f241e36860640ad1dac644ede", "sha256": "a2f32a615b03c83d075fd49eba266c9f6c13df790cbe549db3bf8c0c1f3e8877", "url": "https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/fast_hadamard_transform/fast_hadamard_transform_interface.py"} |
| 7 | {"file": "sources/deepseek-v4-flash/model.safetensors.index.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "7e975ba3bef8947a94e7da0abd60888375b232b4dfad883d59653e65c6ba522a", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model.safetensors.index.json"} |
| 8 | {"file": "sources/deepseek-v4-flash/headers/model-00001-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "7bdd252c75d1e8975a69b8399b226f0129ce119b23da7bd68deac4ba4b1a4a40", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00001-of-00046.safetensors?header=1"} |
| 9 | {"file": "sources/deepseek-v4-flash/headers/model-00002-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "adbe0338649aec4a8099bd12e7f99b18b3497f73b38345f84ecb1c46eca9d992", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00002-of-00046.safetensors?header=1"} |
| 10 | {"file": "sources/deepseek-v4-flash/headers/model-00003-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "066ac29abaa9071fd8af1166d76c411844336d778eea985781354b0a651bfd5f", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00003-of-00046.safetensors?header=1"} |
| 11 | {"file": "sources/deepseek-v4-flash/headers/model-00004-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "739266275c9abeafe21fcf8def381588c2a556bae0206d42659789ab603c997e", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00004-of-00046.safetensors?header=1"} |
| 12 | {"file": "sources/deepseek-v4-flash/headers/model-00005-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "00bf95ba015a6cb4f02c3bd6bab53b2bf12def11ed1201ac8e6b4e8e380299bb", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00005-of-00046.safetensors?header=1"} |
| 13 | {"file": "sources/deepseek-v4-flash/headers/model-00006-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "c3fdf86122ab5d53a8c4d08eba13aaf8063e87cc475dc67072cb7a88106c6eac", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00006-of-00046.safetensors?header=1"} |
| 14 | {"file": "sources/deepseek-v4-flash/headers/model-00007-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "2bb96fe9673587075839f4f38a6758a00c655d1386d93937ecb31a8fae7aa4e4", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00007-of-00046.safetensors?header=1"} |
| 15 | {"file": "sources/deepseek-v4-flash/headers/model-00008-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "0f2cd169dd987424c04f4c04090b72f8ad780e1069fb9a49fd29340434bc0db7", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00008-of-00046.safetensors?header=1"} |
| 16 | {"file": "sources/deepseek-v4-flash/headers/model-00009-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "c42b8df2eb4810f731edf8a646f61ba54226f66de484faa12df306e2bfbc18df", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00009-of-00046.safetensors?header=1"} |
| 17 | {"file": "sources/deepseek-v4-flash/headers/model-00010-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "4ddfce5b94da6cf104f0c569357107d75466f57896eea5913f14bf2d9d669df8", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00010-of-00046.safetensors?header=1"} |
| 18 | {"file": "sources/deepseek-v4-flash/headers/model-00011-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "a166d9008aebc86ffa5292305b5cd47b0ebfab13e59d2e9727bdff64f2273cf6", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00011-of-00046.safetensors?header=1"} |
| 19 | {"file": "sources/deepseek-v4-flash/headers/model-00012-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "817002743a975c90a12ba1305d7a1cb31e2c1e3aee54fe7ecb1c01f052ace3c8", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00012-of-00046.safetensors?header=1"} |
| 20 | {"file": "sources/deepseek-v4-flash/headers/model-00013-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "d2ca46ad597b90fbf32413a3f722a20d965500556d18c1a8c3d7fd362e7162d0", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00013-of-00046.safetensors?header=1"} |
| 21 | {"file": "sources/deepseek-v4-flash/headers/model-00014-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "96a3457df88bcb76bd021b88abc4affa414a7337959ba53483474a8dc3c87325", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00014-of-00046.safetensors?header=1"} |
| 22 | {"file": "sources/deepseek-v4-flash/headers/model-00015-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "cf8bce7b372e692d908185249a2f2405432b21f7e7d209fa701d13934e599ad0", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00015-of-00046.safetensors?header=1"} |
| 23 | {"file": "sources/deepseek-v4-flash/headers/model-00016-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "758a06cf96357bcc35172bb569673cf3da9a49a7b7c0196d700734fe3ed6ceef", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00016-of-00046.safetensors?header=1"} |
| 24 | {"file": "sources/deepseek-v4-flash/headers/model-00017-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "bef71dd20ade402de29a55026e7ca4239286c1e17767a5a06a6985888ad00b77", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00017-of-00046.safetensors?header=1"} |
| 25 | {"file": "sources/deepseek-v4-flash/headers/model-00018-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "d752870f40b3db91c87e95dd9e4264ea1df5cad65d48365d1559d62bf6074b57", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00018-of-00046.safetensors?header=1"} |
| 26 | {"file": "sources/deepseek-v4-flash/headers/model-00019-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "9c59b39cf7e4411fd6be6cef6be84d9505479e7c74cd6a6aed31e4acbbbfe4db", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00019-of-00046.safetensors?header=1"} |
| 27 | {"file": "sources/deepseek-v4-flash/headers/model-00020-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "b78c94a19d78e815a59e381c070f9bb71c80afca32fb65b8cf3ddd4869f76a40", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00020-of-00046.safetensors?header=1"} |
| 28 | {"file": "sources/deepseek-v4-flash/headers/model-00021-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "f4eae632cce4ebb4c7d6604a26b4404bbe0ed780b85309d370789901773f8865", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00021-of-00046.safetensors?header=1"} |
| 29 | {"file": "sources/deepseek-v4-flash/headers/model-00022-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "e51e7f6ee11a7398e16082d2c821302cafb272a0f6760b848eba4457ed33091e", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00022-of-00046.safetensors?header=1"} |
| 30 | {"file": "sources/deepseek-v4-flash/headers/model-00023-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "c834cc39b1bfab2222a6e61d61cd897012694f46b395cbb8c5dcee273667e875", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00023-of-00046.safetensors?header=1"} |
| 31 | {"file": "sources/deepseek-v4-flash/headers/model-00024-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "bce06d093a55e7549d1c7828dde524d0274e08fd2b0906459b5df8311a728344", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00024-of-00046.safetensors?header=1"} |
| 32 | {"file": "sources/deepseek-v4-flash/headers/model-00025-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "bcd896440e657458ffc1a03748c740c8da52d6a8792279d96a1aa30785ee0211", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00025-of-00046.safetensors?header=1"} |
| 33 | {"file": "sources/deepseek-v4-flash/headers/model-00026-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "a8ccf8bfe0299db51fe7ba2a372be4e8b216b8e757e1f28376aeabe520f79b71", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00026-of-00046.safetensors?header=1"} |
| 34 | {"file": "sources/deepseek-v4-flash/headers/model-00027-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "9761e7cdccbac4388df634eeb6135335742fb57c0a2291b49545d5846dc5d59c", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00027-of-00046.safetensors?header=1"} |
| 35 | {"file": "sources/deepseek-v4-flash/headers/model-00028-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "ed35c3458805563571cc084014f95b1b520ddb2f720dc7be313fb36e85c2b631", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00028-of-00046.safetensors?header=1"} |
| 36 | {"file": "sources/deepseek-v4-flash/headers/model-00029-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "df0037d7d7b0c8c3533ba7d8017b080ba628141ceb432046c18b7b80c7641ee8", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00029-of-00046.safetensors?header=1"} |
| 37 | {"file": "sources/deepseek-v4-flash/headers/model-00030-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "f10b48bae9465a0ecf009b78e2602988dcce8f11efcb8ecf39be8eb60c3de41c", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00030-of-00046.safetensors?header=1"} |
| 38 | {"file": "sources/deepseek-v4-flash/headers/model-00031-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "5b9ba12c0356d38bb4be66ef38feed3f7dd5ae558e39e8da6190396bba2bb129", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00031-of-00046.safetensors?header=1"} |
| 39 | {"file": "sources/deepseek-v4-flash/headers/model-00032-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "03874e0e912e3639adea07b51aeafe9ab3eb84d5715defbace83a6ed0a002a95", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00032-of-00046.safetensors?header=1"} |
| 40 | {"file": "sources/deepseek-v4-flash/headers/model-00033-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "13ef931a9fcd6bca4ffabdbbeccefbb7b4fa014facde32eeaeeb6e3bed6453ce", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00033-of-00046.safetensors?header=1"} |
| 41 | {"file": "sources/deepseek-v4-flash/headers/model-00034-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "61c718832c85e4673c46a50b910e0c9ea0aeadd9f12a7131f1f40157d020c6de", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00034-of-00046.safetensors?header=1"} |
| 42 | {"file": "sources/deepseek-v4-flash/headers/model-00035-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "22a3adf08b435595c3862f5289bf2797ff7157258c7cfa24ff1b0313aeae8bd0", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00035-of-00046.safetensors?header=1"} |
| 43 | {"file": "sources/deepseek-v4-flash/headers/model-00036-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "359e010953a51169166f7140842b149e9f236c942cb99b2dc6082d7961011e16", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00036-of-00046.safetensors?header=1"} |
| 44 | {"file": "sources/deepseek-v4-flash/headers/model-00037-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "8b228cfe5f5f6d5f5834046d5f7cd0045410b6f20048adf533170e3d23071b9a", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00037-of-00046.safetensors?header=1"} |
| 45 | {"file": "sources/deepseek-v4-flash/headers/model-00038-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "deff29eb762eae6765766f6f2b1888cd7f627effd297bc4675d150d55171c425", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00038-of-00046.safetensors?header=1"} |
| 46 | {"file": "sources/deepseek-v4-flash/headers/model-00039-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "44b9d5cec4550fd656c9da02bd51fde182812350601b9415e05210efe16b23bd", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00039-of-00046.safetensors?header=1"} |
| 47 | {"file": "sources/deepseek-v4-flash/headers/model-00040-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "9f4e9b51b358e7f49827305e1b2e8fd1bffcb27567aebee96b5382a58a5a76a8", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00040-of-00046.safetensors?header=1"} |
| 48 | {"file": "sources/deepseek-v4-flash/headers/model-00041-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "3cbe8dd9615eb0f1579a0bf83ab8885859348eaab555ce1fa43453fe78a9d3da", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00041-of-00046.safetensors?header=1"} |
| 49 | {"file": "sources/deepseek-v4-flash/headers/model-00042-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "590483059c64c03a3c140b8a4c692441bda09e1c8d3c8a50e0f3b9e5bdb6569d", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00042-of-00046.safetensors?header=1"} |
| 50 | {"file": "sources/deepseek-v4-flash/headers/model-00043-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "da9f9b7994e40f1b7e34416856e3f0927884cc5adf6ded630a4ce1cfb576fb82", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00043-of-00046.safetensors?header=1"} |
| 51 | {"file": "sources/deepseek-v4-flash/headers/model-00044-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "a95f8067ab7db45ecb0118b4207aa68ed1b270c41e23849b48244c1d78799396", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00044-of-00046.safetensors?header=1"} |
| 52 | {"file": "sources/deepseek-v4-flash/headers/model-00045-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "76d10bb3b022bad26446539ebaf16c9245fdcf835b28fd55a75052e0b0bb60b8", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00045-of-00046.safetensors?header=1"} |
| 53 | {"file": "sources/deepseek-v4-flash/headers/model-00046-of-00046.safetensors.json", "revision": "60d8d70770c6776ff598c94bb586a859a38244f1", "sha256": "10f90b036e608fabcf2c781dd5274a0fbc262f7aeaf959218ff1ccb829903981", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00046-of-00046.safetensors?header=1"} |
