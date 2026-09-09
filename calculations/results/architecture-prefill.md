# 官方基线与声明架构变体

只有基线是已发布checkpoint；其余结构未训练，不假定质量相同。严格等参以实际标志和差额判定。

输入：`{"batch": 1, "history": 0, "tokens": 8192, "tp": 2, "capacity_bytes": 24000000000, "workspace_bytes": 2147483648, "ffn_alignment": 128}`

| 结构 | L/H/FFN/KV头 | 参数 | 差额 | 严格等参 | 矩阵FLOPs | KV bytes/token | 每rank预算占用bytes |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| baseline | 36/4096/12288/8 | 8190735360 | 0 | True | 133594323353600 | 147456 | 10942507008 |
| shallower_same_width | 24/4096/20096/8 | 8178051072 | -12684288 | False | 126790289850368 | 98304 | 10728394752 |
| deeper_same_width | 48/4096/8320/8 | 8165670912 | -25064448 | False | 139779881566208 | 196608 | 11118870528 |
| narrower_same_depth | 36/3072/19328/6 | 8195641344 | 4905984 | False | 133825336442880 | 110592 | 10796343296 |
| shallower_wider | 24/5120/13952/8 | 8209296384 | 18561024 | False | 125502513479680 | 98304 | 10759690240 |
| less_kv_more_ffn_budget_match | 36/4096/12800/2 | 8190735360 | 0 | True | 133594323353600 | 36864 | 10489522176 |

## baseline

工作与TP预算：`{"matrix_flops": 133594323353600, "scalar_flops": 191920152576, "all_unique_weight_bytes": 16381470720, "per_rank_weight_bytes": 8191043584, "aggregate_tp_weight_bytes": 16382087168, "norm_replication_extra_bytes": 616448, "kv_bytes_per_token_per_request": 147456, "per_rank_kv_bytes": 603979776, "per_rank_old_history_read_bytes": 0, "per_rank_kv_append_bytes": 603979776, "per_rank_new_kv_request_bytes": 603979776, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10942507008, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 22, "batch_fits": true, "sequential_decoder_layers": 36, "sequential_collectives": 72, "per_collective_activation_payload_bytes": 67108864, "per_rank_ring_wire_bytes_exact": "4831838208", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 8192], "table": [151936, 4096], "output": [8192, 4096]}` | 1 | 0/0 | 67108864/65536/67108864 | `{}` |
| rope_table | `{"frequencies": [8192, 64], "cos_sin_each": [8192, 128]}` | 1 | 0/524288 | 0/65792/4194304 | `{"sin": 1048576, "cos": 1048576}` |
| input_layernorm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 36 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| q_proj | `{"input": [8192, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [8192, 4096]}` | 36 | 274877906944/0 | 33554432/67108864/67108864 | `{}` |
| k_proj | `{"input": [8192, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [8192, 1024]}` | 36 | 68719476736/0 | 8388608/67108864/16777216 | `{}` |
| v_proj | `{"input": [8192, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [8192, 1024]}` | 36 | 68719476736/0 | 8388608/67108864/16777216 | `{}` |
| q_norm | `{"input": [262144, 128], "weight": [128], "output": [262144, 128]}` | 36 | 0/134479872 | 256/67108864/67108864 | `{"rsqrt": 262144}` |
| k_norm | `{"input": [65536, 128], "weight": [128], "output": [65536, 128]}` | 36 | 0/33619968 | 256/16777216/16777216 | `{"rsqrt": 65536}` |
| apply_rope | `{"Q": [1, 32, 8192, 128], "K": [1, 8, 8192, 128]}` | 36 | 0/125829120 | 0/88080384/83886080 | `{"negate": 20971520}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 8192, 128]}` | 36 | 0/0 | 0/33554432/33554432 | `{}` |
| qk | `{"Q": [1, 32, 8192, 128], "K_shared": [1, 8, 8192, 128], "scores_rectangular": [1, 32, 8192, 8192]}` | 36 | 274911461376/0 | 0/83886080/8589934592 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 8192, 8192]}` | 36 | 0/4295229440 | 0/8589934592/8589934592 | `{"exp": 1073872896, "compare_max": 1073610752, "mask_decisions": 2147483648}` |
| pv | `{"P": [1, 32, 8192, 8192], "V_shared": [1, 8, 8192, 128], "output": [1, 32, 8192, 128]}` | 36 | 274911461376/0 | 0/8606711808/67108864 | `{}` |
| o_proj | `{"input": [8192, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [8192, 4096]}` | 36 | 274877906944/0 | 33554432/67108864/67108864 | `{}` |
| attention_residual | `{"inputs_each": [8192, 4096], "output": [8192, 4096]}` | 36 | 0/33554432 | 0/134217728/67108864 | `{}` |
| post_attention_layernorm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 36 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| gate_proj | `{"input": [8192, 4096], "weight_math": [4096, 12288], "weight_storage": [12288, 4096], "output": [8192, 12288]}` | 36 | 824633720832/0 | 100663296/67108864/201326592 | `{}` |
| up_proj | `{"input": [8192, 4096], "weight_math": [4096, 12288], "weight_storage": [12288, 4096], "output": [8192, 12288]}` | 36 | 824633720832/0 | 100663296/67108864/201326592 | `{}` |
| silu_mul | `{"gate": [8192, 12288], "up": [8192, 12288], "output": [8192, 12288]}` | 36 | 0/402653184 | 0/402653184/201326592 | `{"exp": 100663296, "negate": 100663296}` |
| down_proj | `{"input": [8192, 12288], "weight_math": [12288, 4096], "weight_storage": [4096, 12288], "output": [8192, 4096]}` | 36 | 824633720832/0 | 100663296/201326592/67108864 | `{}` |
| ffn_residual | `{"inputs_each": [8192, 4096], "output": [8192, 4096]}` | 36 | 0/33554432 | 0/134217728/67108864 | `{}` |
| final_norm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 1 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## shallower_same_width

工作与TP预算：`{"matrix_flops": 126790289850368, "scalar_flops": 134132146176, "all_unique_weight_bytes": 16356102144, "per_rank_weight_bytes": 8178257920, "aggregate_tp_weight_bytes": 16356515840, "norm_replication_extra_bytes": 413696, "kv_bytes_per_token_per_request": 98304, "per_rank_kv_bytes": 402653184, "per_rank_old_history_read_bytes": 0, "per_rank_kv_append_bytes": 402653184, "per_rank_new_kv_request_bytes": 402653184, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10728394752, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 33, "batch_fits": true, "sequential_decoder_layers": 24, "sequential_collectives": 48, "per_collective_activation_payload_bytes": 67108864, "per_rank_ring_wire_bytes_exact": "3221225472", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 8192], "table": [151936, 4096], "output": [8192, 4096]}` | 1 | 0/0 | 67108864/65536/67108864 | `{}` |
| rope_table | `{"frequencies": [8192, 64], "cos_sin_each": [8192, 128]}` | 1 | 0/524288 | 0/65792/4194304 | `{"sin": 1048576, "cos": 1048576}` |
| input_layernorm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 24 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| q_proj | `{"input": [8192, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [8192, 4096]}` | 24 | 274877906944/0 | 33554432/67108864/67108864 | `{}` |
| k_proj | `{"input": [8192, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [8192, 1024]}` | 24 | 68719476736/0 | 8388608/67108864/16777216 | `{}` |
| v_proj | `{"input": [8192, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [8192, 1024]}` | 24 | 68719476736/0 | 8388608/67108864/16777216 | `{}` |
| q_norm | `{"input": [262144, 128], "weight": [128], "output": [262144, 128]}` | 24 | 0/134479872 | 256/67108864/67108864 | `{"rsqrt": 262144}` |
| k_norm | `{"input": [65536, 128], "weight": [128], "output": [65536, 128]}` | 24 | 0/33619968 | 256/16777216/16777216 | `{"rsqrt": 65536}` |
| apply_rope | `{"Q": [1, 32, 8192, 128], "K": [1, 8, 8192, 128]}` | 24 | 0/125829120 | 0/88080384/83886080 | `{"negate": 20971520}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 8192, 128]}` | 24 | 0/0 | 0/33554432/33554432 | `{}` |
| qk | `{"Q": [1, 32, 8192, 128], "K_shared": [1, 8, 8192, 128], "scores_rectangular": [1, 32, 8192, 8192]}` | 24 | 274911461376/0 | 0/83886080/8589934592 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 8192, 8192]}` | 24 | 0/4295229440 | 0/8589934592/8589934592 | `{"exp": 1073872896, "compare_max": 1073610752, "mask_decisions": 2147483648}` |
| pv | `{"P": [1, 32, 8192, 8192], "V_shared": [1, 8, 8192, 128], "output": [1, 32, 8192, 128]}` | 24 | 274911461376/0 | 0/8606711808/67108864 | `{}` |
| o_proj | `{"input": [8192, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [8192, 4096]}` | 24 | 274877906944/0 | 33554432/67108864/67108864 | `{}` |
| attention_residual | `{"inputs_each": [8192, 4096], "output": [8192, 4096]}` | 24 | 0/33554432 | 0/134217728/67108864 | `{}` |
| post_attention_layernorm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 24 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| gate_proj | `{"input": [8192, 4096], "weight_math": [4096, 20096], "weight_storage": [20096, 4096], "output": [8192, 20096]}` | 24 | 1348619730944/0 | 164626432/67108864/329252864 | `{}` |
| up_proj | `{"input": [8192, 4096], "weight_math": [4096, 20096], "weight_storage": [20096, 4096], "output": [8192, 20096]}` | 24 | 1348619730944/0 | 164626432/67108864/329252864 | `{}` |
| silu_mul | `{"gate": [8192, 20096], "up": [8192, 20096], "output": [8192, 20096]}` | 24 | 0/658505728 | 0/658505728/329252864 | `{"exp": 164626432, "negate": 164626432}` |
| down_proj | `{"input": [8192, 20096], "weight_math": [20096, 4096], "weight_storage": [4096, 20096], "output": [8192, 4096]}` | 24 | 1348619730944/0 | 164626432/329252864/67108864 | `{}` |
| ffn_residual | `{"inputs_each": [8192, 4096], "output": [8192, 4096]}` | 24 | 0/33554432 | 0/134217728/67108864 | `{}` |
| final_norm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 1 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## deeper_same_width

工作与TP预算：`{"matrix_flops": 139779881566208, "scalar_flops": 249607495680, "all_unique_weight_bytes": 16331341824, "per_rank_weight_bytes": 8166080512, "aggregate_tp_weight_bytes": 16332161024, "norm_replication_extra_bytes": 819200, "kv_bytes_per_token_per_request": 196608, "per_rank_kv_bytes": 805306368, "per_rank_old_history_read_bytes": 0, "per_rank_kv_append_bytes": 805306368, "per_rank_new_kv_request_bytes": 805306368, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 11118870528, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 16, "batch_fits": true, "sequential_decoder_layers": 48, "sequential_collectives": 96, "per_collective_activation_payload_bytes": 67108864, "per_rank_ring_wire_bytes_exact": "6442450944", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 8192], "table": [151936, 4096], "output": [8192, 4096]}` | 1 | 0/0 | 67108864/65536/67108864 | `{}` |
| rope_table | `{"frequencies": [8192, 64], "cos_sin_each": [8192, 128]}` | 1 | 0/524288 | 0/65792/4194304 | `{"sin": 1048576, "cos": 1048576}` |
| input_layernorm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 48 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| q_proj | `{"input": [8192, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [8192, 4096]}` | 48 | 274877906944/0 | 33554432/67108864/67108864 | `{}` |
| k_proj | `{"input": [8192, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [8192, 1024]}` | 48 | 68719476736/0 | 8388608/67108864/16777216 | `{}` |
| v_proj | `{"input": [8192, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [8192, 1024]}` | 48 | 68719476736/0 | 8388608/67108864/16777216 | `{}` |
| q_norm | `{"input": [262144, 128], "weight": [128], "output": [262144, 128]}` | 48 | 0/134479872 | 256/67108864/67108864 | `{"rsqrt": 262144}` |
| k_norm | `{"input": [65536, 128], "weight": [128], "output": [65536, 128]}` | 48 | 0/33619968 | 256/16777216/16777216 | `{"rsqrt": 65536}` |
| apply_rope | `{"Q": [1, 32, 8192, 128], "K": [1, 8, 8192, 128]}` | 48 | 0/125829120 | 0/88080384/83886080 | `{"negate": 20971520}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 8192, 128]}` | 48 | 0/0 | 0/33554432/33554432 | `{}` |
| qk | `{"Q": [1, 32, 8192, 128], "K_shared": [1, 8, 8192, 128], "scores_rectangular": [1, 32, 8192, 8192]}` | 48 | 274911461376/0 | 0/83886080/8589934592 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 8192, 8192]}` | 48 | 0/4295229440 | 0/8589934592/8589934592 | `{"exp": 1073872896, "compare_max": 1073610752, "mask_decisions": 2147483648}` |
| pv | `{"P": [1, 32, 8192, 8192], "V_shared": [1, 8, 8192, 128], "output": [1, 32, 8192, 128]}` | 48 | 274911461376/0 | 0/8606711808/67108864 | `{}` |
| o_proj | `{"input": [8192, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [8192, 4096]}` | 48 | 274877906944/0 | 33554432/67108864/67108864 | `{}` |
| attention_residual | `{"inputs_each": [8192, 4096], "output": [8192, 4096]}` | 48 | 0/33554432 | 0/134217728/67108864 | `{}` |
| post_attention_layernorm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 48 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| gate_proj | `{"input": [8192, 4096], "weight_math": [4096, 8320], "weight_storage": [8320, 4096], "output": [8192, 8320]}` | 48 | 558345748480/0 | 68157440/67108864/136314880 | `{}` |
| up_proj | `{"input": [8192, 4096], "weight_math": [4096, 8320], "weight_storage": [8320, 4096], "output": [8192, 8320]}` | 48 | 558345748480/0 | 68157440/67108864/136314880 | `{}` |
| silu_mul | `{"gate": [8192, 8320], "up": [8192, 8320], "output": [8192, 8320]}` | 48 | 0/272629760 | 0/272629760/136314880 | `{"exp": 68157440, "negate": 68157440}` |
| down_proj | `{"input": [8192, 8320], "weight_math": [8320, 4096], "weight_storage": [4096, 8320], "output": [8192, 4096]}` | 48 | 558345748480/0 | 68157440/136314880/67108864 | `{}` |
| ffn_residual | `{"inputs_each": [8192, 4096], "output": [8192, 4096]}` | 48 | 0/33554432 | 0/134217728/67108864 | `{}` |
| final_norm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 1 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## narrower_same_depth

工作与TP预算：`{"matrix_flops": 133825336442880, "scalar_flops": 155868995584, "all_unique_weight_bytes": 16391282688, "per_rank_weight_bytes": 8195874816, "aggregate_tp_weight_bytes": 16391749632, "norm_replication_extra_bytes": 466944, "kv_bytes_per_token_per_request": 110592, "per_rank_kv_bytes": 452984832, "per_rank_old_history_read_bytes": 0, "per_rank_kv_append_bytes": 452984832, "per_rank_new_kv_request_bytes": 452984832, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10796343296, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 30, "batch_fits": true, "sequential_decoder_layers": 36, "sequential_collectives": 72, "per_collective_activation_payload_bytes": 50331648, "per_rank_ring_wire_bytes_exact": "3623878656", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 8192], "table": [151936, 3072], "output": [8192, 3072]}` | 1 | 0/0 | 50331648/65536/50331648 | `{}` |
| rope_table | `{"frequencies": [8192, 64], "cos_sin_each": [8192, 128]}` | 1 | 0/524288 | 0/65792/4194304 | `{"sin": 1048576, "cos": 1048576}` |
| input_layernorm | `{"input": [8192, 3072], "weight": [3072], "output": [8192, 3072]}` | 36 | 0/100671488 | 6144/50331648/50331648 | `{"rsqrt": 8192}` |
| q_proj | `{"input": [8192, 3072], "weight_math": [3072, 3072], "weight_storage": [3072, 3072], "output": [8192, 3072]}` | 36 | 154618822656/0 | 18874368/50331648/50331648 | `{}` |
| k_proj | `{"input": [8192, 3072], "weight_math": [3072, 768], "weight_storage": [768, 3072], "output": [8192, 768]}` | 36 | 38654705664/0 | 4718592/50331648/12582912 | `{}` |
| v_proj | `{"input": [8192, 3072], "weight_math": [3072, 768], "weight_storage": [768, 3072], "output": [8192, 768]}` | 36 | 38654705664/0 | 4718592/50331648/12582912 | `{}` |
| q_norm | `{"input": [196608, 128], "weight": [128], "output": [196608, 128]}` | 36 | 0/100859904 | 256/50331648/50331648 | `{"rsqrt": 196608}` |
| k_norm | `{"input": [49152, 128], "weight": [128], "output": [49152, 128]}` | 36 | 0/25214976 | 256/12582912/12582912 | `{"rsqrt": 49152}` |
| apply_rope | `{"Q": [1, 24, 8192, 128], "K": [1, 6, 8192, 128]}` | 36 | 0/94371840 | 0/67108864/62914560 | `{"negate": 15728640}` |
| kv_append | `{"new_K_and_V_each": [1, 6, 8192, 128]}` | 36 | 0/0 | 0/25165824/25165824 | `{}` |
| qk | `{"Q": [1, 24, 8192, 128], "K_shared": [1, 6, 8192, 128], "scores_rectangular": [1, 24, 8192, 8192]}` | 36 | 206183596032/0 | 0/62914560/6442450944 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 24, 8192, 8192]}` | 36 | 0/3221422080 | 0/6442450944/6442450944 | `{"exp": 805404672, "compare_max": 805208064, "mask_decisions": 1610612736}` |
| pv | `{"P": [1, 24, 8192, 8192], "V_shared": [1, 6, 8192, 128], "output": [1, 24, 8192, 128]}` | 36 | 206183596032/0 | 0/6455033856/50331648 | `{}` |
| o_proj | `{"input": [8192, 3072], "weight_math": [3072, 3072], "weight_storage": [3072, 3072], "output": [8192, 3072]}` | 36 | 154618822656/0 | 18874368/50331648/50331648 | `{}` |
| attention_residual | `{"inputs_each": [8192, 3072], "output": [8192, 3072]}` | 36 | 0/25165824 | 0/100663296/50331648 | `{}` |
| post_attention_layernorm | `{"input": [8192, 3072], "weight": [3072], "output": [8192, 3072]}` | 36 | 0/100671488 | 6144/50331648/50331648 | `{"rsqrt": 8192}` |
| gate_proj | `{"input": [8192, 3072], "weight_math": [3072, 19328], "weight_storage": [19328, 3072], "output": [8192, 19328]}` | 36 | 972810092544/0 | 118751232/50331648/316669952 | `{}` |
| up_proj | `{"input": [8192, 3072], "weight_math": [3072, 19328], "weight_storage": [19328, 3072], "output": [8192, 19328]}` | 36 | 972810092544/0 | 118751232/50331648/316669952 | `{}` |
| silu_mul | `{"gate": [8192, 19328], "up": [8192, 19328], "output": [8192, 19328]}` | 36 | 0/633339904 | 0/633339904/316669952 | `{"exp": 158334976, "negate": 158334976}` |
| down_proj | `{"input": [8192, 19328], "weight_math": [19328, 3072], "weight_storage": [3072, 19328], "output": [8192, 3072]}` | 36 | 972810092544/0 | 118751232/316669952/50331648 | `{}` |
| ffn_residual | `{"inputs_each": [8192, 3072], "output": [8192, 3072]}` | 36 | 0/25165824 | 0/100663296/50331648 | `{}` |
| final_norm | `{"input": [8192, 3072], "weight": [3072], "output": [8192, 3072]}` | 1 | 0/100671488 | 6144/50331648/50331648 | `{"rsqrt": 8192}` |
| lm_head | `{"input": [1, 3072], "weight_math": [3072, 151936], "weight_storage": [151936, 3072], "output": [1, 151936]}` | 1 | 933494784/0 | 933494784/6144/303872 | `{}` |

## shallower_wider

工作与TP预算：`{"matrix_flops": 125502513479680, "scalar_flops": 158529363968, "all_unique_weight_bytes": 16418592768, "per_rank_weight_bytes": 8209553408, "aggregate_tp_weight_bytes": 16419106816, "norm_replication_extra_bytes": 514048, "kv_bytes_per_token_per_request": 98304, "per_rank_kv_bytes": 402653184, "per_rank_old_history_read_bytes": 0, "per_rank_kv_append_bytes": 402653184, "per_rank_new_kv_request_bytes": 402653184, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10759690240, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 33, "batch_fits": true, "sequential_decoder_layers": 24, "sequential_collectives": 48, "per_collective_activation_payload_bytes": 83886080, "per_rank_ring_wire_bytes_exact": "4026531840", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 8192], "table": [151936, 5120], "output": [8192, 5120]}` | 1 | 0/0 | 83886080/65536/83886080 | `{}` |
| rope_table | `{"frequencies": [8192, 64], "cos_sin_each": [8192, 128]}` | 1 | 0/524288 | 0/65792/4194304 | `{"sin": 1048576, "cos": 1048576}` |
| input_layernorm | `{"input": [8192, 5120], "weight": [5120], "output": [8192, 5120]}` | 24 | 0/167780352 | 10240/83886080/83886080 | `{"rsqrt": 8192}` |
| q_proj | `{"input": [8192, 5120], "weight_math": [5120, 5120], "weight_storage": [5120, 5120], "output": [8192, 5120]}` | 24 | 429496729600/0 | 52428800/83886080/83886080 | `{}` |
| k_proj | `{"input": [8192, 5120], "weight_math": [5120, 1024], "weight_storage": [1024, 5120], "output": [8192, 1024]}` | 24 | 85899345920/0 | 10485760/83886080/16777216 | `{}` |
| v_proj | `{"input": [8192, 5120], "weight_math": [5120, 1024], "weight_storage": [1024, 5120], "output": [8192, 1024]}` | 24 | 85899345920/0 | 10485760/83886080/16777216 | `{}` |
| q_norm | `{"input": [327680, 128], "weight": [128], "output": [327680, 128]}` | 24 | 0/168099840 | 256/83886080/83886080 | `{"rsqrt": 327680}` |
| k_norm | `{"input": [65536, 128], "weight": [128], "output": [65536, 128]}` | 24 | 0/33619968 | 256/16777216/16777216 | `{"rsqrt": 65536}` |
| apply_rope | `{"Q": [1, 40, 8192, 128], "K": [1, 8, 8192, 128]}` | 24 | 0/150994944 | 0/104857600/100663296 | `{"negate": 25165824}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 8192, 128]}` | 24 | 0/0 | 0/33554432/33554432 | `{}` |
| qk | `{"Q": [1, 40, 8192, 128], "K_shared": [1, 8, 8192, 128], "scores_rectangular": [1, 40, 8192, 8192]}` | 24 | 343639326720/0 | 0/100663296/10737418240 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 40, 8192, 8192]}` | 24 | 0/5369036800 | 0/10737418240/10737418240 | `{"exp": 1342341120, "compare_max": 1342013440, "mask_decisions": 2684354560}` |
| pv | `{"P": [1, 40, 8192, 8192], "V_shared": [1, 8, 8192, 128], "output": [1, 40, 8192, 128]}` | 24 | 343639326720/0 | 0/10754195456/83886080 | `{}` |
| o_proj | `{"input": [8192, 5120], "weight_math": [5120, 5120], "weight_storage": [5120, 5120], "output": [8192, 5120]}` | 24 | 429496729600/0 | 52428800/83886080/83886080 | `{}` |
| attention_residual | `{"inputs_each": [8192, 5120], "output": [8192, 5120]}` | 24 | 0/41943040 | 0/167772160/83886080 | `{}` |
| post_attention_layernorm | `{"input": [8192, 5120], "weight": [5120], "output": [8192, 5120]}` | 24 | 0/167780352 | 10240/83886080/83886080 | `{"rsqrt": 8192}` |
| gate_proj | `{"input": [8192, 5120], "weight_math": [5120, 13952], "weight_storage": [13952, 5120], "output": [8192, 13952]}` | 24 | 1170378588160/0 | 142868480/83886080/228589568 | `{}` |
| up_proj | `{"input": [8192, 5120], "weight_math": [5120, 13952], "weight_storage": [13952, 5120], "output": [8192, 13952]}` | 24 | 1170378588160/0 | 142868480/83886080/228589568 | `{}` |
| silu_mul | `{"gate": [8192, 13952], "up": [8192, 13952], "output": [8192, 13952]}` | 24 | 0/457179136 | 0/457179136/228589568 | `{"exp": 114294784, "negate": 114294784}` |
| down_proj | `{"input": [8192, 13952], "weight_math": [13952, 5120], "weight_storage": [5120, 13952], "output": [8192, 5120]}` | 24 | 1170378588160/0 | 142868480/228589568/83886080 | `{}` |
| ffn_residual | `{"inputs_each": [8192, 5120], "output": [8192, 5120]}` | 24 | 0/41943040 | 0/167772160/83886080 | `{}` |
| final_norm | `{"input": [8192, 5120], "weight": [5120], "output": [8192, 5120]}` | 1 | 0/167780352 | 10240/83886080/83886080 | `{"rsqrt": 8192}` |
| lm_head | `{"input": [1, 5120], "weight_math": [5120, 151936], "weight_storage": [151936, 5120], "output": [1, 151936]}` | 1 | 1555824640/0 | 1555824640/10240/303872 | `{}` |

## less_kv_more_ffn_budget_match

工作与TP预算：`{"matrix_flops": 133594323353600, "scalar_flops": 190936915968, "all_unique_weight_bytes": 16381470720, "per_rank_weight_bytes": 8191043584, "aggregate_tp_weight_bytes": 16382087168, "norm_replication_extra_bytes": 616448, "kv_bytes_per_token_per_request": 36864, "per_rank_kv_bytes": 150994944, "per_rank_old_history_read_bytes": 0, "per_rank_kv_append_bytes": 150994944, "per_rank_new_kv_request_bytes": 150994944, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10489522176, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 90, "batch_fits": true, "sequential_decoder_layers": 36, "sequential_collectives": 72, "per_collective_activation_payload_bytes": 67108864, "per_rank_ring_wire_bytes_exact": "4831838208", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 8192], "table": [151936, 4096], "output": [8192, 4096]}` | 1 | 0/0 | 67108864/65536/67108864 | `{}` |
| rope_table | `{"frequencies": [8192, 64], "cos_sin_each": [8192, 128]}` | 1 | 0/524288 | 0/65792/4194304 | `{"sin": 1048576, "cos": 1048576}` |
| input_layernorm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 36 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| q_proj | `{"input": [8192, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [8192, 4096]}` | 36 | 274877906944/0 | 33554432/67108864/67108864 | `{}` |
| k_proj | `{"input": [8192, 4096], "weight_math": [4096, 256], "weight_storage": [256, 4096], "output": [8192, 256]}` | 36 | 17179869184/0 | 2097152/67108864/4194304 | `{}` |
| v_proj | `{"input": [8192, 4096], "weight_math": [4096, 256], "weight_storage": [256, 4096], "output": [8192, 256]}` | 36 | 17179869184/0 | 2097152/67108864/4194304 | `{}` |
| q_norm | `{"input": [262144, 128], "weight": [128], "output": [262144, 128]}` | 36 | 0/134479872 | 256/67108864/67108864 | `{"rsqrt": 262144}` |
| k_norm | `{"input": [16384, 128], "weight": [128], "output": [16384, 128]}` | 36 | 0/8404992 | 256/4194304/4194304 | `{"rsqrt": 16384}` |
| apply_rope | `{"Q": [1, 32, 8192, 128], "K": [1, 2, 8192, 128]}` | 36 | 0/106954752 | 0/75497472/71303168 | `{"negate": 17825792}` |
| kv_append | `{"new_K_and_V_each": [1, 2, 8192, 128]}` | 36 | 0/0 | 0/8388608/8388608 | `{}` |
| qk | `{"Q": [1, 32, 8192, 128], "K_shared": [1, 2, 8192, 128], "scores_rectangular": [1, 32, 8192, 8192]}` | 36 | 274911461376/0 | 0/71303168/8589934592 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 8192, 8192]}` | 36 | 0/4295229440 | 0/8589934592/8589934592 | `{"exp": 1073872896, "compare_max": 1073610752, "mask_decisions": 2147483648}` |
| pv | `{"P": [1, 32, 8192, 8192], "V_shared": [1, 2, 8192, 128], "output": [1, 32, 8192, 128]}` | 36 | 274911461376/0 | 0/8594128896/67108864 | `{}` |
| o_proj | `{"input": [8192, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [8192, 4096]}` | 36 | 274877906944/0 | 33554432/67108864/67108864 | `{}` |
| attention_residual | `{"inputs_each": [8192, 4096], "output": [8192, 4096]}` | 36 | 0/33554432 | 0/134217728/67108864 | `{}` |
| post_attention_layernorm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 36 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| gate_proj | `{"input": [8192, 4096], "weight_math": [4096, 12800], "weight_storage": [12800, 4096], "output": [8192, 12800]}` | 36 | 858993459200/0 | 104857600/67108864/209715200 | `{}` |
| up_proj | `{"input": [8192, 4096], "weight_math": [4096, 12800], "weight_storage": [12800, 4096], "output": [8192, 12800]}` | 36 | 858993459200/0 | 104857600/67108864/209715200 | `{}` |
| silu_mul | `{"gate": [8192, 12800], "up": [8192, 12800], "output": [8192, 12800]}` | 36 | 0/419430400 | 0/419430400/209715200 | `{"exp": 104857600, "negate": 104857600}` |
| down_proj | `{"input": [8192, 12800], "weight_math": [12800, 4096], "weight_storage": [4096, 12800], "output": [8192, 4096]}` | 36 | 858993459200/0 | 104857600/209715200/67108864 | `{}` |
| ffn_residual | `{"inputs_each": [8192, 4096], "output": [8192, 4096]}` | 36 | 0/33554432 | 0/134217728/67108864 | `{}` |
| final_norm | `{"input": [8192, 4096], "weight": [4096], "output": [8192, 4096]}` | 1 | 0/134225920 | 8192/67108864/67108864 | `{"rsqrt": 8192}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## 容量与通信切换条件

容量区间含两端；通信只覆盖声明的两类decoder collective，不代表完整请求时间。
- `{"variant": "shallower_same_width", "matrix_flops_delta": -6804033503232, "per_rank_weights_delta": -12785664, "per_rank_kv_delta": -201326592, "per_rank_live_budget_delta": -214112256, "capacity_interval_where_only_smaller_fits_bytes": [10728394752, 10942507007], "per_rank_ring_wire_delta_exact": "-1610612736", "sequential_collectives_delta": -24, "sequential_layers_delta": -12}`
- `{"variant": "deeper_same_width", "matrix_flops_delta": 6185558212608, "per_rank_weights_delta": -24963072, "per_rank_kv_delta": 201326592, "per_rank_live_budget_delta": 176363520, "capacity_interval_where_only_smaller_fits_bytes": [10942507008, 11118870527], "per_rank_ring_wire_delta_exact": "1610612736", "sequential_collectives_delta": 24, "sequential_layers_delta": 12}`
- `{"variant": "narrower_same_depth", "matrix_flops_delta": 231013089280, "per_rank_weights_delta": 4831232, "per_rank_kv_delta": -150994944, "per_rank_live_budget_delta": -146163712, "capacity_interval_where_only_smaller_fits_bytes": [10796343296, 10942507007], "per_rank_ring_wire_delta_exact": "-1207959552", "sequential_collectives_delta": 0, "sequential_layers_delta": 0}`
- `{"variant": "shallower_wider", "matrix_flops_delta": -8091809873920, "per_rank_weights_delta": 18509824, "per_rank_kv_delta": -201326592, "per_rank_live_budget_delta": -182816768, "capacity_interval_where_only_smaller_fits_bytes": [10759690240, 10942507007], "per_rank_ring_wire_delta_exact": "-805306368", "sequential_collectives_delta": -24, "sequential_layers_delta": -12}`
- `{"variant": "less_kv_more_ffn_budget_match", "matrix_flops_delta": 0, "per_rank_weights_delta": 0, "per_rank_kv_delta": -452984832, "per_rank_live_budget_delta": -452984832, "capacity_interval_where_only_smaller_fits_bytes": [10489522176, 10942507007], "per_rank_ring_wire_delta_exact": "0", "sequential_collectives_delta": 0, "sequential_layers_delta": 0}`

## 范围

- Only baseline is a released checkpoint. Variants are declared untrained architectures; no equal quality or numerical equivalence is asserted.
- Untied embedding/head, no biases, fixed head_dim=128, vocabulary/context and Q/K norms retained from official Qwen3-8B config.
- FFN is nearest positive aligned solution to the same parameter target; exact signed error and half-grid bound are reported. Exact equality depends on alignment; use the reported exact_equal_parameters flag.
- FMA=2, effective causal attention and source logical scalar counts. Operator reads/writes are semantic operands, not measured HBM.
- BF16 weights/activations/KV; score and scalar intermediate precision remains Scenario contract. No low-bit checkpoint claim.
- TP uses complete divisible KV heads; normalization parameters replicate. Uniform equal-length requests, no prefix sharing, no PP/EP. Workspace is a fixed per-rank input budget, not a derived peak.
- Ring bytes and sequential collectives quantify only two decoder collectives per layer. For that subpath declared service is bytes/effective_link_rate + collectives/startup_rate; no hardware rates are invented or whole-request latency inferred.
- Capacity flip interval is inclusive and applies to the declared batch and workspace. Matrix FLOPs, serial depth and communication changes cannot establish a quality-constrained winner alone.

## 固定基线来源

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json) SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json) SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py) SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py) SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`
