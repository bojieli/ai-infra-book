# deepseek-v4-pro：顺序前缀延续

已知后缀逐 token 执行完整基础 forward；不是并行 cached chunk。所有数值沿 JSON 的声明口径，无实际 HBM 或延迟推断。

## 请求与源分配条件

| 输入 | 值 |
| --- | --- |
| model | deepseek-v4-pro |
| prefix_tokens | 125 |
| new_tokens | 5 |
| batch | 1 |
| routing | balanced |
| counts | unknown |
| allocated_max_seq_len | 130 |
| allocated_max_batch_size | 1 |

源 ModelArgs 默认 max_seq_len=4096/max_batch_size=4；此场景明确覆盖分配参数。完整前缀快照必须包含 window 环形布局、压缩/index cache、FP32 kv/score 槽和重叠 carry。

| 源分配字段 | 值 |
| --- | --- |
| max_seq_len | 130 |
| max_batch_size | 1 |
| bf16_history_and_fp32_compressor_bytes | 27966464 |
| scope | Full reference cache/compressor buffers only; frequency tables, weights and other temporaries excluded |

| 固定执行方式 | 值 |
| --- | --- |
| output_head | each sequential call |
| parallel_cached_chunk | False |

## 汇总

| 指标 | 值 |
| --- | --- |
| matrix_flops_effective_attention | 500022149120 |
| matrix_flops_with_reference_sparse_and_expert_tiles | 7998080319488 |
| accounted_scalar_flops | 11836614594 |
| vocabulary_head_matrix_flops | 9266790400 |
| forward_calls | 5 |
| vocabulary_head_calls | 5 |
| useful_final_vocabulary_heads | 1 |
| discarded_intermediate_vocabulary_heads | 4 |
| initial_state_resident_bytes | 27708928 |
| final_state_resident_bytes | 27966464 |
| state_growth_bytes | 257536 |
| complete_hbm_traffic_bytes | unknown |
| complete_runtime_resident_bytes | unknown |
| complete_scalar_flops | unknown |
| predicted_latency_seconds | unknown |

## 全段特殊调用与非 FLOPs 操作

名称表示各自运算/候选/编码/比较次数，不能作为统一 Tensor FLOPs 相加。

| 操作 | 次数 |
| --- | --- |
| rsqrt | 40971 |
| abs | 1396608 |
| amax_compare | 1355526 |
| scale_floor_compare | 41082 |
| clamp_bound_compare | 2793216 |
| power_of_two_scale_bit_round | 41082 |
| fp8_encode | 163968 |
| fp8_decode | 163968 |
| exp | 9330976 |
| compare_max | 9145240 |
| fp4_encode | 1232640 |
| fp4_decode | 1232640 |
| relu_compare | 303360 |
| topk_rows | 440 |
| topk_candidates | 116100 |
| softplus | 117120 |
| sqrt | 117120 |
| integer_lookup_entries | 90 |
| silu | 6558720 |
| clamp_bound_comparisons | 19676160 |
| sigmoid | 4900 |

## 已知接口总量

各字段单位为 bytes。uniform BF16 专家列与 routed actual packed+scale 是替代口径，不得相加。gather 包含当前可见记录；FP32 slot/roll、状态增长和最终驻留均是不同量。

| 接口字段 | bytes |
| --- | --- |
| gathered_kv_bytes | 44738560 |
| query_read_bytes | 39976960 |
| output_write_bytes | 39976960 |
| index_read_bytes | 175492 |
| sink_read_bytes | 156160 |
| embedding_lookup_payload_bytes | 71680 |
| attention_uniform_bf16_matrix_weight_payload_bytes | 194627502080 |
| expert_uniform_bf16_matrix_weight_payload_bytes | 283756462080 |
| routed_expert_actual_packed_and_scale_payload_bytes | 64222986240 |
| hc_fp32_parameter_payload_bytes | 1681392060 |
| vocabulary_head_uniform_bf16_weight_payload_bytes | 9266790400 |
| window_slot_write_bytes | 312320 |
| completed_cache_entry_write_bytes | 70144 |
| index_scan_payload_bytes | 1213440 |
| compressor_fp32_slot_write_bytes | 2170880 |
| overlap_roll_fp32_read_bytes | 1228800 |
| overlap_roll_fp32_write_bytes | 1228800 |

## 静态每调用分区与基础权重

| 分区 | 值 |
| --- | --- |
| matrix_flops_per_call | 58772783104 |
| matrix_flops_with_known_tiles_per_call | 1557812838400 |
| scalar_flops_per_call | 2327095043 |
| special_ops_per_call | {"abs": 0, "amax_compare": 0, "clamp_bound_compare": 0, "clamp_bound_comparisons": 3935232, "compare_max": 1464, "exp": 1952, "fp4_decode": 0, "fp4_encode": 0, "fp8_decode": 0, "fp8_encode": 0, "integer_lookup_entries": 18, "power_of_two_scale_bit_round": 0, "relu_compare": 0, "rsqrt": 246, "scale_floor_compare": 0, "sigmoid": 980, "silu": 1311744, "softplus": 23424, "sqrt": 23424, "topk_candidates": 22272, "topk_rows": 58} |

静态分区每一步都执行，checkpoint 只解析一次。以下保留完整基础参数分项，未把基础 checkpoint 载荷当运行时实际常驻。

| 基础参数分项 | 参数数 |
| --- | --- |
| attention_matrices | 19462750208 |
| expert_matrices_including_router_shared | 1551593766912 |
| hyper_connections | 84069603 |
| embedding | 926679040 |
| vocabulary_head | 926679040 |
| external_norms | 881664 |
| attention_q_lowrank_and_kv_norm | 124928 |
| attention_sinks | 7808 |
| compressor_norms | 35072 |
| compressor_ape | 2185216 |
| router_bias | 22272 |

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
| history_resident_bytes | 8998400 |
| compressor_buffer_bytes | 18710528 |
| resident_bytes | 27708928 |
| selected_history_payload_bytes | 8998400 |

| component 字段 | 值 |
| --- | --- |
| window_history_bytes | 7808000 |
| compressed_history_bytes | 952320 |
| index_history_bytes | 238080 |
| main_compressor_buffer_bytes | 18219008 |
| index_compressor_buffer_bytes | 491520 |
| main_selected_payload_bytes | 8760320 |
| index_scan_payload_bytes | 238080 |
| last_query_main_qk_pv_flops | 2242641920 |
| last_query_index_dot_flops | 15237120 |
| next_token_window_write_bytes | 62464 |
| next_token_completed_entry_write_bytes | 0 |

| layer | kind | ratio | window_history_bytes | compressed_history_bytes | index_history_bytes | main_compressor_buffer_bytes | index_compressor_buffer_bytes | main_selected_payload_bytes | index_scan_payload_bytes | last_query_main_qk_pv_flops | last_query_index_dot_flops | next_token_window_write_bytes | next_token_completed_entry_write_bytes | next_token_completes_compression |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 1 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 2 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 3 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 4 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 5 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 6 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 7 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 8 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 9 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 10 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 11 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 12 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 13 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 14 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 15 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 16 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 17 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 18 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 19 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 20 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 21 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 22 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 23 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 24 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 25 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 26 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 27 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 28 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 29 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 30 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 31 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 32 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 33 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 34 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 35 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 36 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 37 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 38 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 39 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 40 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 41 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 42 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 43 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 44 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 45 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 46 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 47 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 48 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 49 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 50 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 51 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 52 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 53 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 54 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 55 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 56 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 57 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 58 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |
| 59 | HCA | 128 | 128000 | 0 | 0 | 524288 | 0 | 128000 | 0 | 32768000 | 0 | 1024 | 0 | False |
| 60 | CSA | 4 | 128000 | 31744 | 7936 | 65536 | 16384 | 159744 | 7936 | 40894464 | 507904 | 1024 | 0 | False |

### 最终

| summary 字段 | 值 |
| --- | --- |
| history_resident_bytes | 9255936 |
| compressor_buffer_bytes | 18710528 |
| resident_bytes | 27966464 |
| selected_history_payload_bytes | 9255936 |

| component 字段 | 值 |
| --- | --- |
| window_history_bytes | 7995392 |
| compressed_history_bytes | 1014784 |
| index_history_bytes | 245760 |
| main_compressor_buffer_bytes | 18219008 |
| index_compressor_buffer_bytes | 491520 |
| main_selected_payload_bytes | 9010176 |
| index_scan_payload_bytes | 245760 |
| last_query_main_qk_pv_flops | 2306605056 |
| last_query_index_dot_flops | 15728640 |
| next_token_window_write_bytes | 62464 |
| next_token_completed_entry_write_bytes | 0 |

| layer | kind | ratio | window_history_bytes | compressed_history_bytes | index_history_bytes | main_compressor_buffer_bytes | index_compressor_buffer_bytes | main_selected_payload_bytes | index_scan_payload_bytes | last_query_main_qk_pv_flops | last_query_index_dot_flops | next_token_window_write_bytes | next_token_completed_entry_write_bytes | next_token_completes_compression |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 1 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 2 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 3 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 4 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 5 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 6 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 7 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 8 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 9 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 10 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 11 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 12 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 13 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 14 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 15 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 16 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 17 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 18 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 19 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 20 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 21 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 22 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 23 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 24 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 25 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 26 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 27 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 28 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 29 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 30 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 31 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 32 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 33 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 34 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 35 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 36 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 37 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 38 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 39 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 40 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 41 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 42 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 43 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 44 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 45 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 46 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 47 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 48 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 49 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 50 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 51 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 52 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 53 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 54 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 55 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 56 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 57 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 58 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |
| 59 | HCA | 128 | 131072 | 1024 | 0 | 524288 | 0 | 132096 | 0 | 33816576 | 0 | 1024 | 0 | False |
| 60 | CSA | 4 | 131072 | 32768 | 8192 | 65536 | 16384 | 163840 | 8192 | 41943040 | 524288 | 1024 | 0 | False |

## 每一步工作与状态

special/interface ID 指向下方完整字典；相同向量复用 ID，逐步映射和所有字段保留。矩阵/scalar 单位 FLOPs，状态单位 bytes。

| step | 输入位置 | 结束位置 | 完成ratio | 有效矩阵 | 已知tile矩阵 | 已计scalar | 末状态bytes | 特殊操作ID | 接口ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 125 | 126 | [] | 99972153344 | 1599303712768 | 2363418310 | 27771392 | special-0 | interface-0 |
| 1 | 126 | 127 | [] | 99988144128 | 1599303712768 | 2363418310 | 27833856 | special-0 | interface-1 |
| 2 | 127 | 128 | [4, 128] | 100020617216 | 1599824297984 | 2377330918 | 27966464 | special-1 | interface-2 |
| 3 | 128 | 129 | [] | 100020617216 | 1599824297984 | 2366223528 | 27966464 | special-2 | interface-3 |
| 4 | 129 | 130 | [] | 100020617216 | 1599824297984 | 2366223528 | 27966464 | special-2 | interface-3 |

## special 完整向量定义

| ID | 操作/字段 | 次数 |
| --- | --- | --- |
| special-0 | rsqrt | 8176 |
| special-0 | abs | 273088 |
| special-0 | amax_compare | 264981 |
| special-0 | scale_floor_compare | 8107 |
| special-0 | clamp_bound_compare | 546176 |
| special-0 | power_of_two_scale_bit_round | 8107 |
| special-0 | fp8_encode | 27328 |
| special-0 | fp8_decode | 27328 |
| special-0 | exp | 1274400 |
| special-0 | compare_max | 1246648 |
| special-0 | fp4_encode | 245760 |
| special-0 | fp4_decode | 245760 |
| special-0 | relu_compare | 59520 |
| special-0 | topk_rows | 88 |
| special-0 | topk_candidates | 23202 |
| special-0 | softplus | 23424 |
| special-0 | sqrt | 23424 |
| special-0 | integer_lookup_entries | 18 |
| special-0 | silu | 1311744 |
| special-0 | clamp_bound_comparisons | 3935232 |
| special-0 | sigmoid | 980 |
| special-1 | rsqrt | 8267 |
| special-1 | abs | 304256 |
| special-1 | amax_compare | 295602 |
| special-1 | scale_floor_compare | 8654 |
| special-1 | clamp_bound_compare | 608512 |
| special-1 | power_of_two_scale_bit_round | 8654 |
| special-1 | fp8_encode | 54656 |
| special-1 | fp8_decode | 54656 |
| special-1 | exp | 3717536 |
| special-1 | compare_max | 3650744 |
| special-1 | fp4_encode | 249600 |
| special-1 | fp4_decode | 249600 |
| special-1 | relu_compare | 61440 |
| special-1 | topk_rows | 88 |
| special-1 | topk_candidates | 23232 |
| special-1 | softplus | 23424 |
| special-1 | sqrt | 23424 |
| special-1 | integer_lookup_entries | 18 |
| special-1 | silu | 1311744 |
| special-1 | clamp_bound_comparisons | 3935232 |
| special-1 | sigmoid | 980 |
| special-2 | rsqrt | 8176 |
| special-2 | abs | 273088 |
| special-2 | amax_compare | 264981 |
| special-2 | scale_floor_compare | 8107 |
| special-2 | clamp_bound_compare | 546176 |
| special-2 | power_of_two_scale_bit_round | 8107 |
| special-2 | fp8_encode | 27328 |
| special-2 | fp8_decode | 27328 |
| special-2 | exp | 1532320 |
| special-2 | compare_max | 1500600 |
| special-2 | fp4_encode | 245760 |
| special-2 | fp4_decode | 245760 |
| special-2 | relu_compare | 61440 |
| special-2 | topk_rows | 88 |
| special-2 | topk_candidates | 23232 |
| special-2 | softplus | 23424 |
| special-2 | sqrt | 23424 |
| special-2 | integer_lookup_entries | 18 |
| special-2 | silu | 1311744 |
| special-2 | clamp_bound_comparisons | 3935232 |
| special-2 | sigmoid | 980 |

## interface 完整向量定义

| ID | 操作/字段 | bytes |
| --- | --- | --- |
| interface-0 | gathered_kv_bytes | 8822784 |
| interface-0 | query_read_bytes | 7995392 |
| interface-0 | output_write_bytes | 7995392 |
| interface-0 | index_read_bytes | 34952 |
| interface-0 | sink_read_bytes | 31232 |
| interface-0 | embedding_lookup_payload_bytes | 14336 |
| interface-0 | attention_uniform_bf16_matrix_weight_payload_bytes | 38925500416 |
| interface-0 | expert_uniform_bf16_matrix_weight_payload_bytes | 56751292416 |
| interface-0 | routed_expert_actual_packed_and_scale_payload_bytes | 12844597248 |
| interface-0 | hc_fp32_parameter_payload_bytes | 336278412 |
| interface-0 | vocabulary_head_uniform_bf16_weight_payload_bytes | 1853358080 |
| interface-0 | window_slot_write_bytes | 62464 |
| interface-0 | completed_cache_entry_write_bytes | 0 |
| interface-0 | index_scan_payload_bytes | 238080 |
| interface-0 | compressor_fp32_slot_write_bytes | 434176 |
| interface-0 | overlap_roll_fp32_read_bytes | 0 |
| interface-0 | overlap_roll_fp32_write_bytes | 0 |
| interface-1 | gathered_kv_bytes | 8885248 |
| interface-1 | query_read_bytes | 7995392 |
| interface-1 | output_write_bytes | 7995392 |
| interface-1 | index_read_bytes | 34952 |
| interface-1 | sink_read_bytes | 31232 |
| interface-1 | embedding_lookup_payload_bytes | 14336 |
| interface-1 | attention_uniform_bf16_matrix_weight_payload_bytes | 38925500416 |
| interface-1 | expert_uniform_bf16_matrix_weight_payload_bytes | 56751292416 |
| interface-1 | routed_expert_actual_packed_and_scale_payload_bytes | 12844597248 |
| interface-1 | hc_fp32_parameter_payload_bytes | 336278412 |
| interface-1 | vocabulary_head_uniform_bf16_weight_payload_bytes | 1853358080 |
| interface-1 | window_slot_write_bytes | 62464 |
| interface-1 | completed_cache_entry_write_bytes | 0 |
| interface-1 | index_scan_payload_bytes | 238080 |
| interface-1 | compressor_fp32_slot_write_bytes | 434176 |
| interface-1 | overlap_roll_fp32_read_bytes | 0 |
| interface-1 | overlap_roll_fp32_write_bytes | 0 |
| interface-2 | gathered_kv_bytes | 9010176 |
| interface-2 | query_read_bytes | 7995392 |
| interface-2 | output_write_bytes | 7995392 |
| interface-2 | index_read_bytes | 35196 |
| interface-2 | sink_read_bytes | 31232 |
| interface-2 | embedding_lookup_payload_bytes | 14336 |
| interface-2 | attention_uniform_bf16_matrix_weight_payload_bytes | 38925500416 |
| interface-2 | expert_uniform_bf16_matrix_weight_payload_bytes | 56751292416 |
| interface-2 | routed_expert_actual_packed_and_scale_payload_bytes | 12844597248 |
| interface-2 | hc_fp32_parameter_payload_bytes | 336278412 |
| interface-2 | vocabulary_head_uniform_bf16_weight_payload_bytes | 1853358080 |
| interface-2 | window_slot_write_bytes | 62464 |
| interface-2 | completed_cache_entry_write_bytes | 70144 |
| interface-2 | index_scan_payload_bytes | 245760 |
| interface-2 | compressor_fp32_slot_write_bytes | 434176 |
| interface-2 | overlap_roll_fp32_read_bytes | 1228800 |
| interface-2 | overlap_roll_fp32_write_bytes | 1228800 |
| interface-3 | gathered_kv_bytes | 9010176 |
| interface-3 | query_read_bytes | 7995392 |
| interface-3 | output_write_bytes | 7995392 |
| interface-3 | index_read_bytes | 35196 |
| interface-3 | sink_read_bytes | 31232 |
| interface-3 | embedding_lookup_payload_bytes | 14336 |
| interface-3 | attention_uniform_bf16_matrix_weight_payload_bytes | 38925500416 |
| interface-3 | expert_uniform_bf16_matrix_weight_payload_bytes | 56751292416 |
| interface-3 | routed_expert_actual_packed_and_scale_payload_bytes | 12844597248 |
| interface-3 | hc_fp32_parameter_payload_bytes | 336278412 |
| interface-3 | vocabulary_head_uniform_bf16_weight_payload_bytes | 1853358080 |
| interface-3 | window_slot_write_bytes | 62464 |
| interface-3 | completed_cache_entry_write_bytes | 0 |
| interface-3 | index_scan_payload_bytes | 245760 |
| interface-3 | compressor_fp32_slot_write_bytes | 434176 |
| interface-3 | overlap_roll_fp32_read_bytes | 0 |
| interface-3 | overlap_roll_fp32_write_bytes | 0 |

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
| 0 | {"file": "configs/models/deepseek-v4-pro/config.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "5fe4568daee51c208cb8a79538eaeda090ae011ade1dee2c386aa95f569c810e", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/config.json"} |
| 1 | {"file": "configs/models/deepseek-v4-pro/inference/config.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "a6aded1806a2dbacbbab89bae2380d0422a6d0dcc55c946b421c7f5e06ef6094", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/config.json"} |
| 2 | {"file": "sources/deepseek-v4-pro/inference/model.py", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "ce962f1face79d4f633d36436576214057a7e11443c9789935e1deb5c6cd1d71", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/model.py"} |
| 3 | {"file": "sources/deepseek-v4-pro/inference/kernel.py", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "59b325083d7103975cba025bd0d60ea343bb82d8fff53088afb7c04bd380c0c2", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/kernel.py"} |
| 4 | {"file": "sources/fast-hadamard-transform/README.md", "revision": "e7706faf8d1c3b9f241e36860640ad1dac644ede", "sha256": "e9d1a782e751104628590c481ba325bc436292254aaefe4cfa39ee3c0b1eb00e", "url": "https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/README.md"} |
| 5 | {"file": "sources/fast-hadamard-transform/csrc/fast_hadamard_transform_common.h", "revision": "e7706faf8d1c3b9f241e36860640ad1dac644ede", "sha256": "e51345eb6be7b43cb657d73b8db9b2debcb4060de2266c7b42fc45bb3b86b473", "url": "https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/csrc/fast_hadamard_transform_common.h"} |
| 6 | {"file": "sources/fast-hadamard-transform/fast_hadamard_transform/fast_hadamard_transform_interface.py", "revision": "e7706faf8d1c3b9f241e36860640ad1dac644ede", "sha256": "a2f32a615b03c83d075fd49eba266c9f6c13df790cbe549db3bf8c0c1f3e8877", "url": "https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/fast_hadamard_transform/fast_hadamard_transform_interface.py"} |
| 7 | {"file": "sources/deepseek-v4-pro/model.safetensors.index.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "a3a39b9ccb4e729851922fc9c770f5c5755e7b9d7e96cd02c23f0e12b5e25cb9", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model.safetensors.index.json"} |
| 8 | {"file": "sources/deepseek-v4-pro/headers/model-00001-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "f62844ce4c4d47bc40696a831380bb1464ae9717480bb30251ad05fe87b12fbd", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00001-of-00064.safetensors?header=1"} |
| 9 | {"file": "sources/deepseek-v4-pro/headers/model-00002-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "09c84dc7e7d800b1b7eda5f950488a4edde5058dece58842155a2d2c19d38dfa", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00002-of-00064.safetensors?header=1"} |
| 10 | {"file": "sources/deepseek-v4-pro/headers/model-00003-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "a0f61998df192ab90954d0a00a1ccf5166153a66899d6849741d09e38ab4f7a9", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00003-of-00064.safetensors?header=1"} |
| 11 | {"file": "sources/deepseek-v4-pro/headers/model-00004-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "5ad3452b1f4668d7917a18b085a8c5f2767100fd3f36ff7686061eaa810321a0", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00004-of-00064.safetensors?header=1"} |
| 12 | {"file": "sources/deepseek-v4-pro/headers/model-00005-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "9817aa67c797eb172e6c0ae9e84823ea54b04afb41e2e189c3cc7bedd547fff9", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00005-of-00064.safetensors?header=1"} |
| 13 | {"file": "sources/deepseek-v4-pro/headers/model-00006-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "f012bb8296655c4449c76cfb0c78b2e367c0706f5548a64c180a47f9e8835db1", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00006-of-00064.safetensors?header=1"} |
| 14 | {"file": "sources/deepseek-v4-pro/headers/model-00007-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "c48667932097f3843857a56a36870c2ba5a44149c47a8df7c76a4d0a9a7c0409", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00007-of-00064.safetensors?header=1"} |
| 15 | {"file": "sources/deepseek-v4-pro/headers/model-00008-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "366ab679ecbe8e4dcc8809e7caf6432f11329c84363da64eca6459073142226e", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00008-of-00064.safetensors?header=1"} |
| 16 | {"file": "sources/deepseek-v4-pro/headers/model-00009-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "972018fc9cfab2cefa9db1738e7dc52da0220d16552d944e8de9ff57b2f52e0a", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00009-of-00064.safetensors?header=1"} |
| 17 | {"file": "sources/deepseek-v4-pro/headers/model-00010-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "764ed6d21313964fe00dae095c6afe2d75565bf9fe3ecbf87e09e6d83d093e1f", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00010-of-00064.safetensors?header=1"} |
| 18 | {"file": "sources/deepseek-v4-pro/headers/model-00011-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "01db80934aa5584438318e4fdca952fb91afe58ad05d5332026d637cdc8db877", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00011-of-00064.safetensors?header=1"} |
| 19 | {"file": "sources/deepseek-v4-pro/headers/model-00012-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "773af1e79c9f0ec3d1505fa049e80b4ffb670796b4e024951a4f64fb1342bef7", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00012-of-00064.safetensors?header=1"} |
| 20 | {"file": "sources/deepseek-v4-pro/headers/model-00013-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "1c0343aa40c2392238fca1831246f13562779ddfde10d2ccf9a3a22ad701ddf6", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00013-of-00064.safetensors?header=1"} |
| 21 | {"file": "sources/deepseek-v4-pro/headers/model-00014-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "5eb8c0502dc4385719778971d965cca146f76b9348177b6207e8d252c353f171", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00014-of-00064.safetensors?header=1"} |
| 22 | {"file": "sources/deepseek-v4-pro/headers/model-00015-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "94a9511cae977b5916462e10f46fa6cdd7470414b407e6a9fc7f654d2da4e9d0", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00015-of-00064.safetensors?header=1"} |
| 23 | {"file": "sources/deepseek-v4-pro/headers/model-00016-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "893a168b5ff71d4dff9c88f6ba0a6419b2c4cfca1327faa8f475deb9b6c7784b", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00016-of-00064.safetensors?header=1"} |
| 24 | {"file": "sources/deepseek-v4-pro/headers/model-00017-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "c9368805fe734f1654f7e74f22070c19d13e5c3ce0d61d7563960252898725fc", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00017-of-00064.safetensors?header=1"} |
| 25 | {"file": "sources/deepseek-v4-pro/headers/model-00018-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "42b4f2cf60eebbbc77e9765e5f034bf4dacd83f7fcd81edaab18935123ec0aaa", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00018-of-00064.safetensors?header=1"} |
| 26 | {"file": "sources/deepseek-v4-pro/headers/model-00019-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "6c1ba9cd1ffd09fbbec7283b0b5830721eab9fb3048a56f70451cf4089fa6691", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00019-of-00064.safetensors?header=1"} |
| 27 | {"file": "sources/deepseek-v4-pro/headers/model-00020-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "00d744b2ef8dcf64083fbd4c1fa57d88a8beed492d2ad9feb0abb084c324514d", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00020-of-00064.safetensors?header=1"} |
| 28 | {"file": "sources/deepseek-v4-pro/headers/model-00021-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "08005b0a277f86b5d379be73d6c044e61e73a1cb748364487bd83eeae1f19b24", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00021-of-00064.safetensors?header=1"} |
| 29 | {"file": "sources/deepseek-v4-pro/headers/model-00022-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "2096dd2862f84ed281004ede6d700f8c422ac9f5f6708fa4e622e78c089a3360", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00022-of-00064.safetensors?header=1"} |
| 30 | {"file": "sources/deepseek-v4-pro/headers/model-00023-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "46a697dc52e865034ed8d910ede0f222900b3ea8c944a5cb500f72e939b04da3", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00023-of-00064.safetensors?header=1"} |
| 31 | {"file": "sources/deepseek-v4-pro/headers/model-00024-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "e2b9c7a6e404a9d741f6f134c5453b556ba2a1d7a7c24a2ac7d3ed89e1aa2d22", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00024-of-00064.safetensors?header=1"} |
| 32 | {"file": "sources/deepseek-v4-pro/headers/model-00025-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "5b301d2e50951f2cac98ffdcba8f251cd21ee06f9ee9b06c3a10281749b4a8e1", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00025-of-00064.safetensors?header=1"} |
| 33 | {"file": "sources/deepseek-v4-pro/headers/model-00026-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "8d971ac61f41bbb56bae9300470f8fd6a0353125b3408b287ead3b17677fce3b", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00026-of-00064.safetensors?header=1"} |
| 34 | {"file": "sources/deepseek-v4-pro/headers/model-00027-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "65ee01c2da71bd59d980cb77281ef274e7e28f39d5c3c6000355ed5d9f2d901d", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00027-of-00064.safetensors?header=1"} |
| 35 | {"file": "sources/deepseek-v4-pro/headers/model-00028-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "32873d82bb2169171ada203db4fb6e156baa38e43ee4dec54b2135f45bb46372", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00028-of-00064.safetensors?header=1"} |
| 36 | {"file": "sources/deepseek-v4-pro/headers/model-00029-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "6d896e9661a66563808d89ab2d175ca42ae4f454d12240fce5d01d6639f3b830", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00029-of-00064.safetensors?header=1"} |
| 37 | {"file": "sources/deepseek-v4-pro/headers/model-00030-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "7d37c8cb35b4491a885dd93f5af70ab7207cbab58a6395a1ec0e3acda6070245", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00030-of-00064.safetensors?header=1"} |
| 38 | {"file": "sources/deepseek-v4-pro/headers/model-00031-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "af3aa1bc6590a624d28dea59ff01851124e611b1f75d2bf93c82a533b999f063", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00031-of-00064.safetensors?header=1"} |
| 39 | {"file": "sources/deepseek-v4-pro/headers/model-00032-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "111af8344c0da52f7086873f06977dadf4f0a93f2d5a6ba694373dcf0bacb497", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00032-of-00064.safetensors?header=1"} |
| 40 | {"file": "sources/deepseek-v4-pro/headers/model-00033-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "2e27cd1549eb4cce96dd7a2d3c4326bc9b8369bf8ff3f0c0f502c1fd5981a751", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00033-of-00064.safetensors?header=1"} |
| 41 | {"file": "sources/deepseek-v4-pro/headers/model-00034-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "fde9380f0ac661c616d4ca856591ecf953f384d004c5e3e725b4acf098c09c39", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00034-of-00064.safetensors?header=1"} |
| 42 | {"file": "sources/deepseek-v4-pro/headers/model-00035-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "b444ab6670871e112d2f925a4037aec0fb48c236616b9861bde6da1b076b62a8", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00035-of-00064.safetensors?header=1"} |
| 43 | {"file": "sources/deepseek-v4-pro/headers/model-00036-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "260f19fd3091cf5f1e1e02627b21d0ed3699c815ac7645d0bc7f6878b2ec85a9", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00036-of-00064.safetensors?header=1"} |
| 44 | {"file": "sources/deepseek-v4-pro/headers/model-00037-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "ada278d9a5d040f4198791954d2120fa1234736a90082a5694ec920e638733c7", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00037-of-00064.safetensors?header=1"} |
| 45 | {"file": "sources/deepseek-v4-pro/headers/model-00038-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "20636aa9b7a63fbf8bc48536c668720ca283cd6fbef63a94b912ff0a93e683a9", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00038-of-00064.safetensors?header=1"} |
| 46 | {"file": "sources/deepseek-v4-pro/headers/model-00039-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "cdffc26189719dabd1301e040f1158a2d69ab5e88a7eb2247aa89c949f6f8437", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00039-of-00064.safetensors?header=1"} |
| 47 | {"file": "sources/deepseek-v4-pro/headers/model-00040-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "ae12150988f04ff7a3c64ad20742c0b2039eb2003d271833b9ecce22872e9d98", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00040-of-00064.safetensors?header=1"} |
| 48 | {"file": "sources/deepseek-v4-pro/headers/model-00041-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "4d1f15d8c4588f0735028cb6d2b9d308b9a8baf80e4a65d2565e53e71272decf", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00041-of-00064.safetensors?header=1"} |
| 49 | {"file": "sources/deepseek-v4-pro/headers/model-00042-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "78245a3e3a163146cb8640ee7249e43baacbd6b0c1294f7f0b86f2c3a2ee262a", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00042-of-00064.safetensors?header=1"} |
| 50 | {"file": "sources/deepseek-v4-pro/headers/model-00043-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "bcf24f2bd0eb8d597e3b3cca50941e34cc317b0a0aafeaa809941ba55ae65de4", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00043-of-00064.safetensors?header=1"} |
| 51 | {"file": "sources/deepseek-v4-pro/headers/model-00044-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "9a0112e1ab9bd7cc7989e71e65b33b541180697794cd8aa328694d94f9b5fa5c", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00044-of-00064.safetensors?header=1"} |
| 52 | {"file": "sources/deepseek-v4-pro/headers/model-00045-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "5024100086c9989a18c0d867643cb2058d954266686b979b0c1ca98132927830", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00045-of-00064.safetensors?header=1"} |
| 53 | {"file": "sources/deepseek-v4-pro/headers/model-00046-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "123e4096f27146b8d7209e1f78b808025ec238ee719147eb5c375914f199b1de", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00046-of-00064.safetensors?header=1"} |
| 54 | {"file": "sources/deepseek-v4-pro/headers/model-00047-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "f78fb5091fa057f1b09e034d0a66e5ca6c4ec444c0689d0928ff86247e7b3845", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00047-of-00064.safetensors?header=1"} |
| 55 | {"file": "sources/deepseek-v4-pro/headers/model-00048-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "ff75f7a6cbe6b0558a94a304d4470c840db4e9b69de4143d555c28a85dafc1ef", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00048-of-00064.safetensors?header=1"} |
| 56 | {"file": "sources/deepseek-v4-pro/headers/model-00049-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "f745de46aaea647f5b966cc61e6bf9f26643f7780b547f1206afa6b88b527cfd", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00049-of-00064.safetensors?header=1"} |
| 57 | {"file": "sources/deepseek-v4-pro/headers/model-00050-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "d4b43bcc44eccceebb30a8d07ba7ec1bf626771a49007bc7ac4407f4d9a82b3b", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00050-of-00064.safetensors?header=1"} |
| 58 | {"file": "sources/deepseek-v4-pro/headers/model-00051-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "d01cf662b54ab837ec7de7399d182f372d30bad1a1cf20a0e922918e662fc34c", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00051-of-00064.safetensors?header=1"} |
| 59 | {"file": "sources/deepseek-v4-pro/headers/model-00052-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "8fd10a263f7d795c5fdae4cef849153ab1f4fc5cbe08c4f6f46fb57592fcb557", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00052-of-00064.safetensors?header=1"} |
| 60 | {"file": "sources/deepseek-v4-pro/headers/model-00053-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "530bd227b6a95c4998bfe4539e32bbb68ca927487b2de154ff1d55f121402984", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00053-of-00064.safetensors?header=1"} |
| 61 | {"file": "sources/deepseek-v4-pro/headers/model-00054-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "377c88b1ddd5ed0d29dd5fc0e1dc801c003773dbb6ff4cee594ec5c3572a3cf8", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00054-of-00064.safetensors?header=1"} |
| 62 | {"file": "sources/deepseek-v4-pro/headers/model-00055-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "7f4fbfd6bd08895ae4f4f553af562e0977eb1ded070bb6fff6b585e54a5dced4", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00055-of-00064.safetensors?header=1"} |
| 63 | {"file": "sources/deepseek-v4-pro/headers/model-00056-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "ce3736415591d513968768ab86dd164333b4d0a1a6491b846c8af0fbc1573ede", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00056-of-00064.safetensors?header=1"} |
| 64 | {"file": "sources/deepseek-v4-pro/headers/model-00057-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "804da0c9349206088b99f94ea81b57845cca54d1eaeb30603675906d326f0e4b", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00057-of-00064.safetensors?header=1"} |
| 65 | {"file": "sources/deepseek-v4-pro/headers/model-00058-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "7ccc9e5f5419659d4baa12760c05fa1fb3da4fe9d581060b219b4124c84d509f", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00058-of-00064.safetensors?header=1"} |
| 66 | {"file": "sources/deepseek-v4-pro/headers/model-00059-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "e88377ef55fa69722cc08e7fc4720ce21e6c39000104bc7d05ce9e915391b87b", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00059-of-00064.safetensors?header=1"} |
| 67 | {"file": "sources/deepseek-v4-pro/headers/model-00060-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "1af641c19db47af20c62850890c45ed4daaeb2035d311c4866b253a4cf20d3d9", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00060-of-00064.safetensors?header=1"} |
| 68 | {"file": "sources/deepseek-v4-pro/headers/model-00061-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "e5e13b5c696c3f3c6306fde2be41f45111635ddb5f51bff597826f02ac59a78a", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00061-of-00064.safetensors?header=1"} |
| 69 | {"file": "sources/deepseek-v4-pro/headers/model-00062-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "7258653c3c98ca6615f76c0eda6d6283222424370e9dd58758d6b1e80e19d8e3", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00062-of-00064.safetensors?header=1"} |
| 70 | {"file": "sources/deepseek-v4-pro/headers/model-00063-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "711b38904bc397fca30cddf887b2c6581a48ffcf868fe258c3369af68147366f", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00063-of-00064.safetensors?header=1"} |
| 71 | {"file": "sources/deepseek-v4-pro/headers/model-00064-of-00064.safetensors.json", "revision": "b5968e9190ef611bbf34a7229255be88a0e937c1", "sha256": "14a863bf950f74e19fdcaa16ebbdc192e125e9a7972fbc3f6a9985d100a3a6bb", "url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00064-of-00064.safetensors?header=1"} |
